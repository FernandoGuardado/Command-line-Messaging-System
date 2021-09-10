# Fernando Guardado
# CSCI 3920 - PA2
# Multithreaded Server

import socket
import sys
from threading import Thread


class User(object):
    def __init__(self, phone, password):
        self.__phone = phone
        self.__password = password

    @property
    def phone(self):
        return self.__phone

    @phone.setter
    def phone(self, phone):
        return self.__phone
        self.__phone = phone

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password

    def formatUser(self):
        return 'A|{}|{}'.format(self.__phone, self.__password)

    def __str__(self):
        return 'Users phone number is: {}'.format(self.__phone)


class Userbase(object):
    def __init__(self):
        self.__userList = []

    @property
    def user(self):
        return self.__userList

    def addUser(self, user):
        self.__userList.append(user)


def runServer(host='localhost', port=8080, backlog=100):
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    u = Userbase()
    loadFile(u)
    allConnections = {}
    online = []

    try:
        soc.bind((host, port))
    except:
        print("Bind failed\nError : {}".format(str(sys.exc_info())))
        sys.exit()

    soc.listen(backlog)
    print("waiting for connection(s) to server\nip: {} port: {}".format(host, port))

    try:
        while True:
            connection, address = soc.accept()
            ip, port = str(address[0]), str(address[1])

            allConnections[connection] = None

            print("Connected with {} : {}".format(ip, port))

            try:
                Thread(target=clientThread, args=(u,
                                                  connection, ip, port, allConnections, online)).start()
            except:
                print("Thread did not start")
    except KeyboardInterrupt:
        closeServer(soc)


def clientThread(u, connection, ip, port, allConnections, online, max_buffer_size=5120):
    isActive = True
    loginFlag = False
    phone = ''

    sendMessage(
        connection, "Welcome to the CMD Messaging System!\nPlease Login or Sign Up\n!help for a list of protocols")

    while isActive:
        try:
            message = receiveInput(connection, max_buffer_size)

            if len(message) <= 0:
                userOffline(allConnections, connection, online, phone)
                connection.close()
                print('User at IP: {} and Port: {} disconnected'.format(ip, port))
                isActive = False
            elif message == 'END' or message == 'end':
                userOffline(allConnections, connection, online, phone)
                connection.close()
                print('User at IP: {} and Port: {} disconnected'.format(ip, port))
                isActive = False
            else:
                message = processMessage(
                    u, message, ip, port, connection, allConnections, loginFlag, phone, online)

                if isinstance(message, tuple):
                    loginFlag = message[1]
                    phone = message[2]
                    online = message[3]
                    displayMessage(message[0], ip, port)
                    sendMessage(connection, message[0])
                else:
                    displayMessage(message, ip, port)
                    sendMessage(connection, message)

        except KeyboardInterrupt:
            userOffline(allConnections, connection, online, phone)
            print('User at IP: {} and Port: {} disconnected'.format(ip, port))
            break
        except Exception as e:
            userOffline(allConnections, connection, online, phone)
            print('User at IP: {} and Port: {} disconnected due to an error:'.format(
                ip, port))
            print(e)
            break


def userOffline(userList, connection, online, phone):
    del userList[connection]
    if len(online) != 0:
        online.remove(phone)


def displayMessage(message, ip, port):
    if message[0].isdigit():
        message = message.replace('\n', '')
        print('\tRSP: {}'.format(message))
    elif 'Users Currently Online:' in message:
        message = message.replace('\n', '')
        print('\tRSP: {}'.format(message))
    else:
        message = message.replace('\n', '')
        print('CMD: User @ {} : {} >> {}'.format(ip, port, message))


def sendMessage(connection, message):
    connection.send(message.encode("UTF-8"))


def relayMessage(connections, fromPhone, toPhone, message):
    toConnection = None
    message = 'Message from: {} >> {}'.format(fromPhone, message)

    for key, value in connections.items():
        if toPhone == value:
            toConnection = key
    toConnection.send(message.encode('UTF-8'))


def loadFile(u):
    try:
        with open('user.txt') as f:
            for line in f:
                processFile(u, line.strip())
        print('Done loading user file')
        print('{} user(s) have been loaded onto server\n'.format(len(u.user)))
    except IOError:
        print('File does not exist\n')


def addToFile(u):
    newUser = u.formatUser()
    try:
        with open('user.txt', 'a') as f:
            f.write('\n{}'.format(newUser))
    except IOError:
        print('File does not exist\n')


def closeServer(soc):
    try:
        soc.close()
        print(
            "\n================\nServer Terminated.")
    except IOError as e:
        print(e.__str__())


def receiveInput(connection, max_buffer_size):
    message = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(message)

    if client_input_size > max_buffer_size:
        print("The input size is greater than: {}".format(client_input_size))

    message = message.decode("UTF-8").rstrip()

    return message


