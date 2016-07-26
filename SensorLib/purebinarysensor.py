from sensor import Sensor
#from ubinascii import b2a_base64, a2b_base64, unhexlify,  hexlify


class JustBinary(Sensor):
    """
    Sending arbitrary binary payload
    CloudChannel-In endpoint MUST be defined as expecting BINARY !!!
    """
    def __init__( self ):
        streamName = self.__class__.__name__
        Sensor.__init__(self, streamName)
        self.hasCCINdefinition = True
        self.binaryMeterValue = None

    def getStreamDefinition(self):
        return {}

    def sendAsBinary(self):
        return True

    def getAsJson(self):
        return self.binaryMeterValue
        
    def setValue(self, byteArrayValue):
        self.binaryMeterValue = byteArrayValue

    def getValue(self):
        return self.byteArrayValue
