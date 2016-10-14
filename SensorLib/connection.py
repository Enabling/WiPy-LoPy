import http_client
from utime import time, localtime
import ubinascii
from sensor import Sensor
from m2m_sensor import M2M_Sensor
from json import dumps


class Connection:
    """Base connection class"""
    OVERCC = True  # cloudchannels or SEaaS API

    def pushSensorData(self, enCoSensor,  debug = False):
        raise NotImplementedError("Please Implement this method")

# ------------------------ WiFi ------------------------

class WiFi(Connection):
    """
    Putting sensor data onto the Enabling platform.
    USING WiFi and going through the NEW 'cloudchannel-in' API.
    """
    _baseURL = 'https://api.enco.io'
    
    def __init__(self, userName, apiKey,  apiSecret):
        self.userName = userName    #URL ENCODED !!
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        self.validUntil = None
        self.tokenBearer = None
        self.connectToURLforToken = "{}/token".format(WiFi._baseURL)
        self.connectToURLforSEaaS = "{}/seaas/0.0.1".format(WiFi._baseURL)
        self.connectToURLforCC_In = "{}/platform/cloudchannels/1.0.0".format(WiFi._baseURL)

    @property
    def sendOverCloudchannels(self,  useCC):
        return self.OVERC
        
    @sendOverCloudchannels.setter
    def sendOverCloudchannels(self,  useCC):
        self.OVERCC = useCC
        
    def _getToken(self, debug = False):
        if self.apiKey == None or self.apiSecret == None or self.userName == None :
            raise OSError('Missing authentication info!')
            
        if self.validUntil == None or time() >= self.validUntil:
            basic_auth = ubinascii.b2a_base64("{}:{}".format(self.apiKey, self.apiSecret)).decode('ascii')
            auth_header = {'Authorization':'Basic {}'.format(basic_auth), 'Accept':'application/json'}

            body = 'grant_type=client_credentials&scope=openid'
            if debug: print(self.connectToURLforToken)
            resp = http_client.post(self.connectToURLforToken, headers=auth_header, textMsg=body, contentType='application/x-www-form-urlencoded',  debug = debug)
            resp.raise_for_status()
            resp.content
            if debug:
                print ('Response : ')
                print (resp.content)
            
            authInfo = resp.json()
            self.tokenBearer = authInfo['access_token']
            
            try:
                self.validUntil = time() + authInfo['expires_in']
                localtime(self.validUntil)
            except OverflowError:
                if debug:
                    print("Permanent token, setting to 1 week validity")
                self.validUntil = time() + 7 * 24 * 60 * 60

            resp.close()
            if debug: print ("Token retrieved ! valid until {}".format(localtime(self.validUntil)))
        else:
            if debug: print ("Token still valid !  Re-using it ! {}".format(self.tokenBearer))
                    
    def _createCC_MessagedefinitionPK(self, m2mSensor,  debug = False):
        #POST message definition pk  !!
        #check if exists ??  Doesn't fail if already there, so ....
        postUrl = "{}/cc-in/bymessagedefinitionpk".format(self.connectToURLforCC_In)
        data = {"owner":self.userName,  "name":m2mSensor.getStreamId()}
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        if debug: 
            print('Sending endpoint : ', postUrl)
            print('Payload : ',  data)
        resp = http_client.post(postUrl, headers=auth_header, json=data, debug = debug)
        resp.raise_for_status()
        if debug: print (resp.getStatus())
        httpstatus = resp.getStatus()[0] == 200
        resp.close()
        if not httpstatus:
            print ("### PK : creation FAILED ###")
            return False
        
        print ("### PK : created ###")
        return True

    def _createCC_Messagedefinition(self, m2mSensor, debug = False):
        #PUT the definition
        #check if exists? FAILS if there, but perhaps CC not yet defined -> do check !! or handle exception en continue!
        putUrl = "{}/messagedefinition/latest".format(self.connectToURLforCC_In)
        # BINARY (-> json_schema : null) / JSON
        data = m2mSensor.getStreamDefinitionJSON()
        data["owner"] = self.userName
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        if debug: 
            print('Sending endpoint : ', putUrl)
            print('Payload : ',  data)
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        if debug: print (resp.getStatus())
        httpstatus = resp.getStatus()[0] == 200
        if not httpstatus:
            resp.close()
            print ("### MD : creation FAILED ###")
            return -1
        
        resp.content
        messagedefinition = resp.json()
        versionMD = messagedefinition['version']
        if debug: print (messagedefinition)
        
        print ("### MD : created ###")
        return versionMD

    def _createCCvOld(self, m2mSensor, debug = False):
        #PUT the cloudchannel
        putUrl = "{}/cc/".format(self.connectToURLforCC_In)
        # BINARY / JSON
        data = m2mSensor.getCloudChannelInDefinitionJSON()
        data["owner"] = self.userName
        data["latest_message_definition"]["owner"] = self.userName
        url = m2mSensor.getCloudChannelCustomHTTP()
        urls = []
        urls.append(url)
        data["user_defined_urls"]["HTTP"] = urls
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        if debug: 
            print('Sending endpoint : ', putUrl)
            print('Payload : ',  data)
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        if debug: print (resp.getStatus())
        httpstatus = resp.getStatus()[0] == 200
        resp.close()
        if not httpstatus:
            print ("### CC : creation FAILED ###")
            return False

        print ("### CC : created ###")
        return True
            
    def _createCC(self, m2mSensor, version, debug = False):
        #PUT the cloudchannel
        putUrl = "{}/cc/".format(self.connectToURLforCC_In)
        # BINARY / JSON
        data = m2mSensor.getCloudChannelBaseDefinitionJSON(self.userName, version)
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        if debug: 
            print('Sending endpoint : ', putUrl)
            print('Payload : ',  data)
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        if debug: print (resp.getStatus())
        httpstatus = resp.getStatus()[0] == 200
        resp.close()
        if not httpstatus:
            print ("### CC : creation FAILED ###")
            return False

        print ("### CC : created ###")
        return True
            
                    
    def _createCCInStreamDefinition (self, m2mSensor,  debug = False):
        """
        Creates a cloudchannel with HTTP source and SEaaS sink
        """
        if m2mSensor.getStreamDefinition() == None:
            raise OSError ("Can't create cloudchannel-in stream for given sensor.")
        
        self._getToken(debug)
        
        if not self._createCC_MessagedefinitionPK(m2mSensor, debug):
            return
            
        latestVersion = self._createCC_Messagedefinition(m2mSensor, debug)
        if latestVersion < 0:
            return

        self._createCC(m2mSensor,  latestVersion,  debug)

     
    def pushSensorData(self,  enCoSensor, debug = False,  forceCreateChannel = False):
        if not enCoSensor or not isinstance(enCoSensor , Sensor):
            raise OSError('\'Sensor\' parameter undefined or wrong type!')

        if self.OVERCC:
            self.pushSensorDataCloudChannels(enCoSensor, debug,  forceCreateChannel)
        else:
            self.pushSensorDataSEaaS(enCoSensor, debug)

    def pushSensorDataSEaaS(self, attSensor,  debug = False):
        if not attSensor or not isinstance(attSensor , Sensor):
            raise OSError('\'Sensor\' parameter undefined or wrong type!')
            
        self._getToken(debug)
        if isinstance(attSensor , M2M_Sensor):
            data = attSensor.getData()
            data["containerId"] = attSensor.getContainerId()
            deviceId = attSensor.getContainerId()
        else:
            data = {}
            data["containerId"] = attSensor.getStreamId()
            data["typedMessage"] = {"json_payload": dumps(attSensor.getAsJson())}
            deviceId = attSensor.getStreamId()
            
        data["macAddress"] = attSensor.getDeviceId()
        data["timestamp"] = attSensor.timestamp
        
        putUrl = "{}/device/{}/stream/{}/add".format(self.connectToURLforSEaaS,  attSensor.getDeviceId(), deviceId)
        if debug: 
            print('Sending endpoint : ', putUrl)
            print('Payload : ',  data)
                
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.put(putUrl, headers=auth_header, json=data, debug = debug)
        if debug: print (resp.getStatus())
        resp.raise_for_status()
        resp.close()

        
        
    def pushSensorDataCloudChannels(self, enCoSensor,  debug = False,  forceCreateChannel = False):
        data = enCoSensor.getAsJson()
        self._getToken(debug)
        
        if not self.sensorHasCCDefinition(enCoSensor, debug):
            if debug: print("-- Sensor has NO CC-IN stream definition.")
            self._createCCInStreamDefinition(enCoSensor, debug)
        else:
            if forceCreateChannel:
                self._createCCInStreamDefinition(enCoSensor, debug)
                if debug: print("-- Sensor HAD CC-IN stream definition! BUT RECREATED !!")
            else:
                if debug: print("-- Sensor HAS CC-IN stream definition!")
        
        postUrl = "{}/cc/u/{}".format(self.connectToURLforCC_In, enCoSensor.getCloudChannelCustomHTTP())
        
        if debug: 
            print('Sending endpoint : ', postUrl)
            print('Payload : ',  data)
                
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        
        #TODO : investigate why binary path causes 500 error, send as JSON seems to work ....
        resp = http_client.post(postUrl, headers=auth_header, json=data, debug = debug)

