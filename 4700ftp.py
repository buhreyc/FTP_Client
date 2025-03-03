#!/usr/bin/env python3
import socket
import sys
import os
from urllib.parse import urlparse

# Constants
BUFFER_SIZE = 4096
CRLF = "\r\n"

def recv_until(sock, delimiter=b'\r\n'):
    # This function reads from a socket until a delimiter is encountered
    data = b""
    while not data.endswith(delimiter):
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode()

def send_command(sock, command):
    # This function sends an FTP command over the control channel
    sock.sendall(command.encode())

def parse_ftp(url):
    """
    This function parses an FTP URL
    Returns a dictionary with keys: user, password, host, port, path
    """
    parsed = urlparse(url)

    # Ensures valid FTP URL - otherwise raise error
    if parsed.scheme != 'ftp':
        raise ValueError("URL must start with ftp://")
    
    # Extract user credentials or default to anonymous login
    user = parsed.username if parsed.username else 'anonymous'
    password = parsed.password if parsed.password else ''

    # Extract host details
    host = parsed.hostname
    
    # If host is None - raise error
    if host is None:
        raise ValueError("URL must specify a host")

    # Parse port and path
    port = parsed.port if parsed.port else 21 # Make default FTP port - 21
    path = parsed.path if parsed.path else "/"

    return {'user': user, 'password': password, 'host': host, 'port': port, 'path': path}

def open_control_connection(host, port):
    # This function establishes a TCP connection to the FTP server

    # Try to establish connection - if Exception occurs, throw error
    try: 
        ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ctrl_sock.connect((host, port))

        # Read welcome message
        welcome = recv_until(ctrl_sock)
        # print(welcome.strip())
        return ctrl_sock
    except Exception as e:
        print(f"Error connecting to {host}:{port} - {e}")
        sys.exit(1)

def login(ctrl_sock, user, password):
    # This function logs in to the FTP server using the USER and the PASS commands.
    send_command(ctrl_sock, f"USER {user}{CRLF}")
    reply = recv_until(ctrl_sock)

    # Based on server reply, attempt to login
    if reply.startswith("331"): # Password required
        send_command(ctrl_sock, f"PASS {password}{CRLF}")
        reply = recv_until(ctrl_sock)
        if not reply.startswith("230"): # Login successful
            print("Login failed:", reply.strip())
            sys.exit(1)
    elif reply.startswith("230"):
        pass
    else:
        print("Unexpected login response:", reply.strip())
        sys.exit(1)

def setup_transfer(ctrl_sock):
    """
    This function sets up the FTP connection for binary file transfers:
        - Binary mode (TYPE I)
        - Stream mode (MODE S)
        - File structure (STRU F)
    """
    for cmd in ["TYPE I", "MODE S", "STRU F"]:
        send_command(ctrl_sock, f"{cmd}{CRLF}")
        reply = recv_until(ctrl_sock)

def enter_passive(ctrl_sock):
    # This function sends PASV and parses the reply to obtain the IP and port for the data channel.
    send_command(ctrl_sock, f"PASV{CRLF}")
    reply = recv_until(ctrl_sock)

    # Extract the IP and port from the PASV response
    start = reply.find('(')
    end = reply.find(')')

    # If either the start or end is -1 - produce error
    if start == -1 or end == -1:
        print("Failed to parse PASV response:", reply.strip())
        sys.exit(1)

    # If response was not expected - produce error
    numbers = reply[start+1:end].split(',')
    if len(numbers) != 6:
        print("Unexpected PASV response format:", reply.strip())
        sys.exit(1)

    ip = '.'.join(numbers[0:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])

    return ip, port

def open_data_connection(ctrl_sock):
    # This function opens the data channel through PASV
    ip, port = enter_passive(ctrl_sock)

    # Try to open the data connection
    try:
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((ip, port))
        return data_sock

    # Print an exception if the connection fails
    except Exception as e:
        print(f"Error opening data connection to {ip}:{port} - {e}")
        sys.exit(1)\

