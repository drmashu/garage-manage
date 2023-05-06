"""
Garage-Manage Pico Controller
Raspberry Pi Pico W での距離センサー使用および、Web RPC構築
"""
import gc
import micropython
from machine import Pin
import uasyncio

from microdot_asyncio import Microdot

import network_utils
import firebase

micropython.alloc_emergency_exception_buf(100)

"""
Webサーバ起動
"""
async def run_web_server():
    app = Microdot()
    led_pin = Pin('LED', Pin.OUT)
    current_distance = 0.0

    @app.get('/on')
    async def _index(request):
        led_pin.on();
        return 'Microdot on Raspberry Pi Pico W'

    @app.get('/off')
    async def _index(request):
        led_pin.off();
        return 'Microdot on Raspberry Pi Pico W'

    print('microdot run')
    app.run(port=80)

PICO_ID = ''

async def distance_loop():
    global PICO_ID
    count = 0
    auth = False
    while True:
        
        if auth and count < 10:
            count = count + 1
            response = firebase.CallFunction('pico',
                                             {'picoId': PICO_ID,
                                              'shutter': 0,
                                              'light': 0,
                                              'fan': 0})
            if response == None:
                print('None')
            else:
                print(response.contents)
                response.close()
        else:
            auth = firebase.Authenticate();
        
        
        print("loop: ", count, "expire : ", firebase.ExpiresIn )
        await uasyncio.sleep(10)
        
async def main():
    global PICO_ID
    wlan = await network_utils.prepare_wifi()
    mac = wlan.config('mac')
    PICO_ID = '{:012x}'.format(int.from_bytes(mac, 'big'))
    print('mac addr: {}'.format(PICO_ID))
    ip = wlan.ifconfig()[0]
    print('Get Distance: http://{}/light/on'.format(ip))

    uasyncio.create_task(distance_loop())

    await run_web_server()
    print(gc.mem_free())
    

if __name__ == '__main__':
    uasyncio.run(main())
    