#        if enCoSensor.sendAsBinary() != True:
#            resp = http_client.post(postUrl, headers=auth_header, json=data, debug = debug)
#        else:
#            resp = http_client.post(postUrl, headers=auth_header, binary=data, debug = debug)
            
        if debug: print (resp.getStatus())
        resp.raise_for_status()
        resp.close()

    def getLatestMessageDefinitions(self, debug = False):
        self._getToken(debug)
        getUrl = "{}/messagedefinition/latest".format(self.connectToURLforCC_In)
        if debug: 
            print('Sending endpoint : ', getUrl)
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.get(getUrl, headers=auth_header, debug = debug)
        if debug: print (resp.content)
        resp.raise_for_status()
        result = resp.json()
        resp.close()
        return result
        
    def checkIfMessageDefinitionExists(self, whatName, debug = False):
        self._getToken(debug)
        getUrl = "{}/messagedefinition/latest/{}".format(self.connectToURLforCC_In, whatName)
        if debug: 
            print('Sending endpoint : ', getUrl)
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.get(getUrl, headers=auth_header, debug = debug)
        if debug: print (resp.content)
        resp.close()
        return resp.getStatus()[0] == 200
      
    def sensorHasMessageDefinition(self, sensor, debug = False):
        if not sensor or not isinstance(sensor , Sensor):
            raise OSError('\'sensor\' parameter undefined or wrong type!')
            
        if sensor.hasCCINdefinition == False:
            if debug: 
                print("performg STREAM check")
            sensor.hasCCINdefinition = self.checkIfMessageDefinitionExists(sensor.getStreamId(), debug)
        else:
            if debug: 
                print("stream was checked before !!")
            
        return sensor.hasCCINdefinition
        
    def checkIfCCExists(self, sensor, debug = False):
        self._getToken(debug)
        postUrl = "{}/cc/bycustomendpoint/http".format(self.connectToURLforCC_In)
        data = {"url":'{}_for_{}'.format(sensor.getStreamId(), sensor.getDeviceId())}
        auth_header = {'Authorization':'Bearer {}\r\n'.format(self.tokenBearer), 'Accept':'application/json'}
        resp = http_client.post(postUrl, headers=auth_header,json=data, debug = debug)
        if debug: print (resp.content)
        resp.close()
        
        return resp.getStatus()[0] == 200
        
    def sensorHasCCDefinition(self,  sensor,  debug = False):
        if sensor.hasCCINdefinition == False:
            if debug: 
                print("performg CC check")
            sensor.hasCCINdefinition = self.checkIfCCExists(sensor, debug)
        else:
            if debug: 
                print("CC was checked before !!")

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
