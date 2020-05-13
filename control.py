"""
control.py
Author: Mike Paxton
Creation Date: 03/30/20
Python Version: 3

Free and open for all to use.  But put credit where credit is due.

OVERVIEW:-----------------------------------------------------------------------
This script controls and monitors various aspects of the chicken coop such temperature, lighting and solar output.
Monitoring information displayed on a 20x4 LCD.  A momentary push button to turn the display on and
start the cycling of the information.  The purpose for using the button is so that the LCD does not waste
solar battery power.

PYTHON LIBRARIES NEEDED:-----------------------------------------------------------
gpiozero
adafruit-circuitpython-am2320
adafruit-circuitpython-ina260
i2c_lcd_driver
Note: The remainder should be installed as dependencies or already installed on the Raspberry Pi.

HARDWARE REQUIREMENTS:-----------------------------------------------------------
Runs on any Raspberry Pi.
I am using a Raspberry Pi 2 because it uses less power than newer models which is important when running from a solar
charged battery.
2004 LCD for displaying information.
Momentary button's for activating LCD and lighting.
A relay board for the internal coop lighting.  I am using Pi-OT Module with 5 built-in relays.
Two ina260 sensors from Adafruit to monitor both solar and battery voltage/current.

UPDATES:------------------------------------------------------------------------

04/04/20 - Started working on LCD information display.
04/13/20 - LCD information is working correctly.
04/24/20 - Added batterystatus to LCD info dispayed.
04/26/20 - Fixed issue with ina260's only using default i2c address.  Added address 0x40 to solar and 0x41 to battery.
           Fixed issue with ina260's not displaying stats on LCD.  Changed Mode to CONTINUOUS as TRIGGERED was not working.
           Fixed issue with Light Relay not working, was using wrong GPIO for Pi-IOT relay #1.  Now using GPIO 5
           Changed Light On Button to GPIO 17
           Changed LCD Button to GPIO 27
05/05/20 - Added a debug function to allow printing of messages to terminal.
"""
# TODO: Look into using InfluxDB and Grafana to log sensor data.

from gpiozero import Button, CPUTemperature, PingServer
import gpiozero
import adafruit_am2320
from adafruit_ina260 import INA260, Mode, AveragingCount
import i2c_lcd_driver
import board
import busio
import sys
import time
import datetime

# Initialize lcd
lcd = i2c_lcd_driver.lcd()


#  GPIO button used to toggle Light relay.
lightsOnRelay = 5  # Coop light relay pin
lightOnButton = Button(17)  # Coop light button.
# GPIO button to turn on/off LCD.
lcdButton = Button(27)

# Server to Ping to check for Internet/Local connection.  The host can be local or over the internet.
# TODO: Implement ping into LCD status display.
pingServer = '192.168.1.1'

# create a relay object.
# Triggered by the output pin going low: active_high=False.
# Initially off: initial_value=False
coopLightRelay = gpiozero.OutputDevice(lightsOnRelay, active_high=False, initial_value=False)

# Set to True will turn on debug printing to console.
debug = True


def current_time():
    #  Used if you opt to print current date/time of opening and closing door.
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now


def debug_print(message):
    if debug:
        print(message + current_time())


def fahrenheit(temperature):
    """Function takes in celsius temperature and returns temp in Fahrenheit"""
    temperature = temperature * 9.0 / 5.0 + 32.00
    return temperature


def am2320():
    """Function initiates AM2320 sensor and returns temperature and humidity"""
    i2c = busio.I2C(board.SCL, board.SDA)  # create the I2C shared bus for AM2320 Temp/Humidity sensor.
    am = adafruit_am2320.AM2320(i2c)
    cooptemp = round(fahrenheit(am.temperature), 2)
    coophumidity = am.relative_humidity
    return cooptemp, coophumidity


