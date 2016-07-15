from m2m_sensor import M2M_Sensor

class AirQualitySensor(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 13, self.__class__.__name__)
        self.data['integerMeterValue'] = 0
        self.stream_def["properties"]["value"]["type"] = "integer"

    def setValue(self, integerValue):
        if not isinstance(integerValue , int):
            raise OSError('Invalid \'integerValue\' parameter!')
            
        self.data['integerMeterValue'] = integerValue
        self._updateTimestamp()
        
    def getValue(self):
        return self.data['integerMeterValue']

    def getAsJson(self):
        return {"value" : self.data['integerMeterValue']}
