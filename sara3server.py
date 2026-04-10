import socket
import threading
import time
import random
import sys

# Initialize server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = '172.19.51.160'  #my server's IP
SERVER_PORT = 5689
server_socket.bind((SERVER_IP, SERVER_PORT))

print(f"Server is running on IP: {SERVER_IP}, Port: {SERVER_PORT}")

# Data structures
Activeclients = {}  
point_Struct = {}  
question_Struct = [  
    ("What is the capital of France?", "Paris"),
    ("What is 2 + 2?", "4"),
    ("5 + 6?", "11"),
    ("2 * 5?", "10"),
    ("What is the chemical symbol for water?", "H2O"),
    ("How many continents are there on Earth?", "7"),
    ("What is the smallest prime number?", "2"),
    ("In which year did World War II end?", "1945"),
    ("What is the square root of 81?", "9"),
    ("What is the longest river in the world?", "Amazon"),
]
Selectedquestions_Struct = [] 


def main_clients():
    while True:
        data, addr = server_socket.recvfrom(4096)
        client_message = data.decode().strip()

        if client_message.lower() == "exit":
            if addr in Activeclients:
                print(f"Client {Activeclients[addr]} ({addr}) has left the game.")
                del Activeclients[addr]
                del point_Struct[addr]
                server_socket.sendto("You have left the game.".encode(), addr)
        elif addr not in Activeclients:
            Activeclients[addr] = client_message
            point_Struct[addr] = 0  # Initialize score
            print(f"{client_message} ({addr}) joined the game.")
            server_socket.sendto(f"Welcome {client_message}! Waiting for the game to start...".encode(), addr)

threading.Thread(target=main_clients, daemon=True).start()

print("Waiting for clients to join...")

try:
    # Main game loop
    while True:
        while len(Activeclients) < 2:
            print("Waiting for at least 2 clients to start the game...")
            time.sleep(5)
            continue

        # Select N random questions
        N = 5
        Selectedquestions_Struct = random.sample(question_Struct, N)
        print("Round starting...")
        for addr in Activeclients:
            server_socket.sendto("Round starting in 1 minute! GET READY!".encode(), addr)
        time.sleep(60)

        # Ask each question
        for i, (question, correct_answer) in enumerate(Selectedquestions_Struct, start=1):
            # Broadcast the question
            for addr in Activeclients:
                server_socket.sendto(f"Question {i}: {question}".encode(), addr)
            print(f"Broadcasted Question {i}: {question}")

            C_Struct = [] 
            start_time = time.time()

            while time.time() - start_time < 90:  
                try:
                    server_socket.settimeout(1)
                    data, addr = server_socket.recvfrom(1024)
                    answer = data.decode().strip()

                    if addr in Activeclients and addr not in C_Struct:  # Only process the first answer
                        C_Struct.append(addr)  # Mark client as having answered
                        is_correct = answer.lower() == correct_answer.lower()

                        if is_correct:
                            time_taken = time.time() - start_time
                            points = round(10 / time_taken, 2)
                            point_Struct[addr] += points
                            print(f"player{Activeclients[addr]} ({addr}) answered: {answer} - Correct! +{points:.2f} points")
                        else:
                            print(f"player {Activeclients[addr]} ({addr}) answered: {answer} - Incorrect")
                    else:
                        print(f"Ignored subsequent answer from {Activeclients.get(addr, 'Unknown')} ({addr})")
                except socket.timeout:
                    continue

            # Broadcast the correct answer
            for addr in Activeclients:
                server_socket.sendto(f"Correct answer: {correct_answer}".encode(), addr)

        # End of round: Announce leaderboard
        leaderboard = sorted(point_Struct.items(), key=lambda x: x[1], reverse=True)
        leaderboard_message = "totalscore:\n" + "\n".join([f"{Activeclients[addr]}: {score:.2f}" for addr, score in leaderboard])
        for addr in Activeclients:
            server_socket.sendto(leaderboard_message.encode(), addr)

        # Announce the leading player
        leading_player = leaderboard[0]
        for addr in Activeclients:
            server_socket.sendto(f"Winning player: {Activeclients[leading_player[0]]}".encode(), addr)

        print("Round ended!")
        print(leaderboard_message)

        # Wait before the next round
        print("Next round will start in 30 seconds...")
        time.sleep(30)

except KeyboardInterrupt:
    print("\nServer is shutting down...")
    for addr in Activeclients:
        server_socket.sendto("Server is shutting down. Goodbye!".encode(), addr)
    sys.exit(0)
