import utime
from json import dumps

class Sensor(object):
    hasCCINdefinition = False #If you're sure it exists, best to overrride in implementing class to save http calls

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
    
    def getStreamId( self ):
        #return self.containerId
        return 'IP_{}'.format(self.containerId)
        
    def getStreamDefinition(self):
        return None
        
    def sendAsBinary(self):
        """
        When sending over WiFi, whether to send it as JSON or binary data
        """
        return False

    def getStreamDefinitionJSON(self):
        result = {"owner":"",  "name":self.getStreamId(), "payload_type":"JSON", "json_schema" : None}
        if self.sendAsBinary() != True:
            result["json_schema"] = dumps(self.getStreamDefinition())
        else:
            result["payload_type"] = "BINARY"
            
        return result
    
    def getCloudChannelInDefinitionJSON(self):
        result = {"owner":"","payload_type":"JSON","latest_message_definition":{"name":self.getStreamId(),"owner":""},"end_point_types":["HTTP"],"selected_assets":["SEAAS","CC_OUT"],"additional_props_for_assets":{"SEAAS":{"deviceId":self.getDeviceId()},"CC_OUT":{}},"user_defined_urls":{"HTTP":[self.getStreamId()]}}
        if self.sendAsBinary() == True:
            result["payload_type"] = "BINARY"

        return result
        
    def getCloudChannelBaseDefinitionJSON_ATT(self, owner):
        """
        Prepares the bare bones JSON structure for our CC definition HTTP->SEaaS
        WIP
        """
        now = utime.localtime()
        name = '{}_for_{}'.format(self.getStreamId(), self.getDeviceId())
        ccdef = {
                  "owner": owner,
                  "enabled_interval": {
                    "start": '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.000+0000'.format(*now)
                  },
                  "cc_name": name,
                  "log_headers": True,
                  "log_body": True,
                  "versioned_message_definition_pk": {
                    "owner": owner,
                    "name": self.getStreamId(),
                    "version": 1, 
                    "payload_type": "ATT_LORA"
                  },
                  "cc_in_sources": [
                    {
                      "end_point_type": "HTTP",
                      "user_defined_urls": [
                        name
                      ]
                    }
                  ],
                  "cc_out_sinks": [
                    {
                      "name": name,
                      "output_type": "SEAAS",
                      "active": True,
                      "identity_transform": True,
                      "conditions": [],
                      "subscription": {
                        "seaas_destination": {
                          "device_id": self.getDeviceId()
                        }
                      }
                    }
                  ]
                }
        
        
        return ccdef
        
    def getCloudChannelBaseDefinitionJSON(self, owner, latestmesagedefinition):
        """
        Prepares the bare bones JSON structure for our CC definition HTTP->SEaaS
        """
        now = utime.localtime()
        name = '{}_for_{}'.format(self.getStreamId(), self.getDeviceId())
        ccdef = {
                  "owner": owner,
                  "enabled_interval": {
                    "start": '{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.000+0000'.format(*now)
                  },
                  "cc_name": name,
                  "log_headers": True,
                  "log_body": True,
                  "versioned_message_definition_pk": {
                    "owner": owner,
                    "name": self.getStreamId(),
                    "version": latestmesagedefinition
                  },
                  "cc_in_sources": [
                    {
                      "end_point_type": "HTTP",
                      "user_defined_urls": [
                        name
                      ]
                    }
                  ],
                  "cc_out_sinks": [
                    {
                      "name": name,
                      "output_type": "SEAAS",
                      "active": True,
                      "identity_transform": True,
                      "conditions": [],
                      "subscription": {
                        "seaas_destination": {
                          "device_id": self.getDeviceId()
                        }
                      }
                    }
                  ]
                }
        
        
        return ccdef

    def getCloudChannelCustomHTTP(self):
        return "{0}_for_{1}".format(self.getStreamId(),self.getDeviceId())

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

    def getData(self):
        pass
