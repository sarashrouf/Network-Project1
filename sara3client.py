import socket
import threading

DEFAULT_SERVER_IP = "172.19.51.160"
DEFAULT_SERVER_PORT = 5689
BUFFER_SIZE = 1024


def receive_messages(client_socket):
    """Listen for messages from the server."""
    while True:
        try:
            message = client_socket.recv(BUFFER_SIZE).decode()
            print(message)
        except Exception as e:
            print(f"Disconnected from server: {e}")
            break


def main():
    print("Welcome to the Game!")
    server_ip = input(f"Enter server IP : ").strip() or DEFAULT_SERVER_IP
    server_port = input(f"Enter server port : ").strip()
    server_port = int(server_port) if server_port.isdigit() else DEFAULT_SERVER_PORT

    username = input("Enter your username: ").strip()
    if not username:
        print("Username cannot be empty. Exiting.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        client_socket.sendto(username.encode(), (server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    try:
        while True:
            answer = input("Your answer (or 'exit' to quit): ").strip()
            if answer.lower() == 'exit':
                print("Exiting game.")
                break
            client_socket.sendto(answer.encode(), (server_ip, server_port))
    except KeyboardInterrupt:
        print("\nExiting game.")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
