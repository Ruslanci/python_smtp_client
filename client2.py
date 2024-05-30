import random
import socket
import ssl
import base64
import mimetypes
import os
import re
import string

host_addr = 'smtp.yandex.ru.'
port = 465
user_name = "morahemora"
receivers = ["morahemora"]
application_password = "lhyhxbbrcpbqzfvg"

attachments_dir = "attachments"


def request(socket, request: str):
    socket.send((request + '\n').encode())
    recv_data = socket.recv(65535).decode()
    return recv_data


def send_data_in_chunks(socket, data):
    try:
        chunk_size = 1024  # Adjust chunk size as needed
        total_sent = 0
        data_bytes = data.encode()  # Convert string to bytes
        while total_sent < len(data_bytes):
            chunk = data_bytes[total_sent: total_sent + chunk_size]
            socket.send(chunk)
            total_sent += len(chunk)
        return "Data sent successfully"
    except ssl.SSLError as e:
        return f"SSL error occurred: {e}"
    except Exception as e:
        return f"Error occurred: {e}"


def attach_files(attachments_dir: str) -> str:
    msg = ""
    for filename in os.listdir(attachments_dir):
        filepath = os.path.join(attachments_dir, filename)
        if os.path.isfile(filepath):
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type:
                print(f"Processing file: {filename}, MIME type: {mime_type}")
                try:
                    with open(filepath, "rb") as file:
                        file_content = file.read()
                        print(f"Read {len(file_content)} bytes from file. {filepath}")
                        encoded_content = base64.b64encode(file_content).decode("utf-8")
                        print("Encoded content:", encoded_content[:50])  # Print a portion of the encoded content
                        msg += f"--{BOUNDARY}\n"
                        msg += f"Content-Disposition: attachment;\n"
                        msg += f"\tfilename=\"{filename}\"\n"
                        msg += "Content-Transfer-Encoding: base64\n"
                        msg += f"Content-Type: {mime_type};\n"
                        msg += f"\tname=\"{filename}\"\n\n"
                        msg += encoded_content + "\n"
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
    return msg


def load_images(base_dir: str) -> list[str]:
    result = list()
    for path in os.listdir(base_dir):
        match os.path.isdir(path):
            case False:
                result.append(path)
            case True:
                result.append(*load_images(path))
    return result


# TODO make boundary random
def generate_boundary(length: int = 16) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((host_addr, port))
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    client = context.wrap_socket(client)
    print(client.recv(1024))

    print(request(client, f"EHLO {user_name}"))
    base64login = base64.b64encode(user_name.encode()).decode()
    base64password = base64.b64encode(application_password.encode()).decode()

    print(request(client, 'AUTH LOGIN'))
    print(request(client, base64login))
    print(request(client, base64password))
    print(request(client, f'MAIL FROM: {user_name}@yandex.ru'))
    for recipient in receivers:
        print(request(client, f'RCPT TO: {recipient}@yandex.ru'))
    print(request(client, 'DATA'))

    msg = ""
    BOUNDARY = generate_boundary()

    with open("headers.txt") as file:
        msg += "".join(file.readlines()) + "\n"

    msg += "Content-Type: multipart/mixed;\n"
    msg += f"\tboundary=\"{BOUNDARY}\""
    msg += "\n\n"
    msg += f"--{BOUNDARY}\n"
    msg += "Content-Type: text/html;\n\n"

    with open('msg.txt') as file:
        for line in file.readlines():
            line = line.strip("\n")
            if re.match("^\.+$", line[:-1]):
                line += "."
            msg += line + "\n"

    msg += f"--{BOUNDARY}\n"

    msg += attach_files(attachments_dir)

    msg += f"--{BOUNDARY}--"

    msg += "\n.\n"
    print(msg)
    print(send_data_in_chunks(client, msg))
