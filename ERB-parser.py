import copy
import Queue
import math
import struct
import ctypes
import sys

waiting_header = 0
msg_id = 1
length = 2
payload = 3
checksum = 4

class ERB_message:

	def __init__(self, msg_id = 0, msg_length = 0, msg_payload = []):
		self.msg_id = msg_id 
		self.msg_length = msg_length
		self.msg_payload = msg_payload
	
	def clear(self):
		self.msg_id = 0
		self.msg_length = 0
		self.msg_payload = []

class ERB:

	def __init__(self):
		self.mess_queue = Queue.Queue()
		self.curr_mess = ERB_message()
		self.state = 0
		self.counter = 0
		self.chk_a = 0
		self.chk_b = 0
		self.accepted_chk_a = 0
		self.accepted_chk_b = 0

	def scan_erb(self, str_byte):
		byte = ctypes.c_uint8(ord(str_byte)).value
		if(self.state == waiting_header):
			self.result = [0,0,0,0,0,0,0,0,0]
			self.accepted = 0
			self.chk_a = 0
			self.chk_b = 0
			if((self.counter == 0) and (byte == 0x45)):
				self.counter += 1
			elif((self.counter == 0) and (byte != 0x45)):
				self.state = waiting_header
				self.counter = 0
			elif((self.counter == 1) and (byte == 0x52)):
				self.counter = 0
				self.state = msg_id
			elif((self.counter == 1) and (byte != 0x52)):
				self.counter = 0
				self.state = waiting_header
		elif(self.state == msg_id):
			self.chk_a = (self.chk_a + byte) % 256
			self.chk_b = (self.chk_b + self.chk_a) % 256
			self.curr_mess.msg_id = byte
			self.state = length
		elif(self.state == length):
			if(self.counter == 0):
				self.chk_a = (self.chk_a + byte) % 256
				self.chk_b = (self.chk_b + self.chk_a) % 256
				self.counter += 1
				self.curr_mess.msg_length = byte
			elif(self.counter == 1):
				self.chk_a = (self.chk_a + byte) % 256
				self.chk_b = (self.chk_b + self.chk_a) % 256
				self.counter = 0
				self.curr_mess.msg_length = self.curr_mess.msg_length + 256 * byte
				self.state = payload
		elif(self.state == payload):
			self.chk_a = (self.chk_a + byte) % 256
			self.chk_b = (self.chk_b + self.chk_a) % 256
			
			self.curr_mess.msg_payload.append(byte)
			if(self.counter < self.curr_mess.msg_length - 1):
				self.counter += 1
			else:
				self.counter = 0
				self.state = checksum

		elif(self.state == checksum):
			if(self.counter == 0):
				self.accepted_chk_a = byte
				self.counter += 1
			elif(self.counter == 1):
				self.accepted_chk_b = byte
				self.counter = 0
				self.state = waiting_header
				self.curr_mess.msg_length = 0
				if((erb.chk_a == erb.accepted_chk_a) & (erb.chk_b == erb.accepted_chk_b)):
					self.mess_queue.put(copy.deepcopy(self.curr_mess))
					self.curr_mess.clear()
				else:
					print("Error! Checksum doesn't match")
					self.curr_mess.clear()

	def parse_erb(self):
		curr_values = [0,0,0,0,0,0,0]
		curr_mess = self.mess_queue.get(False)
		if curr_mess.msg_id == 0x01:
			msg = VerMsg()
			if len(curr_mess.msg_payload) != 7:
				print "Invalid length of version message: %d, need 7" % len(curr_mess.msg_payload)
				return None
			curr_values = struct.unpack("<IBBB", str(bytearray(curr_mess.msg_payload)))
			msg.time = curr_values[0]
			msg.verH = curr_values[1]
			msg.verM = curr_values[2]
			msg.verL = curr_values[3]
			return msg

		if curr_mess.msg_id == 0x02:
			msg = PosMsg()
			if len(curr_mess.msg_payload) != 44:
				print "Invalid length of position message: %d, need 44" % len(curr_mess.msg_payload)
				return None
			curr_values = struct.unpack("<IddddII", str(bytearray(curr_mess.msg_payload)))
			msg.time      = curr_values[0]
			msg.lon       = curr_values[1]
			msg.lat       = curr_values[2]
			msg.heightEll = curr_values[3]
			msg.heightSea = curr_values[4]
			msg.horAcc    = curr_values[5]
			msg.verAcc    = curr_values[6]
			return msg

		if curr_mess.msg_id == 0x03:
			msg = StatusMsg()
			if len(curr_mess.msg_payload) != 9:
				print "Invalid length of status message: %d, need 9" % len(curr_mess.msg_payload)
				return None
			curr_values = struct.unpack("<IHBBB", str(bytearray(curr_mess.msg_payload)))
			msg.time      = curr_values[0]
			msg.week      = curr_values[1]
			msg.fixType   = curr_values[2]
			msg.fixStatus = curr_values[3]
			msg.numSV     = curr_values[4]
			return msg

		if curr_mess.msg_id == 0x04:
			msg = DopsMsg()
			if len(curr_mess.msg_payload) != 12:
				print "Invalid length of DOP message: %d, need 12" % len(curr_mess.msg_payload)
				return None
			curr_values = struct.unpack("<IHHHH", str(bytearray(curr_mess.msg_payload)))
			msg.time = curr_values[0]
			msg.dopG = curr_values[1] * 0.01
			msg.dopP = curr_values[2] * 0.01
			msg.dopV = curr_values[3] * 0.01
			msg.dopH = curr_values[4] * 0.01
			return msg
		if curr_mess.msg_id == 0x05:
			msg = VelMsg()
                        if len(curr_mess.msg_payload) != 28:
                                print "Invalid length of velocity message: %d, need 28" % len(curr_mess.msg_payload)
                                return None
                        curr_values = struct.unpack("<IiiiIiI", str(bytearray(curr_mess.msg_payload)))
                        msg.time = curr_values[0]
                        msg.velN = curr_values[1]
                        msg.velE = curr_values[2]
                        msg.velD = curr_values[3]
                        msg.speed = curr_values[4]
			msg.heading = curr_values[5] * 0.00001
			msg.accS = curr_values[6]
                        return msg
		if curr_mess.msg_id == 0x06:
			curr_values = struct.unpack("<IB", str(bytearray(curr_mess.msg_payload[0:5])))
			n = curr_values[1]
			m = 8
			msg = SviMsg(n)
			msg.time      = curr_values[0]
			msg.nSV       = n
			
			sats = [0] * n
			for i in range(n):
    				sats[i] = [0] * m

			for i in range(n):
				line = (str(bytearray(curr_mess.msg_payload[5+i*20:25+i*20])))
				sats[i] = struct.unpack("<BBiiiHHH", line)
				msg.idSV[i] = sats[i][0]
				msg.typeSV[i] = sats[i][1]
				msg.carPh[i] = sats[i][2]
				msg.psRan[i] = sats[i][3]
				msg.freqD[i] = sats[i][4] * 0.001
				msg.snr[i] = sats[i][5] * 0.25
				msg.azim[i] = sats[i][6] * 0.1
				msg.elev[i] = sats[i][7] * 0.1
			return msg

		return "Unknown message id: %d" % (curr_mess.msg_id)
		return None

