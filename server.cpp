#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <queue>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT 12345

using namespace std;

unordered_map<SOCKET, string> clients;
unordered_map<SOCKET, SOCKET> opponent;
queue<SOCKET> waitingQueue;
CRITICAL_SECTION cs;

DWORD WINAPI handle_client(LPVOID lpParameter) {
    SOCKET client_socket = (SOCKET)lpParameter;
    char buffer[1024];
    string username;

    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        username = string(buffer);
    }

    EnterCriticalSection(&cs);
    clients[client_socket] = username;
    waitingQueue.push(client_socket);
    LeaveCriticalSection(&cs);

    while (true) {
        ZeroMemory(buffer, sizeof(buffer));
        bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
        if (bytes_received <= 0) {
            cerr << client_socket << " left" << endl;
            break;
        }

        buffer[bytes_received] = '\0';
        string data(buffer);
        
        EnterCriticalSection(&cs);
        string message = data + "\n";
        send(opponent[client_socket], message.c_str(), message.size(), 0);
        LeaveCriticalSection(&cs);
    }

    EnterCriticalSection(&cs);
    clients.erase(client_socket);
    LeaveCriticalSection(&cs);
    closesocket(client_socket);
    return 0;
}
DWORD WINAPI match_maker(LPVOID lpParameter) {
    while (true) {
        EnterCriticalSection(&cs);
        if (waitingQueue.size() >= 2) {
            SOCKET player1 = waitingQueue.front();
            waitingQueue.pop();
            SOCKET player2 = waitingQueue.front();
            waitingQueue.pop();

            string start_message = "START:" + clients[player1] + ", " + clients[player2] + "\n";

            opponent[player1] = player2;
            opponent[player2] = player1;

            send(player1, start_message.c_str(), start_message.size(), 0);
            send(player2, start_message.c_str(), start_message.size(), 0);
        }
        LeaveCriticalSection(&cs);
        Sleep(100);
    }
    return 0;
}


int main() {
    WSADATA wsaData;
    int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (result != 0) {
        return 1;
    }

    SOCKET server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server_socket == INVALID_SOCKET) {
        WSACleanup();
        return 1;
    }

    sockaddr_in server_addr;
    ZeroMemory(&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_socket, (sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR) {
        closesocket(server_socket);
        WSACleanup();
        return 1;
    }

    if (listen(server_socket, SOMAXCONN) == SOCKET_ERROR) {
        closesocket(server_socket);
        WSACleanup();
        return 1;
    }

    cout << "Server listening on port " << PORT << endl;

    InitializeCriticalSection(&cs);

    CreateThread(NULL, 0, match_maker, NULL, 0, NULL);

    while (true) {
        sockaddr_in client_addr;
        int client_addr_size = sizeof(client_addr);
        SOCKET client_socket = accept(server_socket, (sockaddr*)&client_addr, &client_addr_size);
        if (client_socket == INVALID_SOCKET) {
            continue;
        }

        CreateThread(NULL, 0, handle_client, (LPVOID)client_socket, 0, NULL);
        cout << client_socket << " joined as " << clients[client_socket] << endl;
    }

    DeleteCriticalSection(&cs);
    closesocket(server_socket);
    WSACleanup();
    return 0;
}
