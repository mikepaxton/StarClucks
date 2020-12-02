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
astral - Version 1.10.1 NEEDED!!!
Note: The remainder either will be installed as dependencies or already installed on the Raspberry Pi.

HARDWARE REQUIREMENTS:-----------------------------------------------------------
Runs on any Raspberry Pi.
I am using a Raspberry Pi 2 because it uses less power than newer models which is important when running from a solar
charged battery.
A 16" Linear Actuator to raise and lower the coop door.
An L289 H-Bridge is used to power and control the actuator.
Momentary buttons for manually opening and closing the coop door.

UPDATES:------------------------------------------------------------------------
04/04/20 - Added main_loop as a function.
04/25/20 - Added useSchedule check to be able to enable/disable use of automated door schedule.
04/26/20 - Simplified function current_time
04/29/20 - Added button 'buttonStop' to stop the motor at any point.
           Changed the name of variables for the time of day to open and close the door.  Was sunrise and dusk, now
           opentime and closetime.
           Removed the return on function door_shedule as it was no longer needed.
05/03/20 - Added buttonScheduleOverride so that coop door scheduling can be manually turned on/off.
           Added two new functions to enable/disable scheduling and print the status to the LCD.
           Added an LED that turns on when coop door scheduling is disabled.
05/05/20 - Added debug function.
05/06/20 - Created new function astral_update and split it out of door_schedule so that astral times can be updated
           every morning at 12:01.  This makes sure at the beginning of each new day the times for door
           opening/closing are correct for the day.
           Removed using LCD from this program.  See second line of update 05/03/20 for why LCD was originally added.
           Fixed bug in astral_update where getting location was causing crash.  However, it currently is not getting
           correct times.
10/31/20 - Fixed Astral.  Now using most recent version of astral (2.2).
"""

# TODO: Consider adding some form of logging to record opening and closing date/time.
from gpiozero import Button, Motor, LED
import gpiozero
import schedule
import time
import datetime
from datetime import date
from astral import LocationInfo
from astral.sun import sun
import pytz
import sys


#  GPIO pins used
buttonOpen = Button(18)  # GPIO for open button.
buttonClose = Button(23)  # GPIO for close button.
buttonStop = Button(24)
motor = Motor(14, 15)  # First GPIO is open, second is close.
buttonSchedOverride = Button(25)  # Override the scheduled opening/closing of coop door.
ledSchedOff = LED(4)  # Use LED to indicate that coop door is in override mode.

#  GPIO button used to toggle Light relay.
lightsOnRelay = 21  # Coop light relay pin
lightOnButton = Button(17)  # Coop light button.

# create a relay object.
# Triggered by the output pin going low: active_high=False.
# Initially off: initial_value=False
coopLightRelay = gpiozero.OutputDevice(lightsOnRelay, active_high=True, initial_value=False)

# Initiate variables for astral_update function.
opentime = 0
closetime = 0


#  Check if scheduled coop door should be run.  If True the dawn/dusk schedule will be run.
#  If False the door will have to be manually opened and closed.
useSchedule = True

# Set to True will turn on debug printing to console.
debug = True


def current_time():
    #  Used if you opt to print current date/time of opening and closing door.
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return now


def debug_print(message):
    if debug:
        print(message)


def open_door():
    motor.forward()
    debug_print("Door opened at: ")
    time.sleep(1)


def close_door():
    motor.backward()
    debug_print("Door closed at: ")
    time.sleep(1)


def stop_door():
    motor.stop()
    debug_print("Door stopped at: ")
    time.sleep(1)


def astral_update():
    """Function grabs sunrise and dusk using your location and creates a schedule of events
        You can change your location by modifying the fourth line of function.
        You may specify alternate open and close times by modifying opentime and closetime.
        Valid options are dawn, sunrise, sunset and dusk."""
    global opentime
    global closetime
    # astral.Location format is: City, Country, Long, Lat, Time Zone, elevation.
    city = LocationInfo('lincoln city', 'USA', 'US/Pacific', 45.014, -123.909)
    s = sun(city.observer, date=date.today(), tzinfo=pytz.timezone(city.timezone))
    opentime = (str(s['sunrise'].isoformat())[11:16])  # Strips date.time to just the time.
    closetime = (str(s['dusk'].isoformat())[11:16])
    return opentime, closetime


def door_schedule():
    """Function for scheduled opening and closing of coop door."""
    global opentime
    global closetime
    schedule.every().day.at(opentime).do(open_door)
    schedule.every().day.at(closetime).do(close_door)
    debug_print('Open Time: ' + str(opentime))
    debug_print('Close Time: ' + str(closetime))


def scheduling_off():
    global useSchedule
    debug_print('Schedule Off at: ')
    ledSchedOff.on()  # Turn on schedule LED.
    useSchedule = False  # Turn off Scheduling.


def scheduling_on():
    global useSchedule
    debug_print('Schedule On at: ')
    ledSchedOff.off()  # Turn off schedule LED.
    useSchedule = True  # Turn on Scheduling.


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


def main_loop():
    while True:
        if buttonOpen.is_pressed:
            open_door()
        if buttonClose.is_pressed:
            close_door()
        if buttonStop.is_pressed:
            stop_door()
        if buttonSchedOverride.is_pressed:  # Check if override schedule button is pressed.
            if useSchedule:
                scheduling_off()  # If useSchedule is True/enabled then override scheduling by turning it off.
            else:
                scheduling_on()  # Scheduling is already off, turn it back on.
        if useSchedule:  # Check to see if useSchedule flag is True.  If True then check for pending schedules.
            schedule.run_pending()
        if lightOnButton.is_pressed:
            toggle_coop_light_relay()
        time.sleep(1)


if __name__ == "__main__":
    try:
        astral_update()  # Initiate astral_update.  Get Astral times.
        door_schedule()  # Initiate door_schedule
        schedule.every().day.at('12:01').do(astral_update)  # Run function astral_times first thing every morning
        # in order to update times for the new day.

        main_loop()
    except RuntimeError as error:
        print(error.args[0])
    # except Exception as e:
    #     # this covers all other exceptions
    #     print(str(e))
    except KeyboardInterrupt:
        print("\nExiting application\n")
        set_coop_light_relay(False)
        # exit the application
        sys.exit(0)
