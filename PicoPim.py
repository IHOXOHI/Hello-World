from machine import I2C, Pin, SPI
import uasyncio
from scd4x4 import SCD4X
from ST7735 import TFT
from seriffont import seriffont
from trackball import Trackball

i2c = I2C(0) 
scd41 = SCD4X(i2c)
scd41.start_periodic_measurement()
#scd30.measurement_interval(5)
co2 = 400
temp = 25
hum = 50

trackball = Trackball( i2c )
#trackball.set_rgbw(0, 0, 0, 0)
Luz = "white"
up, down, left, right, switch, state = trackball.read()

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

async def trackball_check(period_ms):
    global up,down,left,right,state
    down, up, right, left, switch, state = trackball.read()
    #up, down, left, right, switch, state = trackball.read()
    #print("r: {:02d} u: {:02d} d: {:02d} l: {:02d} switch: {:03d} state: {}".format(right, up, down, left, switch, state))

async def main():
    while 1:
        uasyncio.create_task(trackball_check(200))
        uasyncio.create_task(mesure())
        uasyncio.create_task(affichage(co2,temp,hum,state))
        uasyncio.create_task(luz(co2,up,down,left,right))
        await uasyncio.sleep_ms(5100)
        
async def luz(co2,up,down,left,right):
    global Luz
    if up >= 10:
        Luz = "on"
    if down >= 10:
        Luz = "off"
        trackball.set_rgbw(0,0,0, 0)
    if left >= 10:
        Luz = "white"
        trackball.set_rgbw(0,0,200, 255)
    if right >= 10:
        Luz = "green"
        trackball.set_rgbw(0,255,0, 0)    
    if Luz == "on":
        if co2 < 400:
            trackball.set_rgbw(255,255,255, 255)

        if co2 >= 400 and co2 < 800:
            a = 255 - round((co2 - 400) / 1.6)
            b = 0
            c = 255
            trackball.set_rgbw(a,b,c, 0)
    
        if co2 >= 800 and co2 < 1200:
            a = 0
            b = round((co2 - 800) / 1.6)
            c = 255
            trackball.set_rgbw(a,b,c, 0)

        if co2 >= 1200 and co2 < 1600:
            a = 0
            b = 255
            c = 255 - round((co2 - 1200) / 1.6)
            trackball.set_rgbw(a,b,c, 0)

        if co2 >= 1600 and co2 < 2000:
            a = round((co2 - 1600) / 1.6)
            b = 255
            c = 0
            trackball.set_rgbw(a,b,c, 0)

        if co2 >= 2000 and co2 < 2400:
            a = 255
            b = 255 - round((co2 - 2000) / 1.6)
            c = 0
            trackball.set_rgbw(a,b,c, 0)

        if co2 >= 2400:
            a = 255
            b = 0
            c = 0
            trackball.set_rgbw(a,b,c, 0)
    if Luz == "off":
        trackball.set_rgbw(0,0,0, 0)
    if Luz == "white":
        trackball.set_rgbw(0,0,200, 255)
    if Luz == "green":
        trackball.set_rgbw(0,255,0, 0)
            
uasyncio.run(main())