def processMessage(u, msg, ip, port, connection, allConnections, loginFlag, phone, online):
    if ip != 'server':
        displayMessage(msg, ip, port)

    RSP_OK = '0|Ok'
    RSP_NO_SOURCE_USER = '1|No Source User'
    RSP_INVALID_PASSWORD = '2|Wrong Password'
    RSP_NO_TARGET_USER = '3|No Target User'
    RSP_NOT_ONLINE = '4|User Not Online'
    RSP_PHONE_ALREADY_LOGGED_IN = '5|Phone Already Logged In'
    RSP_INVALID_FORMAT = '6|Invalid protocol format'
    RSP_ALREADY_LOGGED_IN = '7|You\'re already logged in!'
    RSP_USER_ALREADY_EXISTS = '8|User Already exists'
    RSP_NOT_A_VALID_PROTOCOL = '9|Not a valid protocol'
    RSP_FROM_USER_INVALID = '10|Can\'t send from phone you\'re not logged in from!'
    RSP_CANT_ADD_WHILE_LOGGED_IN = '11|Can\'t create a new user while already logged in!'
    RSP_NOT_LOGGED_IN = '12|You need to login/create an account before sending messages!'
    RSP_NO_ONLINE_USERS = '13|No users are currently online'
    RSP_ONLY_ONE_ONLINE = '14|You are the only user currently online'
    RSP_MESSAGE_TOO_LONG = '15|The message can\'t be more than 500 characters!'

    arguments = msg.split('|')
    args = len(arguments)
    command = arguments[0].upper()

    if '!help' in msg:
        commands = (
            "Protocols: \n"
            "Add User: A|phone|password\n"
            "Login: L|phone|password\n"
            "Send Message: M|phone_to|message\n"
            "Show Users Currently Online: O\n"
            "Close Client: END")
        return commands
    elif command == 'A':
        if args < 3:
            return RSP_INVALID_FORMAT
        else:
            if loginFlag == False:
                for i in u.user:
                    if i.phone == arguments[1]:
                        return RSP_USER_ALREADY_EXISTS

                new_user = User(arguments[1], arguments[2])
                u.addUser(new_user)
                addToFile(new_user)
                return RSP_OK
            else:
                return RSP_CANT_ADD_WHILE_LOGGED_IN
    elif command == 'L':
        if args < 3:
            return RSP_INVALID_FORMAT
        else:
            if loginFlag == False:
                if len(u.user) >= 1:
                    for i in u.user:
                        if i.phone == arguments[1]:
                            if i.password == arguments[2]:
                                if allConnections[connection] == None:
                                    for value in allConnections.values():
                                        if value == arguments[1]:
                                            return RSP_PHONE_ALREADY_LOGGED_IN
                                    loginFlag = True
                                    phone = arguments[1]
                                    allConnections[connection] = arguments[1]
                                    online.append(phone)
                                    return RSP_OK, loginFlag, phone, online
                                else:
                                    return RSP_PHONE_ALREADY_LOGGED_IN
                            else:
                                return RSP_INVALID_PASSWORD
                    return RSP_NO_SOURCE_USER
            else:
                return RSP_ALREADY_LOGGED_IN
    elif command == 'M':
            # this is how the send message protocol was done in the project pdf
            # but since I'm handling login in a way where I know who is logged in in what
            # client, I don't really have to validate the user and password again so i simplified
            # it so that you only have to pass who you're sending a message to and the message
            # if args < 5:
            #     return RSP_INVALID_FORMAT
            # else:
            #     if arguments[1] == phone:
            #         for i in u.user:
            #             if i.password == arguments[2]:
            #                 if arguments[3] in allConnections.values():
            #                     relayMessage(allConnections, phone,
            #                                  arguments[3], arguments[4])
            #                     return RSP_OK
            #                 else:
            #                     return RSP_NOT_ONLINE
            #             else:
            #                 return RSP_INVALID_PASSWORD
            #     else:
            #         return RSP_FROM_USER_INVALID

        if loginFlag == True:
            if args < 3:
                return RSP_INVALID_FORMAT
            else:
                if len(arguments[2]) > 500:
                    return RSP_MESSAGE_TOO_LONG
                if arguments[1] in allConnections.values():
                    relayMessage(allConnections, phone,
                                 arguments[1], arguments[2])
                    return RSP_OK
                else:
                    return RSP_NOT_ONLINE
        else:
            return RSP_NOT_LOGGED_IN
    elif command == 'O':
        onlinePrint = 'Users Currently Online:\n'
        if len(online) == 0:
            return RSP_NO_ONLINE_USERS
        elif len(online) == 1 and online[0] == phone:
            return RSP_ONLY_ONE_ONLINE
        else:
            for i in online:
                if i != phone:
                    onlinePrint += i + '\n'
            return onlinePrint
    else:
        return RSP_NOT_A_VALID_PROTOCOL


def processFile(u, msg):
    RSP_OK = '0|Ok'
    RSP_INVALID_FORMAT = '5|Invalid protocol format'
    RSP_NOT_A_VALID_PROTOCOL = '9|Not a valid protocol'

    arguments = msg.split('|')
    args = len(arguments)
    command = arguments[0].upper()

    if command == 'A':
        if args < 3:
            return RSP_INVALID_FORMAT
        else:
            newUser = User(arguments[1], arguments[2])
            u.addUser(newUser)
            return RSP_OK
    else:
        return RSP_NOT_A_VALID_PROTOCOL


def main():
    runServer()


if __name__ == "__main__":
    main()