def solarstatus():
    """Function initiates ina260 at address 0x40 and returns current, voltage and power of solar panel."""
    i2c = board.I2C()
    ina260 = INA260(i2c, 0x40)
    ina260.averaging_count = AveragingCount.COUNT_4
    ina260.mode = Mode.CONTINUOUS
    current = ina260.current
    voltage = ina260.voltage
    power = ina260.power
    return current, voltage, power


def batterystatus():
    """Function initiates ina260 at address 0x41 and returns current, voltage and power of battery."""
    i2c = board.I2C()
    ina260 = INA260(i2c, 0x41)
    ina260.mode = Mode.CONTINUOUS
    current = ina260.current
    voltage = ina260.voltage
    power = ina260.power
    return current, voltage, power


def set_coop_light_relay(status):
    """Function called to set the initial state of the light relay.  Under current programing should always be False."""
    if status:
        debug_print('Setting relay: ON ')
        coopLightRelay.on()
    else:
        debug_print('Setting relay: OFF ')
        coopLightRelay.off()


def toggle_coop_light_relay():
    """Function called to turn on/off the light on relay"""
    debug_print('toggling relay ')
    coopLightRelay.toggle()


def coopstats():
    """Function displays various sensor readings on LCD."""
    debug_print('LCD Button Pressed: ')
    lcd.backlight(1)  # Turn LCD backlight on
    lcd.lcd_clear()
    cooptemp, coophudity = am2320()
    lcd.lcd_display_string('Chicken Coop', 1, 4)  # String, row, column
    lcd.lcd_display_string('Temp: ' + str(cooptemp) + chr(223), 2, 0)
    lcd.lcd_display_string('Humidity: ' + str(coophudity) + chr(223), 3, 0)
    time.sleep(4)
    lcd.lcd_clear()
    current, voltage, power = solarstatus()  # Grab solar panel voltage, current, power and display it.
    lcd.lcd_display_string('Solar Status', 1, 4)
    lcd.lcd_display_string('Voltage: %.2f V' % voltage, 2, 0)
    lcd.lcd_display_string('Current: %.2f mA' % current, 3, 0)
    lcd.lcd_display_string('Power: %.2f mW' % power, 4, 0)
    time.sleep(4)
    lcd.lcd_clear()
    current, voltage, power = batterystatus()  # Grab battery voltage, current, power and display it.
    lcd.lcd_display_string('Battery Status', 1, 3)
    lcd.lcd_display_string('Voltage: %.2f V' % voltage, 2, 0)
    lcd.lcd_display_string('Current: %.2f mA' % current, 3, 0)
    lcd.lcd_display_string('Power: %.2f mW' % power, 4, 0)
    time.sleep(4)
    lcd.lcd_clear()
    cpu = CPUTemperature()
    lcd.lcd_display_string('CPU Temperature', 1, 2)
    lcd.lcd_display_string('Temp: ' + str(cpu.temperature) + ' C', 2, 0)  # Display CPU temperature.
    time.sleep(3)
    lcd.lcd_clear()
    lcd.backlight(0)  # Turn LCD backlight off.


def startup_display():
    lcd.backlight(1)
    lcd.lcd_clear()
    lcd.lcd_display_string('Welcome to', 1, 5)
    lcd.lcd_display_string('Starclucks', 2, 5)
    time.sleep(5)
    lcd.lcd_clear()
    lcd.backlight(0)


def main_loop():
    while True:
        if lightOnButton.is_pressed:
            toggle_coop_light_relay()
        if lcdButton.is_pressed:
            coopstats()
        time.sleep(1)


if __name__ == '__main__':
    try:
        startup_display()
        main_loop()
    except RuntimeError as error:
        print(error.args[0])
    # except Exception as e:
    #     # this covers all other exceptions
    #     print(str(e))
    except KeyboardInterrupt:
        # turn the relay off
        set_coop_light_relay(False)
        print('\nExiting application\n')
        # exit the application
        sys.exit(0)
