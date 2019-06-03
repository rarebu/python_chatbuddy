client A (Name foo)							Client B (Name bar)

[S]can
search ip addresses
for open port 50000
conn = sock.connect_ex((ip, 50000))
if conn == 0 then we found a buddy
use the found ip and port to open a
connection and send a 1 and your name
send: "1foo\0"	--------------------------> get message, add buddy to
											list,
										 	keep connection alive for 
										 	chatting
										 	answer with name
get name		<-------------------------- send: 'bar\0'
add buddy to list
keep connectin alive for chatting



[C]chat
choose buddy from list
enter message
send: "00hey whats up bar\0" ---------------> receive message
											  search in list for buddy name (via address)
											  print message



[G]roupchat
enter message
send: "01hey whats up guys\0" --------------> receive message and print
											  message



[Q]uit
send: "2\0" --------------------------------> receive message and remove buddy from list
											  close socket


messages are always ascii encoded
messages always end with \0

Es wird bei diesem Beispiel nur ein TCP-Stream aufgebaut. Entweder wird man gescannt und nimmt den Stream des gegenübers an und lässt genau diesen Socket offen. Oder man scannt selbst und lässt diesen Socket offen. Über diesen Socket werden Nachrichten empfangen und auch gesendet

Übersicht:
01	Private Nachricht erhalten
00	Gruppennachricht erhalten
1	Jemand hat dich gescannt - schicke deinen namen und frage nach seinem und lass den Socket zum chatten offen, füge Buddy zur Buddyliste hinzu
2	Jemand geht - Entferne Buddy von Buddyliste und schließe den Socket
