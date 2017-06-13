import collections, binascii, time, MySQLdb
import serial, datetime
from array import array

QUEUE_SIZE = 3;
packetQueue = collections.deque()

def parsePacket():
    "gets the packet from queue & parse commands received from node"
    print("parse parse")
    packetDetails = array('I') #stores packet details (sourceAddr, command, count, portNum and port data)
    packet = packetQueue.popleft()
    isValid = False
    
    print(packet)
    packet = bytearray(packet) #bytearray(b'\x01\x00\x03\x0b\xfe')

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
        print("insert db")
        if packetDetails[1] == 15: 
            insertPortData(packetDetails)
        else:
            insertCommand(packetDetails)
    else:
        print("invalid packet")
    
def readSerial():
    "read serial data from COM4"
    arduino = serial.Serial()
    arduino.port = 'COM4'
    arduino.baudrate = 9600
    arduino.timeout = None
    arduino.open()

    if arduino.is_open:
        time.sleep(2) #wait
        while arduino.in_waiting > 0: #while there is data
            data = arduino.readline()[:-2] #removes /r and /n
            
            if len(packetQueue) != QUEUE_SIZE:
                packetQueue.append(data) #insert data to queue
                parsePacket() #parse one when full
                # print(data)
                # print(len(packetQueue))
            else:
                parsePacket() #parse one when full
                packetQueue.append(data)
                print('back')
                print(list(packetQueue))
        while len(packetQueue) != 0: #just empty the queue if there is no message
            parsePacket() 
        arduino.close() #close serial
    else:
        print('derp')

def insertPortData(packetDetails): #remember to close db after access    
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeAddr = packetDetails[0]
    print("@ insert port data")
    dataCount = packetDetails[2] #port num & port value
    currentDataCount = 0
    isPortDataLeft = True
    
    try: 
        while isPortDataLeft:
            portNum = packetDetails[3 + (4 * currentDataCount)] + packetDetails[4 + (4 * currentDataCount)] #get port number
            sql = "SELECT port_id FROM NodePort WHERE node_id = '%d' AND port_number = '%d'" % (nodeAddr, portNum)
            cur.execute(sql)
        
            if cur.rowcount == 0: #add new port if there is none
                insertPort(portNum, nodeAddr)
                cur.execute(sql) #execute query again
            else:
                print("port is there!")
            
            portId = cur.fetchone() # got the port id na
            currTime = time.localtime()
            timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
            portValue = (packetDetails[5 + (4 * currentDataCount)] * 256) + packetDetails[6 + (4 * currentDataCount)]
            print(portValue)

            sql = "INSERT INTO PortValue(port_id, port_value, time_stamp) VALUES ('%d', '%d')" % (portId, portValue, timeStamp)
            print(sql)
            cur.execute(sql)
            database.commit()

            if currentDataCount == dataCount:
                isPortDataLeft = False
            else:
                currentDataCount +=1

         
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
        
    database.close()
    
def insertPort(portNum, nodeId):
    "add port to nodePort table in database"
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

def insertCommand(packetDetails):
    "save command sent on database"
    nodeAddr = packetDetails[0]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT * FROM Node WHERE node_id = '%d'" % nodeAddr

    try:
        cur.execute(sql)
        result = cur.fetchone()
        
        if cur.rowcount == 0: #new node
            addNode(nodeAddr)
        else:
            print("proceed with life")

        currTime = time.localtime()
        commandCode = packetDetails[1]
        timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
        sql = "INSERT INTO Command(node_id, command_code, time_stamp) VALUES ('%d', '%d', '%s')" % (nodeAddr, commandCode, timeStamp)
        cur.execute(sql)
        database.commit()
        
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        database.rollback()
        print(e)
    database.close()

def addNode(nodeAddr):
    "add a new node when a new node is detected"
    print("@ add node")
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "INSERT INTO Node(node_address_physical, node_address_logical,node_active) VALUES ('%d', '%d', '%d')" % (nodeAddr, 0, 1)

    try:
        cur.execute(sql)
        database.commit()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()

def inputConfiguration(command):
    "Convert configuration (string) to bytes for saving in the database"               
    command = bytearray(command, 'utf-8')
    packetDetails = array('I') #stores packet details (sourceAddr, command, count, portNum and port data)

    for segment in command:
        # print(packetDetails.append(hex(segment)))
        # string to int
        # append to packetDetails
        # save parameters
        # send 
        print(type(hex(segment))) #0X46 0X46 0X20

    # send data back if there is something there
    #arduino.write
    #time.sleep

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
    elif choice == '2':
        command = input('Enter packet to send (bytes are separated by spaces): ')
        inputConfiguration(command)
    elif choice == '3':
        exit()

