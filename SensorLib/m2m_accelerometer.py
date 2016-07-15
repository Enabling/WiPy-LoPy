from m2m_sensor import M2M_Sensor

class Accelerometer(M2M_Sensor):
    def __init__( self ):

        M2M_Sensor.__init__(self, 8, self.__class__.__name__)
        self.data['accelerometerMeterValue'] = {'x':0, 'y':0, 'z':0}
        self.stream_def["properties"]={"x":{"type":"number"},"y":{"type":"number"},"z":{"type":"number"}}

    def setValue(self, x = None ,  y = None ,  z = None):
#       WiPy DOESN'T have float support !!!
#        if not isinstance(x , float) or not isinstance(y , float) or not isinstance(z , float) :
#            raise OSError('Invalid parameter used!')
            
        if x: self.data['accelerometerMeterValue']['x'] = x
        if y: self.data['accelerometerMeterValue']['y'] = y
        if z: self.data['accelerometerMeterValue']['z'] = z
        self._updateTimestamp()
        
    def getValue(self):
        return self._cleandict(self.data['accelerometerMeterValue'])

    def getAsJson(self):
        return self.getValue()
