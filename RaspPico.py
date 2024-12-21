from machine import I2C, Pin
import ssd1306
import uasyncio
from scd4x4 import SCD4X

i2c = I2C(0) 
lcd = ssd1306.SSD1306_I2C(128,64, i2c)
scd4 = SCD4X(i2c)
scd4.start_periodic_measurement()

co2 = 400
temp = 25
hum = 50

async def mesure():
    if scd4.data_ready:
        try:
            global co2, temp, hum
            co2 = round(scd4.co2)
            temp = round(scd4.temperature, 1)
            hum = round(scd4.relative_humidity, 1)
        except:
            pass

async def oled_display(co2,temp,hum):
    #### display the data on the oled
    lcd.fill(0)
    lcd.text("{}".format(co2), 50,20, 1)
    lcd.text("{}C".format(temp), 5, 45, 1)
    lcd.text("{}%".format(hum), 85, 45, 1)
    lcd.show()

async def main():
    while 1:
        uasyncio.create_task(mesure())
        uasyncio.create_task(oled_display(co2,temp,hum))
        await uasyncio.sleep_ms(5100)        
uasyncio.run(main())
