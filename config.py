"""
" Edit below this line to fit your needs
"""
# Path to pngview (raspidmx) and icons
PNGVIEWPATH = "/etc/recalboxBatteryMonitor/raspidmx/pngview"
ICONPATH = "/etc/recalboxBatteryMonitor/icons"

# Change the association SPI/GPIO as desired 
SPICLK = 23
SPIMISO = 21
SPIMOSI = 19 
SPICS = 24

# Display some debug values when set to 1, and nothing when set to 0
DEBUGMSG = 1
# Force battery to 100% for testing purpose
DEBUGMODE = 1

# Display (wifi and bluetooth are icon only)
BATTERY = 1
WIFI = 0
BLUETOOTH = 0

# Battery Icon, LED, or videoclips or all of them
LEDS = 0
ICON = 1
CLIPS = 0

# Corner is (1)TopLeft, (2)TopRight , (3)BottomRight, (4)BottomLeft
CORNER=1

# Offset position from corner
XOFFSET = 0
YOFFSET = 5

# GPIO (BOARD numbering scheme) pin for good voltage LED
GOODVOLTPIN = 18
LOWVOLTPIN = 17

# Fully charged voltage, voltage at the percentage steps and shutdown voltage. This is where you edit when finetuning the batterymonitor
# by using the monitor.py script.
VOLT100 = 4.2
VOLT75 = 3.7
VOLT50 = 3.6
VOLT25 = 3.5
VOLT0 = 3.2

# Value (in ohms) of the lower resistor from the voltage divider, connected to the ground line (1 if no voltage divider). 
# Default value (2000) is for a lipo battery, stepped down to about 3.2V max.
LOWRESVAL = 2000

# Value (in ohms) of the higher resistor from the voltage divider, connected to the positive line (0 if no voltage divider).
# Default value (5600) is for a lipo battery, stepped down to about 3.2V max.
HIGHRESVAL = 5600

# ADC voltage reference (3.3V for Raspberry Pi)
ADCVREF = 3.3

# MCP3008 channel to use (from 0 to 7)
ADCCHANNEL = 0

# Perform a measure each [WAITING] seconds, [PRECISION] times and do the average.
# WARNING : if PRECISION is too high the performances will be affected negatively !! If you are not sure, let it gooooo
WAITING = 3
PRECISION = 3

# Refresh rate (s)
REFRESH_RATE = 30

# Voltage value measured by the MCP3008 when batteries are fully charged. It should be near 3.3V due to Raspberry Pi GPIO compatibility
# Be careful to edit below this line.
SVOLT100 = (VOLT100)*(HIGHRESVAL)/(LOWRESVAL+HIGHRESVAL)
SVOLT75 = (VOLT75)*(HIGHRESVAL)/(LOWRESVAL+HIGHRESVAL)
SVOLT50 = (VOLT50)*(HIGHRESVAL)/(LOWRESVAL+HIGHRESVAL)
SVOLT25 = (VOLT25)*(HIGHRESVAL)/(LOWRESVAL+HIGHRESVAL)
SVOLT0 = (VOLT0)*(HIGHRESVAL)/(LOWRESVAL+HIGHRESVAL)
# MCP3008 scaling
ADC100 = SVOLT100 / (ADCVREF / 1024.0)
ADC75 = SVOLT75 / (ADCVREF / 1024.0)
ADC50 = SVOLT50 / (ADCVREF / 1024.0)
ADC25 = SVOLT25 / (ADCVREF / 1024.0)
ADC0 = SVOLT0 / (ADCVREF / 1024.0)
