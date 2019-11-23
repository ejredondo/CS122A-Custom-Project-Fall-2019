import subprocess
from gpiozero import LED, Button
from gpiozero.pins.pigpio import PiGPIOFactory
from signal import pause


for ping in range(1,3):
    address = '192.168.4.' + str(ping)
    res = subprocess.call(['ping','-c','3',address])
    if address == '192.168.4.2':
        continue
    elif res == 0:
        print(address," is connected")
        factory = PiGPIOFactory(host=address)
        led = LED(17, pin_factory = factory)
    elif res == 2:
        print("no response from", address)
    else:
        print("ping to", address, "failed")

#factory = PiGPIOFactory(host='192.168.4.1')

button = Button(3)
#led = LED(17, pin_factory=factory)

led.source = button

pause()
