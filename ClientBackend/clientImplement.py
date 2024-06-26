import os.path
import threading
import socket
import ClientBackend.clientLib as clientLib


class Client:
    def __init__(self, server_address, server_port):
        self.sAddr = server_address  # Server IP address
        self.sPort = server_port     # Server port
        self.socket = None           # the socket to connect to server
        self.username = None           # username to distinguish between clients
        self.password = None
        # Create another thread that waiting for request to send file to clients
        self.handle_downloading_thread = threading.Thread(target=self.create_downloading_process, daemon=True)
        self.handle_downloading_thread.start()
        self.FORMAT = 'utf-8'
        self.is_connected = False

    def __del__(self):
        self.socket = None

    def validate_request(self, input):
        if len(input) == 1:
            if input[0] == "GET_INFO":
                return 5
            elif input[0] == "LEAVE":
                return 6
        else:
            if input[0] == "SEND":
                return 1
            elif input[0] == "UPDATE":
                return 3
            if input[0] == "REMOVE":
                return 2
            elif input[0] == "FETCH":
                return 4
        return -1
    def forming_request(self, input):
        userInput = input
        userInput = userInput.split(" ",1)
       
        act = self.validate_request(userInput)
        if act == -1:
            print("Invalid syntax")
            return None
        request = dict(
            type="text/json",
            encoding="utf-8",
            content=dict(client_name=self.username, action=userInput[0])
        )
        if act == 5 or act == 6:
            return request
        if act == 1 or act == 3:
            userInput += userInput.pop(-1).split(" ",1)
          
            request["content"]["path"] = userInput[1]
            request["content"]["file_name"] = userInput[2]
            return request
        request["content"]["file_name"] = userInput[1]
        return request

    def start_connection(self):
        if not (self.socket is None):
            raise ValueError("Thread trying to start another socket to server.")
        addr = (self.sAddr, self.sPort)
        print(f"Starting connection to {addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect_ex(addr)

        request = dict(
            type="text/json",
            encoding="utf-8",
            content=dict(client_name=self.username,client_password=self.password, action="CONNECT")
        )
        message = clientLib.Message(sock, addr, request)
        message.write()
        message.read()
        if message.response.get("result") == "Wrong password.":
            message.close()
            self.username = None
            self.password = None
            return self.is_connected
        self.socket = sock
        self.is_connected = True
        return self.is_connected
    # Create a connection to the client that has file to download from
    def create_connection_and_download(self, client_ip, file_path):
        get_file_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        get_file_socket.connect((client_ip, 50000))
        # Receive info whether connect to server or not
        print(get_file_socket.recv(1024).decode(self.FORMAT))
        # request downloading file
        self.download_file(get_file_socket, file_path)
        get_file_socket.close()

    # Client download file from another client
    def download_file(self, server_socket, file_path):
        server_socket.send(file_path.encode(self.FORMAT))
        file_size = server_socket.recv(1024).decode(self.FORMAT)
        print(f"Size of a file: {file_size}")
        received_file_size = int(file_size)
        filename = file_path[file_path.rfind('/')+1:]
        file = open(filename, "wb")
        data_received = server_socket.recv(received_file_size)
        file.write(data_received)
        file.close()
        print("File downloaded")

    # These functions belows apply for a client that works like a server to send file to another client
    def send_file_to_client(self, sending_socket, file_path):
        # Prepare and send file
        file = open(file_path, "rb")
        file_data_binary = file.read()
        sending_socket.sendall(file_data_binary)
        print("File sent to client")
        file.close()

    # Accept one client socket that want to communicate with server
    def socket_accept_client(self, server_socket):
        while True:
            # conn is a socket used to communicate with client
            conn, addr = server_socket.accept()
            conn.send("Connected to server".encode(self.FORMAT))
            file_path = conn.recv(1024).decode(self.FORMAT)
            print(f"Server receive file path {file_path}")
            file_len = os.path.getsize(file_path)
            print(f"Server side size of a file: {file_len}")
            conn.send(str(file_len).encode(self.FORMAT))
            handle_client_thread = threading.Thread(target=self.send_file_to_client, args=(conn, file_path))
            handle_client_thread.start()

    # Create a new port for sending downloaded file to other client
    def create_downloading_process(self):
        print("Create a thread for downloading file")
        my_ip = socket.gethostbyname(socket.gethostname())
        downloading_port = 50000
        handle_downloading_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        handle_downloading_socket.bind((my_ip, downloading_port))
        handle_downloading_socket.listen()
        self.socket_accept_client(handle_downloading_socket)

    # raw_request: Request of type string like 'FETCH path file'
    def handle_request(self, raw_request):
        if self.socket is None:
            raise ValueError("Socket does not exist")
        request = self.forming_request(raw_request)
        message = clientLib.Message(self.socket, (self.sAddr, self.sPort), request)
        message.write()
        data = message.read()
        if request['content']['action'] == 'GET_INFO':
            if not (data is None):
                return data
            else:
                raise ValueError(f"Data for client {self.username} does not exist")
        elif request['content']['action'] == 'FETCH':
            if not (data is None):
                return data
            else:
                raise ValueError(f"Fetch data for client {self.username} does not exist")
        elif request['content']['action'] == 'LEAVE':
            message.close()
            self.socket.close()
            self.socket = None
            self.is_connected = False
            self.username = None
            self.password = None
        elif request['content']['action'] == 'SEND':
            print("[SEND] sending file to server")
            if data is not None:
                print(data)

