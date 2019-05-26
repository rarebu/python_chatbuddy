# !/usr/bin/env python
# debug with watch -n 0.5 'lsof -i -n'

from contextlib import closing
import threading
import socket
import time
import sys


class ChatBuddy:
    def __init__(self):
        self.initialize()
        self.start_tcp_server()
        self.main_menu()

    @staticmethod
    def initialize():
        global scanning
        global my_name
        global buddy_list
        global my_local_ip

        my_local_ip = ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith('127.')]
                         or [
            [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
             [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ['no IP found'])[0])
        scanning = False
        buddy_list = []
        my_name = input('::::: Enter your Nickname: ')

    @staticmethod
    def check_message(data):
        try:
            data[0]
        except IndexError:
            print('::::: you got scanned!')
            return -1
        msg_list = data.split('\0')
        msg = msg_list[0]
        try:
            msg_prefix1 = msg[0]
        except IndexError:
            return -1
        if msg_prefix1 == '0':
            return 0
        elif msg_prefix1 == '1':
            try:
                msg_prefix2 = msg[1]
            except IndexError:
                print('OOPS - Got invalid first two bytes in check_message()')
                return -1
            if msg_prefix2 == '0':
                return 10
            elif msg_prefix2 == '1':
                return 11
            return -1
        return -1

    @staticmethod
    def send_name_and_chat(sock):
        my_id = my_name.encode('ascii', 'replace')
        try:
            sock.send(my_id)
        except ConnectionResetError:
            print('ConnectionResetError in send_name()')
        # todo: keep connection active here for chatting DRINGEND
        sock.close()

    @staticmethod
    def ask_for_name_and_chat(address):
        same_name = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((address, 50000))
        except ConnectionRefusedError:
            print('OOPS - eventually port 50000 is used for something else there..')
            return
        msg = '0\0'
        msg = msg.encode('ascii')
        try:
            sock.send(msg)
        except ConnectionResetError:
            print('OOPS - ConnectionResetError in ask_for_name()')
            return
        except BrokenPipeError:
            print('OOPS - Broken Pipe')
            return
        try:
            name = sock.recv(1004).decode('ascii', 'replace')
        except socket.timeout:
            print('OOPS - Socket timed out at', time.asctime())
            return
        if not buddy_list:
            print('::::: New Buddy found: ' + name + ' (' + address + ')')
            buddy_list.append((name, address))
            sock.close()
        for entry in buddy_list:
            if entry[0] == name:
                same_name = True
                print('OOPS - cannot add client, name already exists..')  # todo handle if two clients have same name
            break
        if not same_name:
            print('::::: New Buddy found: ' + name + ' (' + address + ')')
            buddy_list.append((name, address))
        # todo: keep connection active here for chatting DRINGEND
        sock.close()
        # todo remove buddy from buddy_list after connection is closed

    def port_scan(self, host):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(.1)
            conn = sock.connect_ex(
                (host, 50000))
            if conn == 0:
                if host != my_local_ip:
                    ney_buddy_thread = threading.Thread(target=self.ask_for_name_and_chat, kwargs={'address': host})
                    ney_buddy_thread.daemon = True
                    ney_buddy_thread.start()

    def search_partners(self):
        global scanning
        global my_local_ip
        count = 0
        ip_list = my_local_ip.split('.')
        scanning = True
        for ip in range(1, 256):
            count += 1
            self.port_scan(ip_list[0] + '.' + ip_list[1] + '.' + ip_list[2] + '.' + str(ip))
        scanning = False
        print('::::: Scanning finished')

    def handle_incoming_connection(self, conn):
        try:
            data = conn.recv(1004)
            msg = data.decode('ascii', 'replace')
            check_message_value = self.check_message(msg)
            if check_message_value == 0:
                self.send_name_and_chat(conn)
                conn.close()
            elif check_message_value == 10:
                print('10')                 # todo chat? DRINGEND
            elif check_message_value == 11:
                print('11')                 # todo chat? DRINGEND
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            conn.close()
            return
        except OSError:
            print('OOPS - OSError in handle_incoming_connection()')
            return

    def start_tcp_server(self):
        server_thread = threading.Thread(target=self.tcp_server)
        server_thread.daemon = True
        server_thread.start()

    def tcp_server(self):
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
                    print('OOPS - Cannot start TCP-Server')
                    sys.exit(1)  # todo: proper exit
            except TypeError:
                print('OOPS - TypeError in tcp_server')
        print('\n::::: Binding Server to ' + my_local_ip + ':50000')
        sock.listen(1)
        while True:
            try:
                conn, address = sock.accept()
                if my_local_ip == address[0]:
                    continue
                p = threading.Thread(target=self.handle_incoming_connection, args=[conn])
                p.daemon = True
                p.start()
            except socket.timeout:
                pass
        conn.close()
        sock.close()

    @staticmethod
    def print_list():
        if len(buddy_list) > 1:
            print(':::::  There are ' + str(len(buddy_list)) + ' buddys in your Buddylist')
            count = 0
            for buddy in buddy_list:
                print('::::: ' + str(count) + ' ' + buddy[0] + ' (' + buddy_list[0][1] + ')')
                count += 1
        elif len(buddy_list) == 1:
            print(':::::  There is one buddy in your Buddylist')
            print(':::::  0 ' + str(buddy_list[0][0]) + ' (' + buddy_list[0][1] + ')')
        elif len(buddy_list) == 0:
            print('::::: The Buddylist is empty :/')

    # @staticmethod
    # def chat():
    #     selection = input('\n::::: Please choose the Number of your ChatBuddy: ')
    #     try:
    #         entry = int(float(selection))
    #     except ValueError:
    #         print('OOPS - bad input')
    #         return
    #     data = input('\n::::: Enter your Message: ')
    #     msg = ('10' + data + '\0').encode('ascii', 'replace')
    #     try:
    #         buddy = buddy_list[entry]
    #         buddy_addr = buddy[1]
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         try:
    #             sock.connect((buddy_addr, 50000))
    #         except ConnectionResetError:
    #             print('OOPS - ConnectionResetError in chat() at sock.connect()')
    #         except ConnectionRefusedError:
    #             data = input('\n::::: Buddy not online. Remove from Buddylist? (Y/N): ')
    #             if data == 'Y':
    #                 buddy_list.remove(buddy_list[entry])
    #                 print('\n::::: Buddy removed')
    #             else:
    #                 sock.close()
    #                 return
    #         try:
    #             sock.send(msg)
    #         except ConnectionResetError:
    #             print('OOPS - ConnectionResetError in chat() at sock.send()')
    #             sock.close()
    #             return
    #         except BrokenPipeError:
    #             sock.close()
    #             return
    #         print('::::: Message sent to ' + buddy[0] + ': ' + data)
    #         sock.close()
    #     except ValueError:
    #         print('OOPS - ValueError in chat()')
    #     except IndexError:
    #         print('OOPS - IndexError in chat()')
    #
    # @staticmethod
    # def group_chat():
    #     data = input('\n::::: Enter your Message: ')
    #     msg = ('11' + data + '\0').encode('ascii', 'replace')
    #     for buddy in buddy_list:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         sock.connect((buddy[1], 50000))
    #         try:
    #             sock.send(msg)
    #         except ConnectionResetError:
    #             print('::::: ConnectionResetError in group_chat()')
    #             return ConnectionResetError
    #         print('::::: Message Sent: ' + data + ' (Group Message)')

    @staticmethod
    def print_options():
        print('Valid options are S (Scan), L (List), C (Chat), G (GroupChat), Q (Quit)')

    def main_menu(self):
        while True:
            try:
                choice = input('\n::::: choose an option (h for help): ')
            except KeyboardInterrupt:
                continue
            if choice == 'S':
                print('::::: Scanning...')
                scan_thread = threading.Thread(target=self.search_partners)
                scan_thread.daemon = True
                scan_thread.start()
            elif choice == 'L':
                self.print_list()
            elif choice == 'C':
                self.print_list()
                # todo : chat?
            elif choice == 'G':
                print('gc')
                # todo : chat?
            elif choice == 'Q':
                print('::::: Quitting..')
                sys.exit()  # todo: proper exit
            else:
                self.print_options()


cb = ChatBuddy()
