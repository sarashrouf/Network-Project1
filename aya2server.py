import socket
import os
from urllib.parse import parse_qs

#_________________________________________________________________________________
# Server configuration
PORT = 5698
HTML_DIR = 'html_pages'  # Directory containing HTML files
MEDIA_DIR = 'media_files'  # Directory containing media files (like images)

#_________________________________________________________________________________
# Create and configure the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', PORT))
server_socket.listen(5)

print(f"Server is running on port: {PORT}")
print(f"Serving HTML files from directory: {HTML_DIR}")

#_________________________________________________________________________________
# Function to handle incoming requests
def handle_request(client_socket):
    """
    Reads the client request, determines the requested file,
    and sends the appropriate HTTP response.
    """
    request = client_socket.recv(1024).decode()  # Read up to 1024 bytes
    print(f"Request received:\n{request}")       
    if not request:
        response = "HTTP/1.1 400 Bad Request\nContent-Type: text/html\n\n" \
                   "<html><body><h1>Error 400</h1><p>Bad Request</p></body></html>"
        client_socket.sendall(response.encode())  # Send Bad Request response
        client_socket.close()  # Close the connection
        return

    try:
        method, path, _ = request.split(' ', 2)  # Extract the method, path, and protocol from the request
        print(f"Method: {method}, Path: {path}, Protocol: {_}")  # Log request details
    except ValueError:
        response = "HTTP/1.1 400 Bad Request\nContent-Type: text/html\n\n" \
                   "<html><body><h1>Error 400</h1><p>Bad Request: Missing or malformed request</p></body></html>"
        client_socket.sendall(response.encode())  # Send Bad Request response
        client_socket.close()  # Close the connection
        return

    #_________________________________________________________________________________
    # Handle GET requests

    # If the path starts with '/search', handle the search functionality
    if path.startswith('/search'):
        query = parse_qs(path.split('?', 1)[1]).get('query', [''])[0]

        if not query:
            response = "HTTP/1.1 400 Bad Request\nContent-Type: text/html\n\n" \
                       "<html><body><h1>Error 400</h1><p>No query provided.</p></body></html>"
            client_socket.sendall(response.encode())
            client_socket.close()
            return

        file_path = os.path.join(MEDIA_DIR, query)
        _, extension = os.path.splitext(file_path)
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.mp4': 'video/mp4',
        }
        content_type = content_types.get(extension, 'application/octet-stream')

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as media_file:
                media_data = media_file.read()
            response_headers = f"HTTP/1.1 200 OK\nContent-Type: {content_type}\nContent-Length: {len(media_data)}\n\n"
            client_socket.sendall(response_headers.encode() + media_data)
        else:
            if content_type.startswith('video/'):
                youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                response = f"HTTP/1.1 307 Temporary Redirect\nLocation: {youtube_url}\n\n"
                client_socket.sendall(response.encode())
            else:
                google_url = f"https://www.google.com/search?tbm=isch&q={query.replace(' ', '+')}"
                response = f"HTTP/1.1 307 Temporary Redirect\nLocation: {google_url}\n\n"
                client_socket.sendall(response.encode())

        client_socket.close()  # Close the connection
        return

    #_________________________________________________________________________________
    # Default behavior for other requests (HTML and CSS files)
    file_mapping = {
        '/main_en.html': 'main_en.html',
        '/': 'main_en.html',
        '/index.html': 'main_en.html',
        '/en': 'main_en.html',
        '/main_ar.html': 'main_ar.html',
        '/ar': 'main_ar.html',
        '/supporting_material_en.html': 'supporting_material_en.html',
        '/supporting_material_ar.html': 'supporting_material_ar.html',
    }

    if path.endswith('.css'):
        file_path = path.lstrip('/')  # Directly map CSS requests
        full_path = os.path.join(HTML_DIR, file_path)
    else:
        file_path = file_mapping.get(path, '404.html')
        full_path = os.path.join(HTML_DIR, file_path)

    if os.path.exists(full_path):
        _, extension = os.path.splitext(full_path)
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
        }
        content_type = content_types.get(extension, 'text/plain')

        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        response = f"HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n{content}"
    else:
        response = "HTTP/1.1 404 Not Found\nContent-Type: text/html\n\n" \
                   "<html><body><h1>Error 404</h1>" \
                   "<p style='color: red;'>The file is not found</p></body></html>"

    client_socket.sendall(response.encode())
    client_socket.close()

#_________________________________________________________________________________
# Main loop to continuously listen for client connections
while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")
    handle_request(client_socket)
