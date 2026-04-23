import socket
import threading
from protocol import receive_message, encode_message

# Configuration
HOST = '127.0.0.1'
PORT = 5050

# State
clients = {} # {username: {"sock": socket, "room": "general"}}
clients_lock = threading.Lock() # OS Concept: Mutex/Lock for Synchronization

def handle_client(conn, addr):
    """
    OS Concept: Multithreading.
    This function runs in a separate thread for each connected client.
    """
    print(f"[NEW CONNECTION] {addr} connected")
    username = None
    room = "general"

    try:
        # First message must be the join presence with username
        initial_msg = receive_message(conn)
        if initial_msg and initial_msg.get("type") == "presence":
            username = initial_msg.get("sender")
            room = initial_msg.get("room", "general")
            
            with clients_lock: # Protect shared resource
                if username in clients:
                    # Basic auth check (no duplicate names)
                    error_msg = encode_message("system", "Server", "Username already taken. Please reconnect with a different name.", room)
                    conn.sendall(error_msg)
                    return
                
                clients[username] = {"sock": conn, "room": room}
            
            print(f"[{addr}] User joined as {username} in room {room}")
            broadcast(encode_message("system", "Server", f"{username} has joined the chat!", room), room)
            
            # Send welcome message
            welcome = encode_message("system", "Server", f"Welcome {username}! You are in '{room}'.", room)
            conn.sendall(welcome)

        else:
            # Invalid initial protocol (could be a port scan, ngrok health check, or browser)
            if initial_msg is not None:
                print(f"[PROTOCOL ERROR] Invalid initial message from {addr}: {initial_msg}")
            return

        # Main message loop
        while True:
            msg = receive_message(conn)
            if msg is None:
                break # Client disconnected

            msg_type = msg.get("type")
            sender = msg.get("sender")
            content = msg.get("content")
            
            # Handle room change
            if content.startswith("/join "):
                new_room = content.split(" ", 1)[1]
                
                with clients_lock:
                    clients[username]["room"] = new_room
                
                broadcast(encode_message("system", "Server", f"{username} has left the room.", room), room)
                room = new_room
                broadcast(encode_message("system", "Server", f"{username} has joined the room.", room), room)
                
                confirm = encode_message("system", "Server", f"You joined room: {room}", room)
                conn.sendall(confirm)
                continue

            # Check for private message (e.g. content starts with @username)
            if content.startswith("@"):
                parts = content.split(" ", 1)
                if len(parts) > 1:
                    target_user = parts[0][1:] # Remove @
                    private_msg_content = parts[1]
                    send_private_message(sender, target_user, private_msg_content)
                else:
                    err = encode_message("system", "Server", "Invalid private message format. Use @username msg", room)
                    conn.sendall(err)
            else:
                # Regular broadcast to room
                print(f"[{room}] {sender}: {content}")
                out_msg = encode_message("chat", sender, content, room)
                broadcast(out_msg, room)

    except ConnectionResetError:
        pass # Client forcibly closed
    except Exception as e:
        print(f"[ERROR] Exception handling client {username}: {e}")
    finally:
        # OS Concept: Graceful Disconnect & Resource Cleanup
        if username:
            with clients_lock:
                if username in clients:
                    del clients[username]
            print(f"[DISCONNECT] {username} disconnected.")
            broadcast(encode_message("system", "Server", f"{username} has left the chat.", room), room)
        conn.close()

def broadcast(message_bytes, target_room):
    """ Sends a message to all clients in a specific room. """
    with clients_lock:
        for user, info in list(clients.items()):
            if info["room"] == target_room:
                try:
                    info["sock"].sendall(message_bytes)
                except:
                    # Assume disconnected; cleanup will be handled by the client's thread
                    pass

def send_private_message(sender, target_user, content):
    """ Sends a message to a specific user. """
    with clients_lock:
        if target_user in clients:
            try:
                # Send to target
                msg = encode_message("chat", sender, f"(Private) {content}", clients[target_user]["room"])
                clients[target_user]["sock"].sendall(msg)
                
                # Send echo back to sender
                if sender in clients:
                    echo_msg = encode_message("chat", sender, f"(Private to {target_user}) {content}", clients[sender]["room"])
                    clients[sender]["sock"].sendall(echo_msg)
            except:
                pass
        else:
            if sender in clients:
                err = encode_message("system", "Server", f"User {target_user} is not online.", clients[sender]["room"])
                clients[sender]["sock"].sendall(err)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # OS Concept: Resource Allocation (Allowing port reuse immediately after termination)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    print(f"[STARTING] Server is listening on {HOST}:{PORT}")
    
    try:
        while True:
            conn, addr = server.accept()
            # OS Concept: Process Management & Multithreading (Daemon threads close when main exits)
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
