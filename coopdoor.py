"""
coopdoor.py
Author: Mike Paxton
Creation Date: 03/15/20
Python Version: 3

Free and open for all to use.  But put credit where credit is due.

OVERVIEW:-----------------------------------------------------------------------
A simple program which opens and closes a chicken coop door at sunrise and dusk.
I use dusk to give the chickens ample time to get back in the coop at night.
Astral determines the times based on current location.
Schedule is used to actually schedule the opening and closing of the door.
See Wiki for more information:  https://github.com/mikepaxton/StarClucks/wiki

PYTHON MODULES NEEDED:-----------------------------------------------------------
gpiozero
schedule
astral

HARDWARE REQUIREMENTS:-----------------------------------------------------------
Runs on any Raspberry Pi.
I am using a Raspberry Pi 2 because it uses less power than newer models which is important when running from a solar
charged battery.
A 16" Linear Actuator is used to raise and lower the coop door.
An L289 H-Bridge is used to power and control the actuator.
Momentary buttons for manually opening and closing the coop door.

UPDATES:------------------------------------------------------------------------
04/03/20 - Added buzzer when door opens/closes
04/04/20 - Added main_loop as a function
"""
# TODO: Consider adding some form of logging to record opening and closing date/time.
from gpiozero import Button, Motor
import schedule
import time
import datetime
from datetime import date
import astral
import sys

#  GPIO pins used
buttonOpen = Button(18)  # GPIO for open button.
buttonClose = Button(23)  # GPIO for close button.
motor = Motor(14, 15)  # First GPIO is open, second is close.

# Initiate variables for dawn_dusk function.
sunrise = 0
dusk = 0


def current_time():
    #  Used if you opt to print current date/time of opening and closing door.
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    return now


def open_door():
    motor.forward()
    print("Door opened at:", current_time())  # Comment out if you donn't wish to print
    time.sleep(3)



def close_door():
    motor.backward()
    print("Door closed at:", current_time())  # Comment out if you donn't wish to print
    time.sleep(5)


def dawn_dusk():
    global sunrise
    global dusk
    # astral.Location format is: City, Country, Long, Lat, Time Zone, elevation.
    loc = astral.Location(('lincoln city', 'USA', 45.0216, -123.9399, 'US/Pacific', 390))
    sun = loc.sun(date.today())  # Gets Astral info for today
    sunrise = (str(sun['sunrise'].isoformat())[11:16])  # Strips date.time to just the time.
    dusk = (str(sun['dusk'].isoformat())[11:16])
    schedule.every().day.at(sunrise).do(open_door)
    schedule.every().day.at(dusk).do(close_door)


def main_loop():
    while True:
        if buttonOpen.is_pressed:
            open_door()
        if buttonClose.is_pressed:
            close_door()

        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        dawn_dusk()  # Start the schedule
        main_loop()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print("\nExiting application\n")
        # exit the application
        sys.exit(0)
