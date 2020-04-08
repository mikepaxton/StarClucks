"""
control.py
Author: Mike Paxton
Creation Date: 03/30/20
Python Version: 3

Free and open for all to use.  But put credit where credit is due.

OVERVIEW:-----------------------------------------------------------------------
WARNING, this script is currently not functioning as intended.  It's actively being developed.
This script controls and monitors various aspects of the chicken coop such temperature, lighting and solar output.
Monitoring information is displayed on a 16x2 LCD.  A momentary push button is used to turn the display on and
start the cycling of the information.  The purpose for using the button is so that the LCD does not waste
solar battery power.

PYTHON LIBRARIES NEEDED:-----------------------------------------------------------
gpiozero
adafruit-circuitpython-am2320
adafruit-circuitpython-ina260
adafruit-circuitpython-charlcd
Note: The remainder either will be installed as dependencies or already installed on the Raspberry Pi.

HARDWARE REQUIREMENTS:-----------------------------------------------------------
Runs on any Raspberry Pi.
I am using a Raspberry Pi 2 because it uses less power than newer models which is important when running from a solar
charged battery.
1602 LCD for displaying information.
Momentary button for activating LCD display.
A relay board for the internal coop lighting.

UPDATES:------------------------------------------------------------------------
This script controls and monitors various aspects of the chicken coop such as temperature, lighting and solar output.

04/04/20 - Started working on LCD information display.
"""

from gpiozero import Button, CPUTemperature
import gpiozero
import adafruit_am2320
from adafruit_ina260 import INA260, Mode
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import board
import busio
import sys
import time


#  GPIO button used to toggle Light relay.
lightsOnRelay = 17  # Coop light relay pin
lightOnButton = Button(27)  # Coop light button.
# GPIO button to turn on/off LCD display.
lcdButton = Button(22)


# create a relay object.
# Triggered by the output pin going low: active_high=False.
# Initially off: initial_value=False
coopLightRelay = gpiozero.OutputDevice(lightsOnRelay, active_high=False, initial_value=False)


def lcddisplay():
    # Initialise the lcd class
    i2c = busio.I2C(board.SCL, board.SDA)
    lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2)
    lcd.display = True
    lcd.backlight = True  # Turn backlight on.
    lcd.cursor = False  # Turn off the cursor.
    cooptemp, coophumidity = am2320()  # Grab temp and humidity and display it.
    lcd.message = "Temp: ", str(cooptemp) + "Humidity: ", str(coophumidity)  # print two line message.
    time.sleep(3)
    lcd.clear()
    lcd.display = "CPU Temp: ", str(CPUTemperature)  # Display CPU temperature.
    time.sleep(3)
    lcd.clear()
    current, voltage = solarstatus()  # Grab solar panel voltage, current, power and display it.
    #lcd.message = "Solar Output" + "%.2f V %.2f mA" % (voltage, current)
    lcd.cursor_position(0, 0)
    lcd.message = "Solar: Volts %.2f" % voltage
    lcd.cursor_position(0,1)
    lcd.message = "Current %.2f mA" % current
    time.sleep(3)
    lcd.clear()
    current, voltage = batterystatus()  # Grab battery voltage, current and display it.
    #lcd.message = "Solar Panel Output" + "Voltage: %.2f V Current: %.2f mA" % (voltage, current)
    lcd.cursor_position(0, 0)
    lcd.message = "Batt: Volts %.2f" % voltage
    lcd.cursor_position(0, 1)
    lcd.message = "Current %.2f mA" % current
    time.sleep(3)
    lcd.clear()
    lcd.display = False
    lcd.backlight = False  # Turn backlight off to save battery power.


def fahrenheit(temperature):
    """Function takes in celsius temperature and returns temp in Fahrenheit"""
    temperature = temperature * 9.0 / 5 + 32
    return temperature


def am2320():
    i2c = busio.I2C(board.SCL, board.SDA)  # create the I2C shared bus for AM2320 Temp/Humidity sensor.
    am = adafruit_am2320.AM2320(i2c)
    cooptemp = round(fahrenheit(am.temperature), 2)
    coophumidity = am.relative_humidity
    return cooptemp, coophumidity


def solarstatus():
    i2c = board.I2C()
    ina260 = INA260(i2c)
    ina260.mode = Mode.TRIGGERED  # Grab one current instance of sensor readings.
    current = ina260.current
    voltage = ina260.voltage
    ina260.mode = Mode.SHUTDOWN  # Shut down sensor to save battery power.
    return current, voltage


def batterystatus():
    i2c = board.I2C()
    ina260 = INA260(i2c)
    ina260.mode = Mode.TRIGGERED  # Grab one current instance of sensor readings.
    current = ina260.current
    voltage = ina260.voltage
    ina260.mode = Mode.SHUTDOWN  # Shut down sensor to save battery power.
    return current, voltage


def set_coop_light_relay(status):
    if status:
        print("Setting relay: ON")
        coopLightRelay.on()
    else:
        print("Setting relay: OFF")
        coopLightRelay.off()


def toggle_coop_light_relay():
    print("toggling relay")
    coopLightRelay.toggle()


def main_loop():
    # start by turning the relay off
    set_coop_light_relay(False)
    while True:
        if lightOnButton.is_pressed:
            toggle_coop_light_relay()
        if lcdButton.is_pressed:
            lcddisplay()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main_loop()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        # turn the relay off
        set_coop_light_relay(False)
        print("\nExiting application\n")
        # exit the application
        sys.exit(0)