def list_directory(ctrl_sock, remote_path):
    # This function implements the FTP LIST command to get a directory listing
    data_sock = open_data_connection(ctrl_sock)
    send_command(ctrl_sock, f"LIST {remote_path}{CRLF}")

    # Read the directory listing from data socket
    listing = b""
    while True:
        data = data_sock.recv(BUFFER_SIZE)
        if not data:
            break
        listing += data
    
    # Print directory contents
    print(listing.decode())
    data_sock.close()

    # Read the final control channel reply.
    final_reply = recv_until(ctrl_sock)

def upload_file(ctrl_sock, local_path, remote_path):
    # This function implements the FTP STOR command to upload a file

    # Check to see if the file exists - if not print error and exit
    if not os.path.isfile(local_path):
        print(f"Local file '{local_path}' does not exist.")
        sys.exit(1)
    
    # Open a data connection and send the command
    data_sock = open_data_connection(ctrl_sock)
    send_command(ctrl_sock, f"STOR {remote_path}{CRLF}")
    
    # Check if the server is ready to receive the file.
    reply = recv_until(ctrl_sock)

    # If server is not ready - print error
    if not (reply.startswith("125") or reply.startswith("150")):
        print("Server did not accept STOR command:", reply.strip())
        data_sock.close()
        sys.exit(1)
    
    # Try to open the file and send the contents
    try:
        with open(local_path, 'rb') as f:
            while True:
                chunk = f.read(BUFFER_SIZE) 
                if not chunk:
                    break
                data_sock.sendall(chunk) # Send the chunk over the connection
    # If file cannot be read, close the data connection
    except Exception as e:
        print("Error reading local file:", e)
        data_sock.close()
        sys.exit(1)

    # Close data connection and read the reply to ensure upload was successful
    data_sock.close()
    final_reply = recv_until(ctrl_sock)

def download_file(ctrl_sock, remote_path, local_path):
    # This function implements the FTP RETR command to download a file
    data_sock = open_data_connection(ctrl_sock)
    send_command(ctrl_sock, f"RETR {remote_path}{CRLF}")

    # Wait for server reply and ensure that server is ready to transfer file
    reply = recv_until(ctrl_sock)
    # If error occurs - print error and close the sock
    if not (reply.startswith("125") or reply.startswith("150")):
        print("Server did not accept RETR command:", reply.strip())
        data_sock.close()
        sys.exit(1)
    
    # Try to open the file in write-binary and save the downloaded data
    try:
        with open(local_path, 'wb') as f:
            while True:
                chunk = data_sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk) # Write the chunk to the local file
    # If Exception occurs, print error and close the data connection
    except Exception as e:
        print("Error writing to local file:", e)
        data_sock.close()
        sys.exit(1)
    
    # Close the data socket and then read the final response to ensure download was successful
    data_sock.close()
    final_reply = recv_until(ctrl_sock)


def delete_file(ctrl_sock, remote_path):
    # This function implements the FTP DELE command to delete a remote file
    send_command(ctrl_sock, f"DELE {remote_path}{CRLF}")
    reply = recv_until(ctrl_sock)

    # If the reply is not equivalent - throw an error
    if not reply.startswith("250"):
        print("Failed to delete remote file:", reply.strip())

def make_remote_directory(ctrl_sock, remote_path):
    # This function implements the FTP MKD command to create a remote directory
    send_command(ctrl_sock, f"MKD {remote_path}{CRLF}")
    reply = recv_until(ctrl_sock)

    # If the reply is not equivalent - throw an error
    if not reply.startswith("257"):
        print("Failed to create remote directory:", reply.strip())

def remove_remote_directory(ctrl_sock, remote_path):
    # This function implements the FTP RMD command to remove a remote directory
    send_command(ctrl_sock, f"RMD {remote_path}{CRLF}")
    reply = recv_until(ctrl_sock)

    # If the reply is not equivalent - throw an error
    if not reply.startswith("250"):
        print("Failed to remove remote directory:", reply.strip())


def quit(ctrl_sock):
    # This function closes the FTP session using the command QUIT
    send_command(ctrl_sock, f"QUIT{CRLF}")
    reply = recv_until(ctrl_sock)
    ctrl_sock.close()

