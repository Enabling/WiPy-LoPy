from sensor import Sensor
#import json

class Environment(Sensor):
    def __init__( self ):
        self.streamID = "Environment"
        # Specify the STREAM-ID as it's specified in your stream definition on the SeaaS platform
        Sensor.__init__(self, self.streamID)
        # Copy/Paste from web portal
        # Call API to get LATEST stream information .....
        self.sensorValue[self.streamID] = {}
        
        self.stream_def["title"] = self.streamID
        self.stream_def["properties"] = {
                                        self.streamID: {
                                          "type": "object",
                                          "properties": {
                                            "temperature": {
                                              "type": "integer"
                                            },
                                            "humidity": {
                                              "type": "integer"
                                            },
                                            "airpressure": {
                                              "type": "integer"
                                            }
                                          },
                                          "additionalProperties": False
                                        }
                                      }

    def getStreamDefinition(self):
        return self.stream_def

    def setTemperature(self, val):
        self.sensorValue[self.streamID]['temperature'] = val
        self._updateTimestamp()
        
    def setHumidity(self, val):
        self.sensorValue[self.streamID]['humidity'] = val
        self._updateTimestamp()
        
    def setAirpressure(self, val):
        self.sensorValue[self.streamID]['airpressure'] = val
        self._updateTimestamp()
        
    def getValue(self):
        return self.sensorValue
        
    def getValues(self):
        return self._buildValueDict()
        
    def clearValues(self):
        self.sensorValue[self.streamID] = {}
        self._updateTimestamp()


