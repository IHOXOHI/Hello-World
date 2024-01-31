import time
from micropython import const
import struct

class SCD4X:
    """
    Based on https://github.com/adafruit/Adafruit_CircuitPython_SCD4X
    Copyright (c) 2021 ladyada for Adafruit Industries
    MIT License

     &&

     Code by Tutaka Kato: https://github.com/mikan/rpi-pico-scd4x
     &&IHOXOHI just add severals functions:
     Arthung!!!!Ther is an os error whixh happen with the set_command.. but the command pass... A 'try' jump upside this error... I will appreciate a better form if someone could post...
    """

    DEFAULT_ADDRESS = 0x62
    DATA_READY = const(0xE4B8)
    STOP_PERIODIC_MEASUREMENT = const(0x3F86)
    START_PERIODIC_MEASUREMENT = const(0x21B1)
    READ_MEASUREMENT = const(0xEC05)
    SCD4X_FACTORYRESET = const(0x3632)
    FORCED_RECAL = const(0x362F)
    SCD4X_GETASCE = const(0x2313)
    SCD4X_SETASCE = const(0x2416)
    SCD4X_PERSISTSETTINGS = const(0x3615)
    SCD4X_GETTEMPOFFSET = const(0x2318)
    SCD4X_SETTEMPOFFSET = const(0x241D)

    def __init__(self, i2c_bus, address=DEFAULT_ADDRESS):
        self.i2c = i2c_bus
        self.address = address
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)

        # cached readings
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

        self.stop_periodic_measurement()

    @property
    def co2(self):
        """Returns the CO2 concentration in PPM (parts per million)
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._co2

    @property
    def temperature(self):
        """Returns the current temperature in degrees Celsius
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._temperature

    @property
    def relative_humidity(self):
        """Returns the current relative humidity in %rH.
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._relative_humidity

    def _read_data(self):
        """Reads the temp/hum/co2 from the sensor and caches it"""
        self._send_command(self.READ_MEASUREMENT, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 2 ** 16)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 2 ** 16)

    @property
    def data_ready(self):
        """Check the sensor to see if new data is available"""
        self._send_command(self.DATA_READY, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x03 == 0) and (self._buffer[1] == 0))

    def stop_periodic_measurement(self):
        """Stop measurement mode"""
        self._send_command(self.STOP_PERIODIC_MEASUREMENT, cmd_delay=0.5)

    def start_periodic_measurement(self):
        """Put sensor into working mode, about 5s per measurement"""
        self._send_command(self.START_PERIODIC_MEASUREMENT, cmd_delay=0.01)

    def _send_command(self, cmd, cmd_delay=0.0):
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF
        self.i2c.writeto(self.address, self._cmd)
        time.sleep(cmd_delay)

    def _read_reply(self, buff, num):
        self.i2c.readfrom_into(self.address, buff, num)
        self._check_buffer_crc(self._buffer[0:num])

    def _check_buffer_crc(self, buf):
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC check failed while reading data")
        return True

    def forced_recalibration(self, co2_ref: int):
        "force the sensor to recalibrate"
        self.stop_periodic_measurement()
        self.set_command_value(FORCED_RECAL, co2_ref)
        time.sleep(0.5)
        self.read_reply(self._buffer)
        correction = struct.unpack_from(">h", self._buffer[0:2])[0]
        if correction == 0xFFFF:
            raise RuntimeError("forced recalibration failed.\
            Make sure sensor is active for 3 minutes")
            
    def set_command_value(self, cmd, value, cmd_delay=0):
        self._buffer[0] = (cmd >> 8) & 0xFF
        self._buffer[1] = cmd & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        try:
            self.i2c.writeto(self.address, self._buffer)
        except:
            pass
        #self.i2c.writeto(self.address, self._buffer, stop=True)
        #i2c.write(self._buffer, end=5)
        #i2c.write(self._buffer)
        time.sleep(cmd_delay)

        
    def factory_reset(self):
        """Resets all configuration settings stored in the EEPROM and erases the
        FRC and ASC algorithm history."""
        self.stop_periodic_measurement()
        self._send_command(SCD4X_FACTORYRESET, cmd_delay=1.2)
        
    def read_reply(self,buff):
        self.i2c.readfrom_into(self.address,buff)
        
    def get_autocalibration(self):
        self._send_command(SCD4X_GETASCE, cmd_delay=0.001)
        self._read_reply(self._buffer,3)   
        return self._buffer[1] == 1

    def set_autocalibration(self, enabled:bool):
        self.set_command_value(SCD4X_SETASCE, enabled)
        
    def persist_settings(self):
        """Save temperature offset, altitude offset, and selfcal enable settings to EEPROM"""
        self._send_command(SCD4X_PERSISTSETTINGS, cmd_delay=0.8)
        
    def get_temperature_offset(self):
        """Specifies the offset to be added to the reported measurements to account for a bias in
        the measured signal. Value is in degrees Celsius with a resolution of 0.01 degrees and a
        maximum value of 20 C

        .. note::
            This value will NOT be saved and will be reset on boot unless saved with
            persist_settings().

        """
        self._send_command(SCD4X_GETTEMPOFFSET, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        temp = (self._buffer[0] << 8) | self._buffer[1]
        return 175.0 * temp / 2**16
        
    def set_temperature_offset(self, offset:float):
        if (offset > 20) or (offset < 0):
            raise AttributeError(
                "Offset value must be positive and less than or equal to 20 degrees Celsius"
            )
        temp = int(offset * 2**16 / 175)
        self.set_command_value(SCD4X_SETTEMPOFFSET, temp,cmd_delay=0.001)

    @staticmethod
    def _crc8(buffer):
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
