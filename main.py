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
BATTSTATUS = -1
WIFISTATUS = ""
BTSTATUS = ""
DICTIONNARY = dict({"battery": 0, "wifi": 0, "bluetooth": 0})

# Get the screen resolution on X and Y axis
XRESOLUTION = int(check_output("fbset | grep 'x' | tr 'a-z\"-' ' ' | awk '{ printf $1 }'", shell=True))
YRESOLUTION = int(check_output("fbset | grep 'x' | tr 'a-z\"-' ' ' | awk '{ printf $2 }'", shell=True))

# Debug
if DEBUGMSG:
    print("Screen resolution :          {}x{}".format(XRESOLUTION, YRESOLUTION))
    print("Battery 100% voltage:      {}".format(VOLT100))
    print("Battery 75% voltage:       {}".format(VOLT75))
    print("Battery 50% voltage:       {}".format(VOLT50))
    print("Battery 25% voltage:       {}".format(VOLT25))
    print("Battery dangerous voltage: {}".format(VOLT0))
    print("ADC 100% value:              {}".format(ADC100))
    print("ADC 75% value:               {}".format(ADC75))
    print("ADC 50% value:               {}".format(ADC50))
    print("ADC 25% value:               {}".format(ADC25))
    print("ADC dangerous voltage value: {}".format(ADC0))

# Coordinates for the choosen corner
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
    """ Show an icon and can update it
    icon : name of the icon (ex : wifi)
    state : state of the icon (ex : connected)

    Create a Python subprocess to show the icon using "pngview"binary.

    PID of the subprocess is save, next time the same icon need to be updated,
    "pngview" is call again. The previous PID is use to terminate the subprocess and new PID is save.

    This behavior of superposition is used to avoid a "empty icon" during the transition between two statess.
    """
    if ICON:
        global DICTIONNARY

        # Test
        if CORNER == 2:
            if icon == "wifi":
                XPOS -= 5
            elif icon == "bluetooth":
                XPOS -= 10

        # Pngview command and arguments
        cmd = '{}/pngview'.format(PNGVIEWPATH)
        arg1 = '-b 0'
        arg2 = '-l 299999'
        arg3 = '-x {}'.format(XPOS)
        arg4 = '-y {}'.format(YPOS)
        img = '{}/{}_{}.png'.format(ICONPATH, icon, state)

        # Create "pngview" subprocess
        popen = subprocess.Popen([cmd, arg1, arg2, arg3, arg4, img])
        time.sleep(2)

        # Terminate the previous subprocess if it exists
        pid = DICTIONNARY[icon]
        if pid != 0:
            os.kill(pid, signal.SIGTERM)

        # Get the PID of the new subprocess and update the dictionnary
        new_pid = popen.pid
        if new_pid != "":
            DICTIONNARY[icon] = new_pid

        # Debug
        if DEBUGMSG:
            print("Pngview previous pid was {} for {} icon".format(pid, icon))
            print("Change {} icon to {}".format(icon, state))
            print("Pngview pid is now {} for {} icon".format(new_pid, icon))


def changeLed(led):
    """ Change LED color
    led : color of the led (green or red)

    Send a signal through the GPIOs to change the led color
    """
    if LEDS:
        if led == "green":
            GPIO.output(GOODVOLTPIN, GPIO.HIGH)
            GPIO.output(LOWVOLTPIN, GPIO.LOW)
        elif led == "red":
            GPIO.output(GOODVOLTPIN, GPIO.LOW)
            GPIO.output(LOWVOLTPIN, GPIO.HIGH)


def playClip(level):
    """ Display a video
    level : level of alert about battery level (warning or critical)

    The critical level add the shutdown function
    """
    global WARNING

    if CLIPS:
        if level == "warning" and WARNING != 1:
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbatt_warning.mp4 --alpha 160".format(VIDEOPATH))
            WARNING = 1
        elif level == "critical":
            os.system("/usr/bin/omxplayer --no-osd --layer 999999 {}/lowbatt_critical.mp4 --alpha 160;shutdown -h now".format(VIDEOPATH))


