import serial
import telnetlib
import re
import time
import Queue
import threading
 
DEVICE = '/dev/ttyS5'
BAUD = 9600
 
HOST = "g7rau.demon.co.uk"
HOST_PORT = "7374"
 
DXC_LOGIN = "NT7S"   #<-----set your callsign
DXC_LOGIN_PATTERN = "login: "
DXC_PROMPT = "dxspider >"
DXC_CMD_NOHERE = "unset/here"
DXC_DX_PATTERN = r'DX de (?P<spotter>.*?):\s+(?P<qrg>\d+)\.\d\s+(?P<call>[\w\/]+)\s+(?P<remark>.*?)\s*\d{4}Z.*'
 
DISPLAY_TIME = 5
 
FIRICH = {'init': '\x1b\x11\x1b\x40',
          'clear': '\x0c',
          'clrline': '\x18',
          'home1': '\x1b\x6c\x01\x01',
          'home2': '\x1b\x6c\x01\x02'}
 
DSP800 = {'init': '\x04\x01\x25\x17',
          'clear': '\x04\x01\x43\x31\x58\x17',
          'home1': '\x04\x01\x50\x31\x17',
          'home2': '\x04\x01\x50\x45\x17'}
 
IBM = {'init': '\x00\x01\x11\x14' +
               '\x03\x15\x70\x88\xC8\xA8\x98\x88\x70\x00' +
               '\x03\x16\x70\x88\x88\x88\x88\x88\x70\x00',
       'clear': 40*' '+'\x10\x00',     
       'home1': '\x10\x00',
       'home2': '\x10\x14',
       'convert': [['0','\x15'],['O','\x16']]}
 
vfd = FIRICH
 
def convert_data(dat, tr_table):
        for key in dat:
                for t in tr_table:
                        dat[key] = dat[key].replace(t[0],t[1])
        return dat
 
def smart_split(s,p):
    if (len(s)>=p):
        while (p):
            if (s[p-1]==' '):
                return p
            p -= 1
    return 0

def get_spot():
	rcv = dxc.read_until("\n",900)
        print rcv.rstrip()
        tmp = re.match(DXC_DX_PATTERN,rcv)
        if tmp is not None:
                data = tmp.groupdict()
		if (vfd.has_key('convert')):
                        data = convert_data(data,vfd['convert'])
		q.put(data)
 
ser = serial.Serial(DEVICE, BAUD)
print ser.portstr
 
ser.write(vfd['init'])
ser.write(vfd['clear'])
 
ser.write("Connect:")
ser.write(HOST)
 
dxc = telnetlib.Telnet(HOST,HOST_PORT)
 
#Wait for login prompt and send username/callsign
dxc.read_until(DXC_LOGIN_PATTERN)
ser.write(vfd['clear'])
ser.write("Login...")
dxc.write(DXC_LOGIN+'\n')
 
#Wait for prompt
dxc.read_until(DXC_PROMPT)
 
#set nohere
ser.write(vfd['clear'])
ser.write("CMD: %s" % (DXC_CMD_NOHERE))
dxc.write(DXC_CMD_NOHERE+'\n')
 
#Wait for prompt
dxc.read_until(DXC_PROMPT)
 
#clear DISPLAY before 1st DX
ser.write(vfd['clear'])

#Setup queue and start thread for first time
q = Queue.Queue()
t = threading.Thread(target=get_spot)
t.daemon = True
t.start()
 
while (1):
	# Display UTC time on first line
	curutc = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
	ser.write(vfd['home1'])
	ser.write("%s" % curutc)

	# Start a thread to get a cluster spot
	if (t.is_alive() == False):
		t = threading.Thread(target=get_spot)
		t.daemon = True
		t.start()
	
	# Check the queue to see if there's spots to display
	if (q.empty() == False):
		spot = q.get()
		ser.write(vfd['home2'])
		ser.write(vfd['clrline'])
                ser.write("%s %s" % (spot['qrg'],spot['call']))
                #spot_hold = True
                #time.sleep(DISPLAY_TIME)
	
	#print threading.active_count()
	#time.sleep(DISPLAY_TIME)

