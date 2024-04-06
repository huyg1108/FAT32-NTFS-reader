#include <Windows.h>
#include <Winioctl.h>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
using namespace std;

void deleteNFTS(LPCWSTR folder_path, long long offset = 0, int entry_size = 512)
{
    DWORD read;
    DWORD size = entry_size * 2;
    BYTE buffer[entry_size * 2];

    HANDLE hRead = CreateFileW(folder_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);

    if (hRead == INVALID_HANDLE_VALUE)
    {
        return;
    }
    LARGE_INTEGER liRead;

    liRead.QuadPart = offset;
    if (!SetFilePointerEx(hRead, liRead, NULL, FILE_BEGIN))
    {
        CloseHandle(hRead);
        return;
    }

    if (!ReadFile(hRead, buffer, size, &read, NULL) || read != sizeof(buffer))
    {
        CloseHandle(hRead);
        return;
    }
    CloseHandle(hRead);

    HANDLE hWrite = CreateFileW(folder_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

    if (hWrite == INVALID_HANDLE_VALUE)
    {
        return;
    }
    DWORD bytesReturned;

    // Dismount
    BOOL result = DeviceIoControl(hWrite, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);

    // File
    if (buffer[0x16] == 0x1)
    {
        buffer[0x16] = 0x0;
    }
    // Folder
    else if (buffer[0x16] == 0x3)
    {
        buffer[0x16] = 0x2;
    }

    LARGE_INTEGER liWrite;

    liWrite.QuadPart = offset;
    if (!SetFilePointerEx(hWrite, liWrite, 0, FILE_BEGIN))
    {
        CloseHandle(hWrite);
        return;
    }

    DWORD bytesWritten;
    if (!WriteFile(hWrite, buffer, size, &bytesWritten, NULL))
    {
        CloseHandle(hWrite);
        return;
    }

    CloseHandle(hWrite);
}

void restoreNFTS(LPCWSTR folder_path, long long offset = 0, int entry_size = 1024)
{
    DWORD read;
    DWORD size = entry_size;
    BYTE buffer[entry_size];

    HANDLE hRead = CreateFileW(folder_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);

    if (hRead == INVALID_HANDLE_VALUE)
    {
        return;
    }
    LARGE_INTEGER liRead;

    liRead.QuadPart = offset;
    if (!SetFilePointerEx(hRead, liRead, NULL, FILE_BEGIN))
    {
        CloseHandle(hRead);
        return;
    }

    if (!ReadFile(hRead, buffer, size, &read, NULL) || read != sizeof(buffer))
    {
        CloseHandle(hRead);
        return;
    }
    CloseHandle(hRead);

    HANDLE hWrite = CreateFileW(folder_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

    if (hWrite == INVALID_HANDLE_VALUE)
    {
        return;
    }
    DWORD bytesReturned;

    // Dismount
    BOOL result = DeviceIoControl(hWrite, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);

    int flag = (int) buffer[0x16];
    
    // File
    if (flag == 0)
    {
        buffer[0x16] = 0x1;
    }
    // Folder
    else if (flag == 2)
    {
        buffer[0x16] = 0x3;
    }

    LARGE_INTEGER liWrite;

    liWrite.QuadPart = offset;
    if (!SetFilePointerEx(hWrite, liWrite, 0, FILE_BEGIN))
    {
        CloseHandle(hWrite);
        return;
    }

    DWORD bytesWritten;
    if (!WriteFile(hWrite, buffer, size, &bytesWritten, NULL))
    {
        CloseHandle(hWrite);
        return;
    }

    CloseHandle(hWrite);
}


void adjustByteFAT32(LPCWSTR folder_path, long long offset, long long value = 0xE5)
{
    DWORD read;
    DWORD size = 512;
    BYTE buffer[512];
    // Open file for reading
    HANDLE hRead = CreateFileW(folder_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
    if (hRead == INVALID_HANDLE_VALUE)
    {
        // std::cerr << "1 Failed to open file for reading. Error code: " << GetLastError() << std::endl;
        return;
    }
    LARGE_INTEGER liRead;
    liRead.QuadPart = offset / size * size;

    // std::cerr << "afsdjlk; Failed to set file pointer for reading. Error code: " << GetLastError() << std::endl;

    // Set file pointer to the desired offset
    if (SetFilePointerEx(hRead, liRead, NULL, FILE_BEGIN) == 0)
    {
        // std::cerr << "2 Failed to set file pointer for reading. Error code: " << GetLastError() << std::endl;
        CloseHandle(hRead);
        return;
    }

    // Read data from file

    if (!ReadFile(hRead, buffer, size, &read, NULL) || read != size)
    {
        // std::cerr << "3 Failed to read from file. Error code: " << GetLastError() << std::endl;
        CloseHandle(hRead);
        return;
    }

    HANDLE hWrite = CreateFileW(folder_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

    if (hWrite == INVALID_HANDLE_VALUE)
    {
        // std::cerr << "Failed to open volume for writing. Error code: " << GetLastError() << std::endl;
        return;
    }
    DWORD bytesReturned;

    // Dismount
    BOOL result = DeviceIoControl(hWrite, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);

    buffer[offset % size] = value;

    LARGE_INTEGER liWrite;

    liWrite.QuadPart = offset / size * size;
    if (!SetFilePointerEx(hWrite, liWrite, 0, FILE_BEGIN))
    {
        // std::cerr << "Failed to set file pointer for writing. Error code: " << GetLastError() << std::endl;
        CloseHandle(hWrite);
        return;
    }

    DWORD bytesWritten;
    if (!WriteFile(hWrite, buffer, size, &bytesWritten, NULL))
    {
        // std::cerr << "Failed to write to volume. Error code: " << GetLastError() << std::endl;
        CloseHandle(hWrite);
        return;
    }
    CloseHandle(hWrite);
}

long long convertToInt(const string &s)
{
    return stoll(s);
}

wstring convertToWideString(const char *str)
{
    wstring wideStr;
    if (str != nullptr)
    {
        int numChars = MultiByteToWideChar(CP_UTF8, 0, str, -1, nullptr, 0);
        if (numChars > 0)
        {
            wideStr.resize(numChars);
            MultiByteToWideChar(CP_UTF8, 0, str, -1, &wideStr[0], numChars);
        }
    }
    return wideStr;
}
// slipt the command line arguments
vector<pair<int,int>> splitArgs(char* s)
{
    vector<pair<int,int>> res;
    string str = s;
    stringstream ss(str);
    string token;
    while (getline(ss, token, ' '))
    {
        int offset = stoi(token);
        getline(ss, token, ' ');
        int value = stoi(token);
        res.push_back({offset, value});
    }
    return res;
}

// NTFS DELETE : delete.exe <volume> DEL NTFS
// NTFS RESTORE : delete.exe <volume> RESTORE NTFS
// FAT32 DELETE : delete.exe <volume> DEL FAT32 <offset1>  <value1> <offset2> <value2> ...
// FAT32 RESTORE : delete.exe <volume> RESTORE FAT32 <offset1> <value1> <offset2> <value2> ...

int main(int argc, char *argv[])
{
    wstring volume = L"\\\\.\\" + convertToWideString(argv[1]);
    if (strcmp(argv[2], "DEL") == 0)
    {
        if (strcmp(argv[3], "NTFS") == 0)
        {
            deleteNFTS(volume.c_str(), convertToInt(argv[4]), stoi(argv[5]));
        }
        else if (strcmp(argv[3], "FAT32") == 0)
        {
            for (int i = 4; i < argc; i += 2)
                adjustByteFAT32(volume.c_str(), convertToInt(argv[i]));
        }
    }
    else if (strcmp(argv[2], "RESTORE") == 0)
    {
        if (strcmp(argv[3], "NTFS") == 0)
        {
            restoreNFTS(volume.c_str(), convertToInt(argv[4]), stoi(argv[5]));
        }
        else if (strcmp(argv[3], "FAT32") == 0)
        {
            vector<pair<int,int>> args = splitArgs(argv[4]);
            for (auto arg : args)
            {
                adjustByteFAT32(volume.c_str(), arg.first, arg.second);
            }
        }
    }
    return 0;
}