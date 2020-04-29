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

PYTHON LIBRARIES NEEDED:-----------------------------------------------------------
gpiozero
schedule
astral
Note: The remainder either will be installed as dependencies or already installed on the Raspberry Pi.

HARDWARE REQUIREMENTS:-----------------------------------------------------------
Runs on any Raspberry Pi.
I am using a Raspberry Pi 2 because it uses less power than newer models which is important when running from a solar
charged battery.
A 16" Linear Actuator to raise and lower the coop door.
An L289 H-Bridge is used to power and control the actuator.
Momentary buttons for manually opening and closing the coop door.

UPDATES:------------------------------------------------------------------------
04/03/20 - Added buzzer when door opens/closes.
04/04/20 - Added main_loop as a function.
04/25/20 - Added useSchedule check to be able to enable/disable use of automated door schedule.
04/26/20 - Simplified function current_time
04/29/20 - Added button 'buttonStop' to stop the motor at any point.
           Changed the name of variables for the time of day to open and close the door.  Was sunrise and dusk, now
           opentime and closetime.
           Removed the return on function door_shedule as it was no longer needed.
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
buttonStop = Button(24)
motor = Motor(14, 15)  # First GPIO is open, second is close.

# Initiate variables for door_schedule function.
opentime = 0
closetime = 0

#  Check if scheduled coop door should be run.  If True the dawn/dusk schedule will be run.
#  If False the door will have to be manually opened and closed.
# TODO: In the future use a button on the control panel to enable/disable schedule.
useSchedule = False


def current_time():
    #  Used if you opt to print current date/time of opening and closing door.
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now


def open_door():
    motor.forward()
    print("Door opened at:", current_time())  # Comment out if you donn't wish to print
    time.sleep(1)


def close_door():
    motor.backward()
    print("Door closed at:", current_time())  # Comment out if you donn't wish to print
    time.sleep(1)


def stop_door():
    motor.stop()
    print("Door stopped at:", current_time())  # Comment out if you donn't wish to print
    time.sleep(1)


def door_schedule():
    """Function grabs sunrise and dusk using your location and creates a schedule of events
    You can change your location by modifying the fourth line of function.
    You may specify alternate open and close times by modifying 'sunrise' and 'dusk'.  See astral docs for alternate
    times of day"""
    global opentime
    global closetime
    # astral.Location format is: City, Country, Long, Lat, Time Zone, elevation.
    loc = astral.Location(('lincoln city', 'USA', 45.0216, -123.9399, 'US/Pacific', 390))
    sun = loc.sun(date.today())  # Gets Astral info for today
    opentime = (str(sun['sunrise'].isoformat())[11:16])  # Grabs sunrise for today and strips date.time to just the time.
    closetime = (str(sun['dusk'].isoformat())[11:16])  # Grabs dusk for today and strips date.time to just the time.
    schedule.every().day.at(opentime).do(open_door)
    schedule.every().day.at(closetime).do(close_door)


def main_loop():
    while True:
        if buttonOpen.is_pressed:
            open_door()
        if buttonClose.is_pressed:
            close_door()
        if buttonStop.is_pressed:
            stop_door()
        if useSchedule:
            schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        main_loop()
    except RuntimeError as error:
        print(error.args[0])
    except KeyboardInterrupt:
        print("\nExiting application\n")
        # exit the application
        sys.exit(0)
