import utime

class Sensor(object):
    hasCCINdefinition = False

    def __init__( self, streamId):
            
        self.macAddress = None
        self.containerId = streamId
        self.timestamp = None
        
        self.sensorValue = {}

        self.stream_def = {}
        self.stream_def["$schema"] = "http://json-schema.org/draft-04/schema#"
        self.stream_def["type"] = "object"
        self.stream_def["properties"]= {}
        self.stream_def["additionalProperties"]= False
        self.stream_def["title"] = None
        
        self._updateTimestamp()
        
    def getType(self):
        return type(self.getValue())
        
    def _updateTimestamp(self):
        now = utime.localtime()
        self.timestamp = '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.000+0000'.format(*now)

    def _cleandict(self, d):
        if not isinstance(d, dict):
            return d
        return dict((k,self._cleandict(v)) for k,v in d.items() if v is not None)
       
#    def getData( self ):
#        return self.data
    
    def getStreamId( self ):
        return self.containerId
        
    def getStreamDefinition():
        return None

    def setDeviceId( self,  deviceId ):
        self.macAddress = deviceId

    def getDeviceId( self ):
        return self.macAddress

    def getAsJson(self):
        return self._cleandict(self.sensorValue)
        
    def getAsBinary(self):
        raise OSError('Provide specific implementation!')
        
    def getValue(self):
        return self.sensorValue

