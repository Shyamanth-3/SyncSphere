# 🌐 SyncSphere

SyncSphere is a real-time multi-user communication system built with Python and Streamlit. It is specifically designed to demonstrate core Operating System concepts through a practical, interactive chat application.

## 🚀 Execution Steps

### Prerequisites
Make sure you have Python installed. You also need to install `streamlit`:
```bash
pip install streamlit
```

### 1. Start the Server
Open a terminal, navigate to the `SyncSphere` directory, and run the server:
```bash
cd /Users/thekundannadella/Desktop/SyncSphere
python server.py
```
You should see output indicating the server is listening on `127.0.0.1:5050`.

### 2. Start Clients (Streamlit UI)
Open **multiple new terminals** to simulate different users. In each new terminal, run:
```bash
cd /Users/thekundannadella/Desktop/SyncSphere
streamlit run client_ui.py
```
This will open the Streamlit web interface in your browser.
*Note: Because Streamlit applications are web-based, if you want to run multiple clients locally, you can open multiple browser tabs navigating to the Streamlit local URL (e.g., `http://localhost:8501`).*

### 3. Usage Guide
1. **Connect**: Enter a username and an optional room name in the sidebar and click "Connect".
2. **Global Chat**: Type messages in the input box to broadcast to your current room.
3. **Private Messaging**: Prefix your message with `@username ` to send a private message (e.g., `@alice Hello there!`).
4. **Rooms**: Use the sidebar "Switch Room" input to change your active channel. Only users in the same room will see your broadcasted messages.
5. **Real-time Refresh**: Since Streamlit executes synchronously, use the "🔄 Refresh" button to fetch new messages if they don't appear automatically when you aren't sending messages.

---

## 🧠 OS Concepts Mapping

This project serves as a practical implementation of the following Operating System concepts:

### 1. Process Management
* **Implementation**: The Server and each Client run as entirely separate OS processes. 
* **Concept**: Processes are isolated execution environments. They do not share memory space directly, which is why we must use Inter-Process Communication (IPC) to pass data between them.

### 2. Inter-Process Communication (IPC)
* **Implementation**: Uses pure **TCP Sockets** (stream sockets) via the `socket` module.
* **Concept**: Sockets are an OS-provided mechanism for IPC over a network loopback (`127.0.0.1`). The protocol handles byte-stream fragmentation using a custom 4-byte length prefix header (see `protocol.py`).

### 3. Multithreading & Concurrency
* **Implementation**: The `server.py` main loop accepts connections. For every accepted socket connection, it spawns a new `threading.Thread(target=handle_client, daemon=True)`.
* **Concept**: Instead of creating heavy distinct processes for each user, the server allocates lightweight threads sharing the same memory space. This allows the server to block on `recv()` for one client without stopping the entire server.

### 4. Synchronization (Locks/Mutexes)
* **Implementation**: A `threading.Lock()` named `clients_lock` is used in `server.py`.
* **Concept**: Because multiple threads (one per client) read and write to the shared `clients` dictionary simultaneously, a **Race Condition** could occur (e.g., two users joining/leaving at the exact same millisecond). The Mutex lock ensures only one thread can modify the dictionary at a time, providing Thread Safety.

### 5. Resource Allocation
* **Implementation**: 
  - `socket.SO_REUSEADDR` is used to tell the OS kernel to release the port binding immediately upon server shutdown.
  - Sockets (File Descriptors) are gracefully closed in `finally` blocks.
* **Concept**: The OS allocates finite resources (Ports, File Descriptors, Memory). Proper allocation and deallocation prevent memory leaks and "Port already in use" errors.

---

## 🧪 Testing Scenarios for Viva/Demo

1. **Concurrency Demonstration**: 
   - Start the server.
   - Open 3 separate browser tabs for the UI. Join as UserA, UserB, and UserC.
   - Show how messages from UserA appear for UserB and UserC, demonstrating the server's multi-threaded broadcast.
2. **Private Messaging**:
   - Have UserA send `@UserB Secret message`.
   - Show that UserB receives it, but UserC does not.
3. **Synchronization & State**:
   - Join different rooms and show how broadcasts are isolated per room, proving the `clients` dictionary state is maintained properly across threads.
4. **Fault Tolerance (Graceful Disconnect)**:
   - Close UserC's browser tab or kill the terminal.
   - Observe the server terminal gracefully handle the disconnection and notify UserA and UserB that UserC left, without crashing the server process.
