from machine import I2C
from scd4x4 import SCD4X
from time import sleep_ms


i2c = I2C(0) 
scd41 = SCD4X(i2c)
#scd41.start_periodic_measurement()

scd41.stop_periodic_measurement()
sleep_ms(500)
#scd41.forced_recalibration(550)
#if scd41.data_ready:
etat = scd41.get_autocalibration()
print(etat)
#else:
 #   print("do it again")
sleep_ms(1000)

