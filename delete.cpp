#include <Windows.h>
#include <Winioctl.h>
#include <iostream>
#include <string>
using namespace std;

void deleteNFTS(LPCWSTR folder_path, long long offset = 0, int entry_size = 512) {
    DWORD read;
    DWORD size = entry_size * 2;
    BYTE buffer[entry_size * 2];

    HANDLE hRead = CreateFileW(folder_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);

    if (hRead == INVALID_HANDLE_VALUE) {
        return;
    }
    LARGE_INTEGER liRead;

    liRead.QuadPart = offset;
    if (!SetFilePointerEx(hRead, liRead, NULL, FILE_BEGIN)) {
        CloseHandle(hRead);
        return;
    }

    if (!ReadFile(hRead, buffer, size, &read, NULL) || read != sizeof(buffer)) {
        CloseHandle(hRead);
        return;
    }
    CloseHandle(hRead);

    HANDLE hWrite = CreateFileW(folder_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

    if (hWrite == INVALID_HANDLE_VALUE) {
        return;
    }
    DWORD bytesReturned;

    // Dismount
    BOOL result = DeviceIoControl(hWrite, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);

    // File
    if (buffer[0x16] == 0x1) {
        buffer[0x16] = 0x0;
    }
    // Folder
    else if (buffer[0x16] == 0x3) {
        buffer[0x16] = 0x2;
    }

    LARGE_INTEGER liWrite;

    liWrite.QuadPart = offset;
    if (!SetFilePointerEx(hWrite, liWrite, 0, FILE_BEGIN)) {
        CloseHandle(hWrite);
        return;
    }

    DWORD bytesWritten;
    if (!WriteFile(hWrite, buffer, size, &bytesWritten, NULL)) {
        CloseHandle(hWrite);
        return;
    }
    
    CloseHandle(hWrite);
}

void deleteFAT32(LPCWSTR folder_path, long long offset = 0) {
    DWORD read;
    DWORD size = 32;
    BYTE buffer[32];

    HANDLE hRead = CreateFileW(folder_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);

    if (hRead == INVALID_HANDLE_VALUE) {
        return;
    }
    LARGE_INTEGER liRead;

    liRead.QuadPart = offset;
    if (!SetFilePointerEx(hRead, liRead, NULL, FILE_BEGIN)) {
        CloseHandle(hRead);
        return;
    }

    if (!ReadFile(hRead, buffer, size, &read, NULL) || read != sizeof(buffer)) {
        CloseHandle(hRead);
        return;
    }
    CloseHandle(hRead);

    HANDLE hWrite = CreateFileW(folder_path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0);

    if (hWrite == INVALID_HANDLE_VALUE) {
        return;
    }
    DWORD bytesReturned;

    // Dismount
    BOOL result = DeviceIoControl(hWrite, FSCTL_DISMOUNT_VOLUME, NULL, 0, NULL, 0, &bytesReturned, NULL);

    buffer[0x0] = 0xE5;

    LARGE_INTEGER liWrite;

    liWrite.QuadPart = offset;
    if (!SetFilePointerEx(hWrite, liWrite, 0, FILE_BEGIN)) {
        CloseHandle(hWrite);
        return;
    }

    DWORD bytesWritten;
    if (!WriteFile(hWrite, buffer, size, &bytesWritten, NULL)) {
        CloseHandle(hWrite);
        return;
    }
    
    CloseHandle(hWrite);
}

long long convertToInt(const string& s) {
    return stoll(s);
}

wstring convertToWideString(const char* str) {
    wstring wideStr;
    if (str != nullptr) {
        int numChars = MultiByteToWideChar(CP_UTF8, 0, str, -1, nullptr, 0);
        if (numChars > 0) {
            wideStr.resize(numChars);
            MultiByteToWideChar(CP_UTF8, 0, str, -1, &wideStr[0], numChars);
        }
    }
    return wideStr;
}

// int main(int argc, char* argv[]) {
//     wstring volume = L"\\\\.\\" + convertToWideString(argv[1]);
//     if (strcmp(argv[3], "0") == 0) {
//         deleteNFTS(volume.c_str(), convertToInt(argv[2]), stoi(argv[4]));
//     }
//     else if (strcmp(argv[3], "1") == 0) {
//         deleteFAT32(volume.c_str(), convertToInt(argv[2]));
//     }
//     return 0;
// }

int main(int argc, char* argv[]) {
    deleteFAT32(L"\\\\.\\E:", 12583712);
    return 0;
}