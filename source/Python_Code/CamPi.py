import picamera
import io
import logging
import socketserver
import threading
from threading import Condition
from http import server
from gpiozero import Button, LED
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
import os
import sys

PAGE="""\
<html>
<head>
<title>Raspberry Pi - Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Camera</h1></center>
<center><img src="stream.mjpeg" width="1296" height="730"></center>
</body>
</html>
"""

#pigpio.pi('192.168.1.16',8888)

x = 0
mnt = True
cmd = "sudo umount /dev/sda1"
cmd2 = "sudo mount /dev/sda1 /mnt/images"
hostname = '192.168.4.2'
#response = os.system("ping -c 1 " + hostname)

while x == 0:
    response = os.system("ping -c 1 " + hostname)
    if response == 0:
        factory = PiGPIOFactory(host=hostname)
        button = Button(2,pin_factory=factory)
        button2 = Button(3, pin_factory=factory)
        led = LED(11, pin_factory=factory)
        led2 = LED(12, pin_factory=factory)
        led.on()
        os.system(cmd2)
        led2.on()
        x = 1
        #print("Connected")
    else:
        #print("connecting...")
        sleep(10)

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self,buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpeg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                        'Removed streaming client %s: %s',
                        self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='1296x730', framerate=30) as camera:
    i = 0
    address = ('', 8080)
    server = StreamingServer(('',8080), StreamingHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        server_thread.start()
        while True:
            if button2.is_pressed:
                if mnt == True:
                    os.system(cmd)
                    led2.off()
                    mnt = False
                    print("usb drive is safe to remove")
                else:
                    os.system(cmd2)
                    led2.on()
                    mnt = True
                    print("usb drive is mounted")
            if button.is_pressed:
                camera.stop_recording()
                #camera.wait_recording(10)
                camera.capture('/mnt/images/img' + str(i) + '.jpg',format=None, use_video_port=True,resize=(1920,1080), splitter_port=2)
                i = i + 1
                sleep(3)
                camera.start_recording(output,format='mjpeg')
                sleep(2)
                print("Picture Captured")
    finally:
        camera.stop_recording()


