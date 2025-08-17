import pyperclip
import time
import re
import socket
import threading

# Configuration
SERVER_IP = "192.168.1.7"
SERVER_PORT = 7246
LISTEN = '0.0.0.0'

def is_zhbl_rule(text):
    """
    Check if the clipboard text is a valid ZHBL rule.
    - Full format: u,generation,urlToken,userID,name
    - Short format: urlToken,userID,name
    """
    text = text.strip()
    if not text:
        return False
    parts = text.split(',')
    if len(parts) == 5 and parts[0].lower() == 'u':
        try:
            int(parts[1])  # Validate generation is integer
            return True
        except ValueError:
            return False
    elif len(parts) == 3:
        return True
    return False

def udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN, SERVER_PORT))
    print(f"Listening for UDP packets on {LISTEN}:{SERVER_PORT}")
    while True:
        data, addr = sock.recvfrom(1024)
        print(f'{addr}: {data.decode("utf-8")}')

if __name__ == "__main__":
    print("Starting clipboard monitor for ZHBL rules...")

    udp_thread = threading.Thread(target=udp_server, daemon=True)
    udp_thread.daemon = True
    udp_thread.start()

    last_clipboard = pyperclip.paste()  # Initial clipboard content
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            time.sleep(1)
            current = pyperclip.paste()
            if current != last_clipboard:
                last_clipboard = current
                if is_zhbl_rule(current):
                    print(f"Detected ZHBL rule: {current}")
                    # Send via UDP
                    sock.sendto(current.encode('utf-8'), (SERVER_IP, SERVER_PORT))
                    print("Sent to server")
        except KeyboardInterrupt:
            print('Interrupted')
            sock.close()
            exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sock.close()

