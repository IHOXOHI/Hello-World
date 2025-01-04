from machine import I2C, Pin, SPI
import uasyncio
from scd4x4 import SCD4X
from ST7735 import TFT
from seriffont import seriffont

i2c = I2C(0) 
scd41 = SCD4X(i2c)
scd41.start_periodic_measurement()
co2 = 400
temp = 25
hum = 50

spi = SPI(0, baudrate=20000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19),miso=Pin(16))
tft=TFT(spi,20,22,17)
tft.initr()
tft.rgb(True)
tft.rotation(1)
lcd = "on"

async def mesure():
    if scd41.data_ready:
        try:
            global co2, temp, hum
            co2 = round(scd41.co2)
            temp = round(scd41.temperature, 1)
            hum = round(scd41.relative_humidity, 1)
        except:
            pass

async def affichage(co2,temp,hum,state):
    #### display the data on the prettty lcd
    global lcd
    if lcd == "on":
        tft.fill(TFT.BLACK)
        tft.text((10, 30), str(co2), TFT.WHITE, seriffont, 5, nowrap=True)
        tft.text((10, 82), str(temp) + "C", TFT.WHITE, seriffont, 2, nowrap=True)
        tft.text((90, 82), str(hum) + "%", TFT.WHITE, seriffont, 2, nowrap=True)
        if state == True:
            lcd = "off"
            tft.on(False)
    else:
        if state == True:
            lcd = "on"
            tft.on()
            tft.fill(TFT.BLACK)
            tft.text((10, 30), str(co2), TFT.WHITE, seriffont, 5, nowrap=True)
            tft.text((10, 82), str(temp) + "C", TFT.WHITE, seriffont, 2, nowrap=True)
            tft.text((90, 82), str(hum) + "%", TFT.WHITE, seriffont, 2, nowrap=True)

async def main():
    while 1:
        uasyncio.create_task(mesure())
        uasyncio.create_task(affichage(co2,temp,hum,state))
        await uasyncio.sleep_ms(5100) 
uasyncio.run(main())