class VerMsg:

	def __init__(self):
		self.time = 0
		self.verH = 0
		self.verM = 0
		self.verL = 0

	def __str__(self):
		time = "GPS Time of Week: %d s" % (self.time)
		ver = "Current version of protocol: %d.%d.%d" % (self.verH, self.verM, self.verL)
		return '{}\n{}\n'.format(time, ver)	

class PosMsg:

	def __init__(self):
		self.time = 0
		self.lon = 0
		self.lat = 0
		self.heightEll = 0
		self.heightSea = 0
		self.horAcc = 0
		self.verAcc = 0

	def __str__(self):
		time = "GPS Time of Week: %d s" % (self.time)
		lon = "Longitude: %.6f"  % (self.lon)
		lat = "Latitude: %.6f" % (self.lat)
		heightEll = "Height above Ellipsoid: %.3f m" % (self.heightEll)
		heightSea = "Height above mean sea level: %.3f m" % (self.heightSea)
		horAcc = "Horizontal Accuracy Estateimate: %.3f m" % (self.horAcc)
		verAcc = "Vertical Accuracy Estateimate: %.3f m" % (self.verAcc)
		return '{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(time, lon, lat, heightEll, heightSea, horAcc, verAcc)

class StatusMsg:

	def __init__(self):
		self.time = 0
		self.week = 0
		self.fixType = 0
		self.fixStatus = 0
		self.numSV = 0

	def __str__(self):
                time = "GPS Time of Week: %d s" % (self.time)
                week = "GPS Week: %d" % (self.week)
		if   (self.fixType == 0x00): Type = "No fix"
		elif (self.fixType == 0x01): Type = "Single"
		elif (self.fixType == 0x02): Type = "Float"
		elif (self.fixType == 0x03): Type = "Fix"
		else: Type = "Reserved value. Current state unknown, %d" % (self.fixType)
		fixStatus = "Status: %d" % (0x01 & self.fixStatus)
		numSV = "Number of used satellites: %d" % (self.numSV)
		return '{}\n{}\n{}\n{}\n{}\n'.format(time, week, Type, fixStatus, numSV)

