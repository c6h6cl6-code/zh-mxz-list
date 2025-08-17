import os
import sys
import re
import socket
import threading
import time

LISTEN = '0.0.0.0'
UDP_PORT = 7246

INPUT_PROMPT = 'ZHBL> '

def parse_blocklist(file_path):
    user_ids = set()
    highest_generation = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = re.sub(r'!.*$', '', line).strip()
            if not line or not line.startswith('u,'):
                continue
            parts = line.split(',')
            if len(parts) >= 4 and line.startswith('u,'):
                try:
                    user_ids.add(parts[3])
                    generation = int(parts[1])
                    if generation > highest_generation:
                        highest_generation = generation
                except ValueError:
                    print(f"Invalid ZHBL entry: {line}")
                    continue
                except Exception:
                    continue
    return user_ids, highest_generation

def is_valid_url_token(s):
    return s.replace('-', '').isalnum()

def normalize_user_line(user_input, generation):
    user_input = re.sub(r'!.*$', '', user_input).strip().replace('\r', '').replace('\n', '')
    if user_input.startswith('u,'):
        parts = user_input.split(',')
        if len(parts) < 5:
            raise ValueError("Invalid full-format user entry")
        if not is_valid_url_token(parts[2]):
            raise ValueError("Invalid urlToken")
        parts[1] = str(generation)
        return ','.join(parts), parts[3]
    else:
        parts = user_input.split(',')
        if len(parts) < 3:
            raise ValueError("Invalid short-format user entry")
        if not is_valid_url_token(parts[0]):
            raise ValueError("Invalid urlToken")
        return f"u,{generation},{parts[0]},{parts[1]},{parts[2]}", parts[1]

def process_user_file(input_path, generation, user_ids, target_path):
    added = 0
    with open(input_path, 'r', encoding='utf-8') as f, open(target_path, 'a', encoding='utf-8') as out:
        for line in f:
            raw = re.sub(r'!.*$', '', line).strip()
            if not raw or not raw.startswith('u,'):
                continue
            parts = raw.split(',')
            if len(parts) < 5:
                continue
            user_id = parts[3]
            if user_id in user_ids:
                continue
            parts[1] = str(generation)
            final_line = ','.join(parts)
            out.write(final_line + '\n')
            user_ids.add(user_id)
            added += 1
    print(f"Imported {added} new user(s) from: {input_path}")

def udp_server(file_path, user_ids, generation, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN, UDP_PORT))
    print(f"UDP server started on {LISTEN}:{UDP_PORT}")
    while not stop_event.is_set():
        try:
            sock.settimeout(1.0)
            data, addr = sock.recvfrom(1024)
            line = data.decode('utf-8').strip()
            message = ''
            print(f"\nReceived from {addr}: {line}")
            try:
                print(INPUT_PROMPT + line)
                normalized_line, user_id = normalize_user_line(line, generation)
                if user_id in user_ids:
                    message = f"Duplicate user ID from UDP {addr}: {user_id}. Skipped."
                else:
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(normalized_line + '\n')
                    user_ids.add(user_id)
                    message = f"Added from UDP {addr}: {normalized_line}"
            except ValueError as e:
                message = f"Error processing line from UDP {addr}: {e}"
            except Exception as e:
                message = f"Unexpected error processing from UDP {addr}: {e}"
            finally:
                if message:
                    print(message)
                    sock.sendto(message.encode('utf-8'), (addr[0], UDP_PORT))
                else:
                    print("Warning: WTF?")
        except socket.timeout:
            continue
        except Exception as e:
            print(f"UDP server error: {e}")
        
        print(INPUT_PROMPT, end='', flush=True)

    sock.close()
    print("UDP server stopped")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Enter path to blocklist file: ").strip()
    if not os.path.exists(file_path):
        print("Target blocklist file not found")
        exit(1)
    user_ids, highest_generation = (set(), 0)
    files = [file_path]
    if len(sys.argv) > 1:
        for input_file in sys.argv[2:]:
            if os.path.isfile(input_file):
                files.append(input_file)
            else:
                print(f"File not found: {input_file}")
    for input_file in files:
        try:
            new_user_ids, new_highest_generation = parse_blocklist(input_file)
            user_ids.update(new_user_ids)
            if new_highest_generation > highest_generation:
                highest_generation = new_highest_generation
            print(f"Loaded {len(new_user_ids)} user(s) from: {input_file} with highest generation {new_highest_generation}")
        except Exception as e:
            print(f"Failed to load from file {input_file}: {e}")
    print(f"Total unique user(s) loaded: {len(user_ids)}")
    print(f"Highest generation number found: {highest_generation}")
    try:
        generation = int(input(f"Enter generation number (default {highest_generation + 1}): ").strip() or highest_generation + 1)
        if generation <= highest_generation:
            print(f"Warning: Generation number {generation} is not greater than the highest generation {highest_generation}.")
    except ValueError:
        print("Invalid generation number")
        exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        exit(1)
    
    # Start UDP server in a separate thread
    stop_event = threading.Event()
    udp_thread = threading.Thread(target=udp_server, args=(file_path, user_ids, generation, stop_event))
    udp_thread.daemon = True
    udp_thread.start()

    # sleep 0.1s
    time.sleep(0.1)

    try:
        while True:
            try:
                user_input = input(INPUT_PROMPT).strip()
            except EOFError:
                print("\nExiting.")
                break
            if not user_input:
                continue
            if os.path.isfile(user_input):
                try:
                    process_user_file(user_input, generation, user_ids, file_path)
                except Exception as e:
                    print(f"Failed to import from file: {e}")
                continue
            try:
                line, user_id = normalize_user_line(user_input, generation)
                if user_id in user_ids:
                    print(f"Duplicate user ID detected: {user_id}. Skipped.")
                    continue
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
                user_ids.add(user_id)
                print(f"Added: {line}")
            except ValueError as e:
                if not os.path.exists(user_input):
                    print(f"Error: {e} (or file not found)")
                else:
                    print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nInterrupted.")
        stop_event.set()  # Signal UDP server to stop
        udp_thread.join(timeout=2.0)  # Wait for UDP thread to close
