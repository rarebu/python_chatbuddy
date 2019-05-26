# !/usr/bin/env python
# debug with watch -n 0.5 "lsof -i -n"

from contextlib import closing
import threading
import socket
import time
import sys


class ChatBuddy:
    def __init__(self):
        self.init()
        self.print_options()
        self.main_menu()

    @staticmethod
    def init():
        global scanning
        global myname
        global buddylist
        global mylocalip

        mylocalip = ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [
            [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in
             [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0])
        scanning = False
        buddylist = []
        myname = input('Enter your Nickname: ')

    def handle_new_buddy_with_buddylist(self, addr):
        ney_buddy_thread = threading.Thread(target=self.ask_for_name, kwargs={"address": addr})
        ney_buddy_thread.daemon = True
        ney_buddy_thread.start()

    @staticmethod
    def get_sender_from_ip(addr):
        for buddy in buddylist:
            if buddy[1] == addr:
                return buddy[0]
        return None

# todo: funktionen anchbauen und input auf /0 prüfen
    # def check_message(self, msg, addr):
    #     msg_list = msg.split("\0")
    #     print("1: " + str(msg_list))
    #     msg = msg_list[0]
    #     print("2: " + msg)
    #     try:
    #         msg_prefix1 = msg[0]
    #     except IndexError:
    #         print("msg: " + msg)
    #         print("yeep")
    #         return "-1"
    #     print("3: " + msg_prefix1)
    #     if msg_prefix1 == "0":
    #         print("4: returning")
    #         return "0"
    #     elif msg_prefix1 == "1":
    #         try:
    #             msg_prefix2 = msg[1]
    #         except IndexError:
    #             return "-1"
    #         if msg_prefix2 == "0":
    #             message = msg[2:]
    #             try:
    #                 print("\nMessage from " + self.get_sender_from_ip(addr[0]) + ": " + message)
    #             except TypeError:
    #                 print("\nMessage from unknown Sender (" + addr[0] + "): " + message)
    #         elif msg_prefix2 == "1":
    #             try:
    #                 print("\nGroupmessage from " + self.get_sender_from_ip(addr[0]) + ": " + message)
    #             except TypeError:
    #                 print("\nGroupmessage from unknown Sender (" + addr[0] + "): " + message)
    #         return "1"
    #     else :
    #         return "-1"

    def check_message(self, msg, addr):
        try:
            msg_end = msg[2:]  # todo: zwischen prefix und \0
        except IndexError:
            print("IndexError in check_message() at msg_end = msg[2:]")
        try:
            msg_prefix1 = msg[0]
        except IndexError:
            return "-1"               # empty message
        if msg_prefix1 == "0":
            return "0"
        elif msg_prefix1 == "1":
            try:
                msg_prefix2 = msg[1]
            except IndexError:
                print("IndexError in check_message() at msg_prefix2 = msg[1]")
            if msg_prefix2 == "0":
                try:
                    print("\nMessage from " + self.get_sender_from_ip(addr[0]) + ": " + msg_end)
                except TypeError:
                    print("\nMessage from unknown Sender (" + addr[0] + "): " + msg_end)
            elif msg_prefix2 == "1":
                try:
                    print("\nGroupmessage from " + self.get_sender_from_ip(addr[0]) + ": " + msg_end)
                except TypeError:
                    print("\nGroupmessage from unknown Sender (" + addr[0] + "): " + msg_end)
            return "1"
        return "-1"

    @staticmethod
    def send_name(tmp_socket):
        my_id = myname.encode("ascii", "replace")
        try:
            tmp_socket.send(my_id)
        except ConnectionResetError:
            print("ConnectionResetError in send_name()")
        tmp_socket.close()

    # @staticmethod
    # def ask_for_name(address):
    #     tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         tmpsock.connect((address, 50000))
    #     except:
    #         print("\nOOPS - in ask_for_name() at sock.connect")
    #     msg = "0\0"
    #     msg = msg.encode("ascii")
    #     try:
    #         print("ASKING FOR NAME")
    #         tmpsock.send(msg)
    #     except ConnectionResetError:
    #         print("ConnectionResetError in ask_for_name()")
    #     try:    # todo somewhereelse(?): also ask for name if appending to buddy_list (if name changes)
    #         name = tmpsock.recv(1004).decode("ascii", "replace")
    #         for buddy in buddy_list:
    #             if (buddy[1] != address) and (buddy[0] != name):
    #                     print("\n::::: New Buddy found: " + name + " (" + address + ")")
    #                     buddy_list.append((name, address))
    #             elif (buddy[1] == address) and (buddy[0] != name):
    #                     print("\n::::: Buddy " + buddy[1] + " has a new name: " + name + " (" + address + ")")
    #                     buddy_list.remove(buddy)
    #                     buddy_list.append((name, address))
    #     except socket.timeout:
    #         print('Socket timed out at', time.asctime())
    #     tmpsock.close()

    @staticmethod
    def ask_for_name(address):
        tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmpsock.connect((address, 50000))
        msg = "0\0"
        msg = msg.encode("ascii")
        try:
            tmpsock.send(msg)
        except ConnectionResetError:
            print("ConnectionResetError in ask_for_name()")
        try:    # todo somewhereelse(?): also ask for name if appending to buddylist (if name changes)
            name = tmpsock.recv(1004).decode("ascii", "replace")
            for buddy in buddylist:
                print("BUDDY: " + str(buddy))
            if (name, address) not in buddylist:
                buddylist.append((name, address))
                print("\n::::: New Buddy found: " + name + " (" + address + ")")
        except socket.timeout:
            print('Socket timed out at', time.asctime())
        tmpsock.close()

    def port_scan(self, host):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(.1)
            conn = sock.connect_ex(
                (host, 50000))
            if conn == 0:
                if host != mylocalip:
                    ney_buddy_thread = threading.Thread(target=self.ask_for_name, kwargs={"address": host})
                    ney_buddy_thread.daemon = True
                    ney_buddy_thread.start()

    def search_partners(self):
        global scanning
        scanning = True
        count = 0
        for ip in range(1, 256):
            count += 1
            self.port_scan("192.168.0." + str(ip))
        print("Scanned " + str(count) + " Hosts")
        scanning = False

    def handle_incoming_connection(self, conn, addr):
        try:
            data = conn.recv(1004)
            msg = data.decode("ascii", "replace")
            try:
                if self.check_message(msg, addr) == "0":
                    self.send_name(conn)
                    conn.close()
                    global scanning
                    if not scanning:
                        self.handle_new_buddy_with_buddylist(addr[0])
            except IndexError:
                print("OOPS - IndexError in handle_incoming_connection()")
                return
            except ConnectionResetError:
                print("OOPS - ConnectionResetError in handle_incoming_connection()")
                return
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            conn.close()
            return
        except OSError:
            print("OOPS - OSError in handle_incoming_connection()")
            return

    def tcp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((mylocalip, 50000))
        except OSError:
            print("address already in use. trying to reassign..")
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((mylocalip, 50000))
                except OSError:
                    print("OOPS - Cannot start TCP-Server")
                    exit(1)
            except TypeError:
                print("OOPS - TypeError in tcp_server")
        print("Binding Server to " + mylocalip + ":50000")
        sock.listen(1)
        while True:
            try:
                conn, address = sock.accept()
                if mylocalip == address[0]:
                    continue
                p = threading.Thread(target=self.handle_incoming_connection, args=[conn, address])
                p.daemon = True
                p.start()
            except socket.timeout:
                pass
        conn.close()
        sock.close()

    @staticmethod
    def print_list():
        if len(buddylist) > 1:
            print(":::::  There are " + str(len(buddylist)) + " buddys in your Buddylist")
            count = 0
            for buddy in buddylist:
                print("::::: " + str(count) + " " + buddy[0] + " (" + buddylist[0][1] + ")")
                count += 1
        elif len(buddylist) == 1:
            print(":::::  There is one buddy in your Buddylist")
            print(":::::  0 " + str(buddylist[0][0]) + " (" + buddylist[0][1] + ")")
        elif len(buddylist) == 0:
            print("::::: The Buddylist is empty :/")

    @staticmethod
    def chat():
        selection = input("\nPlease choose the Number of your ChatBuddy: ")
        data = input("\nEnter your Message: ")
        msg = ("10" + data + "\0").encode("ascii", "replace")
        try:
            buddy = buddylist[int(float(selection))]
            buddy_addr = buddy[1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((buddy_addr, 50000))
            except ConnectionResetError:
                print("OOPS - ConnectionResetError in chat() at sock.connect()")
            try:
                sock.send(msg)
            except ConnectionResetError:
                print("OOPS - ConnectionResetError in chat() at sock.send()")
                return ConnectionResetError
            sock.close()
        except ValueError:
            print("OOPS - ValueError in chat()")

    @staticmethod
    def group_chat():
        data = input("\nEnter your Message: ")
        msg = ("11" + data).encode("ascii", "replace")
        for buddy in buddylist:
            tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmpsock.connect((buddy[1], 50000))
            try:
                tmpsock.send(msg)
            except ConnectionResetError:
                print("ConnectionResetError in group_chat()")
                return ConnectionResetError

    @staticmethod
    def print_options():
        print('Valid options are S (Scan), L (List), C (Chat), G (GroupChat), Q (Quit)')

    def main_menu(self):
        server_thread = threading.Thread(target=self.tcp_server)
        server_thread.daemon = True
        server_thread.start()
        while True:
            try:
                choice = input('choose an option (h for help): ')
            except KeyboardInterrupt:
                continue
            if choice == 'S':
                print("Scanning...")
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
                print("Quitting..")
                sys.exit()
            else:
                self.print_options()


cb = ChatBuddy()
