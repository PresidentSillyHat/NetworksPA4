import queue
import threading
import ast


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths 
    dst_S_length = 5
    prot_S_length = 1
    
    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]
        #if (prot_S == 'control'):
        #    ast.literal_eval(data_S)        
        return self(dst, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return self.addr
       
    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router
class Router:
    
    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}

        #TODO: set up the routing table for connected hosts
        self.rt_tbl_D = {self.name:{2:0}}      # {destination: {router: cost}}
        self.rt_tbl_D.update(cost_D)
        print('%s: Initialized routing table' % self)
        self.print_routes()


    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1
            # only applies to data, not control
            # i is outgoing?
            if i<1: #in this topology, only two ways to route, more logic needed for part 3
                j=1
            else:
                j=0
            self.intf_L[j].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, j))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        #create a routing table update packet

        #networkPacket(DESTINATION, CONTROL OR DATA, PAYLOAD)
        #Need to get cost for self on i

        #GOAL: send both updates so both routers have all 4, calculate shortest paths from the 4

        payload=""
        for key in self.rt_tbl_D:
            f= self.rt_tbl_D.get(key)
            if type(f) is dict:
                for key2 in f:
                    ff=f.get(key2)
                        #Interface 1 is move forward, 0 is back
                        #1 for RA is RB, 1 for RB is H2
                        #0 for RA is H1, 0 for RB is RA
                    if self.name == "RA":
                        if str(key2)=="1":
                            payload="RB"
                        elif str(key2)=="0":
                            payload="H1"
                        else:
                            payload="RA"
                    elif self.name=="RB":
                        if str(key2)=="1":
                            payload="H2"
                        elif str(key2)=="0":
                            payload="RA"
                        else:
                            payload="RB"
                    
                    #all hail repetitive statements
                    payload=self.name+payload+"|"+str(key2)+"|"+str(ff)
            #else:
                #ff=self.name+str(f)
                #print(ff)

        
                    p = NetworkPacket(0, 'control', payload)
        
                    try:
                        print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                        self.intf_L[i].put(p.to_byte_S(), 'out', True)
                    except queue.Full:
                        print('%s: packet "%s" lost on interface %d' % (self, p, i))
                        pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information

    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates

        #p is the received packet marked Control (000002(p.data_S))
        #p.data_S will be dest|intf|cost
        #print(p.data_S)
        parser=p.data_S
        break1=parser.index("|")
        key1=parser[0:break1]
        parser=parser[break1+1:]
        break1=parser.index("|")
        key2=parser[0:break1]
        key3=parser[break1+1:]
        updater={key1:{int(key2):int(key3)}}

        if(key1 in self.rt_tbl_D):
            comp=self.rt_tbl_D.get(key1)
            if type(comp) is dict:
                comp=comp.get(key2)
            elif type(comp is int)and (int(key3)<int(comp)):
                self.rt_tbl_D.update(updater)
                self.send_routes(i)
            else:
                print(self.rt_tbl_D.get(key1))
        else:
            self.rt_tbl_D.update(updater)
            self.send_routes(i)
        
        print('%s: Received routing update %s from interface %d' % (self, p, i))
         #might need to reverse?
        
    ## Print routing table
    def print_routes(self):
        #TODO: print the routes as a two dimensional table
        #TODO: checking statements that print to right format
        
        f0=f1=f2=f3=f4=f5=f6=f7=10
        for key in self.rt_tbl_D:
            f= self.rt_tbl_D.get(key)
            if type(f) is dict:
                for key2 in f:
                    ff=f.get(key2)
            else:
                ff=f
            #TODO: apply update properly
            if self.name=="RA":
                if str(key) == "H1":
                    f0=str(ff)
                elif str(key)=="H2":
                    f1=str(ff)
                    #f1=f3+f5
                elif str(key)=="RA":
                    f2=str(ff)
                elif str(key)=="RB":
                    f3=str(ff)
                elif str(key)=="RBH1":
                    f4=str(ff)
                elif str(key)=="RBH2":
                    f5=str(ff)
                    #f1=f3+f5
                elif str(key)=="RBRA":
                    f6=str(ff)
                elif str(key)=="RBRB":
                    f7=str(ff)
                
            if self.name=="RB":      
                if str(key) == "H1":
                    f4=str(ff)
                    #f4=f6+f0
                elif str(key)=="H2":
                    f5=str(ff)
                elif str(key)=="RA":
                    f6=str(ff)
                elif str(key)=="RB":
                    f7=str(ff)
                elif str(key) == "RAH1":
                    f0=str(ff)
                elif str(key)=="RAH2":
                    f1=str(ff)
                    #f1=f3+f5
                elif str(key)=="RARA":
                    f2=str(ff)
                elif str(key)=="RARB":
                    f3=str(ff)
                #my code will block out the sun
        if (self.name == "RB" and "RAH1" in self.rt_tbl_D) or (self.name == "RA" and "RBRA" in self.rt_tbl_D):
            f4=int(f6)+int(f0)
        if (self.name == "RA" and "RBH2" in self.rt_tbl_D) or (self.name == "RB" and "RARB" in self.rt_tbl_D):
            f1=int(f3)+int(f5)
        print(self.rt_tbl_D)
        print("╒══════╤══════╤══════╤══════╤══════╕")
        print("│ {0}   │   H1 │   H2 │   RA │   RB │".format(self.name))
        print("│ RA   │    {0} │    {1} │    {2} │    {3} │".format(f0,f1,f2,f3))   #RA problems with RBRB, RB problems with RARA, same with f0/f6 (RAH1/RBRA)
        print("│ RB   │    {0} │    {1} │    {2} │    {3} │".format(f4,f5,f6,f7))
        print("╘══════╧══════╧══════╧══════╧══════╛")
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 