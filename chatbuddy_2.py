# !/usr/bin/env python
# debug with watch -n 0.5 "lsof -i -n"

import threading, time, sys
import socket, types
import ipaddress
from multiprocessing import Process
from contextlib import closing


def handle_new_buddy_with_buddylist(buddyname, addr):
    if type(addr) == tuple:
        addr = addr[0]
    if (buddyname, addr) not in buddylist:
        print("\n----- ----- ----- ----- -----")
        print("New Buddy found: " + buddyname)
        print("----- ----- ----- ----- -----")
        buddylist.append((buddyname, addr))


def check_message(msg, addr):  # todo nichts returnen
    print("\n--- msg: " + msg)
    try:
        msg_end = msg[2:]  # todo: zwischen prefix und \0
    except IndexError:
        return IndexError
    try:
        msg_prefix1 = msg[0]
    except IndexError:
        return IndexError
    print("\n--- msg_prefix1: " + msg_prefix1)
    if msg_prefix1 == "0":
        send_name(addr)
        handle_new_buddy_with_buddylist(msg_end, addr)  # todo: sende namen zurück
        return msg_end
    elif msg_prefix1 == "1":
        try:
            msg_prefix2 = msg[:1]
        except IndexError:
            return IndexError
        if msg_prefix2 == "0":
            handle_new_buddy_with_buddylist(msg_end, addr)
            print("\nMessage from " + msg_end + ": " + msg_end)
        elif msg_prefix2 == "1":
            handle_new_buddy_with_buddylist(msg_end, addr)
            print("\nGroupmessage from " + msg_end + ": " + msg_end)
        handle_new_buddy_with_buddylist(msg_end, addr)
        print("\nMessage from " + msg_end + ": " + msg_end)
    elif msg_end == "buddyQUIT":
        print("Buddy " + msg_end + " left")
        try:
            buddylist.remove((msg_end, addr))
        except ValueError:
            pass


def handle_found_host(address=None):  # todo: prefix 0 (nach namen fragen) #todo:
    print("----- YES HANdle_foudn_host")
    foundhost_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    foundhost_sock.connect((address, 50000))
    msg = "0\0"  # todo keep connection active here and APPEND to buddylist[]
    foundhost_sock.send(msg.encode("ascii", "replace"))
    buddylist.append((address, foundhost_sock))  # danach??
    while True:
        try:
            msg = foundhost_sock.recv(1004).decode("ascii")
            if not msg:
                print("connection closed!!!")
                foundhost_sock.close()
                break
            msg_buddyname = check_message(msg, address)
            time.sleep(0.5)
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            break
    try:
        buddylist.remove((msg_buddyname, address))
        print("Buddy " + msg_buddyname + " removed from buddylist")
    except UnboundLocalError:
        pass
    except ValueError:
        pass
    foundhost_sock.close()


def port_scan(host):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(.1)
        conn = sock.connect_ex(
            (host, 50000))  # todo scan for addresses add to buddylist as tuple with connection and addr
        if conn == 0:
            if host != mylocalip:
                print("----- YES FOUND ONE")
                newbuddy_thread = threading.Thread(target=handle_found_host, kwargs={"address": host})
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
        data = conn.recv(1024)  # todo<. receive until \0
        msg = data.decode("ascii", "replace")
        try:
            msg_buddyname = check_message(msg, addr)
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
            if mylocalip == incomingaddr[0]:  # todo what is happening here
                continue
            my_id = myname.encode("ascii", "replace")
            conn[0].send(my_id)
            p = threading.Thread(target=handle_incoming_connection, args=conn)
            p.daemon = True
            p.start()
        except socket.timeout:
            print('\nSocket timed out listening', time.asctime())
    conn.close()
    sock.close()


def printlist():
    print("\n----- ----- ----- ----- -----")
    print("There are " + str(len(buddylist)) + " buddys in your list.")
    count = 0
    for buddy in buddylist:
        print(str(count) + " " + buddy[0])
        count += 1
    print("----- ----- ----- ----- -----")


def send_name(addr):
    tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tmpsock.connect((addr[0], addr[1]))
    msg = myname + "\o"
    try:
        tmpsock.send(msg)
    except ConnectionResetError:
        print("connection reset error")
        return ConnectionResetError
    tmpsock.close()


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
        # sssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("\n(buddy addr: " + str(buddy[1]))
        # conn = sssock.connect((buddy[1], 50000))
        try:
            sock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            # conn.close()
            return ConnectionResetError


def send_quit_msg():
    msg = ("buddyQUIT-" + myname).encode("ascii", "replace")
    for buddy in buddylist:
        tmpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmpsock.connect((buddy[1], 50000))  # todo port
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
