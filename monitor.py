#!/usr/bin/python
import RPi.GPIO as GPIO
import time
from time import localtime, strftime

from mcp3008 import *

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
print(" ")
print("Time           ADC          Volt")

while True:
    # Calcul the average battey left
    i = 0
    ret = 0
    while i < PRECISION:
        ret += readadc(ADCCHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS)
        i += 1
        time.sleep(WAITING)
    ret = ret/PRECISION

    voltage = (HIGHRESVAL+LOWRESVAL)*ret*(ADCVREF/1024)/HIGHRESVAL
    print(strftime("%H:%M", localtime()) + "          {}          {}".format(ret, voltage))

    time.sleep(170)