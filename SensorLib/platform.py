from connection import *
from sensor import Sensor

class Platform(object):
    """
    Putting sensor data onto the network (WiFi / LoRa / ...)
    
    Todo : Allow for multiple network settings (LoRa + WiFi + ..)
        -> set preference on which to use for putting sensor data onto the wire
    """
    
    def __init__(self, network, deviceId):
        if not isinstance(network , Connection):
            raise OSError('Invalid \'network\' parameter!')
        if not network:
            raise OSError('\'network\' parameter IS MANDATORY!')
        if not deviceId:
            raise OSError('\'deviceId\' parameter IS MANDATORY!')
        
        self.connection = network
        self.deviceId = deviceId
        self.location = {}
        self.locationFriendlyName = None
        
    def getDeviceId(self):
        return self.deviceId
        
    def setDeviceId(self, deviceID):
        self.deviceId = deviceID

        
    def setLocation(self , latitude = None ,  longitude = None , altitude = None , friendlyName = None):
        if latitude: self.location['latitude'] = latitude
        if longitude: self.location['longitude'] = longitude
        if altitude: self.location['altitude'] = altitude
        if friendlyName: self.locationFriendlyName = friendlyName
        
    def setLocationFriendlyName(self, friendlyName):
        self.locationFriendlyName = friendlyName
        
    def getLocation(self):
        return self.location
        
    def pushSensorData(self, enCoSensor, debug=False, forceCreateChannel = False):
        if not isinstance(enCoSensor , Sensor):
            raise OSError('Invalid \'Sensor\' parameter!')
            
        enCoSensor.setDeviceId(self.deviceId)
        self.connection.pushSensorData(enCoSensor, debug, forceCreateChannel)


    def createCCInDefinition(self, enCoSensor, debug=False):
        if not isinstance(enCoSensor , Sensor):
            raise OSError('Invalid \'Sensor\' parameter!')
            
        self.connection._createCCInStreamDefinition(enCoSensor, debug)
        