def checkWifi():
    """ Manage the WIFI icon

    Use "nmcli" commands

    Checking if wifi is activated or not.
    If wifi is activated, checking the connection to display the right icon
    """
    global WIFISTATUS

    wifi_status = check_output("LC_ALL=C nmcli -f WIFI,STATE -m multiline g | grep WIFI | awk '{ printf $2 }'", shell=True)
    # Avoid updating icon if not necessary
    if wifi_status == "disabled" and WIFISTATUS != "disabled":
        changeIcon("wifi", "disabled")
        WIFISTATUS = "disabled"
    elif wifi_status != "disabled":
        wifi_connection = check_output("LC_ALL=C nmcli -f WIFI,STATE -m multiline g | grep STATE | awk '{ printf $2 }'", shell=True)
        # Avoid updating icon if not necessary
        if WIFISTATUS != wifi_connection:
            changeIcon("wifi", wifi_connection)
            WIFISTATUS = wifi_connection


def checkBluetooth():
    """ Manage the BLUETOOTH icon

    Use "systemctl" and "hcitool" commands
    """
    global BTSTATUS

    bt_connection = check_output("hcitool con | awk '{ printf $2 }'", shell=True)
    # Avoid updating icon if not necessary
    if bt_connection != "" and BTSTATUS != "paired":
        changeIcon("bluetooth", "paired")
        BTSTATUS = "paired"
    elif bt_connection == "":
        # Avoid updating icon if not necessary
        bt_status = check_output("systemctl is-active bluetooth", shell=True)
        if BTSTATUS != bt_status:
            changeIcon("bluetooth", bt_status)
            BTSTATUS = bt_status


def checkBattery():
    """ Manage the BATTERY icon

    Use "readadc" command
    """
    global BATTSTATUS
    global WARNING

    # Calcul the average battey left
    ret = 0
    for i in range(1, PRECISION):
        ret += readadc(ADCCHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS)
        time.sleep(WAITING)
    ret = ret/PRECISION

    # Loop over battery level for testing purpose
    if DEBUGMODE:
        if BATTSTATUS == 100:
            # 75%
            ret = ADC75 - 1
        elif BATTSTATUS == 75:
            # 50%
            ret = ADC50 - 1
        elif BATTSTATUS == 50:
            # 25%
            ret = ADC25 - 1
        elif BATTSTATUS == 25:
            # Near 0%
            ret = ADC0 - 1
        else:
            # 100%
            ret = ADC75 + 1

    # Debug
    if DEBUGMSG:
        voltage = (HIGHRESVAL+LOWRESVAL)*ret*(ADCVREF/1024)/HIGHRESVAL
        print("ADC value: {} ({}V)".format(ret, voltage))
        print("Battery level : {}%".format(BATTSTATUS))

    # Battery monitor
    if ret < ADC0 and BATTSTATUS != 0:
        changeLed("red")
        changeIcon("battery", "0")
        playClip("critical")
        BATTSTATUS = 0
    elif ret < ADC25 and BATTSTATUS != 25:
        changeLed("red")
        changeIcon("battery", "25")
        playClip("warning")
        BATTSTATUS = 25
    elif ret < ADC50 and BATTSTATUS != 50:
        changeLed("green")
        changeIcon("battery", "50")
        BATTSTATUS = 50
    elif ret < ADC75 and BATTSTATUS != 75:
        changeLed("green")
        changeIcon("battery", "75")
        BATTSTATUS = 75
    elif BATTSTATUS != 100:
        changeLed("green")
        changeIcon("battery", "100")
        BATTSTATUS = 100


def endProcess(signalnum=None, handler=None):
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
    if WIFI:
        checkWifi()

    if BLUETOOTH:
        checkBluetooth()

    if BATTERY:
        checkBattery()

    # Debug
    if DEBUGMSG:
        pprint("GLOBAL Variables are : WARNING = {} STATUS = {} LAYER = {} PID = {}".format(WARNING, STATUS, LAYER, DICTIONNARY))

    # Wainting for next loop
    time.sleep(REFRESH_RATE)
