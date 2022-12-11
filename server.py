import socket
import sys 
import os

# -- DEFINE CONSTANTS -- #
END_INTERACTION = "close"
CONTINUE_INTERACTION = "keep-alive"
EMPTY = 0
OK = 200
REDIRECT = 301
NOT_FOUND = 404
EXIST = True
NOT_EXIST = False
# -- DEFINE CONSTANTS -- #


# -- DEBUGG PRINTS -- #
def prettty_print_data(data, file, con_stat):
    print('Originaly recieved: ', data)
    print('Extracted Filename: ', file)
    print('Connections Status: ', con_stat)
# -- DEBUGG PRINTS -- #

# Validate port
def valid_port(port):
    if not(sys.argv[1].isnumeric()):
        return False
    if int(sys.argv[1]) in range(1, 65536):
        return True
    else:
        return False

"""
    Responsible for phrasing client request.
    Returns file name and the connection_status (keep-alive\ closed)
"""
def phrase_data(data):
    empty_req = "GET / HTTP/1.1"

    connection_string = data.split("\r\n")[2]
    connection_status = connection_string.split(" ")[1]

    req = data.split("\r\n", 1)[0]
    if(req == empty_req):
        file = "/index.html"
    else:    
        splitted_req = req.split(" ")
        file = splitted_req[1].split(" ")[0]

    return file, connection_status


"""
    Returns True if the file is inside the current Directory.
    If not, returns False.
"""
def is_exist(file):
    current_dir = os.getcwd() + "/files"
    path = current_dir + file
    return os.path.isfile(path) 

# Gets full path of a file name and returns it.
def get_full_path(file):
    current_dir = os.getcwd() + "/files"
    path = current_dir + file
    return path

# Checks if one of the conditions for interacting with a specific client is up.
def is_finished(req_stat, con_stat):
    return req_stat == REDIRECT or req_stat == NOT_FOUND or con_stat == END_INTERACTION

# Get content of a file given it's file path.
def get_content(file_path):
    if file_path.lower().endswith(('.ico', '.jpg')):
        with open(file_path, "rb") as bf:
            content = bf.read()
        return content
    else:
        with open(file_path, "r") as f:
            content = f.read()
        return content.encode()
        
"""
    Build the response of the server matching client request.
    If redirect_flag is on -> returns a 301 redirect response.
    Else, if the file exists -> returns the matching message + file content
    Finally, if file not exists -> returns 404.
"""
def build_res(con_stat, file_path, file_exists, redirect_flag):
    res = ""
    if redirect_flag:
            lines_of_res = [
                "HTTP/1.1 301 Moved Permanently",
                f"Connection: closed",
                "Location: /result.html",
                '\r\n'
            ]
            res = '\r\n'.join(lines_of_res).encode() 
    else:
        if file_exists:
            content = get_content(file_path)
            lines_of_res =[
                "HTTP/1.1 200 OK",f"Connection: {con_stat}",
                f"Content-Length: {str(len(content))}",
                '\r\n'
            ]
            res = '\r\n'.join(lines_of_res).encode() + content
        else:
            lines_of_res = [
                "HTTP/1.1 404 Not Found",
                "Connection: closed",
                '\r\n'
            ]
            res = '\r\n'.join(lines_of_res).encode() 
    return res

"""
    Handle client based on his request.
    Returns the status of the request: 200(OK), 301(Redirect), 404(Not Found)
"""
def handle(file, client_socket, con_stat):
    if file == "/redirect":
        client_socket.send(build_res("close", None, NOT_EXIST, True))
    if is_exist(file):
        client_socket.send(build_res(con_stat, get_full_path(file), EXIST, False))
        return OK
    else:
        client_socket.send(build_res("close", None, NOT_EXIST, False))
        return NOT_FOUND    


def main():

    # Get port and validate it
    port = int(sys.argv[1])
    if not valid_port(port):
        print("Not a valid port")
        exit()

    # Set up server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)


    while True:

        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)

        # Initialized for 1st iteration
        con_stat = CONTINUE_INTERACTION
        res_stat = ""

        # As long as the conditions for communication with a specific client live:
        while not is_finished(res_stat, con_stat):
            client_socket.settimeout(1)                     # set timeout for 1 sec
            try:
                data = bytes.decode(client_socket.recv(1024))
                client_socket.settimeout(None)
                # If empty request -> end iteraction with this client
                if len(data) == EMPTY:
                    con_stat = END_INTERACTION
                    continue
            except socket.timeout as e:
                # If timeout occured -> end iteraction with this client.
                con_stat = END_INTERACTION
                continue

            print(data)
            file, con_stat = phrase_data(data)              

            res_stat = handle(file, client_socket, con_stat) 

        client_socket.close()

if __name__ == "__main__":
    main()