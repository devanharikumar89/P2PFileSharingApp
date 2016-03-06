from socket import *
import pickle
import random
import P2PUtils
from P2PUtils import check_checksum
import os
from time import sleep

prob = 0.0
expected_seq_num= 0
outputfile = "output.pdf"
CIserverName = "10.139.61.39"
CIserverPort = 7734
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.bind(('', 7733))
clientSocket.connect((CIserverName, CIserverPort))
rfcno = ""
pendingAdds = False

class Client(object):
    
    def create_request(self):
        input_list = []
        while 1:
            stro = input(">")
            if stro == "" or stro.isspace():
                break
            else:
                input_list.append(stro)
        request = ""
        for i in input_list:
            request = request + i + "|"
        return request

    def get_ip_addr(self, request):
        if request:
            lines = request.split('|')
            ipline = lines[1].split(':')
            return "".join(ipline[1].split())

    def receive_file(self):
        global fs_socket
        global expected_seq_num
        global eof
        global outputfile
        global pendingAdds
        
        if os.path.exists(outputfile):
            os.remove(outputfile)
        #status area
        mesg = fs_socket.recv(1024)
        print(mesg.decode())
        #status area
        
        while True:
            a= fs_socket.recv(4096)
            received_data = pickle.loads(a)
            data = received_data[3]
            
            checksum = received_data[1]
            seq_num = received_data[0]
            random_prob = random.random()
            packetdropped = False
            if random_prob <= prob or not check_checksum(data.decode("ISO-8859-1"), -checksum):
                packetdropped = True
            if packetdropped and seq_num > expected_seq_num:
                print("packet loss, sequence number = ",expected_seq_num)
            if not packetdropped:
                if seq_num == expected_seq_num:
                    with open(outputfile, 'ab') as file:
                        file.write(data)
                    self.send_ack(expected_seq_num)
                    if received_data[2] == P2PUtils.TYPE_EOF:
                        print("\nDOWNLOAD COMPLETE\n")
                        pendingAdds = True
                        #Add this file to the server's index
                        break
                    expected_seq_num=expected_seq_num+1              
                

    def send_ack(self, expected_seq_num):
        global fs_socket
        ackmessage = [expected_seq_num, 0b0000000000000000,P2PUtils.TYPE_ACK]
        ackpkt = pickle.dumps(ackmessage)
        fs_socket.sendto(ackpkt, (file_server, fs_port))

            
client = Client()
while 1:
    if pendingAdds:
        msg = ["ADD RFC "+rfcno+" P2P-CI/1.0","Host: thishost.csc.ncsu.edu", "Port: 5678",
                               "Title: A Preferred Official ICP|"]
        addReq = "|".join(msg)
        clientSocket.send(addReq.encode())
        serverResponse = clientSocket.recv(4096)
        print(serverResponse.decode())
        pendingAdds = False
        
    request = client.create_request()
    if request and not request.isspace():
        clientSocket.send(request.encode())
        serverResponse = clientSocket.recv(4096)
        if serverResponse:
            response = serverResponse.decode()
            print(response)
            commandlines = request.split("|")
            if commandlines[0].split()[0]=="LOOKUP":
                if response:
                    responselines = response.split("\n")
                    if(responselines[0].split()[1]=="200"):
                        userresp = input("Request file ? Y or N\n")
                        if userresp=="Y" or userresp=="y":
                            rfcno = commandlines[0].split()[2]
                            outputfile = rfcno+".pdf"
                            expected_seq_num=0
                            file_server=input("Choose an IP address\n")
                            fs_port = 7735
                            fs_socket = socket(AF_INET, SOCK_DGRAM)
                            fs_socket.bind(("10.139.61.39",7736));
                            prob = input("Enter the packet loss threshold (0.0 - 1.0)\n")
                            try:
                                prob = float(prob)
                            except ValueError:
                                print("INVALID INPUT")
                            else:    
                                fs_socket.sendto(pickle.dumps(request),(file_server,fs_port))#
                                client.receive_file()
                                


