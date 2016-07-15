from m2m_sensor import M2M_Sensor

class LightSensor(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 6, self.__class__.__name__)
        self.data['doubleMeterValue'] = 0
        self.stream_def["properties"]["value"]["type"] = "number"

    def setValue(self, decimalValue):
#       WiPy DOESN'T have float support !!!
#        if not isinstance(decimalValue , float):
#            raise OSError('Invalid \'decimalValue\' parameter!')
            
        self.data['doubleMeterValue'] = decimalValue
        self._updateTimestamp()
        
    def getValue(self):
        return self.data['doubleMeterValue']

    def getAsJson(self):
        return {"value" : self.data['doubleMeterValue']}
