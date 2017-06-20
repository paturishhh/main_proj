import collections, binascii, time, MySQLdb
import serial, datetime
from array import array

QUEUE_SIZE = 100;
PORT_COUNT = 12;
STARTUP_CONFIGURATION_MAX_PART = 5; #(0-4)

packetQueue = collections.deque()

arduino = serial.Serial()
arduino.port = 'COM4'
arduino.baudrate = 9600
arduino.timeout = None
arduino.open()

#Note: nodePhysicalAddr == node's physical address
# nodeId = id of the node at the database

def addPortData(packetDetails):
    "insert port data details; accepts int[]; returns True/False"  
    isSuccess = False;
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
                isSuccess = True
            else:
                currentDataCount +=1
         
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
        
    database.close()
    return isSuccess
    
def addPort(portNum, nodeId):
    "add port to nodePort table in database accepts int; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    print("@ insert port")

    try:
        sql = "INSERT INTO NodePort(port_number, node_id) VALUES ('%d', '%d')" % (portNum, nodeId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess

def addCommand(nodePhysicalAddr, commandCode):
    #physical address node , commandCode
    "save command sent on database; accepts int []; returns True/False"
    isSuccess = False
    print("@ insert command")
    print(commandCode)
    try:
        nodeId = findNodeId(nodePhysicalAddr) #check if there is already added
        commandCodeId = findCommandCodeId(commandCode)
        
        if nodeId == 0: #new node
            addNode(nodePhysicalAddr)
            nodeId = findNodeId(nodePhysicalAddr)
        else:
            print("proceed with life")

        database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
        cur = database.cursor()

        currTime = time.localtime()
        timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
        sql = "INSERT INTO Command(node_id, command_code_id, time_stamp, command_code) VALUES ('%d', '%d', '%s', '%d')" % (nodeId, commandCodeId, timeStamp, commandCode)
        cur.execute(sql)
        database.commit()
        isSuccess = True
        
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        database.rollback()
        print(e)
    database.close()

def addNode(nodePhysicalAddr):
    "add a new node at database when a new node is detected, auto add ports at database; accepts int; returns True/False"
    isSuccess = False
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
        isSuccess = True
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()
    return isSuccess

def addNodeConfig(configVersion, nodeId, nodeConfiguration):
    "adds node configuration to database; accepts int, int, string; returns True/False"
    isSuccess = False

    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    currTime = time.localtime()
    timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime) 
    sql = "INSERT INTO NodeConfiguration(node_configuration_version, node_id, time_stamp, node_configuration)"\
    " VALUES ('%d', '%d', '%s', '%s')" % (configVersion, nodeId, timeStamp, nodeConfiguration)

    try:
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()
    return isSuccess

def addNodeConfigReply(nodePhysicalAddr):
    "upon receiving a reply, it will insert a new row at nodeconfigreply with time_stamp and port config status set to 1; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeId = findNodeId(nodePhysicalAddr) 

    currTime = time.localtime()
    timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)  

    sql = "INSERT INTO Nodeconfiguration(node_id, time_stamp, port_configuration_status)"\
    " VALUES ('%d', '%s', 1)" % (nodeId, timeStamp)

    try:
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()
    return isSuccess

def addNodeProbeStatus(nodeId):
    "adds node probe status log to database with probe_time only filled; accepts int; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    currTime = time.localtime()
    timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)
    sql = "INSERT INTO ProbeStatusLog(node_id, probe_time)"\
    " VALUES ('%d', '%s')" % (nodeId, timeStamp)

    try:
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()

def addNodeProbeReply(nodePhysicalAddr): 
    "upon receiving a reply, it will insert a new row at probestatuslog with reply_time filled up; accepts int; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeId = findNodeId(nodePhysicalAddr) 

    currTime = time.localtime()
    timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime)  

    sql = "INSERT INTO ProbeStatusLog(node_id, reply_time, node_reply)"\
    " VALUES ('%d', '%s', 1)" % (nodeId, timeStamp)

    try:
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()
    return isSuccess

def findCommandCodeId(commandCode):
    "returns command code id by giving the command code"
    print("@ command command code id")
    commandCodeId = 0
    try:
        database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
        cur = database.cursor()
        sql = "SELECT command_code_id FROM command_code WHERE command_code = '%d'" % commandCode
        cur.execute(sql)
        result = cur.fetchone()

        if result is None:
            commandCodeId = 0
        else:
            commandCodeId = result[0]
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return commandCodeId

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

