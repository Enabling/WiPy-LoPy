from m2m_sensor import M2M_Sensor
from ubinascii import b2a_base64, a2b_base64

class BinaryPayloadSensor(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 17, self.__class__.__name__)
        self.data['binaryMeterValue'] = 0
        self.stream_def["properties"]["value"]["type"] = "string"

    def setValue(self, byteArrayValue):
#        if not isinstance(byteArrayValue , array):
#            raise OSError('Invalid \'byteArrayValue\' parameter!')
        
        # BASE64 encode the data !!!!
        converted = str(b2a_base64(byteArrayValue), 'utf-8').strip('\n')
        self.data['binaryMeterValue'] = converted
        self._updateTimestamp()
        
    def getValue(self):
        # BASE64 decode the data !!!!
        converted = a2b_base64(self.data['binaryMeterValue'])
        return converted

    def getAsJson(self):
        return {"value" : self.data['binaryMeterValue']}
