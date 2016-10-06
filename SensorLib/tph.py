from machine import I2C
from struct import unpack
from utime import ticks_diff,  ticks_ms,  sleep_ms

class TPH():
    
    _bmp_180_addr = 0x77
    _sht_21_addr = 0x40

    def __init__(self, pinsI2C = ('GP24', 'GP23'),  debug = False):
        self._debugging = debug
        self._i2c = I2C(0, I2C.MASTER, pins=pinsI2C)
#        self.chip_id = unpack('b', self._i2c.readfrom_mem(self._bmp_180_addr, 0xD0, 1))[0]
#        self.chip_version = unpack('b', self._i2c.readfrom_mem(self._bmp_180_addr, 0xD1, 1))[0]
#        if debug:
#            print ("ID : {} / Ver : {}".format(self.chip_id,  self.chip_version))

        self._readCalibrationData()
        self._sht21SoftReset()
        
        # settings to be adjusted by user
        self.oversample_setting = 3
        self.read_delay_temp = 5
        self.read_delay_press = (5, 8, 14, 25)
        self.read_delay_sht21_temp = 85
        self.read_delay_sht21_humidity = 30
        
        self.baseline = 101325

        self._PARAM_MG = 3038
        self._PARAM_MH = -7357
        self._PARAM_MI = 3791
       
        
    @property
    def oversample_sett(self):
        return self.oversample_setting

    @oversample_sett.setter
    def oversample_sett(self, value):
        if value in range(4):
            self.oversample_setting = value
        else:
            print('oversample_sett can only be 0, 1, 2 or 3, using 3 instead')
            self.oversample_setting = 3
            
    def _readCalibrationData(self):
        # read calibration data from EEPROM
        # read in 1 go ....
        self._AC1 = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xAA, 2))[0]
        self._AC2 = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xAC, 2))[0]
        self._AC3 = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xAE, 2))[0]
        self._AC4 = unpack('>H', self._i2c.readfrom_mem(self._bmp_180_addr, 0xB0, 2))[0]
        self._AC5 = unpack('>H', self._i2c.readfrom_mem(self._bmp_180_addr, 0xB2, 2))[0]
        self._AC6 = unpack('>H', self._i2c.readfrom_mem(self._bmp_180_addr, 0xB4, 2))[0]
        self._B1 = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xB6, 2))[0]
        self._B2 = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xB8, 2))[0]
        self._MB = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xBA, 2))[0]
        self._MC = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xBC, 2))[0]
        self._MD = unpack('>h', self._i2c.readfrom_mem(self._bmp_180_addr, 0xBE, 2))[0]
        
        if self._debugging:
            print("calibration : AC1 = {}".format(self._AC1))
            print("calibration : AC2 = {}".format(self._AC2))
            print("calibration : AC3 = {}".format(self._AC3))
            print("calibration : AC4 = {}".format(self._AC4))
            print("calibration : AC5 = {}".format(self._AC5))
            print("calibration : AC6 = {}".format(self._AC6))
            print("calibration :  B1 = {}".format(self._B1))
            print("calibration :  B2 = {}".format(self._B2))
            print("calibration :  MB = {}".format(self._MB))
            print("calibration :  MC = {}".format(self._MC))
            print("calibration :  MD = {}".format(self._MD))
            
    def _sht21SoftReset(self):
        self._i2c.writeto(self._sht_21_addr , 0xFE)
        sleep_ms(50)
        

    def _getUncompensatedTemperature(self):
        self._i2c.writeto_mem(self._bmp_180_addr, 0xF4, 0x2E)
        
        t_start = ticks_ms()
        while ticks_diff(t_start, ticks_ms()) <= self.read_delay_temp:
            pass
        
        try:
            UT_raw = self._i2c.readfrom_mem(self._bmp_180_addr, 0xF6, 2)
            v_ut_u16 = unpack('>h', UT_raw)[0]
        except:
            return None
            
        if self._debugging:
            print ("Uncompensated temp : {}".format(v_ut_u16))
        
        return v_ut_u16

    def getTemperature(self):
        '''
        In 0.1 °C
        from BMP180 module
        Absolute 0 as error??
        '''
        temp_uncompensated = self._getUncompensatedTemperature()
        if temp_uncompensated is None:
            return None

        x1 = ((temp_uncompensated - self._AC6) * self._AC5) >> 15
        if x1 == 0 and self._MD == 0:
            return None
        
        x2 = (self._MC << 11) // (x1 + self._MD)
        self._B5 = x1 + x2
        temperature = (self._B5 + 8) >> 4
        
        return temperature

    def _getUncompensatedPressure(self):
        self._i2c.writeto_mem(self._bmp_180_addr, 0xF4, 0x34 + (self.oversample_setting << 6))
        
        t_start = ticks_ms()
        while ticks_diff(t_start, ticks_ms()) <= self.read_delay_press[self.oversample_setting]:
            pass
        
        try:
            MSB = self._i2c.readfrom_mem(self._bmp_180_addr, 0xF6, 1)
            LSB = self._i2c.readfrom_mem(self._bmp_180_addr, 0xF7, 1)
            LLSB = self._i2c.readfrom_mem(self._bmp_180_addr, 0xF8, 1)

            _msb = unpack('<h',MSB )[0]
            _mesb = unpack('<h',LSB )[0]
            _lsb = unpack('<h',LLSB )[0]

            v_up_u32 = ((_msb << 16) + (_mesb << 8) + _lsb) >> (8 - self.oversample_setting)
        except:
            return None

        if self._debugging:
            print ("Uncompensated pressure : {} @ {} times oversampling".format(v_up_u32, self.oversample_setting))
        
        return v_up_u32

    def getPressure(self):
        '''
        In Pa
        '''
        press_uncompensated = self._getUncompensatedPressure()
        if press_uncompensated is None:
            return None
        
        if self.getTemperature() is None:
            return None
            
        B6 = self._B5 - 4000
        if self._debugging:
            print("B6 : {}".format(B6))

        # ***** calculate B3 ************
        X1 = (self._B2*((B6**2) >> 12)) >> 11
        X2 = (self._AC2 * B6) >> 11
        X3 = X1 + X2
        B3 = ((int((self._AC1 * 4) + X3) << self.oversample_setting) + 2) >> 2
        if self._debugging:
            print("B3 : {}".format(B3))
        
        # ***** calculate B4 ************
        X1 = (self._AC3 * B6) >> 13
        X2 = (self._B1 * ((B6**2) >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (abs(self._AC4) * (X3 + 32768)) >> 15
        if self._debugging:
            print("B4 : {}".format(B4))
        if B4 == 0:
            return None
        B7 = (abs(press_uncompensated) - B3) * (50000 >> self.oversample_setting)
        if self._debugging:
            print("B7 : {}".format(B7))
        if B7 < 0x80000000:
            v_pressure_s32 = (B7 << 1) // B4
        else:
            v_pressure_s32 = (B7 // B4) << 1

        X1 = (((v_pressure_s32 >> 8) << 1) * self._PARAM_MG) >> 16
        X2 = (v_pressure_s32  * self._PARAM_MH) >> 16
        
        v_pressure_s32 += (X1 + X2 + self._PARAM_MI) >> 4
        return v_pressure_s32
    
    def getRelativeHumidity(self):
        """This function reads the first two bytes of data and returns
        the relative humidity in percent by using the following function:
        RH = -6 + (125 * (SRH / 2 ^16))
        where SRH is the value read from the sensor
        """        
        self._i2c.writeto(self._sht_21_addr, 0xF5)
        t_start = ticks_ms()
        while ticks_diff(t_start, ticks_ms()) <= self.read_delay_sht21_humidity:
            pass
        
        data = bytearray(2)
        self._i2c.readfrom_into(self._sht_21_addr, data)

        unadjusted = unpack('>h', data)[0]
        
        unadjusted &= 0xFFFC
        unadjusted *= 100
        unadjusted *= 12500
        unadjusted //= ((1 << 16) * 100)
        unadjusted -= 600
        return unadjusted
        
#    def _tempFromSHT21(self):
#        """This function reads the first two bytes of data and
#        returns the temperature in 0.01 °C by using the following function:
#        T = -46.82 + (175.72 * (ST/2^16))
#        where ST is the value from the sensor
#        """
#        self._i2c.writeto(self._sht_21_addr, 0xF3)
#        t_start = ticks_ms()
#        while ticks_diff(t_start, ticks_ms()) <= self.read_delay_sht21_temp:
#            pass
#        
#        data = bytearray(2)
#        self._i2c.readfrom_into(self._sht_21_addr, data)
#
#        unadjusted = unpack('>h', data)[0]
#        
#        unadjusted &= 0xFFFC
#        unadjusted *= 100
#        unadjusted *= 17572
#        unadjusted //= ((1 << 16) * 100)
#        unadjusted -= 4685
#        return unadjusted
    
#    def display(self):
#        t = self.getTemperature()
#        p = self.getPressure()
#        t2 = self._tempFromSHT21()
#        h = self.getRelativeHumidity()
#        
#        
#        tW = t // 10
#        tF = t % 10
#        pW = p // 100
#        pF = p % 100
#        t2W = t2 // 100
#        t2F = t2 % 100
#        hW = h // 100
#        hF = h % 100
#        print ("#BMP180# Temperature = {},{}0 C, pressure = {},{:02d} hPa".format(tW, tF, pW, pF))
#        print ("#SHT21#  Temperature = {},{:02d} C, humidity = {},{:02d} %".format(t2W, t2F, hW, hF))