def findNodeByPhysicalAddr(nodePhysicalAddr): #untested
    "views node details by searching the physical address"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_address_logical, node_active, node_name FROM Node WHERE node_address_physical = '%d'" % (nodePhysicalAddr)
    try:
        cur.execute(sql)
        result = cur.fetchone()

        if result is None:
            result = 0
        else:
            result = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

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

def parseStringToIntArray(strInput): #untested
    "for input type commands; accepts string; return int []"
    strInput = strInput.upper() # upper case all
    strInput = strInput.split() # split parameters ['FF', '00'] a str
    packetDetails = array('I') #stores packet (sourceAddr, command, count, portNum and port data)

    for c in strInput: #FF
        temp = int(c, 16) #255; int
        packetDetails.append(temp) 
    return packetDetails
        
def inputConfiguration(command):
    "Convert configuration to bytes for saving in the database; accepts string"               
    packetDetails = parseStringToIntArray(command)
        
    print(packetDetails) #255 0 1 2 255 0 12(0C) 0 0 254

    nodePhysicalAddr = int(packetDetails[2])

    nodeId = findNodeId(nodePhysicalAddr) 

    if nodeId == 0: #if new node
        addNode(nodePhysicalAddr)
        nodeId = findNodeId(nodePhysicalAddr) 

    api = packetDetails[3]
    if api == 2:
        configVersion = packetDetails[4]
        
        nodeConfiguration = ""
        for s in packetDetails:
            nodeConfiguration += chr(s)
            nodeConfiguration += " "

        if packetDetails[-1] == 254:
            addNodeConfig(configVersion, nodeId, nodeConfiguration)
            print("footer found")
        else:
            print("dropped")
    elif api == 3:
        commandCode = packetDetails[4]
        if commandCode == 0:
            addNodeProbeStatus(nodeId)
        else:
            addCommand(nodePhysicalAddr, commandCode)

    sendMessage(packetDetails)
    readSerial()
    retrievePacketQueue()
    
def parsePacket(): #node can only send commands & data
    "gets the packet from queue & parse commands or data received from node"
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
        elif index == 8: #port data 2
            packetDetails.append(b) #packetDetails[5]
            if (curCount == count) == True:
                index = 9
            else:
                curCount += 1
                index = 6
        elif index == 7: #port data 1
            packetDetails.append(b) #packetDetails[4]
            index = 8
        elif index == 6: #port number 1
            packetDetails.append(b) #packetDetails[3]
            index = 7
        elif index == 5: #count
            packetDetails.append(b) #packetDetails[2]
            count = b
            curCount = 0
            index = 6
        elif index == 4: #command
            packetDetails.append(b) #packetDetails[1]
            if b == 15:
                index = 5
            else:
                index = 9
        elif index == 3: #api
            index = 4
        elif index == 2: #dest 
            index = 3
        elif index == 1: #source address
            packetDetails.append(b) #packetDetails[0]
            index = 2
        elif index == 0:
            if b == 255:
                print("header found")
                index = 1
    if isValid == True:
        #check if inserting port data, command or probe node status
        command = packetDetails[1]
        if command == 15: 
            #sending port data
            print(packetDetails)
            addPortData(packetDetails) # okay lang int [] kasi pwede madami
            addCommand(packetDetails[0], packetDetails[1]) # still log it at database
        elif command == 1:
            #updateProbeNodeStatus
            print("a node reply")
            addNodeProbeReply(packetDetails[0])        
        elif command == 6:
            #node config acknowledgement
            print("port config acknowledgement")
            addNodeConfigReply(packetDetails[0])
            addCommand(packetDetails[0], packetDetails[1]) # still log it at database
        else:
            print(packetDetails)
            addCommand(packetDetails[0], packetDetails[1])
    else:
        print("invalid packet")
    
def readSerial():
    "read serial data from COM4 and store to queue"
    
    try:
        if arduino.is_open:
            # time.sleep(2) #wait
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

def retrievePacketQueue():
    "parse messages while queue is not empty"
    while len(packetQueue) != 0:
            parsePacket() 

def sendMessage(packetDetails):
    "send message to serial; accepts int[]"

    arduino.write(array('B',packetDetails).tobytes())
    time.sleep(0.5)

