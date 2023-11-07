def logout(clientThread, connectedClients):
    if clientThread.clientUsername in connectedClients:
        connectedClients.pop(clientThread.clientUsername)
    updateUserlog(clientThread.clientUsername)
    clientThread.clientSocket.send("Later gator!".encode())
    clientThread.clientSocket.close()
    return

def updateUserlog(username):
    with open('userlog.txt', 'r') as f:
        lines = f.readlines()
        
    with open('userlog.txt', 'w') as f:
        for idx, line in enumerate(lines):
            if username in line:
                continue
            seq, _ = line.split(';')
            seq = str(idx + 1)
            f.write('; '.join(seq, _))
        