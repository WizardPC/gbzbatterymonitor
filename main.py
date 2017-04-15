#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import os
import signal
import subprocess
from subprocess import check_output
from pprint import pprint
from mcp3008 import *

WARNING = 0
STATUS = 999
LAYER = 299999
DICTIONNARY = dict({"battery":0, "wifi":0, "bluetooth":0, })

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


def changeIcon(icon, state):
    if ICON:
        global LAYER
        global DICTIONNARY

        #LAYER -= 1 # Useless ???
        cmd = '{}/pngview'.format(PNGVIEWPATH)
        arg1 = '-b 0'
        arg2 = '-l {}'.format(LAYER)
        arg3 = '-x {}'.format(XPOS)
        arg4 = '-y {}'.format(YPOS)
        img = '{}/{}_{}.png'.format(ICONPATH, icon, state)

        # New image
        popen = subprocess.Popen([cmd, arg1, arg2, arg3, arg4, img])
        time.sleep(2)
        

        #os.system("{}/pngview -b 0 -l {} -x {} -y {} {}/{}_{}.png &".format(PNGVIEWPATH, LAYER, XPOS, YPOS, ICONPATH, icon, state))

        # Get the last id of pngview for this specific icon
        pid = DICTIONNARY[icon]
        # Remove previous icon if it exist
        if pid != 0:
            #os.system("kill {}".format(pid))
            os.kill(pid, signal.SIGTERM)
        # Get the process id of the new image
        #num = check_output("pgrep -f pngview | tail -1 | tr -d '\n'", shell=True) # TODO > Ne retourne pas le bon id ???
        new_pid = popen.pid
        # Update the dictionnary
        if new_pid != "":
            DICTIONNARY[icon] = new_pid
            
        # Debug
        if DEBUGMSG:
            print("Pngview previous pid was {} for {} icon".format(pid, icon))
            print("Change {} icon to {}".format(icon, state))
            print("Pngview pid is now {} for {} icon".format(new_pid, icon))

def changeLed(led):
    if LEDS:
        if led == "green":
            GPIO.output(GOODVOLTPIN, GPIO.HIGH)
            GPIO.output(LOWVOLTPIN, GPIO.LOW)
        elif led == "red":
            GPIO.output(GOODVOLTPIN, GPIO.LOW)
            GPIO.output(LOWVOLTPIN, GPIO.HIGH)

def playClip(clip, warn):
    if CLIPS:
        if clip == "alert" and warn != 1:
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbattalert.mp4 --alpha 160").format(ICONPATH)
            warn = 1
        elif clip == "shutdown":
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbattshutdown.mp4 --alpha 160;shutdown -h now").format(ICONPATH)

def checkWifi():
    if WIFI:
        wifiStatus = check_output("LC_ALL=C nmcli -f WIFI,STATE -m multiline g | grep WIFI | awk '{ printf $2 }'", shell=True)
        wifiConnection = check_output("LC_ALL=C nmcli -f WIFI,STATE -m multiline g | grep STATE | awk '{ printf $2 }'", shell=True)

        if wifiStatus == "enabled":
            changeIcon("wifi", wifiConnection)

def checkBluetooth():
    if BLUETOOTH:
        btStatus = check_output("systemctl is-active bluetooth", shell=True)
        btConnection = check_output("hcitool con | awk '{ printf $2 }'", shell=True)
        if btStatus == "active":
            if btConnection != "":
                changeIcon("bluetooth", "pair")
            else:
                changeIcon("bluetooth", "none")

def checkBattery():
    if BATTERY:
        global STATUS
        global WARNING

        # Calcul the average battey left
        ret = 0
        for i in range(1, PRECISION):
            ret += readadc(ADCCHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS)
            time.sleep(WAITING)
        ret = ret/PRECISION

        # Test mode
        if DEBUGMODE:
            if STATUS == 100:
                ret = ADC75 - 1 # 75%
            elif STATUS == 75:
                ret = ADC50 - 1 # 50%
            elif STATUS == 50:
                ret = ADC25 - 1 # 25%
            elif STATUS == 25:
                ret = ADC0 - 1 # Near 0%
            else:
                ret = ADC75 + 1 # 100%

        if DEBUGMSG:
            voltage = (HIGHRESVAL+LOWRESVAL)*ret*(ADCVREF/1024)/HIGHRESVAL
            print("ADC value: {} ({}V)".format(ret, voltage))
            print("Battery level : {}%".format(STATUS))

        # Battery monitor
        if ret < ADC0 and STATUS != 0:
            changeLed("red")
            changeIcon("battery", "0")
            playClip("shutdown", WARNING)
            STATUS = 0
        elif ret < ADC25 and STATUS != 25:
            changeLed("red")
            changeIcon("battery", "25")
            playClip("alert", WARNING)
            STATUS = 25
        elif ret < ADC50 and STATUS != 50:
            changeLed("green")
            changeIcon("battery", "50")
            STATUS = 50
        elif ret < ADC75 and STATUS != 75:
            changeLed("green")
            changeIcon("battery", "75")
            STATUS = 75
        elif STATUS != 100:
            changeLed("green")
            changeIcon("battery", "100")      
            STATUS = 100

def endProcess(signalnum = None, handler = None):
    GPIO.cleanup()
    os.system("killall pngview")
    exit(0)

def initPins():
    GPIO.setup(GOODVOLTPIN, GPIO.OUT)
    GPIO.setup(LOWVOLTPIN, GPIO.OUT)
    GPIO.output(GOODVOLTPIN, GPIO.LOW)
    GPIO.output(LOWVOLTPIN, GPIO.LOW)

# Prepare handlers for process exit
signal.signal(signal.SIGTERM, endProcess)
signal.signal(signal.SIGINT, endProcess)

# Prepare LEDs
if LEDS:
    GPIO.setmode(GPIO.BOARD)
    initPins()

# Main function
while True:
    
    checkWifi()
    checkBluetooth()
    checkBattery()

    # Debug
    if DEBUGMSG:
        pprint("GLOBAL Variables are : \nWARNING = {}\nSTATUS = {}\nLAYER = {}\n PID = {}".format(WARNING, STATUS, LAYER, DICTIONNARY))

    # Wainting for next loop
    time.sleep(REFRESH_RATE)