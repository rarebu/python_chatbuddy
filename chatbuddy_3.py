# !/usr/bin/env python
# debug with watch -n 0.5 'lsof -i -n'

from contextlib import closing
import threading
import socket
import time
import sys


class ChatBuddy:
    def start(self):
        self.initialize()
        self.start_tcp_server()
        self.start_send_messages()
        self.main_menu()

    @staticmethod
    def initialize():
        global quitting
        global my_name
        global buddy_list
        global my_local_ip
        global message_list

        my_local_ip = ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')]
                         or [
                             [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                              [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ['no IP found'])[0])
        quitting = False
        buddy_list = []
        message_list = []
        my_name = input('\n::::: Enter your Nickname: ')

    @staticmethod
    def check_message(data, name):
        try:
            data[0]
        except IndexError:
            return '2'
        msg_list = data.split('\0')
        msg = msg_list[0]
        try:
            msg_prefix1 = msg[0]
        except IndexError:
            return '-1'
        if msg_prefix1 == '1':
            return msg[1:]
        elif msg_prefix1 == '0':
            try:
                msg_prefix2 = msg[1]
            except IndexError:
                print('\nOOPS - Got invalid first two bytes in check_message()')
                return '3'
            if msg_prefix2 == '0':
                print('\n:---: Message from ' + name + ': ' + msg[2:])
                return '-1'
            elif msg_prefix2 == '1':
                print('\n:---: Groupmessage from ' + name + ': ' + msg[2:])
                return '-1'
            return '-1'
        return '-1'

    def send_name_and_chat(self, sock, name):
        address = sock.getpeername()[0]
        msg = my_name + '\0'
        message = msg.encode('ascii', 'replace')
        try:
            sock.send(message)
        except ConnectionResetError:
            print('ConnectionResetError in send_name()')
        if self.add_to_buddylist(name, address, sock) == 1:
            return
        p = threading.Thread(target=self.receive_messages, args=[sock, name])
        p.start()
        p.join()
        self.remove_buddy(name)

    @staticmethod
    def add_to_buddylist(name, address, sock):  # wenn buddy schon da, mache nichts
        if not buddy_list:
            print('\n::::: New Buddy found: ' + name + ' (' + address + ')')
            buddy_list.append((name, address, sock))
            return 0
        else:
            for entry in buddy_list:
                if entry[0] == name:
                    if entry[1] == address:  # if buddy has same name and address, do nothing
                        return 1
                    else:
                        print('\n::::: New Buddy with same name found.')
                break
            print('\n::::: New Buddy found: ' + name + ' (' + address + ')')
            buddy_list.append((name, address, sock))
            return 0

    def receive_messages(self, sock, name):
        while True:
            global quitting
            if quitting:
                break
            # try:
            incoming_msg = sock.recv(1004).decode('ascii', 'replace')
            if self.check_message(incoming_msg, name) == '2':
                break
            # except socket.timeout:
            #     print('\nOOPS - Socket timed out at', time.asctime())
            #     break
        self.remove_buddy(name)

    def start_send_messages(self):
        p = threading.Thread(target=self.send_messages)
        p.daemon = True
        p.start()

    def send_messages(self):
        global message_list
        global buddy_list
        while True:
            global quitting
            if quitting:
                break
            for message in message_list:
                for buddy in buddy_list:
                    if message[0] == buddy[0]:
                        msg = '00' + message[1] + '\0'
                        msg_encoded = msg.encode('ascii', 'replace')
                        try:
                            try:
                                buddy[2].send(msg_encoded)
                            except OSError:
                                print()
                                self.remove_buddy(buddy[0])
                        except ConnectionResetError:
                            print('ConnectionResetError in send_messages()')
                        print('\n::::: Message sent')
                        try:
                            message_list.remove(message)
                        except ValueError:
                            pass

    def ask_for_name_and_chat(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((address, 50000))
        except ConnectionRefusedError:
            print('\nOOPS - eventually port 50000 is used for something else there..')
            return
        msg = '1' + my_name + '\0'
        msg = msg.encode('ascii')
        try:
            sock.send(msg)
        except ConnectionResetError:
            print('\nOOPS - ConnectionResetError in ask_for_name()')
            return
        except BrokenPipeError:
            print('\nOOPS - Broken Pipe')
            return
        try:
            name = sock.recv(1004).decode('ascii', 'replace')
        except socket.timeout:
            print('\nOOPS - Socket timed out at', time.asctime())
            return
        if self.add_to_buddylist(name, address, sock) == 1:  # wenn buddy schon da, mache nichts
            return
        p = threading.Thread(target=self.receive_messages, args=[sock, name])
        p.start()
        p.join()
        sock.close()
        self.remove_buddy(name)

    @staticmethod
    def remove_buddy(name):
        for buddy in buddy_list:
            if buddy[0] == name:
                try:
                    buddy_list.remove(buddy)
                    print('\n::::: Buddy ' + name + ' left')
                except ValueError:
                    pass

    def port_scan(self, host):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(.1)
            conn = sock.connect_ex((host, 50000))
            if conn == 0:
                if host != my_local_ip:
                    ney_buddy_thread = threading.Thread(target=self.ask_for_name_and_chat, kwargs={'address': host})
                    ney_buddy_thread.daemon = True
                    ney_buddy_thread.start()

    def search_partners(self):
        count = 0
        ip_list = my_local_ip.split('.')
        for ip in range(1, 256):
            target_ip = ip_list[0] + '.' + ip_list[1] + '.' + ip_list[2] + '.' + str(ip)
            for buddy in buddy_list:  # only scan addresses that are not in buddylist
                if target_ip == buddy[1]:
                    continue
            count += 1
            self.port_scan(target_ip)
        print('\n::::: Scanning finished')

    def handle_incoming_connection(self, conn):
        try:
            data = conn.recv(1004)
            msg = data.decode('ascii', 'replace')
            check_message_value = self.check_message(msg, '')
            if check_message_value == '-1':
                return
            elif check_message_value == '2':
                return
            elif check_message_value == '3':
                self.send_name_and_chat(conn, check_message_value)
                conn.close()
            else:
                self.send_name_and_chat(conn, check_message_value)
                conn.close()
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            conn.close()
            return
        except OSError:
            print('\nOOPS - OSError in handle_incoming_connection()')
            return

    def start_tcp_server(self):
        server_thread = threading.Thread(target=self.tcp_server)
        server_thread.daemon = True
        server_thread.start()

    def tcp_server(self):
        global quitting
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((my_local_ip, 50000))
        except OSError:
            print('\nOOPS - Address already in use. Trying to reassign..')
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((my_local_ip, 50000))
                except OSError:
                    print('\nOOPS - Cannot start TCP-Server')
                    quitting = True
                    sys.exit(1)
            except TypeError:
                print('\nOOPS - TypeError in tcp_server')
        print('\n::::: Binding Server to ' + my_local_ip + ':50000')
        sock.listen(1)
        while True:
            if quitting:
                break
            try:
                conn, address = sock.accept()
                if my_local_ip == address[0]:
                    continue
                p = threading.Thread(target=self.handle_incoming_connection, args=[conn])
                p.daemon = True
                p.start()
            except socket.timeout:
                pass
        sock.close()

    @staticmethod
    def print_list():
        if len(buddy_list) > 1:
            print('\n::::: There are ' + str(len(buddy_list)) + ' Buddys in your Buddylist')
            count = 0
            for buddy in buddy_list:
                print('\n::::: ' + str(count) + ' ' + buddy[0] + ' (' + buddy_list[0][1] + ')')
                count += 1
        elif len(buddy_list) == 1:
            print('\n::::: There is one buddy in your Buddylist')
            print('\n::::: 0 ' + str(buddy_list[0][0]) + ' (' + buddy_list[0][1] + ')')
        elif len(buddy_list) == 0:
            print('\n::::: The Buddylist is empty :/')

    @staticmethod
    def chat():
        selection = input('\n::::: Please choose the Number of your ChatBuddy: ')
        try:
            entry = int(float(selection))
        except ValueError:
            print('\nOOPS - bad input')
            return
        data = input('\n::::: Enter your Message: ')
        try:
            buddy = buddy_list[entry]
        except IndexError:
            return
        message_list.append((buddy[0], data))

    @staticmethod
    def group_chat():
        data = input('\n::::: Enter your Message: ')
        msg = '01' + data + '\0'
        message = msg.encode('ascii', 'replace')
        for buddy in buddy_list:
            sock = buddy[2]
            sock.send(message)
        print('\n::::: Groupmessage sent')

    @staticmethod
    def print_options():
        print('Valid options are S (Scan), L (List), C (Chat), G (GroupChat), Q (Quit)')

    def main_menu(self):
        global quitting
        while True:
            try:
                choice = input('\n::::: choose an option (h for help): ')
            except KeyboardInterrupt:
                continue
            if choice == 'S':
                print('\n::::: Scanning...')
                scan_thread = threading.Thread(target=self.search_partners)
                scan_thread.daemon = True
                scan_thread.start()
            elif choice == 'L':
                self.print_list()
            elif choice == 'C':
                self.print_list()
                self.chat()
            elif choice == 'G':
                self.group_chat()
            elif choice == 'Q':
                print('\n::::: Quitting..')
                quitting = True
                break
            else:
                self.print_options()
        sys.exit()


cb = ChatBuddy()
cb.start()
