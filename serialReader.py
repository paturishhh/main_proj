import collections, binascii, time, MySQLdb
import serial, datetime
from array import array

QUEUE_SIZE = 100;
PORT_COUNT = 12;

packetQueue = collections.deque()

arduino = serial.Serial()
arduino.port = 'COM4'
arduino.baudrate = 9600
arduino.timeout = None
arduino.open()

def loadNodeConfig():
    "load node config to database"
    print("Derp")

def addNodeConfig(configVersion, nodeId, nodeConfiguration):
    "adds node configuration to database; accepts int, int, string"

    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    currTime = time.localtime()
    timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime) 
    sql = "INSERT INTO NodeConfiguration(node_configuration_version, node_id, time_stamp, node_configuration)"\
    " VALUES ('%d', '%d', '%s', '%s')" % (configVersion, nodeId, timeStamp, nodeConfiguration)

    try:
        cur.execute(sql)
        database.commit()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()

def sendNodeConfig(packetDetails):
    "send node config details to serial; accepts int[]"

    arduino.write(array('B',packetDetails).tobytes())
    time.sleep(2)
    
def parsePacket():
    "gets the packet from queue & parse commands received from node"
    packetDetails = array('I') #stores packet details (sourceAddr, command, count, portNum and port data)
    packet = packetQueue.popleft()
    isValid = False
    
    print(packet)
    packet = bytearray(packet) #bytearray(b'\x01\x00\x03\x0b\xfe')

    count = 0
    curCount = 0
    index = 0

    for b in packet: #255, 1, 0, 3, 15, 0, 0, 0, 1, 254
        if index == 9:#port data 2
            if b == 254:
                print("footer found")
                isValid = True    
        elif index == 8: #port data 1
            packetDetails.append(b)
            if (curCount == count) == True:
                index = 9
            else:
                curCount += 1
                index = 6
        elif index == 7: #port number 2
            packetDetails.append(b)
            index = 8
        elif index == 6: #port number 1
            packetDetails.append(b)
            index = 7
        elif index == 5: #count
            packetDetails.append(b)
            count = b
            curCount = 0
            index = 6
        elif index == 4: #command
            packetDetails.append(b)
            if b == 15:
                index = 5
            else:
                index = 9
        elif index == 3: #api
            index = 4
        elif index == 2: #dest 
            index = 3
        elif index == 1: #source address
            packetDetails.append(b)
            index = 2
        elif index == 0:
            if b == 255:
                print("header found")
                index = 1
    if isValid == True:
        #check if inserting port data or command
        # print("insert db")
        if packetDetails[1] == 15: 
            print("printing packet details")
            print(packetDetails)
            addPortData(packetDetails)
        else:
            print(packetDetails)
            addCommand(packetDetails)
    else:
        print("invalid packet")
    
def readSerial():
    "read serial data from COM4"
    
    try:
        if arduino.is_open:
            time.sleep(2) #wait
            while arduino.in_waiting > 0 and (len(packetQueue) != QUEUE_SIZE): 
            #while there is data and queue not full
                data = arduino.readline()[:-2] #removes /r and /n
                
                if len(packetQueue) != QUEUE_SIZE:
                    packetQueue.append(data) #insert data to queue
                    # parsePacket() #parse one when full
                    # print(data)
                    # print(len(packetQueue))
                else:
                    print("queue is full")
            # arduino.close() #close serial
        else:
            print('derp')
    except SerialException as e:
        print(e)

def findNodeId(nodePhysicalAddr):
    "returns the nodeId given the node's physical address; accepts int"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_id FROM Node WHERE node_address_physical = '%d'" % nodePhysicalAddr
    try:
        cur.execute(sql)
        result = cur.fetchone()
        if result is None:
            nodeId = 0
        else:
            nodeId = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return nodeId

def findPortId(nodeId, portNum):
    "return port id by sending node id and portNum; accepts int"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT port_id FROM NodePort WHERE node_id = '%d' AND port_number = '%d'" % (nodeId, portNum)
    try:
        cur.execute(sql)
        result = cur.fetchone()
        if result is None:
            portId = 0
        else:
            portId = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return portId
    
