from socket import *
import pickle
import time
import P2PUtils
import _thread
import platform
import os
from P2PUtils import generateChecksum

file_name = ""
MSS = 500
no_of_packets = 0
packet_index = 0
window_size = 7
window_start = 0
eof = False
packetbytes = []
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(("10.139.56.217", 7735))
RTT=1
MSS=500
lastack=[]
lastackinitialized = False

client_socket = socket(AF_INET, SOCK_DGRAM)
class UDPServer():

    def file_sender_thread(self, request):
        global server_socket
        global clientAddress
        commandlines = request.split("|")
        
        rfcno = commandlines[0].split()[2]
        self.rdt_send(rfcno)

    def send_packet(self, pkts):
        global server_socket
        global clientAddress
        #print("packet sent : ",pkts);
        server_socket.sendto(pkts,clientAddress)

    def make_packets(self, fileData):

        global no_of_packets
        seq_num = 0
        total_seq = 0
        packetsList = []
        no_of_packets = len(fileData)
        for datachunk in fileData:
            if total_seq < no_of_packets-1:
                packet = [seq_num, generateChecksum(datachunk.decode("ISO-8859-1")), P2PUtils.TYPE_DATA, datachunk]
            else:
                packet = [seq_num, generateChecksum(datachunk.decode("ISO-8859-1")), P2PUtils.TYPE_EOF, datachunk]
            packetsList.append(pickle.dumps(packet))
            seq_num +=1
            total_seq +=1
            if seq_num >= (1024*1024*1024*4):
                seq_num = 0
        return packetsList
    
    def udt_send(self, packetbytes):

        #current_max_window
        global packet_index
        global window_start
        global window_size
        global eof
        global file_name
        global no_of_packets

        #print(packet_index)
        info = os.stat(file_name)
        
        message = ["P2P-CI/1.0 200 OK", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),
                               "Last-Modified: " + time.ctime(info.st_mtime), "Content-Length: "+str(info.st_size), "Content-Type:  text/text","DOWNLOADING FILE...",""]
        resp = "\n".join(message)
        server_socket.sendto(resp.encode(),clientAddress)
        eof = False
        while eof==False:
            while packet_index < window_start+window_size and packet_index < no_of_packets:
                #print("PACKET SENT : ",packet_index)
                packet_ = pickle.loads(packetbytes[packet_index])
                self.send_packet(packetbytes[packet_index])
                _thread.start_new_thread(self.timer, (float(RTT/1000),packet_[0]))
                packet_index+=1
        
    def timer(self, msecs, seq_no):
        time.sleep(msecs)
        global lastack
        global lastackinitialized
        if not lastackinitialized:#first packet hasn't gone through
            dummyack = [int(-1), 0b0000000000000000, P2PUtils.TYPE_ACK]
            dummypkt = pickle.dumps(dummyack)
            self.resend_thread(dummypkt)
        if lastackinitialized and lastack[2] == P2PUtils.TYPE_ACK and lastack[0]<seq_no:
            self.resend_thread(pickle.dumps(lastack))
        else:
            pass        

    def rdt_send(self, rfcno):

        fileData = []
        global MSS
        global packetbytes
        global file_name
        file_name = str(rfcno)+".pdf"
        if not os.path.isfile(file_name):
            message = ["P2P-CI/1.0 404 Not Found", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),""]
            resp = "\n".join(message)
            server_socket.sendto(resp.encode(),clientAddress)
        else:    
            with open(file_name, 'rb') as fs:
                    while True:
                        mssChunk = fs.read(int(MSS))
                        if mssChunk :
                            fileData.append(mssChunk)
                        else:
                            break
    
            packetbytes  = self.make_packets(fileData)
            self.udt_send(packetbytes)

    def resend_thread(self, pkts):
        
            global window_start
            global window_size
            global packetbytes
            global clientAddress
            global packet_index
            global no_of_packets
            
            ackdata = pickle.loads(pkts)
            
            if ackdata[2] == P2PUtils.TYPE_ACK:
                next_seq = ackdata[0]+1
                if next_seq == no_of_packets:
                    eof=True
                if next_seq < no_of_packets :
                    print("Timeout, sequence number = ", next_seq)
                    window_start  = next_seq
                    packet_index = next_seq
                    
    def ack_thread(self, pkts):
        
            global window_start
            global window_size
            global packetbytes
            global clientAddress
            global lastack
            global lastackinitialized
            global no_of_packets
            
            ackdata = pickle.loads(pkts)
            lastack = ackdata
            lastackinitialized = True
            #print("INCOMING ACK", ackdata)
            if ackdata[2] == P2PUtils.TYPE_ACK:
                next_seq = ackdata[0]+1
                if next_seq == no_of_packets:
                    eof=True
                    print("\nUPLOAD COMPLETE\n")
                if next_seq > window_start and next_seq < no_of_packets :
                    window_start  = next_seq


u_server = UDPServer()
while True:
    
    print("FILE SERVER LISTENING...")
    request,clientAddress = server_socket.recvfrom(4096)
    if request:
        list_ = pickle.loads(request)
        if not isinstance(list_, list):#GET
            lastackinitialized = False
            no_of_packets = 0
            eof = True
            packetbytes = []
            packet_index=0
            window_start=0
            MSS = input("ENTER THE MSS\n")
            RTT = input("ENTER THE ROUND TRIP TIME IN MILLISECONDS\n")
            window_size = input("ENTER THE SENDER WINDOW SIZE\n")
            
            try: 
                RTT = int(RTT)
                MSS = int(MSS)
                window_size = int(window_size)
            except ValueError:
                print("INVALID INPUT")
            else:
                _thread.start_new_thread(u_server.file_sender_thread, (str(request),))
        if isinstance(list_, list):
            u_server.ack_thread(request)
    else:
        message = ["P2P-CI/1.0 400 Bad Request", "Date: " + time.strftime("%c"), "OS: " +
                               platform.system() + " " + platform.release() + " " + platform.version(),
                               "CHECK THE COMMAND AGAIN"]
        resp = "\n".join(message)
        server_socket.send(resp.encode())
