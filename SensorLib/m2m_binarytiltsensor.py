from m2m_sensor import M2M_Sensor

class BinaryTiltSensor(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 2, self.__class__.__name__)
        self.data['booleanMeterValue'] = False

    def setValue(self, booleanValue):
        if not isinstance(booleanValue , bool):
            raise OSError('Invalid \'booleanValue\' parameter!')
            
        self.data['booleanMeterValue'] = booleanValue
        self._updateTimestamp()
        
    def getValue(self):
        return self.data['booleanMeterValue']
    
    def getAsJson(self):
        return {"value" : self.data['booleanMeterValue']}

