import json
from datetime import datetime

def encode_message(msg_type, sender, content, room="general"):
    """
    Encodes a message into bytes with a length prefix.
    msg_type: 'chat', 'system', 'presence'
    """
    data = {
        "type": msg_type,
        "sender": sender,
        "content": content,
        "room": room,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    msg_bytes = json.dumps(data).encode('utf-8')
    # 4-byte length prefix ensures we don't face TCP stream fragmentation issues
    length = len(msg_bytes)
    return length.to_bytes(4, byteorder='big') + msg_bytes

def receive_message(sock):
    """
    Decodes a length-prefixed message from a socket.
    Returns the parsed JSON dictionary, or None if connection closed.
    """
    # Read 4 bytes for length
    raw_length = _recv_all(sock, 4)
    if not raw_length:
        return None
    msg_length = int.from_bytes(raw_length, byteorder='big')
    
    # Read the exact payload length
    data = _recv_all(sock, msg_length)
    if not data:
        return None
    
    return json.loads(data.decode('utf-8'))

def _recv_all(sock, n):
    """ Helper to receive exactly n bytes. """
    data = bytearray()
    while len(data) < n:
        try:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        except Exception:
            return None
    return data
