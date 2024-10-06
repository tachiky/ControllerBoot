import bluetooth
import struct
import utime

from micropython import const

_IRQ_SCAN_RESULT                 = const(5)
_IRQ_SCAN_DONE                   = const(6)

_ADV_TYPE_NAME             = const(0x09)

# decode field name
def decode_field(payload, adv_type):
    i = 0
    result = []
    while( i + 1 < len(payload) ):
        if payload[i + 1] == adv_type:
            result.append(payload[i + 2:i + payload[i] + 1])
        i += 1 + payload[i]
    return result

# decode device name
def decode_name(payload):
    n = decode_field(payload, _ADV_TYPE_NAME)
    return str(n[0], 'utf-8') if n else ''

# decode MAC address
def decode_addr(payload):
    ret = ''
    for d in payload:
        ret = ret + ':' + '{:02X}'.format(d)
    return ret[1:]

# BLE GamePad central object
class gamepad(object):
    def __init__(self, ble, controller_mac):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._reset()
        self._controller_mac = controller_mac

    # reset
    def _reset(self):
        # Cached name and address from a successful scan.
        self._name      = None
        self._addr_type = None
        self._addr      = None

        self._is_scanning  = False
        self._is_find_controller = False


    # interrupt function
    def _irq(self, event, data):
        # check event
        if(event == _IRQ_SCAN_RESULT):
            # get scan result            
            (addr_type, addr, adv_type, rssi, adv_data) = data # get detected device data
            mac = decode_addr(list(bytes(addr)))
            #print( 'FOUND DEVICE! : TYPE={}\tADDR={}\tNAME={}'.format(addr_type, mac, decode_name(adv_data)) )
            # device check
            if(mac == self._controller_mac):
                #print( 'FOUND DEVICE! : TYPE={}\tADDR={}\tNAME={}'.format(addr_type, mac, decode_name(adv_data)) )
                self._is_find_controller = True

        elif(event == _IRQ_SCAN_DONE):
            #print('### SCAN DONE ###')            
            # scanned all devices
            self._is_scanning   = False

    # scanning check
    def is_scanning(self):
        return(self._is_scanning)    

    # scan
    def scan(self, callback=None):
        self._addr_type     = None
        self._addr          = None
        self._is_scanning   = True

        self._ble.gap_scan(2000, 30000, 30000)

    # controller find check
    def is_find_controller(self):
        return(self._is_find_controller)