def addPortData(packetDetails): #remember to close db after access  
    "insert port data details; accepts int[]"  
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeAddr = packetDetails[0]
    nodeId = findNodeId(nodeAddr)
    print("@ insert port data")
    dataCount = packetDetails[2] #port num & port value
    currentDataCount = 0
    isPortDataLeft = True
    
    try: 
        while isPortDataLeft: #loop while there is data
            portNum = packetDetails[3 + (3 * currentDataCount)] #get port number
            portId = findPortId(nodeId, portNum)
        
            if portId == 0: #add new port if port id not found
                addPort(portNum, nodeId)
                portId = findPortId(nodeId, portNum)        
            # else: #port is stored
            #     print("port is there!")


            # print("port num: " + str(portNum))
            # print("port id: " + str(portId))
            currTime = time.localtime()
            timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
            portValue = (packetDetails[4 + (3 * currentDataCount)] * 256) + packetDetails[5 + (3 * currentDataCount)]

            sql = "INSERT INTO PortValue(port_id, port_value, time_stamp) VALUES ('%d', '%d', '%s')" % (portId, portValue, timeStamp)
            # print(sql)
            cur.execute(sql)
            database.commit()

            if (currentDataCount == dataCount):
                isPortDataLeft = False
            else:
                currentDataCount +=1
         
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
        
    database.close()
    
def addPort(portNum, nodeId):
    "add port to nodePort table in databasel accepts int"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    print("@ insert port")

    try:
        sql = "INSERT INTO NodePort(port_number, node_id) VALUES ('%d', '%d')" % (portNum, nodeId)
        cur.execute(sql)
        database.commit()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()

def addCommand(packetDetails):
    "save command sent on database; accepts int []"
    print("@ insert command")

    nodeAddr = packetDetails[0]
    try:
        nodeId = findNodeId(nodeAddr) #check if there is already added
        
        if nodeId == 0: #new node
            addNode(nodeAddr)
            nodeId = findNodeId(nodeAddr)
        else:
            print("proceed with life")

        database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
        cur = database.cursor()

        currTime = time.localtime()
        commandCode = packetDetails[1]
        timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
        sql = "INSERT INTO Command(node_id, command_code, time_stamp) VALUES ('%d', '%d', '%s')" % (nodeId, commandCode, timeStamp)
        cur.execute(sql)
        database.commit()
        
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        database.rollback()
        print(e)
    database.close()

def addNode(nodePhysicalAddr):
    "add a new node at database when a new node is detected, auto add ports at database; accepts int"
    print("@ add node")
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "INSERT INTO Node(node_address_physical, node_address_logical,node_active) VALUES ('%d', '%d', '%d')" % (nodePhysicalAddr, 0, 1)

    try:
        cur.execute(sql)
        database.commit()
        nodeId = findNodeId(nodePhysicalAddr)
        for x in range(0, PORT_COUNT):
            addPort(x, nodeId)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()

def retrievePacketQueue():
    "parse messages while queue is not empty"
    while len(packetQueue) != 0:
            parsePacket() 

def inputConfiguration(command):
    "Convert configuration to bytes for saving in the database; accepts string"               
    command = command.upper() # upper case all
    command = command.split() # split parameters ['FF', '00'] a str
    packetDetails = array('I') #stores packet (sourceAddr, command, count, portNum and port data)

    for c in command: #FF
        temp = int(c, 16) #255; int
        packetDetails.append(temp) 
        
    print(packetDetails) #255 0 1 2 255 0 12(0C) 0 0 254

    nodePhysicalAddr = int(packetDetails[2])

    nodeId = findNodeId(nodePhysicalAddr) 

    if nodeId == 0: #if new node
        addNode(nodePhysicalAddr)
        nodeId = findNodeId(nodePhysicalAddr) 

    configVersion = packetDetails[4]
    
    nodeConfiguration = ""
    for s in packetDetails:
        nodeConfiguration += chr(s)
        nodeConfiguration += " "

    addNodeConfig(configVersion, nodeId, nodeConfiguration)
    sendNodeConfig(packetDetails)
    readSerial()
    retrievePacketQueue()
    
    

#main program
choice = 0
while choice != 3:
    print('*************************')
    # print('Command line control')
    print('Choose the corresponding number for command: ')
    print('1. Read WSAN data')
    print('2. Send WSAN config')
    print('3. Exit')
    print('*************************')
    choice = input('Enter choice: ')

    if choice == '1':
        readSerial()
        retrievePacketQueue()
    elif choice == '2':
        print("use uppercase")
        command = input('Enter packet to send (bytes are separated by spaces): ')
        inputConfiguration(command)
    elif choice == '3':
        exit()

