from machine import I2C, Pin
import ssd1306
import uasyncio
from scd30 import SCD30
import neop as np

#button for change led brightness
p = Pin(19, Pin.IN, Pin.PULL_UP)

#i2c for oled display and scd sensor
i2c = I2C(0) 

lcd = ssd1306.SSD1306_I2C(128,32, i2c)
scd30 = SCD30(i2c, 0x61)

##globals data
co2 = 400
temp = 25
hum = 50

async def brightness_up():
    ### for change brightness (refer to my lib neop.py ; you have to add this function in the ws2812 lib; lib which is use for neopixel with the rp2; that I have rename neop;the func to add in the lib:
 #   def brightness_up():
  #      global brightness
   #     brightness += 0.1
    #    if brightness > 1:
     #       brightness = 0
        
    if p.value() == 0:
        np.brightness_up()

async def mesure(event):
    ###scd mesure
    while scd30.get_status_ready() != 1:
        #time.sleep_ms(200)
        await uasyncio.sleep_ms(200)
    try:
        data = scd30.read_measurement()
        print(data)
        global co2
        global temp
        global hum
        co2 = round(data[0])
        co2 = co2 - 200
        temp = round(data[1],1)
        temp = temp - 2.5
        hum = round(data[2])
        hum = hum
    except:
        print("no news data")

    await event.wait()
    event.clear()

async def affichage(co2,temp,hum):
    #### display the data on the oled
    lcd.fill(0)
    lcd.text("CO2:{} ppm".format(co2), 20,0, 1)
    lcd.text("T:{}C   H:{}%".format(temp,hum), 0, 25, 1)
    lcd.show()

    ### color of led depending of co2 concentration
    if co2 < 400:
        a = 255
        b = 400 - co2
        c = 255
        np.pixels_fill([a,b,c])
        np.pixels_show()

    if co2 >= 400 and co2 < 800:
        a = 255 - round((co2 - 400) / 1.6)## to have a number between 255 and 0
        b = 0
        c = 255
        np.pixels_fill([a,b,c])
        np.pixels_show()
    
    if co2 >= 800 and co2 < 1200:
        a = 0
        b = round((co2 - 800) / 1.6)
        c = 255
        np.pixels_fill([a,b,c])
        np.pixels_show()

    if co2 >= 1200 and co2 < 1600:
        a = 0
        b = 255
        c = 255 - round((co2 - 1200) / 1.6)
        np.pixels_fill([a,b,c])
        np.pixels_show()

    if co2 >= 1600 and co2 < 2000:
        a = round((co2 - 1600) / 1.6)
        b = 255
        c = 0
        np.pixels_fill([a,b,c])
        np.pixels_show()

    if co2 >= 2000 and co2 < 2400:
        a = 255
        b = 255 - round((co2 - 2000) / 1.6)
        c = 0
        np.pixels_fill([a,b,c])
        np.pixels_show()

    if co2 >= 2400:
        a = 255
        b = 0
        c = 0
        np.pixels_fill([a,b,c])
        np.pixels_show()
     
async def main():
    while 1:
        uasyncio.create_task(brightness_up())
        event = uasyncio.Event()
        uasyncio.create_task(mesure(event))
        event.set()
        uasyncio.create_task(affichage(co2,temp,hum))
        await uasyncio.sleep_ms(2200)
         
uasyncio.run(main())

