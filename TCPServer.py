from socket import *
import Lists
import RFCLists
import _thread
import time
import platform
import select

list_of_peers = []
list_of_rfcs = []


class TCPServer(object):
    serverPort = 7734
    no_of_clients = 0;
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(("10.139.61.39", serverPort))
    serverSocket.listen(10)
    print("The CI server (TCP) is listening")

    def threadPerClient(self, peersocket, addr):
        global list_of_peers
        global list_of_rfcs
        while 1:
            try:
                command = peersocket.recv(4096)
            except Exception:
                print(addr[0], " left")
                peersocket.close()
                list_of_peers = [x for x in list_of_peers if x.ipaddr != addr[0]]
                list_of_rfcs = [y for y in list_of_rfcs if y.ipaddr != addr[0]]
                break
            if command:
                decodedCom = command.decode()
                commandlines = decodedCom.split("|")

                firstline = commandlines[0]
                if firstline == " ":
                    method = "UNDEFINED"
                else:
                    method = firstline.split()[0]

                if method == "ADD":
                    print("from ",addr[0])
                    print(commandlines)
                    print
                    if len(commandlines) != 5:
                        message = ["P2P-CI/1.0 400 Bad Request", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),
                               "CHECK THE COMMAND AGAIN"]
                        resp = "\n".join(message)
                        peersocket.send(resp.encode())

                    else:
                        peerPresent = False
                        for a in range(0, len(list_of_peers)):
                            peer = list_of_peers[a]
                            if peer.ipaddr == addr[0]:
                                peerPresent = True
                                break

                        if peerPresent is False:
                            peer = Lists.LLNodePeer()
                            peer.set_ipaddr(addr[0])
                            peer.set_portno(int(addr[1]))
                            list_of_peers.append(peer)

                        rfcPresentWithPeer = False
                        line1 = commandlines[0]
                        line4 = commandlines[3]
                        rfcno = line1.split()[2]
                        rfcno = int(rfcno)
                        ipaddr = addr[0]
                        rfcname = line4.split()[1:]
                        rfcname = " ".join(rfcname)
                        for a in range(0, len(list_of_rfcs)):
                            rf = list_of_rfcs[a]
                            if rf.ipaddr == ipaddr and rf.rfcno == rfcno:
                                rfcPresentWithPeer = True
                                break
                        if rfcPresentWithPeer is False:
                            rfc = RFCLists.LLNodeRFC()
                            rfc.xset_ipaddr(ipaddr)
                            rfc.xset_rfcname(rfcname)
                            rfc.xset_rfcno(int(rfcno))
                            list_of_rfcs.append(rfc)

                            message = ["P2P-CI/1.0 200 OK", "RFC"+" "+str(rfcno)+" "+rfcname+
                                       " "+str(addr[0])+" "+str(addr[1])]
                            resp = "\n".join(message)
                            peersocket.send(resp.encode())

                        else:
                            message = ["P2P-CI/1.0 200 OK", "RFC"+" "+str(rfcno)+" "+rfcname+
                                           " "+str(addr[0])+" "+str(addr[1])+" "+"ALREADY EXISTS"]
                            resp = "\n".join(message)
                            peersocket.send(resp.encode())
                elif method == "LOOKUP":
                    print("from ",addr[0])
                    print(commandlines)
                    print
                    atleastone = False
                    line1 = commandlines[0]
                    line4 = commandlines[3]
                    rfcno = line1.split()[2]
                    rfcname = line4.split()[1:]
                    rfcno = int(rfcno)
                    message = ["P2P-CI/1.0 200 OK", ""];
                    if len(list_of_rfcs)==0:
                        message = ["P2P-CI/1.0 404 NOT FOUND", ""];
                    for i in range(0, len(list_of_rfcs)):
                        obj = list_of_rfcs[i]
                        if obj.rfcno == rfcno:
                            message.append(str(rfcno)+" "+(" ".join(rfcname))+" "+obj.ipaddr+" "+"7735")
                            atleastone = True
                    if not atleastone:
                        message = ["P2P-CI/1.0 404 NOT FOUND", ""];
                    resp = "\n".join(message)
                    peersocket.send(resp.encode())
                elif method == "LIST":
                    print("from ",addr[0])
                    print(commandlines)
                    print
                    message = ["P2P-CI/1.0 200 OK", ""];
                    if len(list_of_rfcs)==0:
                        message = ["P2P-CI/1.0 404 NOT FOUND", ""];
                    for i in range(0, len(list_of_rfcs)):
                        obj = list_of_rfcs[i]
                        message.append(str(obj.rfcno)+" "+obj.rfcname+" "+obj.ipaddr+" "+"7735")
                    resp = "\n".join(message)
                    peersocket.send(resp.encode())
                else:
                    message = ["P2P-CI/1.0 400 Bad Request", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),
                               "CHECK THE COMMAND AGAIN"]
                    resp = "\n".join(message)
                    peersocket.send(resp.encode())
            else:
                message = ["P2P-CI/1.0 400 Bad Request", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),
                               "CHECK THE COMMAND AGAIN"]
                resp = "\n".join(message)
                peersocket.send(resp.encode())


server = TCPServer()
while 1:
    connectionSocket, addr = server.serverSocket.accept()
    print("INCOMING CLIENT", addr, "\n")
    _thread.start_new_thread(server.threadPerClient, (connectionSocket, addr))
