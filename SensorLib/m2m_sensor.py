from sensor import Sensor
from ustruct import pack

class M2M_Sensor(Sensor):
    def __init__( self, m2mContainerId,  streamName ):
        Sensor.__init__(self, streamName)
        self.data = {}
        self.m2mContainerId = m2mContainerId
        self.stream_def["title"] = streamName
        self.stream_def["properties"]={"value":{"type":"boolean"}}

    def getStreamDefinition(self):
        return self.stream_def

    def getContainerId(self):
        return self.m2mContainerId

    def getAsBinary(self):
        #Build the binary payload as specified by the M2M container definition ...
        loraPacket = self._createLoRaPacket()
        self._addSensorData(loraPacket)
        self._finalize(loraPacket)
        #DEBUG
        #print (''.join('{:02X}'.format(x) for x in loraPacket))
        return ''.join('{:02X}'.format(x) for x in loraPacket)
        
    def _createLoRaPacket(self):
        packet = bytearray(b'\x7E\x00\x00\x40')
        packet.append(self.getContainerId() & 0xFF)
        return packet
        
    def _addSensorData(self, packet):
        #BinaryPayloadContainer ???
        if self.getContainerId() == 17:
            packet.extend(self.getValue())
            return
        
        if self.data['booleanMeterValue']:
            packet.append(0x01)
        else:
            packet.append(0x00)
        
        if not self.data['booleanMeterValue'] is None:
            return
        
        #ATT LIBRARY USING 'SHORT' where mentioning 'INT' !!!!!
        if self.data['integerMeterValue']:
            packet.append(0x01)
            packet.extend(pack('>h',self.data['integerMeterValue']))
            return
        else:
            packet.append(0x00)

        if self.data['doubleMeterValue']:
            packet.append(0x01)
            packet.extend(pack('>f',self.data['doubleMeterValue']))
            return
        elif self.data['accelerometerMeterValue']:
            packet.append(0x03)
            packet.extend(pack('>fff',self.data['accelerometerMeterValue']['x'], self.data['accelerometerMeterValue']['y'], self.data['accelerometerMeterValue']['z']))
            return
        elif self.data['gpsMeterValue']:
            packet.append(0x04)
            packet.extend(pack('>ffff',self.data['gpsMeterValue']['latitude'], self.data['gpsMeterValue']['longitude'], self.data['gpsMeterValue']['altitude'], self.data['gpsMeterValue']['timestamp']))
            return
        else:
            #Nothing left for now ... so shouldn't really be getting here.
            packet.append(0x00)


    def _finalize(self,  packet):
        checksum = self._calCSum(packet[3:])
        packet.append(checksum & 0xFF)
        packet[2] = (len(packet) - 4) & 0xFF

    def _calCSum(self, arr):
        sum = 0
        for x in arr:
#            print('Debug 0 : x[.]=', x)
            sum += x
            
#        print('Debug 1 : sum=', sum)
            
        while sum > 0xFF:
            newsum = 0
            for x in range(0, 3):
                newsum += sum & 0xFF
#                print('Debug 2 : NEWsum=', newsum)
                sum >> 8
            sum = newsum
#            print('Debug 2 : sum=', sum)

        sum = 0XFF - sum
#        print('Debug 3 : sum=', sum)

        return sum

