#!/usr/bin/env python3

import subprocess
import time
import psutil
import sys

gridfan = '/usr/local/bin/gridfan'
#gridfan = '/usr/local/bin/gridfan -d /dev/GridPlus1' # Error testing
check_interval = 5
previous_state = ''
state = 'low'
verbosity = 1

system_thresholds = {
    'cold': 40,
    'warm': 45,
    'hot': 50,
}

cpu_thresholds = {
    'cold': 45,
    'warm': 48,
    'hot': 55,
}

gpu_thresholds = {
    'cold': 45,
    'warm': 50,
    'hot': 60,
}

def gridfan_init():
    ping = subprocess.run(gridfan + " ping", shell=True)

    if (ping.returncode != 0):
        return subprocess.run(gridfan + " init", shell=True, check=True)


def set_fans(fans, speed):
    cmd = gridfan + " set fans " + ' '.join(map(str,fans)) + " speed " + str(speed)
    try:
        fan = subprocess.run(cmd, shell=True)
        if (fan.returncode == 0):
            return True
        return False
    except (OSError, ValueError, CalledProcessError, TimeoutExpired, SubprocessError) as err:
        print('Error while trying to set fans', err)
        return False
    #print([gridfan, 'set', 'fans', fans, 'speed', speed])
    #sys.stdout.flush() #systemd journal

def check_temps():
    global temperatures    # If anyone gets above hot, go to high state

    temperatures = {
        #'System': float(psutil.sensors_temperatures()['it8622'][1].current), #kernel lacking support for new ryzen chipset
        #'CPU': float(psutil.sensors_temperatures()['it8622'][0].current),
        'System': 0, #kernel lacking support for new ryzen chipset
        'CPU': 0,
        'GPU': float(psutil.sensors_temperatures()['amdgpu'][0].current),
    }

# Main Program

gridfan_init()

while True:
    check_temps()

    r1 = False
    r2 = False

    # Determine state
    if (temperatures['System'] > system_thresholds['hot']
        or temperatures['CPU'] > cpu_thresholds['hot']
        or temperatures['GPU'] > gpu_thresholds['hot']):
        state = 'high'
    elif (temperatures['System'] > system_thresholds['warm']
        or temperatures['CPU'] > cpu_thresholds['warm']
        or temperatures['GPU'] > gpu_thresholds['warm']):
        state = 'medium'
    elif (temperatures['System'] < system_thresholds['cold']
        and temperatures['CPU'] < cpu_thresholds['cold']
        and temperatures['GPU'] < gpu_thresholds['cold']):
        state = 'low'

    # Attempt set fan if required
    if (previous_state != state):
        print(temperatures)
        sys.stdout.flush() #systemd journal
        print(state)
        sys.stdout.flush() #systemd journal

        gridfan_init()

        if (state == 'high'):
            r1 = set_fans([1,2,3,4,5,6], 80)
            r2 = True
        elif (state == 'medium'):
            r1 = set_fans([2,3,5], 40)
            r2 = set_fans([1,4,6], 60)
        elif (state == 'low'):
            r1 = set_fans([2,3,5], 0)
            r2 = set_fans([1,4,6], 40)

        if (r1 & r2):
            previous_state = state

    # Snooze
    time.sleep(check_interval)
