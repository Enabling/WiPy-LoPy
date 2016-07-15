from m2m_sensor import M2M_Sensor
from utime import time

class GPS(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 9, self.__class__.__name__)
        self.data['gpsMeterValue'] = {'longitude':0, 'latitude':0, 'altitude':0, 'timestamp':time()}
        self.stream_def["properties"]={"longitude":{"type":"number"},"latitude":{"type":"number"},"altitude":{"type":"number"},"timestamp":{"type":"integer"}}

    def setValue(self, longitude = None ,  latitude = None ,  altitude = None, timestamp=None):
#       WiPy DOESN'T have float support !!!
#        if not isinstance(longitude , float) or not isinstance(latitude , float) or not isinstance(altitude , float) :
#            raise OSError('Invalid parameter used!')
            
        if longitude: self.data['gpsMeterValue']['longitude'] = longitude
        if latitude: self.data['gpsMeterValue']['latitude'] = latitude
        if altitude: self.data['gpsMeterValue']['altitude'] = altitude
        if timestamp: self.data['gpsMeterValue']['timestamp'] = timestamp
        self._updateTimestamp()
        
    def getValue(self):
        return self._cleandict(self.data['gpsMeterValue'])

    def getAsJson(self):
        return self.getValue()
