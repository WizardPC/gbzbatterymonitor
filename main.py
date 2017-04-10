#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import os
import signal
import subprocess
from subprocess import check_output

from mcp3008 import *

WARNING = 0
STATUS = 0

# Get the screen resolution on X and Y axis
XRESOLUTION = int(check_output("fbset | grep 'x' | tr 'a-z\"-' ' ' | awk '{printf $1;}'", shell=True))
YRESOLUTION = int(check_output("fbset | grep 'x' | tr 'a-z\"-' ' ' | awk '{printf $2;}'", shell=True))

# Debug
if DEBUGMSG:
    print("Screen resolution :          {}x{}".format(XRESOLUTION,YRESOLUTION))
    print("Batteries 100% voltage:      {}".format(VOLT100))
    print("Batteries 75% voltage:       {}".format(VOLT75))
    print("Batteries 50% voltage:       {}".format(VOLT50))
    print("Batteries 25% voltage:       {}".format(VOLT25))
    print("Batteries dangerous voltage: {}".format(VOLT0))
    print("ADC 100% value:              {}".format(ADC100))
    print("ADC 75% value:               {}".format(ADC75))
    print("ADC 50% value:               {}".format(ADC50))
    print("ADC 25% value:               {}".format(ADC25))
    print("ADC dangerous voltage value: {}".format(ADC0))

# Positions for the choosen corner
if ICON:
    if CORNER == 1:
        XPOS = XOFFSET
        YPOS = YOFFSET
    elif CORNER == 2:
        XPOS = XRESOLUTION - XOFFSET
        YPOS = YOFFSET
    elif CORNER == 3:
        XPOS = XRESOLUTION - XOFFSET
        YPOS = YRESOLUTION - YOFFSET
    elif CORNER == 4:
        XPOS = XOFFSET
        YPOS = YRESOLUTION - YOFFSET

    # Initialisation
    os.system("{}/pngview -b 0 -l 299999 -x {} -y {} {}/blank.png &".format(PNGVIEWPATH, XPOS, YPOS, ICONPATH))

def changeicon(percent):
    if ICON:
        os.system("{}/pngview -b 0 -l 3000{} -x {} -y {} {}/battery{}.png &".format(PNGVIEWPATH, percent, XPOS, YPOS, ICONPATH, percent))

        if DEBUGMSG:
            print("Changed battery icon to {}%".format(percent))

        nums = check_output("ps aux | grep pngview | awk '{ print $1 }'", shell=True).split('\n')
        os.system("kill {}".format(nums[0]))

def changeled(led):
    if LEDS:
        if led == "green":
            GPIO.output(GOODVOLTPIN, GPIO.HIGH)
            GPIO.output(LOWVOLTPIN, GPIO.LOW)
        elif led == "red":
            GPIO.output(GOODVOLTPIN, GPIO.LOW)
            GPIO.output(LOWVOLTPIN, GPIO.HIGH)

def playclip(clip):
    if CLIPS:
        if clip == "alert" and WARNING != 1:
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbattalert.mp4 --alpha 160").format(ICONPATH)
            WARNING = 1
        elif clip == "shutdown":
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbattshutdown.mp4 --alpha 160;shutdown -h now").format(ICONPATH)

def endProcess(signalnum = None, handler = None):
    GPIO.cleanup()
    os.system("killall pngview");
    exit(0)

def initPins():
    GPIO.setup(GOODVOLTPIN, GPIO.OUT)
    GPIO.setup(LOWVOLTPIN, GPIO.OUT)
    GPIO.output(GOODVOLTPIN, GPIO.LOW)
    GPIO.output(LOWVOLTPIN, GPIO.LOW)

# Prepare handlers for process exit
signal.signal(signal.SIGTERM, endProcess)
signal.signal(signal.SIGINT, endProcess)

if LEDS:
    GPIO.setmode(GPIO.BOARD)
    initPins()

while True:
    # Calcul the average battey left
    i = 0
    ret = 0
    while i < PRECISION:
        ret += readadc(ADCCHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS)
        i += 1
        time.sleep(WAITING)
    ret = ret/PRECISION

    # Force full charged battery for test
    if FULLCHARGE:
        ret = 999999

    if DEBUGMSG:
        voltage = (HIGHRESVAL+LOWRESVAL)*ret*(ADCVREF/1024)/HIGHRESVAL
        print("ADC value: {} ({}V)".format(ret, voltage))
 
    # Battery monitor
    if ret < ADC0 and STATUS != 0:
        changeled("red")
        changeicon("0")
        playclip("shutdown")
        STATUS = 0
    elif ret < ADC25 and STATUS != 25:
        changeled("red")
        changeicon("25")
        playclip("alert")
        STATUS = 25
    elif ret < ADC50 and STATUS != 50:
        changeled("green")
        changeicon("50")
        STATUS = 50
    elif ret < ADC75 and STATUS != 75:
        changeled("green")
        changeicon("75")
        STATUS = 75
    elif STATUS != 100:
        changeled("green")
        changeicon("100")      
        STATUS = 100

    # Wainting for next loop
    time.sleep(REFRESH_RATE)