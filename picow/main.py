"""
Raspberry Pi Pico Web Server with Microdot and Distance Sensor Test.
"""
import math
import machine
import urequests
import network_utils
from microdot_asyncio import Microdot
import uasyncio
import time
import uio

trigger = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(15, machine.Pin.IN)
fsuri = "https://firestore.googleapis.com/v1/projects/garagemanage-65b5b/databases/(default)/documents/picos/"

class Properties:

    # コンストラクタを定義
    def __init__(self, hwid, fbkey):

        # メンバ
        self.hwid = hwid
        self.fbkey = fbkey

props = Properties("", "")


async def read_distance():
    trigger.low()
    time.sleep_us(2)
    trigger.high()
    time.sleep_us(10)
    trigger.low()
    while echo.value() == 0:
        signaloff = time.ticks_us()
    while echo.value() == 1:
        signalon = time.ticks_us()
    timepassed = signalon - signaloff
    distance = math.floor((timepassed * 0.0343) / 2 * 1000)
    return distance

def mid(list):
    newList = sorted(list)
    return math.floor((newList[4] + newList[5]) / 2)
    
def md(list):
    max = 0
    for i in list:
        num = list.count(i)
        print(i)
        if num > max:
            max = num
            result = i
    return result

async def get_distance():
    list = []
    for i in range(1, 10):
        list.append(await read_distance())
    return md(list)

async def distance_loop(ip):
    """
    Distance listener loop

    When change distance, send request to http web server.
    """
    print('start distance_loop')
    
    loop_count = 0
    send_count = 0

    current_distance = 0
    while True:
        loop_count += 1
        new_distance = await get_distance()
        print("new distance" , new_distance)
        if abs(current_distance - new_distance) > 100:
            send_count += 1
            current_distance = new_distance
            # Change the URL to your own server, IFTTT, Slack, etc.
            print('distance:', current_distance, 'mm')
            #response = urequests.post(url, headers = {'content-type': 'text/plain'}, data = str(current_distance) )
            #print(response.content)
            #response.close()
        print("loop: ", loop_count, " send: ", send_count)
        await uasyncio.sleep(10)

async def run_web_server():
    """
    Start microdot web server
    https://microdot.readthedocs.io/en/latest/index.html
    """
    app = Microdot()
    led_pin = machine.Pin('LED', machine.Pin.OUT)
    current_distance = 0.0
    @app.get('/')
    async def _index(request):
        return 'Microdot on Raspberry Pi Pico W'

    @app.get('/distance/')
    async def _get_distance():
        return str(current_distance)

    print('microdot run')
    app.run(port=80)

async def main():
    pf = uio.open("properties", "r")
    
    props.hwid = pf.readline()
    props.fbkey = pf.readline()
    pf.close()
    
    wlan = await network_utils.prepare_wifi()
    ip = wlan.ifconfig()[0]
    print('Get Distance: http://{}/distance/'.format(ip))

    uasyncio.create_task(distance_loop(ip))
    await run_web_server()


if __name__ == '__main__':
    uasyncio.run(main())
    
