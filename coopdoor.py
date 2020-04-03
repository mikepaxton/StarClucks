"""
This script opens and closes the chicken coop door at sunrise and dusk.  I use dusk to give the chickens
ample time to get back in the coop at night.  Astral determines both of the those times based on current location.
Schedule is used to actually schedule the opening and closing of the door.
Runs on a Raspberry Pi with an L289 H-Bridge Controller
Author: Mike Paxton
Modified on: 03/30/20
"""
# TODO: Consider adding some form of logging to record opening and closing date/time.
from gpiozero import Button, Motor, Buzzer
import schedule
import time
import datetime
from datetime import date
import astral

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


def close_door():
    motor.backward()
    print("Door closed at:", current_time())  # Comment out if you donn't wish to print


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


dawn_dusk()  # Start the schedule


try:
    while True:

        if buttonOpen.is_pressed:
            open_door()
        if buttonClose.is_pressed:
            close_door()

        schedule.run_pending()
        time.sleep(1)

except KeyboardInterrupt:
    print('Control-C pressed')
