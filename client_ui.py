import streamlit as st
import socket
import threading
import time
from protocol import encode_message, receive_message

# Streamlit Page Config
st.set_page_config(page_title="SyncSphere", page_icon="🌐")
st.title("🌐 SyncSphere")
st.markdown("A real-time multi-user communication system demonstrating OS Concepts.")

# Initialize Session State
if 'sock' not in st.session_state:
    st.session_state.sock = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'room' not in st.session_state:
    st.session_state.room = "general"

def receive_thread():
    """
    Background thread to listen for incoming socket messages.
    OS Concept: Multithreading in the client to prevent blocking the UI.
    """
    while st.session_state.connected and st.session_state.sock:
        try:
            msg = receive_message(st.session_state.sock)
            if msg:
                st.session_state.messages.append(msg)
        except Exception as e:
            print(f"Receive error: {e}")
            st.session_state.connected = False
            st.session_state.sock.close()
            st.session_state.sock = None
            break

# Sidebar for Connection / Authentication
with st.sidebar:
    st.header("Connection Settings")
    if not st.session_state.connected:
        server_ip = st.text_input("Server IP (or Host:Port)", value="127.0.0.1", help="e.g., 127.0.0.1, 192.168.1.5, or 0.tcp.ngrok.io:12345")
        username_input = st.text_input("Username", max_chars=20)
        room_input = st.text_input("Room", value="general")
        
        if st.button("Connect"):
            if username_input.strip() == "":
                st.error("Please enter a username.")
            else:
                try:
                    # OS Concept: Socket Initialization (IPC Endpoint)
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # Parse host and port if provided (e.g., for ngrok tcp)
                    host = server_ip
                    port = 5050
                    if ":" in server_ip:
                        parts = server_ip.split(":", 1)
                        host = parts[0]
                        port = int(parts[1])
                        
                    client_socket.connect((host, port))
                    
                    st.session_state.sock = client_socket
                    st.session_state.connected = True
                    st.session_state.username = username_input
                    st.session_state.room = room_input
                    
                    # Send initial presence message
                    presence_msg = encode_message("presence", st.session_state.username, "joined", st.session_state.room)
                    st.session_state.sock.sendall(presence_msg)
                    
                    # Start listener thread with Streamlit context so it can access st.session_state
                    listener = threading.Thread(target=receive_thread, daemon=True)
                    from streamlit.runtime.scriptrunner import add_script_run_ctx
                    add_script_run_ctx(listener)
                    listener.start()
                    
                    st.success("Connected!")
                    st.rerun()
                except ConnectionRefusedError:
                    st.error("Connection Refused. Is the server running?")
                except Exception as e:
                    st.error(f"Error connecting: {e}")
    else:
        st.success(f"Connected as **{st.session_state.username}**")
        st.info(f"Current Room: **{st.session_state.room}**")
        
        # Room Switching
        new_room = st.text_input("Switch Room", value=st.session_state.room)
        if st.button("Switch"):
            if new_room != st.session_state.room:
                msg = encode_message("chat", st.session_state.username, f"/join {new_room}", st.session_state.room)
                st.session_state.sock.sendall(msg)
                st.session_state.room = new_room
                st.rerun()

        if st.button("Disconnect"):
            if st.session_state.sock:
                st.session_state.sock.close()
            st.session_state.connected = False
            st.session_state.sock = None
            st.session_state.messages.append({"type": "system", "sender": "Client", "content": "Disconnected from server.", "timestamp": ""})
            st.rerun()

# Main Chat Interface
if st.session_state.connected:
    # Adding a Refresh button because Streamlit doesn't auto-update from background threads naturally
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    st.markdown("---")
    
    # Display Messages
    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            msg_type = msg.get("type")
            sender = msg.get("sender")
            content = msg.get("content")
            timestamp = msg.get("timestamp")
            
            if msg_type == "system":
                st.markdown(f"*{timestamp} - **{sender}**: {content}*")
            else:
                if sender == st.session_state.username:
                    st.markdown(f"**You** [{timestamp}]: {content}")
                else:
                    st.markdown(f"**{sender}** [{timestamp}]: {content}")
                    
    # Message Input
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            msg_input = st.text_input("Message (Use '@user msg' for private)", label_visibility="collapsed")
        with col2:
            submit_btn = st.form_submit_button("Send")
            
        if submit_btn and msg_input.strip():
            # Send via socket
            try:
                out_msg = encode_message("chat", st.session_state.username, msg_input, st.session_state.room)
                st.session_state.sock.sendall(out_msg)
            except Exception as e:
                st.error("Connection lost.")
                st.session_state.connected = False
else:
    st.info("Please connect using the sidebar to start chatting.")
    st.markdown("""
    ### About SyncSphere
    This application demonstrates:
    - **Process Management & IPC**: Server and clients communicate via TCP sockets.
    - **Multithreading**: The server handles each client in a separate thread.
    - **Synchronization**: Mutex locks prevent race conditions when updating shared resources.
    """)
