#!/usr/bin/env python
import subprocess
import time

gridfan = '/usr/local/bin/gridfan'
check_interval = 60
state = 'low'
verbosity = 1

system_thresholds = {
    'cold': 35,
    'warm': 40,
    'hot': 45,
}

cpu_thresholds = {
    'cold': 35,
    'warm': 40,
    'hot': 50,
}

gpu_thresholds = {
    'cold': 30,
    'warm': 35,
    'hot': 40,
}

def set_fans(fans, speed):
    cmd = gridfan + " set fans " + ' '.join(map(str,fans)) + " speed " + str(speed)
    subprocess.call(cmd, shell=True)
    #print [gridfan, 'set', 'fans', fans, 'speed', speed]

def check_temps():
    global temperatures
    output = subprocess.check_output(['sensors', '-u']);
    sensors = {}
    for item in output.split("\n"):
        sensor = item.strip().split(":")
        if len(sensor) > 1:
            if sensor[1] != '':
                sensors[sensor[0]] = sensor[1].strip()
    output = subprocess.check_output('nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits', shell=True)
    temperatures = {
        'System': float(sensors['temp1_input']),
        'CPU': float(sensors['temp2_input']),
        'GPU': float(output),
    }
    if verbosity > 0:
        print temperatures

while True:
    check_temps()

    # If everybody has cooled down, go to the low state
    if (temperatures['System'] < system_thresholds['cold']
        and temperatures['CPU'] < cpu_thresholds['cold']
        and temperatures['GPU'] < gpu_thresholds['cold']
        and state != 'low'):
        set_fans([1,2,3], 0)
        set_fans([4,5], 50)
        state = 'low'
    # If everybody has cooled down to warm, go to the medium state
    elif (temperatures['System'] < system_thresholds['warm']
        and temperatures['CPU'] < cpu_thresholds['warm']
        and temperatures['GPU'] < gpu_thresholds['warm']
        and state != 'low'):
        set_fans([1,2,3], 0)
        set_fans([4,5], 50)
        state = 'medium'
    # If anyone gets above warm, go to medium state
    elif (temperatures['System'] > system_thresholds['warm']
        or temperatures['CPU'] > cpu_thresholds['warm']
        or temperatures['GPU'] > gpu_thresholds['warm']
        and state != 'medium'):
        set_fans([1,2,3], 75)
        set_fans([4,5], 50)
        state = 'medium'
    # If anyone gets above hot, go to high state
    elif (temperatures['System'] > system_thresholds['hot']
        or temperatures['CPU'] > cpu_thresholds['hot']
        or temperatures['GPU'] > gpu_thresholds['hot']
        and state != 'high'):
        set_fans([1,2,3], 100)
        set_fans([4,5], 100)
        state = 'high'

    # Snooze
    time.sleep(check_interval)
