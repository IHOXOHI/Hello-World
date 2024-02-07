from machine import I2C, Pin, SPI
from scd4x4 import SCD4X
from ST7735 import TFT
from seriffont import seriffont
from trackball import Trackball
import uasyncio

modi = "impressa"
ref = 400

i2c = I2C(0) 
scd41 = SCD4X(i2c)
scd41.start_periodic_measurement()
co2 = 400
temp = 25
hum = 50

trackball = Trackball( i2c )
trackball.set_rgbw(0, 0, 255, 0)

#up, down, left, right, switch, state = trackball.read()
down,up,right,left,switch,state = trackball.read()
spi = SPI(0, baudrate=20000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(19),miso=Pin(16))
tft=TFT(spi,20,22,17)
tft.initr()
tft.rgb(True)
tft.rotation(1)

async def trackball_check(period_ms):
    global up,down,left,right,state
    down,up,right,left,switch,state = trackball.read()
    print("r: {:02d} u: {:02d} d: {:02d} l: {:02d} switch: {:03d} state: {}".format(right, up, down, left, switch, state))

async def impressa():
    tft.fill(TFT.BLACK)
    tft.text((5, 40), "Up-FactoryR", TFT.WHITE, seriffont, 2, nowrap=True)
    tft.text((5, 80), "Down-Calib", TFT.WHITE, seriffont, 2, nowrap=True)
    
    global up, down
    if up >= 10:
        try:
            scd41.stop_periodic_measurement()
            await uasyncio.sleep_ms(500)
            scd41.factory_reset()
            await uasyncio.sleep_ms(1200)
            tft.fill(TFT.BLACK)
            tft.text((10, 40), "Done", TFT.WHITE, seriffont, 2, nowrap=True)
            tft.text((10, 80), "Reset Now", TFT.WHITE, seriffont, 2, nowrap=True)
            await uasyncio.sleep_ms(10000)
        except:
            pass
    if down >= 10:
        global modi
        modi = "recalib"

async def recalib(period_ms):
    tft.fill(TFT.BLACK)
    tft.text((10, 40), "Left Forced", TFT.WHITE, seriffont, 2, nowrap=True)
    tft.text((10, 80), "Right Auto", TFT.WHITE, seriffont, 2, nowrap=True)                  
    global left, right
    if left >= 10:
        global modi
        modi = "mesure"
    if right >= 10:
        global modi
        modi = "recalib_auto"

async def mesure():
    for i in range(40):
        if scd41.data_ready:
            try:
                global co2, temp, hum
                co2 = round(scd41.co2)
                tft.fill(TFT.BLACK)
                tft.text((10, 40), str(co2), TFT.WHITE, seriffont, 2, nowrap=True)
                tft.text((10, 62), "Wait heat", TFT.WHITE, seriffont, 2, nowrap=True)
                tft.text((10, 88), "the sensor", TFT.WHITE, seriffont, 2, nowrap=True)
            except:
                pass
        await uasyncio.sleep_ms(5500)
    global modi
    modi = "recalib_forced"

async def recalib_forced():
    try:      
        global ref, up, down, state
        tft.fill(TFT.BLACK)
        tft.text((10, 40), str(ref), TFT.WHITE, seriffont, 2, nowrap=True)
        tft.text((10, 62), "Up Down ref", TFT.WHITE, seriffont, 2, nowrap=True)
        tft.text((10, 88), "press Save", TFT.WHITE, seriffont, 2, nowrap=True)                
        if state == True:   
            scd41.stop_periodic_measurement()
            await uasyncio.sleep_ms(500)
            scd41.forced_recalibration(ref)
            tft.fill(TFT.BLACK)
            tft.text((10, 40), "Done", TFT.WHITE, seriffont, 2, nowrap=True)
            tft.text((10, 72), "Reset Now", TFT.WHITE, seriffont, 2, nowrap=True)
            await uasyncio.sleep_ms(10000)
        if down >= 10:  
            ref -= 10
        if up >= 10:
            ref += 10
    except:
        pass
    await uasyncio.sleep_ms(1000)

async def recalib_auto():
    try:
        scd41.stop_periodic_measurement()
        await uasyncio.sleep_ms(1000)
        mode = scd41.get_autocalibration()
        tft.fill(TFT.BLACK)
        texti = "Mode: " + str(mode)
        print(texti) 
        tft.text((10, 40), texti, TFT.WHITE, seriffont, 2, nowrap=True)
        tft.text((10, 62), "Up ON", TFT.WHITE, seriffont, 2, nowrap=True)
        tft.text((10, 88), "Down OFF", TFT.WHITE, seriffont, 2, nowrap=True)
        await uasyncio.sleep_ms(10000)
        global up, down
        if up >= 10:
            scd41.set_autocalibration(1)
            await uasyncio.sleep_ms(1000)
            scd41.persist_settings()
            tft.fill(TFT.BLACK)
            tft.text((10, 40), "Auto Active", TFT.WHITE, seriffont, 2, nowrap=True)
            tft.text((10, 72), "Reset Now", TFT.WHITE, seriffont, 2, nowrap=True)
            await uasyncio.sleep_ms(10000)
        if down >= 10:
            scd41.set_autocalibration(0)
            await uasyncio.sleep_ms(1000)
            scd41.persist_settings()
            tft.fill(TFT.BLACK)
            tft.text((10, 40), "Auto OFF", TFT.WHITE, seriffont, 2, nowrap=True)
            tft.text((10, 72), "Reset Now", TFT.WHITE, seriffont, 2, nowrap=True)
            await uasyncio.sleep_ms(10000)
    except:
        pass
    await uasyncio.sleep_ms(1000)
    
async def main():
    while 1:
        uasyncio.create_task(trackball_check(200))
        if modi == "impressa":
            uasyncio.create_task(impressa())
        if modi == "recalib":
            uasyncio.create_task(recalib(1000))
        if modi == "mesure":
            uasyncio.create_task(mesure())
        if modi == "recalib_forced":
            uasyncio.create_task(recalib_forced())
        if modi == "recalib_auto":
            uasyncio.create_task(recalib_auto())
            
        await uasyncio.sleep_ms(1000)
        
uasyncio.run(main())