def updateCommandCodeDescription(commandCode, description): #untested
    "updates command code description; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    commandCodeId = findCommandCodeId(commandCode)

    print("@ update node status")

    try:
        sql = "UPDATE Command_code SET description = '%s' WHERE command_code_id = '%d'" % (description, commandCodeId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess

def updateNodeLogicalAddress(nodePhysicalAddr, logicalAddr):
    "update node logical address; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeId = findNodeId(nodePhysicalAddr)

    print("@ update logical addr")

    try:
        sql = "UPDATE Node SET node_address_logical = '%d' WHERE node_id = '%d'" % (logicalAddr, nodeId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess #untested

def updateNodeName(nodePhysicalAddr, nodeName): #untested
    "updates node name for node distinction; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeId = findNodeId(nodePhysicalAddr)

    print("@ update node name")

    try:
        sql = "UPDATE Node SET node_name = '%s' WHERE node_id = '%d'" % (nodeName, nodeId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess

def updateNodeStatus(nodePhysicalAddr, nodeStatus): #untested
    "updates node status eg active(1) or not(0);returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    nodeId = findNodeId(nodePhysicalAddr)

    print("@ update node status")

    try:
        sql = "UPDATE Node SET node_active = '%d' WHERE node_id = '%d'" % (nodeStatus, nodeId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess #untested

#port
def updateDeviceAttached(portId, deviceType): #untested
    "to determine which device is connected to port eg servo, led, relay; returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    print("@ update device attach")

    try:
        sql = "UPDATE NodePort SET device_attached = '%s' WHERE port_id = '%d'" % (deviceType, portId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess

def updatePortDataType(portId, dataType): #untested
    "update data type interpretation of port value of node eg float, int, string, byte;returns True/False"
    isSuccess  = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    print("@ update port data type")

    try:
        sql = "UPDATE NodePort SET data_type = '%s' WHERE port_id = '%d'" % (dataType, portId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()
    database.close()
    return isSuccess

def updatePortMode(portId, portMode): #untested
    "update port type eg analog/digital;returns True/False"
    isSuccess = False
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()

    print("@ update port type")

    try:
        sql = "UPDATE NodePort SET port_mode = '%s' WHERE port_id = '%d'" % (portMode, portId)
        cur.execute(sql)
        database.commit()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        database.rollback()

    database.close()
    return isSuccess

def updatePortType(portId, portType): 
    "update port type : actuator/sensor depending on node id"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")

    cur = database.cursor()
    sql = "UPDATE NodePort SET port_type = '%s' WHERE port_id = '%d'" % (portType, portId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllActiveNode(): #untested
    "displays all active nodes"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_address_physical, node_address_logical, node_name FROM Node WHERE node_active = 1"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result

def viewAllInactiveNode(): #untested
    "displays all inactive nodes"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_address_physical, node_address_logical, node_name FROM Node WHERE node_active = 0"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result

def viewAllNodeName(): #untested
    "views all node names"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_name FROM Node"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result

def viewAllNode(): #untested
    "views all nodes"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT * FROM Node"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result    

def viewAllDataTypeOfNode(nodeId): #untested
    "displays all data type of a node"
    #[portNumber, data_type]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT port_number, data_type FROM nodeport as p, node as n WHERE n.node_id = p.node_id AND n.node_id = '%d'" %(nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result    

def viewAllPortModeOfNode(nodeId): #untested
    "display all port type of a node"
    #[portNumber, port_mode]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT port_number, port_mode FROM nodeport as p, node as n WHERE n.node_id = p.node_id AND n.node_id = '%d'" %(nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result    

def viewAllPortDataOfPort(portId):
    "display all saved port data of node"
    #[port_value, time_stamp, port_number]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT v.port_value, v.time_stamp, p.port_number FROM portvalue as v, nodeport as p WHERE "\
    "v.port_id = p.port_id and p.port_id = '%d'" % (portId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result    

def findAllConfigVersionOfNode(nodeId): #untested
    "display all configversions of a node"
    #[configVersion, configuration, configurationStatus]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT c.node_configuration_version, c.node_configuration, c.port_configuration_status, c.time_stamp FROM "\
    "node as n, nodeconfiguration as c WHERE n.node_id = c.node_id AND n.node_id ='%d'" % (nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def findNodeName(nodeId): #untested
    "finds the node name given the nodeId"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT n.node_name FROM node AS n WHERE n.node_id = '%d'" % (nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchone()
        if result is None:
            result = 0
        else:
            result = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllProbeStatus(nodeId): #untested
    "views all probe node status of a node"
    #[probe_time, isReply, reply_time]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT p.probe_time, p.node_reply, p.reply_time FROM node AS n, probestatuslog as p WHERE "\
    "n.node_id = p.node_id AND n.node_id = '%d'" % (nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllConfigurations(): #untested
    "views all configurations sent"
    #[nodeConfigVersion, config, configStatus, timeStamp]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT c.node_configuration_version, c.node_configuration, c.port_configuration_status, c.time_stamp FROM " \
    "node as n, nodeconfiguration as c WHERE n.node_id = c.node_id"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllCommandSentByNode(nodeId): #untested
    "views all commands that node sent to the database"
    #[commandCode, timeStamp, description]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT c.command_code, c.time_stamp, cd.description FROM command as c, command_code as cd WHERE "\
    "cd.command_code_id = c.command_code_id AND c.node_id = '%d'" % (nodeId)
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllCommandSent(): #untested
    "views all commands sent"
    #[commandCode, timeStamp, description]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT c.command_code, c.time_stamp, cd.description FROM command as "\
    "c, command_code as cd WHERE cd.command_code_id = c.command_code_id"
    try:
        cur.execute(sql)
        result = cur.fetchall()
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def viewAllPortDetailsOfAPort(nodeId, portNum): #untested
    "views all port details of a specific node port"
    #[portNumber, port_mode]
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT p.port_number, p.port_mode, p.data_type, p.device_attached FROM " \
    "nodeport as p, node as n WHERE n.node_id = p.node_id AND n.node_id = '%d' AND p.port_number = '%d'" % (nodeId, portNumber)
    try:
        cur.execute(sql)
        result = cur.fetchone()

        if result is None:
            result = 0
        else:
            result = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result 

def sendStartupConfig(nodeId): #untested; multiple periodical
    "sends startup config of a node from database; all"
    isSuccess = False

    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    toSendMessage = []
    #gets most recent part numbers of the port
    try:
        for x in range(0, STARTUP_CONFIGURATION_MAX_PART):
            sql = "SELECT startup_configuration FROM startup_configuration WHERE "\
            "node_id = '%d' AND part_number = '%d' ORDER BY time_stamp DESC LIMIT 1" % (nodeId, x)
            cur.execute(sql)
            result = cur.fetchone()
            if result is None:
                result = 0
            else:
                result = result[0]
            intArray = convertStringToInt(result)
            toSendMessage.append(intArray) #this is a list
        for y in range(0, STARTUP_CONFIGURATION_MAX_PART):
            print("sending")
            print(toSendMessage[y])
            sendMessage(toSendMessage[y])
            # time.sleep(2)
            # readSerial()
        isSuccess = True
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()

    return isSuccess

def addStartupConfig(nodePhysicalAddr, partNumber, startupConfiguration): #untested; bawal din iupdate yung startup config table
    "adds startup config to database; returns if it is added to database"
    nodeId = findNodeId(int(nodePhysicalAddr))
    partNumber = int(partNumber)
    isSuccess = False   

    if nodeId != 0: #if node exists
        startupConfiguration = parseStringToIntArray(startupConfiguration)
        if startupConfiguration[-1] == 254:
            print("footer found")
            startupConfigurationStr = ""
            for s in startupConfiguration:
                startupConfigurationStr += chr(s)
                startupConfigurationStr += " "
            currTime = time.localtime()
            timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', currTime) 
            
            database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
            cur = database.cursor() 
            sql = "INSERT INTO startup_configuration(part_number, startup_configuration, node_id, time_stamp) " \
            "VALUES ('%d', '%s', '%d', '%s')" % (partNumber, startupConfigurationStr, nodeId, timeStamp)
            try:
                cur.execute(sql)
                database.commit()
                isSuccess = True
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                print(e)
                database.rollback()
            database.close()
            #sends immediately
            # sendMessage(startupConfiguration)
            # readSerial()
            # retrievePacketQueue()
        else:
            print("dropped")
    else:
        print("invalid node")
    return isSuccess

def convertStringToInt(commandStr):
    "parses command from string to int[]"
    convertedValue = array('I')
    # print(type(commandStr))
    for x in commandStr:
        convertedValue.append(ord(x))
    # print("packet to send: ")
    # print(convertedValue)
    return convertedValue 

def fetchLatestConfig(configVersion, nodeId):
    "fetch the config of the latest configversion of nodeId"
    database = MySQLdb.connect(host="localhost", user ="root", passwd = "root", db ="thesis")
    cur = database.cursor()
    sql = "SELECT node_configuration FROM nodeconfiguration WHERE node_id = '%d' AND node_configuration_version = '%d'"\
    "ORDER BY time_stamp DESC LIMIT 1" % (nodeId, configVersion)
    result = ""
    try:
        cur.execute(sql)
        result = cur.fetchone()
        result = result[0]
    except(MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    database.close()
    return result  

def sendConfig(nodePhysicalAddr, configVersion):
    "send latest configuration"
    nodeId = findNodeId(nodePhysicalAddr)
    latestConfig = fetchLatestConfig(configVersion, nodeId)
    intConfigArray = convertStringToInt(latestConfig)
    sendMessage(intConfigArray)
    # time.sleep(2)
    # readSerial()
    # retrievePacketQueue()

def resendPacket(recentSent, timeInterval, count): #untested
    "resends recentSent for count times every timeInterval (in seconds)"
    tempCount = 0
    while count != tempCount:
        sendMessage(recentSent)
        time.sleep(timeInterval) 
        tempCount += 1
#check ifs

#get specific port data

def convertHexToVoltageFloat(hexValue):
    "convert from hex value (values in database are in hex); returns float"
    convertedValue = int(hexValue)
    convertedValue = ((convertedValue * 1023) / 999) * (5/1023)
    return convertedValue

def convertVoltageToInt(hexValue):
    "convert data from float voltage to int"
    convertedValue = int(hexValue)
    return convertedValue

def convertVoltageToBoolean(hexValue):
    "convert data from int to boolean"
    hexValue = convertVoltageToInt(hexValue)
    return bool(hexValue)

def convertIntVoltageToString(hexValue):
    "convert int voltage value to string"
    convertedValue = convertVoltageToInt(hexValue)
    convertedValue = str(convertedValue)
    return convertedValue

def convertFloatVoltageToString(hexValue):
    "convert float voltage value to string; rounded off to 3 decimal places"
    return str(hexValue)

def truncateFloat(floatValue, decimalPlaceCount):
    "truncates float value to # of decimal places"
    return round(floatValue, decimalPlaceCount)

# def checkIfNodeConfigSent:
# def checkIfProbeStatusSuccess:
# def formatPacket(): #form the packet to send depending on input

#main program
choice = 0
while choice != 4:
    print('*************************')
    # print('Command line control')
    print('Choose the corresponding number for command: ')
    print('1. Read WSAN data')
    print('2. Send WSAN config')
    print('3. Add Startup Config')
    print('4. Exit')
    print('*************************')
    choice = input('Enter choice: ')

    if choice == '1':
        time.sleep(2)
        readSerial()
        retrievePacketQueue()
    elif choice == '2':
        print("use uppercase")
        command = input('Enter packet to send (bytes are separated by spaces): ')
        inputConfiguration(command)
    elif choice == '3':
        choiceInput = 'X'
        while choiceInput != 'N':
            print("Start from 0")
            nodePhysicalAddr = input('Enter node physical address:')
            partNumber = input('Enter part number: ')
            print("Use uppercase")
            print("Bytes are separated by spaces")
            configuration = input('Enter configuration: ')
            addStartupConfig(nodePhysicalAddr, partNumber, configuration)
            choiceInput = input('Input more? (Y/N)')
    elif choice == '4':
        exit()
    elif choice == '5':
        # sendConfig(1, 255)
        # sendStartupConfig(2)
        data = viewAllPortDataOfPort(10)
        #value, stamp, number
        hexValue = convertHexToVoltageFloat(data[0][0])
        print(hexValue)
        print(truncateFloat(hexValue, 5))
        print(convertVoltageToInt(hexValue))
        print(convertVoltageToBoolean(hexValue))
        print(type(convertIntVoltageToString(hexValue)))
        print(convertIntVoltageToString(hexValue))
        print(convertFloatVoltageToString(truncateFloat(hexValue, 3)))

