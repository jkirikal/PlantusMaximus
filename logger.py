import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import time
from picamera import PiCamera
from picamera import Color
import os

import sqlite3
import datetime

import RPi.GPIO as GPIO
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
GPIO.output(21, True) #pump esialgu kinni

camera = PiCamera()
camera.iso = 100
camera.saturation = 20
camera.annotate_foreground = Color('black')

class Logger:
    def __init__(self):
        self.data_dict = []
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(board.D5)
        mcp = MCP.MCP3008(spi, cs)
        self.channel1 = AnalogIn(mcp, MCP.P0)
        self.channel2 = AnalogIn(mcp, MCP.P1)
        self.trig = 23
        self.echo = 24
        GPIO.setup(self.trig, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)


    def collect_data(self):

        ''' Collects information about water level inn tank '''

        GPIO.output(self.trig, False)
        time.sleep(2)
        GPIO.output(self.trig, True)
        time.sleep(0.0001)
        GPIO.output(self.trig, False)
        while GPIO.input(self.echo)==0:
            pulse_start = time.time()
        while GPIO.input(self.echo)==1:
            pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)
        asd = 25.96 - distance
        veekogus = 59 * 5 * asd
        veekogus1 = round(veekogus * 0.001, 2)

        ''' Collects information about soil humidity '''

        low = 26304
        high = 60600
        vana = high - low
        uus1 = 100 - (((self.channel1.value - low) * 100) / vana)
        uus2 = 100 - (((self.channel2.value - low) * 100) / vana)
        print('esimene andur : ' + str(self.channel1.value))
        print('teine andur : ' + str(self.channel2.value))

        ''' adds information to data '''

        now = datetime.datetime.now()
        date = now.strftime("%d:%m:%H")
        self.totniisk = round((uus1 + uus2) / 2, 2)
        self.data_dict.append(date)
        self.data_dict.append(float(self.totniisk))
        self.data_dict.append(float(veekogus1))
        if self.totniisk < 90.0: #kriitiline niiskustase
            GPIO.output(21, False)
            time.sleep(5) #kaua pump peaks töötama sek
            GPIO.output(21, True)


    def print_data(self):
        ''' print select data in nicely formatted string '''
#        print("~~ {0:%Y-%m-%d, %H:%M:%S} ~~".format(self.data_dict[0]))
        print("~~ {} ~~".format(self.data_dict[0]))
        print("protsendid,{}".format(self.data_dict[1]))
        print("veetase,{} L".format(self.data_dict[2]))



    def log_data(self):
        ''' log the data into sqlite database '''
        conn = sqlite3.connect('/home/pi/Dev/plantmax/src/datalogger.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO andmed VALUES ('{}', {}, {})".format(self.data_dict[0], self.data_dict[1], self.data_dict[2]))
        conn.commit()

        conn.close()

    #def irrigation(self):
        #if self.totniisk < 90: #kriitiline niiskustase
            #GPIO.output(21, False)
            #time.sleep(5) #kaua pump peaks töötama sek
            #GPIO.output(21, True)


def pildista(paev, counter):
    a = str(counter)
    b = 5 - len(a)
    tekst = 'Day: ' + str(paev)
    camera.annotate_text = tekst
    nullid = b * '0' + a
    asukoht = '/home/pi/timelapse/kasv' + nullid + '.png'
    camera.capture(asukoht)
    print('pilt tehtud kohal: ' + nullid)



file = open('counters.txt', 'r')
f = file.read()
file.close()
xyz = f.splitlines()
valja = datetime.time(21,0,0)
paev = int(xyz[1])
counter = int(xyz[0]) #peab salvestama txt faili ja programmi käivitades sealt lugema
try:
    while True:
        GPIO.output(20, False)#lambid tööle
        a = datetime.datetime.now()
        b = a.time().replace(minute=0, second=0, microsecond=0)
        pildista(paev, counter)
        counter += 1
        paev3 = str(paev)
        counter3 = str(counter)
        file3 = open('counters.txt', 'w')
        file3.write(counter3 + '\n' + paev3)
        file3.close()
        if (counter % 30) == 0: #kui on 60 pilti päevas, kontrollib niiskust ja veetaset ühe korra
            logger = Logger()
            logger.collect_data()
#            logger.irrigation()
            logger.log_data()
            logger.print_data()
        if b == valja:
            GPIO.output(20, True)
            paev += 1
            file2 = open('counters.txt', 'w')
            paev2 = str(paev)
            counter2 = str(counter)
            file2.write(counter2 + '\n' + paev2)
            file2.close()
            os.system('ffmpeg -framerate 30 -i /home/pi/timelapse/kasv%05d.png -y /home/pi/Dev/plantmax/static/videos/plantmax.mp4')
            #video üleslaadimine ka
            time.sleep(36000) #ei tööta 12h
        time.sleep(720)#iga tsükkel kestab 12minutit


except KeyboardInterrupt:
    GPIO.cleanup()

#def rename(fn, p2ev):    with open(fn, 'r') as in_fn, open('vana_video' + p2ev + '.mpg4', 'w') as out_fn:        out_fn.write(in_fn.read())
