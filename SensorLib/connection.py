import http_client
from utime import time, localtime
import ubinascii
from sensor import Sensor
import json

class Connection:
    """Base connection class"""

    def pushSensorData(self, enCoSensor,  debug = False):
        raise NotImplementedError("Please Implement this method")

# ------------------------ WiFi ------------------------

class WiFi(Connection):
    """
    Putting sensor data onto the Enabling platform.
    USING WiFi and going through the NEW 'cloudchannel-in' API.
    """
    _serverUrlsToken = { 'UAT':'https://login.enabling.be/oauth2/token'}
    _serverUrlsCC_In = { 'UAT':'https://api.enabling.be/platform/cloudchannels/1.0.0' }
    
    
    def __init__(self, userName,  passWord, apiKey,  apiSecret):
        self.userName = userName    #URL ENCODED !!
        self.passWord = passWord    #URL ENCODED !!
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        self.validUntil = None
        self.tokenBearer = None
        self.tokenRefresh = None
        self.connectToURLforToken = WiFi._serverUrlsToken["UAT"]
        self.connectToURLforCC_In = WiFi._serverUrlsCC_In["UAT"]
        
        
    def _getToken(self, debug = False):
        
        
        if self.apiKey == None or self.apiSecret == None or self.userName == None or self.passWord == None:
            raise OSError('Missing authentication info!')
            
        if self.validUntil == None or time() >= self.validUntil:
            # get the token ....
            # use another approach when the refresh token is available ?
            basic_auth = ubinascii.b2a_base64("{}:{}".format(self.apiKey, self.apiSecret)).decode('ascii')
            auth_header = {'Authorization':'Basic {}'.format(basic_auth), 'Accept':'application/json'}
            body = 'grant_type=password&username=%s&password=%s' % (self.userName, self.passWord)
            if debug: print(self.connectToURLforToken)
            resp = http_client.post(self.connectToURLforToken, headers=auth_header, textMsg=body, contentType='application/x-www-form-urlencoded',  debug = debug)
            resp.raise_for_status()
            resp.content
            if debug:
                print ('Response : ')
                print (resp.content)
            
            authInfo = resp.json()
            self.tokenBearer = authInfo['access_token']
            self.tokenRefresh = authInfo['refresh_token']
            self.validUntil = time() + authInfo['expires_in']
            resp.close()
            if debug: print ("Token retrieved ! valid until {}".format(localtime(self.validUntil)))
        else:
            if debug: print ("Token still valid !  Re-using it ! {}".format(self.tokenBearer))
                    
                    
    def _createCCInStreamDefinition(self, m2mSensor,  debug = False):
        if m2mSensor.getStreamDefinition() == None:
            raise OSError ("Can't create cloudchannel-in stream for given sensor.")
        
        self._getToken(debug)
        #POST message definition pk  !!
        postUrl = "{}/cc-in/bymessagedefinitionpk".format(self.connectToURLforCC_In)
        data = {"owner":self.userName,  "name":m2mSensor.getStreamId()}
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.post(postUrl, headers=auth_header, json=data, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.getStatus())
        resp.close()
        print ("### PK : created ###")
        #PUT the definition
        putUrl = "{}/messagedefinition".format(self.connectToURLforCC_In)
        data = {"owner":self.userName,  "name":m2mSensor.getStreamId(), "json_schema" : json.dumps(m2mSensor.getStreamDefinition())}
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.getStatus())
        resp.close()
        print ("### MD : created ###")
        #PUT the cloudchannel
        putUrl = "{}/cc-in/".format(self.connectToURLforCC_In)
        data = {"owner":self.userName,"payload_type":"JSON","latest_message_definition":{"name":m2mSensor.getStreamId(),"owner":self.userName},"end_point_types":["HTTP"],"selected_assets":["SEAAS"],"additional_props_for_assets":{"SEAAS":{"deviceId":m2mSensor.getDeviceId()}},"user_defined_urls":{"HTTP":[m2mSensor.getStreamId()]}}
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.getStatus())
        resp.close()
        print ("### CC : created ###")
        
        
        
    def pushSensorData(self, enCoSensor,  debug = False,  forceCreateChannel = False):
        if not enCoSensor or not isinstance(enCoSensor , Sensor):
            raise OSError('\'Sensor\' parameter undefined or wrong type!')

        data = enCoSensor.getAsJson()
        #deviceId = enCoSensor.getDeviceId()
        self._getToken(debug)
        
        #self.getLatestMessageDefinitions(debug)  
        if not self.sensorHasMessageDefinition(enCoSensor, debug):
            if debug: print("-- Sensor has NO CC-IN stream definition.")
            self._createCCInStreamDefinition(enCoSensor, debug)
            pass # toDO Create the sensor stream (ATT !!)
        else:
            if forceCreateChannel:
                self._createCCInStreamDefinition(enCoSensor, debug)
                if debug: print("-- Sensor HAD CC-IN stream definition! BUT RECREATED !!")
            else:
                if debug: print("-- Sensor HAS CC-IN stream definition!")
            pass
        
        postUrl = "{}/cc-in/u/{}".format(self.connectToURLforCC_In, enCoSensor.getStreamId())
        
        if debug: 
            print('Sending endpoint : ', postUrl)
            print('Payload : ',  data)
                
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.post(postUrl, headers=auth_header, json=data, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.getStatus())
        resp.close()

    def getLatestMessageDefinitions(self, debug = False):
        self._getToken(debug)
        getUrl = "{}/messagedefinition/latest".format(self.connectToURLforCC_In)
        if debug: 
            print('Sending endpoint : ', getUrl)
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.get(getUrl, headers=auth_header, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.content)
        resp.close()
        
    def checkIfMessageDefinitionExists(self, whatName, debug = False):
        self._getToken(debug)
        getUrl = "{}/messagedefinition/latest/{}".format(self.connectToURLforCC_In, whatName)
        if debug: 
            print('Sending endpoint : ', getUrl)
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.get(getUrl, headers=auth_header, debug = debug)
        if debug: print (resp.content)
        resp.close()
        #print(resp.getStatus())
        return resp.getStatus()[0] == 200
      
    def sensorHasMessageDefinition(self, sensor, debug = False):
        if not sensor or not isinstance(sensor , Sensor):
            raise OSError('\'sensor\' parameter undefined or wrong type!')
            
        if sensor.hasCCINdefinition == False:
            print("performg STREAM check")
            sensor.hasCCINdefinition = self.checkIfMessageDefinitionExists(sensor.getStreamId(), debug)
        else:
            print("stream was checked before !!")
            
        return sensor.hasCCINdefinition

# ------------------------ LoRa ------------------------

class LoRa(Connection):
    """Putting sensor data onto the Enabling platform. USING LoRa"""

    def __init__(self, deviceAddress, applicationKey, networkKey):
        self.deviceAddress = deviceAddress
        self.applicationKey = applicationKey
        self.networkKey = networkKey
        # TODO : complete when access to REAL LoPi device

    def pushSensorData(self, enCoSensor,  debug = False):
        if not enCoSensor or not isinstance(enCoSensor , Sensor):
            raise OSError('\'Sensor\' parameter undefined or wrong type!')
