import os
import re

def parse_blocklist(file_path):
    user_ids = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = re.sub(r'!.*$', '', line).strip()
            if not line or not line.startswith('u,'):
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    user_ids.add(parts[3])
                except Exception:
                    continue
    return user_ids

def normalize_user_line(user_input, generation):
    user_input = re.sub(r'!.*$', '', user_input).strip()
    if user_input.startswith('u,'):
        parts = user_input.split(',')
        if len(parts) < 5:
            raise ValueError("Invalid full-format user entry")
        parts[1] = str(generation)
        return ','.join(parts), parts[3]
    else:
        parts = user_input.split(',')
        if len(parts) < 3:
            raise ValueError("Invalid short-format user entry")
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

if __name__ == "__main__":
    file_path = input("Enter path to blocklist file: ").strip()
    if not os.path.exists(file_path):
        print("Target blocklist file not found")
        exit(1)

    try:
        generation = int(input("Enter your generation number: ").strip())
    except ValueError:
        print("Invalid generation number")
        exit(1)

    user_ids = parse_blocklist(file_path)

    try:
        while True:
            try:
                user_input = input("Enter user rule or file path (Ctrl+D/Ctrl+Z to quit): ").strip()
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
