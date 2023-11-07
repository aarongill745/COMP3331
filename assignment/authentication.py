import time

def authenticateUser(username, password):
    # Finds username and password in credentials.txt
    with open("credentials.txt", "r") as f:
        for line in f:
            u, p = line.strip().split()
            if u == username and p == password:
                return True
    return False

def processLogin(clientThread, username, password):
    if clientThread.failedAttempts + 1 >= clientThread.maxFailedAttempts:
        time.sleep(10)
        clientThread.failedAttempts = 0

    if authenticateUser(username, password): 
        clientThread.clientAuthenticated = True
        clientThread.clientUsername = username
        clientThread.clientSocket.send("Authentication successful".encode())
        clientThread.failedAttempts = 0
        return True
    else:
        clientThread.clientSocket.send("Invalid Password. Please try again".encode())
        clientThread.failedAttempts += 1
        return False
