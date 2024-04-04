#include <Windows.h>
#include <Winioctl.h>
#include <iostream>
using namespace std;
void deleteFolder_File(LPCWSTR drivePath, long long startOffSet_Byte = 0)
{
    DWORD bytesRead;
    DWORD bufSize = 1024;
    BYTE buffer[1024];

//handle để đọc lấy buffer
    HANDLE hDeviceRead = CreateFileW(drivePath,                          // Drive to open
                                 GENERIC_READ,                       // Access mode
                                 FILE_SHARE_READ | FILE_SHARE_WRITE, // Share Mode
                                 NULL,                               // Security Descriptor
                                 OPEN_EXISTING,                      // How to create
                                 0,                                  // File attributes
                                 NULL);                              // Handle to template

    if (hDeviceRead == INVALID_HANDLE_VALUE)
    {
        cout << "Error opening drive to read: " << GetLastError() << endl;
        return;
    }
    LARGE_INTEGER liRead;

    liRead.QuadPart = startOffSet_Byte;
    if (!SetFilePointerEx(hDeviceRead, liRead, NULL, FILE_BEGIN))
    {
        cout << "Error setting file pointer to the MFT entry offset: " << GetLastError() << std::endl;
        CloseHandle(hDeviceRead);
        return;
    }

    if (!ReadFile(hDeviceRead, buffer, bufSize, &bytesRead, NULL) || bytesRead != sizeof(buffer))
    {
        cout << "Error reading MFT entry: " << GetLastError() << std::endl;
        CloseHandle(hDeviceRead);
        return;
    }
    CloseHandle(hDeviceRead);

// mở handle để ghi
    HANDLE hDeviceWrite = CreateFileW(
        drivePath,
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        0,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        0);

    if (hDeviceWrite == INVALID_HANDLE_VALUE)
    {
        cerr << "Error opening drive: " << GetLastError() << std::endl;
        return;
    }
    DWORD bytesReturned;

//dismount
    BOOL result = DeviceIoControl(
        hDeviceWrite,               // Handle to the volume
        FSCTL_DISMOUNT_VOLUME, // Dismount control code
        NULL,                  // No input buffer
        0,                     // Input buffer size
        NULL,                  // No output buffer
        0,                     // Output buffer size
        &bytesReturned,        // Bytes returned
        NULL                   // No overlap
        );

    if (buffer[0x16] == 0x1)
    {
        buffer[0x16] = 0x0;
    }
    else if (buffer[0x16] == 0x3)
    {
        buffer[0x16] = 0x2;
    }

    LARGE_INTEGER liWrite;
    //0
    liWrite.QuadPart = startOffSet_Byte;
    if (!SetFilePointerEx(hDeviceWrite, liWrite, 0, FILE_BEGIN))
    {
        cerr << "Error setting file pointer: " << GetLastError() << std::endl;
        CloseHandle(hDeviceWrite);
        return;
    }
    
    DWORD bytesWritten;
    if (!WriteFile(hDeviceWrite, buffer, bufSize, &bytesWritten, NULL))
    {
        cerr << "Error writing to drive: " << GetLastError() << std::endl;
        CloseHandle(hDeviceWrite);
        return;
    }
    CloseHandle(hDeviceWrite);
}
long long convertToInt(const std::string& s) {
    return std::stoll(s);
}
int main(int argc, char* argv[]) {
    // // path offset 
    cout << "Path: " << argv[1] << endl;
    cout << "Offset: 0x" << hex << convertToInt(argv[2]) << endl;
    deleteFolder_File(L"\\\\.\\" + *argv[1], convertToInt(argv[2]));
    return 0;
}