import json.decoder
from pprint import pprint
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from typing import Literal

from _socket import SO_REUSEADDR, SOL_SOCKET

from FancyLog import log


class TContactConnectionManager:
    HOST: str
    PORT: int
    SOCKET: socket | None
    is_listening: bool
    listen_thread: Thread

    def __init__(self, host='localhost', port=65432):
        self.CONNECTION = None
        self.HOST = host
        self.PORT = port
        self.is_listening = False

    def start_listening(self):
        self.SOCKET = socket(AF_INET, SOCK_STREAM)
        self.SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.SOCKET.bind((self.HOST, self.PORT))
        self.SOCKET.settimeout(5)
        self.is_listening = True
        self.listen_thread = Thread(target=self.listen)
        self.listen_thread.start()

        log('TCP Manager', 'INFO', f'Started listening on {self.HOST}:{self.PORT}')

    def listen(self):
        self.SOCKET.listen(20)
        while self.is_listening:
            try:
                clientsocket, address = self.SOCKET.accept()
            except TimeoutError:
                continue

            log('TCP Manager', 'INFO', f'Accepted incoming connection from {address}')

            conn = Connection(clientsocket)
            client_thread = Thread(target=conn.receive, args=())
            client_thread.start()

    def stop_listening(self):
        self.is_listening = False
        self.listen_thread.join()
        self.SOCKET.close()
        log('TCP Manager', 'INFO', f'Stopped listening on {self.HOST}:{self.PORT}')

    def connect_to(self, address, port):
        self.SOCKET = socket(AF_INET, SOCK_STREAM)
        self.SOCKET.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.SOCKET.bind((self.HOST, self.PORT))
        self.SOCKET.connect((address, port))
        self.CONNECTION = Connection(self.SOCKET)
        log('TCP Manager', 'INFO', f'Successfully connected to {address}:{port}')

    def disconnect(self):
        self.SOCKET.close()
        self.SOCKET = None


class Connection:
    SOCKET: socket

    def __init__(self, _socket: socket):
        self.SOCKET = _socket

    def receive(self) -> "Message":
        message = Message()
        message.process_protoheader(self.SOCKET.recv(2))  # RECEIVE THE FIXED-LENGTH HEADER
        message.process_json_header(self.SOCKET.recv(message.JSON_HEADER_LEN))
        message.process_content(self.SOCKET.recv(message.MESSAGE_CONTENT_LENGTH))
        log('Message service', 'INFO', f'Received message of type {message.MESSAGE_CONTENT_TYPE}')
        pprint(message.JSON_HEADER)
        print(message.CONTENT)

        return message

    def send(self, content_type: Literal['PLAIN_TEXT', 'FILE', 'MSG'], content: bytes, address, port) -> int:
        message: bytes = compose_message(content, content_type)

        length = self.SOCKET.sendto(message, (address, port))
        log('TCP Manager', 'INFO', f'Sent message containing {length} bytes to {address}:{port}')
        return length


def compose_message(content: bytes, content_type: Literal['PLAIN_TEXT', 'FILE', 'MSG']) -> bytes:
    json_header: bytes = json.dumps(
        {
            'CONTENT-LENGTH': len(content),
            'CONTENT-TYPE': content_type,
        }
    ).encode('UTF-8')

    protoheader: bytes = len(json_header).to_bytes(2, "big")

    return protoheader + json_header + content


class Message:
    JSON_HEADER: dict
    CONTENT: str | bytes
    JSON_HEADER_LEN: int
    MESSAGE_CONTENT_LENGTH: int
    MESSAGE_CONTENT_TYPE: Literal['PLAIN-TEXT', 'MSG', 'FILE']
    JSON_HEADER_TEXT: str

    def __init__(self):
        pass

    def process_protoheader(self, data: bytes):
        self.JSON_HEADER_LEN = int.from_bytes(data, "big")

    def process_json_header(self, data: bytes):
        self.JSON_HEADER_TEXT = data.decode(encoding='UTF-8')
        self.JSON_HEADER: dict = json.loads(self.JSON_HEADER_TEXT)

        self.MESSAGE_CONTENT_TYPE = self.JSON_HEADER['CONTENT-TYPE']
        self.MESSAGE_CONTENT_LENGTH = self.JSON_HEADER['CONTENT-LENGTH']

    def process_content(self, data: bytes):
        match self.MESSAGE_CONTENT_TYPE:
            case "PLAIN-TEXT":
                self.CONTENT = data.decode('UTF-8')