def main():
     # Check command-line arguments.
    if len(sys.argv) < 2:
        print("Usage: ./4700ftp.py [operation] [param1] [param2]")
        sys.exit(1)
    
    # Handle '--help' argument and print instructions
    if sys.argv[1] in ["-h", "--help"]:
        print("""
        Usage: ./4700ftp [operation] [param1] [param2]
    
        Operations:
        ls <FTP_URL>      - List directory contents on an FTP server.
        mkdir <FTP_URL>   - Create a directory on the FTP server.
        rm <FTP_URL>      - Delete a file on the FTP server.
        rmdir <FTP_URL>   - Remove a directory on the FTP server.
        cp <SRC> <DST>    - Copy a file between local and remote.
        mv <SRC> <DST>    - Move a file between local and remote.
    
        Examples:
        ./4700ftp ls ftp://user:pass@ftp.example.com/
        ./4700ftp cp file.txt ftp://user:pass@ftp.example.com/file.txt
        """)
        sys.exit(0)

    # Extract command-line arguments
    operation = sys.argv[1]
    param1 = sys.argv[2]
    param2 = sys.argv[3] if len(sys.argv) >= 4 else None

    # Handle operations that work solely on a remote FTP server:
    if operation in ["ls", "mkdir", "rm", "rmdir"]:

        # Try to parse FTP URL
        try:
            ftp_info = parse_ftp(param1)
        # If Exception occurs - print the Exception and exit
        except Exception as e:
            print("Error parsing FTP URL:", e)
            sys.exit(1)
        
        # Establish FTP control connection
        ctrl_sock = open_control_connection(ftp_info['host'], ftp_info['port'])
        login(ctrl_sock, ftp_info['user'], ftp_info['password'])
        setup_transfer(ctrl_sock)

        # Execute the given command
        if operation == "ls":
            list_directory(ctrl_sock, ftp_info['path'])
        elif operation == "mkdir":
            make_remote_directory(ctrl_sock, ftp_info['path'])
        elif operation == "rm":
            delete_file(ctrl_sock, ftp_info['path'])
        elif operation == "rmdir":
            remove_remote_directory(ctrl_sock, ftp_info['path'])

        # Close the connection
        quit(ctrl_sock)

    # Handle operations that involve a file transfer (cp and mv)
    elif operation in ["cp", "mv"]:
        # If operation does not have second parameter - print error and exit
        if not param2:
            print(f"Operation {operation} requires two parameters.")
            sys.exit(1)

        # Determine which argument is the FTP URL.
        if param1.startswith("ftp://"):
            # Download from remote to local.
            try:
                ftp_info = parse_ftp(param1)
            except Exception as e:
                print("Error parsing FTP URL:", e)
                sys.exit(1)

            # Establish control connection and login
            ctrl_sock = open_control_connection(ftp_info['host'], ftp_info['port'])
            login(ctrl_sock, ftp_info['user'], ftp_info['password'])
            setup_transfer(ctrl_sock)

            # Perform download function
            download_file(ctrl_sock, ftp_info['path'], param2)

            # If 'mv', delete the original file after mdownloading
            if operation == "mv":
                delete_file(ctrl_sock, ftp_info['path'])

            # Close the ftp connection
            quit(ctrl_sock)

        elif param2.startswith("ftp://"):
            # Upload from local to remote.
            try:
                ftp_info = parse_ftp(param2)
            except Exception as e:
                print("Error parsing FTP URL:", e)
                sys.exit(1)
            
            # Ensure the local file exists before upload - if not print error and exit
            if not os.path.isfile(param1):
                print(f"Local file '{param1}' does not exist.")
                sys.exit(1)
            
            # Establish control connection and login
            ctrl_sock = open_control_connection(ftp_info['host'], ftp_info['port'])
            login(ctrl_sock, ftp_info['user'], ftp_info['password'])
            setup_transfer(ctrl_sock)

            # Perform uploading file
            upload_file(ctrl_sock, param1, ftp_info['path'])

            # If operation is 'mv', delete the local file after uploading
            if operation == "mv":
                try:
                    os.remove(param1)
                except Exception as e:
                    print("Failed to remove local file:", e)
            
            # Close the FTP connection
            quit(ctrl_sock)
        
        # Otherwise it is an invalid command, print error and exit
        else:
            print("For cp and mv operations, one parameter must be an FTP URL.")
            sys.exit(1)
    # Handle unknown operations
    else:
        print("Unknown operation:", operation)
        sys.exit(1)

# Run 'main()' function when script is executed
if __name__ == '__main__':
    main()