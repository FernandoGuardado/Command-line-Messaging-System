# Fernando Guardado
# CSCI 3920 - PA2
# Multithreaded Client

import socket
import sys
from threading import Thread


def displayMessage(message):
    message.replace('\n', '')
    print(message)


def sendMessage(soc, message):
    message = message + '\n'
    soc.send(message.encode("UTF-8").rstrip())


def disconnect(soc):
    try:
        soc.close()

    except IOError as e:
        print(e.__str__())

    finally:
        displayMessage('\nDisconnected from server')


def receiveServerMessage():
    try:
        for message in iter(lambda: soc.recv(5120).decode('UTF-8').rstrip(), ''):
            displayMessage(message)
    except:
        pass


soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = "localhost"
port = 8080

try:
    soc.connect((host, port))
except:
    print("Connection error")
    sys.exit()

sentinel = 'RUN'
cmd = 'RUN'

receivingThread = Thread(
    target=receiveServerMessage)
receiveServerMessage.daemon = True
receivingThread.start()

try:
    while sentinel == 'RUN':
        if cmd == 'END' or cmd == 'end':
            sentinel = 'END'
            disconnect(soc)
        else:
            try:
                cmd = input()
                sendMessage(soc, cmd)

            except KeyboardInterrupt:
                disconnect(soc)
                break
            except:
                displayMessage('Disconnected')
                break

except IOError as e:
    displayMessage('Server Disconnected')
except KeyboardInterrupt:
    disconnect(soc)
except:
    disconnect()
