import socket
import ssl
import base64
import mimetypes
import os
import re

host_addr = 'smtp.yandex.ru.'
port = 465
user_name = "morahemora"
receivers = ["morahemora"]
application_password = "zsdqgprafylnlllt"


# TODO: создать папку attachments, прикрепить файлы из нее в письмо и также указать mime типы

def request(socket, request: str):
    socket.send((request + '\n').encode())
    # TODO: написать получение данных правильно (chunk 2^10)
    recv_data = socket.recv(65535).decode()
    return recv_data


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
def generate_boundary() -> str:
    return "my_bound"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((host_addr, port))
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # context = ssl.create_default_context()
    client = context.wrap_socket(client)
    # TODO: chunk up
    print(client.recv(1024))

    print(request(client, f"EHLO {user_name}"))
    base64login = base64.b64encode(user_name.encode()).decode()
    base64password = base64.b64encode(application_password.encode()).decode()

    print(request(client, 'AUTH LOGIN'))
    print(request(client, base64login))
    print(request(client, base64password))
    print(request(client, f'MAIL FROM: {user_name}@yandex.ru'))
    # TODO: iterate over recipients
    print(request(client, f'RCPT TO: {user_name}@yandex.ru'))
    # TODO: анализировать коды ответов и красиво прекращать работу если не работает
    print(request(client, 'DATA'))

    msg = ""
    BOUNDARY = generate_boundary()

    # TODO chunk up subject, add prefix
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

    msg += "Content-Disposition: attachment;\n"
    msg += "\tfilename=\"cat.jpg\"\n"
    msg += "Content-Transfer-Encoding: base64\n"
    msg += "Content-Type: image/jpeg;\n"
    msg += "\tname=\"dog.jpg\"\n\n"

    with open("cat.jpg", "rb") as file:
        image = base64.b64encode(file.read()).decode("utf-8")
        msg += image + "\n"

    msg += f"--{BOUNDARY}--"

    msg += "\n.\n"
    print(msg)
    print(request(client, msg))

# TODO:
# Обработка ошибок Сети
# MIME формат письма: присоединить картинки
# заголовки письма: Subject, From, и т.д.
# корректное получение данных по сети
# Subject парс табуляция
