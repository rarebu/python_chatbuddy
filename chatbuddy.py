# !/usr/bin/env python
import threading, time, sys
import socket, types
import ipaddress
from multiprocessing import Process
from contextlib import closing

def handle_new_buddy_with_buddylist(buddyname, addr):
    #if isinstance(addr, tuple):
        #print("isinstance")
    if type(addr) ==  tuple:
        #print("istype")
        addr = addr[0]
    #print("MSG_DATA: " + buddyname + " ----- ADDR: " + str(addr) + " ----- BUDDYLIST: " + str(buddylist))
    if (buddyname, addr) not in buddylist:
        #print("\nAdding to Buddylist_neeverreachthis: " + str(buddyname))
        print("New Buddy found: " + buddyname)
        buddylist.append((buddyname, addr))

def check_message(msg, addr):
    try:
        msglist = msg.split("-")
    except IndexError:
        return IndexError
    try:
        msg_prefix = msglist[0]
    except IndexError:
        return IndexError
    try:
        msg_data = msglist[1]
    except IndexError:
        print("No valid name. indexerror")
        return IndexError
    try:
        msg_data2 = msglist[2]
    except IndexError:
        print("empty")
    if msg_prefix == "buddyTCP":
        #print("IF PREFIX BUDDYTCP_CASE")
        #print("Message, addr: " + str(msg) + "-----" + str(addr))
        #re_msg = ("buddyTCP-" + myname).encode('utf-8')
        #shortsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print("addr: "+ str(addr))
        #try:
            #shortsock.connect(addr)
        #except TypeError:
            #shortsock.connect((addr, 50000))
        #try:
            #shortsock.send(re_msg)
        #except ConnectionResetError:
        #    print("connection reset error")
         #   shortsock.close()
        #    return ConnectionResetError
        #shortsock.close()
        handle_new_buddy_with_buddylist(msg_data, addr)
        return msg_data
    elif msg_prefix == "buddyMSG":
        handle_new_buddy_with_buddylist(msg_data, addr)
        print("\nMessage from " + msg_data + ": " + msg_data2)
    elif msg_prefix == "buddyGMSG":
        handle_new_buddy_with_buddylist(msg_data, addr)
        print("\nGroupmessage from " + msg_data + ": " + msg_data2)
    elif msg_prefix == "buddyQUIT":
        print("trying to remove" + msg_data)
        try:
            buddylist.remove((msg_data, addr))
            print("Buddy " + msg_data + " left")
        except ValueError:
            print("empty")


def handle_found_host(address = None):
    ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn = ssock.connect((address, 50000))
    msg = ("buddyTCP-" + myname)
    conn = ssock.send(msg.encode('utf-8'))
    while True:
        try:
            #print("recving message in handle_Found_host")
            msg = ssock.recv(1024).decode('utf-8') #CHANGE TO conn.recv
            if not msg:  # receiving empty messages means that the socket other side closed the socket
                print("connection closed!!!")
                ssock.close()
                break
            msg_buddyname = check_message(msg, address)
            time.sleep(0.5)
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            break
    ssock.close()
    try:
        buddylist.remove((msg_buddyname, address))
        print("Buddy " + msg_buddyname + "removed from buddylist")
    except UnboundLocalError:
        print("empty")
    except ValueError:
        print("empty")

def port_scan(host):
    #print("scanning " + host)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(.1)
        conn = sock.connect_ex((host, 50000))
        sock.close()
        if conn == 0:
            if host != mylocalip:
                #print("\nHost ", host, " is open")
                newbuddy_thread = threading.Thread(target=handle_found_host, kwargs= {"address": host})
                newbuddy_thread.daemon = True
                newbuddy_thread.start()

def search_partners():
    #first = ipaddress.IPv4Address("192.168.0.34")
    #last = ipaddress.IPv4Address("192.168.0.100")
    #ip_range = ipaddress.summarize_address_range(first, last)
    count = 0
    for ip in range(1, 256):
        count += 1
        port_scan("192.168.0." + str(ip))
    print("Scanned " + str(count) +" Hosts")

def handle_incoming_connection(conn, addr):
    nameofconnectedbuddy = ""
    #print('\nIncoming connection accepted: ', addr)
    id = ("buddyTCP-" + myname).encode('utf-8')
    conn.send(id)
    while True:
        try:
            data = conn.recv(1024)
            if not data:  # receiving empty messages means that the socket other side closed the socket
                time.sleep(0.5)
                continue
            msg = data.decode('utf-8')
            try:
                #print("Checking message in IDLER")
                msg_buddyname = check_message(msg, addr)
            except IndexError:
                break
            except ConnectionResetError:
                break
        except socket.timeout:
            print('Socket timed out at', time.asctime())
            conn.close()
            break
        except OSError:
            #print("Connection (closed) because of OSError")
            continue
    try:
        buddylist.remove((msg_buddyname, addr))
        print("Buddy " + msg_buddyname + "disconnected")
    except UnboundLocalError:
        print("empty")


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

    sock.close()

def printlist():
    print("there are " + str(len(buddylist)) + " buddys in your list.")
    count = 0
    for buddy in buddylist:
        print(str(count) + " " + buddy[0])
        count+=1

def chat():
    selection=input("\nPlease choose the Number of your ChatBuddy: ")
    data=input("\nEnter your Message: ")
    msg = ("buddyMSG-" + myname + "-" + data).encode('utf-8')

    x = buddylist[int(float(selection))]
    buddy_addr = x[1]
    ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #print("\n(buddy addr: " + str(buddy_addr))
    conn = ssock.connect((buddy_addr, 50000))

    try:
        ssock.send(msg)
    except ConnectionResetError:
        print("connection reset error")
        conn.close()
        return ConnectionResetError

def group_chat():
    data=input("\nEnter your Message: ")
    msg = ("buddyGMSG-" + myname + "-" + data).encode('utf-8')
    for buddy in buddylist:
        sssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("\n(buddy addr: " + str(buddy[1]))
        conn = sssock.connect((buddy[1], 50000))
        try:
            sssock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            conn.close()
            return ConnectionResetError

def send_quit_msg():
    msg = ("buddyQUIT-" + myname).encode('utf-8')
    for buddy in buddylist:
        ssssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = ssssock.connect((buddy[1], 50000))
        try:
            ssssock.send(msg)
        except ConnectionResetError:
            print("connection reset error")
            conn.close()
            return ConnectionResetError

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
        print("address already in use. try again later.")
        exit(1)
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
