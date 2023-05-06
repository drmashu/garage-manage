"""
Garage-Manage Pico Controller
Raspberry Pi Pico W での距離センサー使用および、Web RPC構築
"""

import gc
import micropython
import math
from machine import Pin, Timer
from microdot_asyncio import Microdot
import uasyncio
import time
import _thread

import network_utils
import firebase

micropython.alloc_emergency_exception_buf(100)

# 超音波センサー 発信
GPIO_HCSR_TRIG = Pin(14, Pin.OUT)
# 超音波センサー 受信
GPIO_HCSR_ECHO = Pin(15, Pin.IN)

# シャッター開 リレー操作
GPIO_RLY_OPEN = Pin(6, Pin.OUT)
# シャッター開 ボタン検知
GPIO_BTN_OPEN = Pin(7, Pin.IN, Pin.PULL_UP)
# シャッター閉 リレー操作
GPIO_RLY_CLOSE = Pin(8, Pin.OUT)
# シャッター閉 ボタン検知
GPIO_BTN_CLOSE = Pin(9, Pin.IN, Pin.PULL_UP)

STT_CLOSED = 0
STT_CLOSE = 1
STT_OPEN = 2
STT_OPENED = 3

shutter_state = 0;

# 照明 リレー操作
GPIO_RLY_LIGHT = Pin(10, Pin.OUT)
# 照明 ボタン検知
GPIO_BTN_LIGHT = Pin(11, Pin.IN, Pin.PULL_DOWN)

# 換気扇 リレー操作
GPIO_RLY_FAN = Pin(12, Pin.OUT)
# 換気扇 ボタン検知
GPIO_BTN_FAN = Pin(13, Pin.IN, Pin.PULL_DOWN)


# 照明 LED
GPIO_LED_LIGHT = Pin(16, Pin.OUT)
# 換気扇 LED
GPIO_LED_FAN = Pin(17, Pin.OUT)

def PushButton(Button):
    print('button on')
    Button.on()
    uasyncio.sleep_ms(500)
    Button.off()

def PushOpenButton(pin):
    PushButton(GPIO_RLY_OPEN)

def PushCloseButton(pin):
    PushButton(GPIO_RLY_CLOSE)

BTN_LIGHT = 0
BTN_FAN = 1
toggle = [0, 0]
button = [GPIO_RLY_LIGHT, GPIO_RLY_FAN]

PICO_ID = ""

def SwButton(pin):
    print('Pin {0} {1}'.format(pin, 'on' if toggle[pin] == 1 else 'off'))
    button[pin].value(toggle[pin])

def ToggleButton(pin):
    toggle[pin] = 1 if toggle[pin] == 0 else 0 
    SwButton(pin)

def PushLightButton(pin):
    ToggleButton(BTN_LIGHT)

def PushFanButton(pin):
    ToggleButton(BTN_FAN)

GPIO_BTN_OPEN.irq(trigger=Pin.IRQ_RISING,  handler=PushOpenButton)
GPIO_BTN_CLOSE.irq(trigger=Pin.IRQ_RISING,  handler=PushCloseButton)

GPIO_BTN_LIGHT.irq(trigger=Pin.IRQ_RISING,  handler=PushLightButton)
GPIO_BTN_FAN.irq(trigger=Pin.IRQ_RISING,  handler=PushFanButton)

"""
距離計測
"""
async def read_distance():
    GPIO_HCSR_TRIG.low()
    time.sleep_us(2)
    GPIO_HCSR_TRIG.high()
    time.sleep_us(10)
    GPIO_HCSR_TRIG.low()
    while GPIO_HCSR_ECHO.value() == 0:
        signaloff = time.ticks_us()
    while GPIO_HCSR_ECHO.value() == 1:
        signalon = time.ticks_us()
    timepassed = signalon - signaloff
    distance = math.floor((timepassed * 0.0343) / 2 * 10)
    return distance

"""
中央値取得
"""
def mid(list):
    newList = sorted(list)
    return math.floor((newList[4] + newList[5]) / 2)

"""
距離取得
"""
async def get_distance():
    list = []
    for i in range(1, 10):
        list.append(await read_distance())
    return mid(list)

current_distance = 0

def getDistance(timer):
    global current_distance
    new_distance = await get_distance()
    print("new distance" , new_distance)
    if abs(current_distance - new_distance) > 100:
        current_distance = new_distance
        print('distance:', current_distance, 'mm')
        #response = firebase.CallFunction('pico',
        #                                 {'picoId': PICO_ID,
        #                                  'shutter': current_distance,
        #                                  'light': toggle[BTN_LIGHT],
        #                                  'fan': toggle[BTN_FAN]})
        #print(response.content)
        #response.close()
    
#distanceTimer = Timer()
#distanceTimer.init(mode=Timer.PERIODIC, period=10000, callback=getDistance)

"""
距離計測ループ
"""
async def distance_loop():
    print('start distance_loop')
    
    global PICO_ID
    loop_count = 0
    send_count = 0
    auth = False

    current_distance = 0
    while True:
        loop_count += 1
        if auth:
            new_distance = await get_distance()
            print("new distance" , new_distance)
            if abs(current_distance - new_distance) > 100:
                send_count += 1
                current_distance = new_distance
                # Change the URL to your own server, IFTTT, Slack, etc.
                print('distance:', current_distance, 'mm')
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
            
        print("loop: ", loop_count, " send: ", send_count)
        await uasyncio.sleep(10)

"""
外部からのスイッチ操作処理
"""
def SwitchButton(pin, sw):
    toggle[pin] = 1 if sw == 'on' else 0
    SwButton(pin)

"""
Webサーバ起動
"""
async def run_web_server():
    app = Microdot()
    led_pin = Pin('LED', Pin.OUT)
    current_distance = 0.0
    @app.get('/')
    async def _index(request):
        return 'Microdot on Raspberry Pi Pico W'

    @app.get('/light/<sw>')
    async def _switch_light(request, sw):
        SwitchButton(BTN_LIGHT, sw)
        return str('OK')

    @app.get('/fan/<sw>')
    async def _switch_fan(request, sw):
        SwitchButton(BTN_FAN, sw)
        return str('OK')

    @app.get('/shutter/<sw>')
    async def _switch_shutter(request, sw):
        if sw == 'open':
            PushOpenButton(0)
        else:
            PushCloseButton(0)
        return str('OK')

    print('microdot run')
    app.run(port=80)

async def main():
    global PICO_ID
    wlan = await network_utils.prepare_wifi()
    mac = wlan.config('mac')
    PICO_ID = '{:012x}'.format(int.from_bytes(mac, 'big'))
    print('mac addr: {}'.format(PICO_ID))
    ip = wlan.ifconfig()[0]
    print('Get Distance: http://{}/light/on'.format(ip))

    print(gc.mem_free())
    firebase.Authenticate();
    
    uasyncio.create_task(distance_loop())

    await run_web_server()


if __name__ == '__main__':
    uasyncio.run(main())
    
