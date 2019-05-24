# !/usr/bin/env python
# debug with watch -n 0.5 "lsof -i -n"

from contextlib import closing
import threading
import socket
import time
import sys


class ChatBuddy:
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
        newbuddy_thread = threading.Thread(target=self.ask_for_name, kwargs={"address": addr})
        newbuddy_thread.daemon = True
        newbuddy_thread.start()

    @staticmethod
    def get_sender_from_ip(addr):
        for buddy in buddylist:
            if buddy[1] == addr:
                return buddy[0]
        return None

    def check_message(self, msg, addr):
        try:
            msg_end = msg[2:]  # todo: zwischen prefix und \0
        except IndexError:
            return IndexError
        try:
            msg_prefix1 = msg[0]
        except IndexError:
            return IndexError
        if msg_prefix1 == "0":
            return "0"
        elif msg_prefix1 == "1":
            try:
                msg_prefix2 = msg[1]
            except IndexError:
                return IndexError
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
            return ConnectionResetError
        tmp_socket.close()

    @staticmethod
    def ask_for_name(address):
        tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmpsock.connect((address, 50000))
        msg = "0\0"
        msg = msg.encode("ascii")
        try:
            tmpsock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            return ConnectionResetError
        try:
            name = tmpsock.recv(1004).decode("ascii", "replace")
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
                    newbuddy_thread = threading.Thread(target=self.ask_for_name, kwargs={"address": host})
                    newbuddy_thread.daemon = True
                    newbuddy_thread.start()

    def search_partners(self):
        self.scanning = True
        count = 0
        for ip in range(1, 256):
            count += 1
            self.port_scan("192.168.0." + str(ip))
        print("Scanned " + str(count) + " Hosts")
        self.scanning = False

    def handle_incoming_connection(self, conn, addr):
        try:
            data = conn.recv(1004)  # todo<. receive until \0
            msg = data.decode("ascii", "replace")
            try:
                if self.check_message(msg, addr) == "0":
                    self.send_name(conn)
                    conn.close()
                    if not scanning:
                        self.handle_new_buddy_with_buddylist(addr[0])
            except IndexError:
                return
            except ConnectionResetError:
                return
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            conn.close()
            return
        except OSError:
            return

    #    try:
    #        buddylist.remove((msg_buddyname, addr))
    #        print("Buddy " + msg_buddyname + "disconnected")
    #    except UnboundLocalError:
    #        pass
    #    conn.close() ##close connection here, remove from buddylist

    def tcp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((mylocalip, 50000))
        except OSError:
            print("address already in use. trying to reassign..")
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except TypeError:
                pass
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
    def printlist():
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
        x = buddylist[int(float(selection))]
        buddy_addr = x[1]
        tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("buddy_addr: " + buddy_addr)
        tmpsock.connect((buddy_addr, 50000))
        try:
            tmpsock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            return ConnectionResetError
        tmpsock.close()

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
                print("connection reset error")
                return ConnectionResetError

    @staticmethod
    def send_quit_msg():  # todo quit mechanism???
        msg = ("buddyQUIT-" + myname).encode("ascii", "replace")
        for buddy in buddylist:
            tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmpsock.connect((buddy[1], 50000))
            try:
                tmpsock.send(msg)
            except ConnectionResetError:
                print("connection reset error")
                return ConnectionResetError
            tmpsock.close()

    @staticmethod
    def print_options():
        print('Valid options are S (Scan), L (List), C (Chat), G (GroupChat), Q (Quit)')

    def main_menu(self):
        server_thread = threading.Thread(target=self.tcp_server)
        server_thread.daemon = True
        server_thread.start()
        self.print_options()
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
                self.printlist()
            elif choice == 'C':
                self.printlist()
                self.chat()
            elif choice == 'G':
                self.group_chat()
            elif choice == 'Q':
                self.send_quit_msg()
                print("Quitting..")
                sys.exit()
            else:
                self.print_options()


cb = ChatBuddy()
cb.main_menu()

