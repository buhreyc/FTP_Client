# Project 2 - FTP Client
**Brey-Michael Ching**
Coded in Python

**Description:** This project implements a command-line FTP client that supports basic file operations using two socket connections.

## High-Level Approach
The FTP client follows these steps:
1. **Initialization**: Establishes a control connection to the FTP server.
2. **Authentication**: Logs in using provided credentials (or defaults to anonymous login).
3. **Command Execution**: Supports six FTP operations:
   - `ls` - List directory contents.
   - `mkdir` - Create a directory.
   - `rm` - Delete a file.
   - `rmdir` - Remove a directory.
   - `cp` - Copy files between local and remote.
   - `mv` - Move/rename files between local and remote.
4. **Data Connection Management**: Uses Passive Mode (`PASV`) for file transfers.
5. **File Handling**: Reads and writes files in chunks to ensure efficient memory usage.
6. **Session Cleanup**: Properly closes both control and data sockets after operations.

## Challenges Faced
### 1. Managing Two Sockets (Control & Data Channels)
- I think for the program, the hardest thing to get was managing two different sockets. It definitely helped with the assignment breakdown of which needed what - either the control or data channels but initially reading through it, I was not able to understand without a few articles online on how that worked
- Additionally, handling Passive Mode (`PASV`) correctly involved extracting IP and port from the server response which was also difficult in implementation for me.

### 2. Handling FTP Responses Properly
- I think through trial and error, understanding FTP responses was kind of difficult. I definitely had to run the program a few times to better understand the response
and how I can either pass the functionality like in login or I have to kill the program in something like file transfers for an error

## Commands & Usage
The client supports the following operations:

| **Command** | **FTP Equivalent** | **Description** |
|------------|-----------------|----------------|
| `ls` `<FTP_URL>` | `LIST` | Lists files in a directory |
| `mkdir` `<FTP_URL>` | `MKD` | Creates a remote directory |
| `rm` `<FTP_URL>` | `DELE` | Deletes a file on the server |
| `rmdir` `<FTP_URL>` | `RMD` | Removes a remote directory |
| `cp` `<SRC> <DST>` | `STOR` / `RETR` | Uploads/downloads files |
| `mv` `<SRC> <DST>` | `RNFR` / `RNTO` | Moves/renames a file |

### Example Commands
```sh
# List directory contents
./4700ftp ls ftp://user:password@ftp.4700.network/

# Create a directory
./4700ftp mkdir ftp://user:password@ftp.4700.network/new-dir

# Upload a file
./4700ftp cp local.txt ftp://user:password@ftp.4700.network/remote.txt

# Download a file
./4700ftp cp ftp://user:password@ftp.4700.network/remote.txt local.txt

# Move a file remotely
./4700ftp mv ftp://user:password@ftp.4700.network/old.txt ftp://user:password@ftp.4700.network/new.txt
```

## Error Handling & Edge Cases
- **Incorrect login credentials** (`530 Login incorrect`)
- **Missing files** (`550 File not found`)
- **Permission errors** (`550 Access denied`)
- **Invalid commands** (graceful handling of incorrect usage)

## Running the Program
```sh
./4700ftp [operation] [param1] [param2]
```

## Testing Overview
To ensure that the FTP client works, I tested it on the login.ccs.neu.edu Linux server with the ftp.4700.network server using the various operators. For me specifically, commands looked like this in full including my password provided:

./4700ftp ls ftp://ching.b:6974dd7def9dd483b3aa3b5b9d65f34ea201582524fb585311fb9e224f8baed3@ftp.4700.network/
./4700ftp cp hello.txt ftp://ching.b:6974dd7def9dd483b3aa3b5b9d65f34ea201582524fb585311fb9e224f8baed3@ftp.4700.network/test-dir/hello.txt
./4700ftp rm ftp://ching.b:6974dd7def9dd483b3aa3b5b9d65f34ea201582524fb585311fb9e224f8baed3@ftp.4700.network/test-dir/hello.txt