class DopsMsg:

	def __init__(self):
                self.time = 0
                self.dopG = 0
                self.dopP = 0
                self.dopV = 0
                self.dopH = 0

	def __str__(self):
                time = "GPS Time of Week: %d s" % (self.time)
                dopG = "GDOP: %.2f"  % (self.dopG)
                dopP = "PDOP: %.2f"  % (self.dopP)
                dopV = "VDOP: %.2f"  % (self.dopV)
                dopH = "HDOP: %.2f"  % (self.dopH)
		return '{}\n{}\n{}\n{}\n{}\n'.format(time, dopG, dopP, dopV, dopH)

class VelMsg:

        def __init__(self):
                self.time    = 0
                self.velN    = 0 
                self.velE    = 0 
                self.velD    = 0
                self.speed   = 0
                self.heading = 0
                self.accS    = 0

        def __str__(self):
                time = "GPS Time of Week: %d s" % (self.time)
                velN = "North velocity: %d"  % (self.velN)
                velE = "East velocity: %d"  % (self.velE)
                velD = "Down velocity: %d"  % (self.velD)
                speed = "Ground speed: %d"  % (self.speed)
                heading = "Heading: %d"  % (self.heading)
                accS = "Speed accuracy: %d"  % (self.accS)
		return '{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(time, velN, velE, velD, speed, heading, accS)

class SviMsg:

	def __init__(self, n):
                self.time   = 0
                self.nSV    = 0
		self.idSV   = [0] * n
		self.typeSV = [0] * n
		self.carPh  = [0] * n
		self.psRan  = [0] * n
		self.freqD  = [0] * n
		self.snr    = [0] * n
		self.azim   = [0] * n
		self.elev   = [0] * n

	def __str__(self):
                time = "GPS Time of Week: %d s" % (self.time)
                nSV = "Number of visible satellites: %d"  % (self.nSV)
		header = "Type ID  Carrier-phase Pseudo range Doppler freq. Strength Azimuth Elevevation"
		table = ""
		satType = {
			0: 'GPS',
			1: 'GLO',
			2: 'GAL',
			3: 'QZSS',
			4: 'BD',
			5: 'LEO',
			6: 'SBAS'
		}
		for i in range(self.nSV):
			table += "%-4s %-3d %-13d %-12d " % (satType[self.typeSV[i]], self.idSV[i], self.carPh[i], self.psRan[i])
                	table += "%-13.3f %-8.0f %-7.1f %-7.1f\n" % (self.freqD[i], self.snr[i], self.azim[i], self.elev[i]) 
		return '{}\n{}\n{}\n{}'.format(time, nSV, header, table)

if len(sys.argv) == 1:
	sys.exit("Enter input file")

try:
	f = open(sys.argv[1], 'rb')
except:
	sys.exit("Can't open file")

erb = ERB()
byt = 0

while(1):
	buffer = f.read(1000)
	if (buffer == ""):
		break
	for byt in buffer:
		erb.scan_erb(byt)
		if(erb.mess_queue.empty() != True):
			msg = erb.parse_erb()
			if (msg != None): print(msg)

f.close()
