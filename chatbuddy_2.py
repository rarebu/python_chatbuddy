# !/usr/bin/env python
# debug with watch -n 0.5 "lsof -i -n"

import threading, time, sys
import socket, types
import ipaddress
from multiprocessing import Process
from contextlib import closing


def handle_new_buddy_with_buddylist(addr):
    newbuddy_thread = threading.Thread(target=ask_for_name, kwargs={"address": addr})
    newbuddy_thread.daemon = True
    newbuddy_thread.start()
    #ask_for_name(addr)
    #if (ask_for_name(addr), addr) not in buddylist:
    #if type(addr) == tuple:
    #    addr = addr[0]
    #    print("addr: " + addr)
    #if (buddyname, addr) not in buddylist:
    #    print("\n----- ----- ----- ----- -----")
    #    print("New Buddy found: " + buddyname)
    #    print("----- ----- ----- ----- -----")
    #    buddylist.append((buddyname, addr))


def get_sender_from_ip(addr):
    for buddy in buddylist:
        if buddy[1] == addr:
            return buddy[0]
    return None


def check_message(msg, addr):
    print("\n--- msg: " + msg)
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
                print("\nMessage from " + get_sender_from_ip(addr[0]) + ": " + msg_end)
            except TypeError:
                print("\nMessage from unknown Sender: " + msg_end)
        elif msg_prefix2 == "1":
            print("\nGroupmessage from " + get_sender_from_ip(addr[0]) + ": " + msg_end)
        return "1"
    return "-1"


def send_name(tmp_socket):
    my_id = myname.encode("ascii", "replace")
    try:
        tmp_socket.send(my_id)
    except ConnectionResetError:
        return ConnectionResetError
    tmp_socket.close()


def ask_for_name(address):
    print("\nask_for_name: " + str(address))
    tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tmpsock.connect((address, 50000))
    msg = "0\0"
    msg = msg.encode("ascii")
    print("betweenstep")
    try:
        print("asking: with a 0")
        tmpsock.send(msg)
    except ConnectionResetError:
        print("connection reset error")
        return ConnectionResetError
    try:
        name = tmpsock.recv(1004).decode("ascii", "replace")
        print("received : " + name)
        if (name, address[0]) not in buddylist:
            buddylist.append((name, address[0]))
            print("\nappending to buddylist:" + name)  # todo check if already in buddy list
    except socket.timeout:
        print('Socket timed out at', time.asctime())
    tmpsock.close()


def port_scan(host):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(.1)
        conn = sock.connect_ex(
            (host, 50000))
        if conn == 0:
            if host != mylocalip:
                newbuddy_thread = threading.Thread(target=ask_for_name, kwargs={"address": host})
                newbuddy_thread.daemon = True
                newbuddy_thread.start()


def search_partners():
    count = 0
    for ip in range(1, 256):
        count += 1
        port_scan("192.168.0." + str(ip))
    print("Scanned " + str(count) + " Hosts")


def handle_incoming_connection(conn, addr):
    try:
        data = conn.recv(1004)  # todo<. receive until \0
        msg = data.decode("ascii", "replace")
        try:
            if check_message(msg, addr) == "0":
                print("handle_incoming_connection: check_message = 0")
                send_name(conn)
                handle_new_buddy_with_buddylist(addr[0])
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


def tcp_server():
    sock.listen(1)
    while True:
        try:
            conn = sock.accept()
            incomingaddr = conn[1]
            if mylocalip == incomingaddr[0]:
                continue
            p = threading.Thread(target=handle_incoming_connection, args=conn)
            p.daemon = True
            p.start()
        except socket.timeout:
            print('\nSocket timed out listening', time.asctime())
    conn.close()
    sock.close()


def printlist():
    print("\n----- ----- ----- ----- -----")
    if len(buddylist) > 1:
        print("There are " + str(len(buddylist)) + " buddys in your Buddylist")
        count = 0
        for buddy in buddylist:
            print(str(count) + " " + buddy[0])
            count += 1
    elif len(buddylist) == 1:
        print("There is one buddy in your Buddylist")
        print("0 " + str(buddylist[0][0]))
    elif len(buddylist) == 0:
        print("The Buddylist is empty :/")
    print("----- ----- ----- ----- -----")


def chat():
    selection = input("\nPlease choose the Number of your ChatBuddy: ")
    data = input("\nEnter your Message: ")
    msg = ("10" + data + "\0").encode("ascii", "replace")
    x = buddylist[int(float(selection))]
    buddy_addr = x[1]  # todo get running socket from buddylist
    tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tmpsock.connect((buddy_addr, 50000))  # todo get addr from buddy list
    try:
        tmpsock.send(msg)
    except ConnectionResetError:
        print("connection reset error")
        return ConnectionResetError
    tmpsock.close()


def group_chat():
    data = input("\nEnter your Message: ")
    msg = ("11" + data).encode("ascii", "replace")
    for buddy in buddylist:
        tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmpsock.connect((buddy[1], 50000))
        print("\n(buddy addr: " + str(buddy[1]))
        try:
            tmpsock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            # conn.close()
            return ConnectionResetError


def send_quit_msg():
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


def main_menu():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global mylocalip
    mylocalip = ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [
        [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in
         [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0])
    print("Binding Server to " + mylocalip + ":50000")
    try:
        sock.bind((mylocalip, 50000))
    except OSError:
        print("address already in use. trying to reassign..")
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except TypeError:
            pass
        # exit(1)
    global myname
    myname = input('Enter your Nickname: ')
    global buddylist
    buddylist = []
    server_thread = threading.Thread(target=tcp_server)
    server_thread.daemon = True
    server_thread.start()
    while True:
        try:
            choice = input('choose an option ')
        except KeyboardInterrupt:
            continue
        if choice == 'S':
            print("Scanning...")
            scan_thread = threading.Thread(target=search_partners)
            scan_thread.daemon = True
            scan_thread.start()
        if choice == 'L':
            printlist()
        if choice == 'C':
            chat()
        if choice == 'G':
            group_chat()
        if choice == 'Q':
            send_quit_msg()
            print("Quitting..")
            sock.close()
            sys.exit()
        else:
            print('Valid options are S (Scan), L (List), C (Chat), G (GroupChat), Q (Quit)')


if __name__ == '__main__':
    main_menu()
