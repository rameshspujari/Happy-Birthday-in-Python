import RPi.GPIO as GPIO
import sys,time
import signal
import subprocess
import json
import threading
import syslog
import os

debug_mode = False
conf_dir = "./conf/"
pipeout = os.open("rfidtest", os.O_WRONLY)

def initialize():
    GPIO.setmode(GPIO.BCM)
#    report("Initializing")
    read_configs()
    setup_readers()
    # Catch some exit signals

def debug(message):
    if debug_mode:
        print message

def read_configs():
    global zone, users, config, locker, lockerzone
    config = load_json(conf_dir + "config.json")

def setup_readers():
    global zone_by_pin
    for name in iter(config):
        if name == "<zone>":
            continue
        if (type(config[name]) is dict and config[name].get("d0")
                                       and config[name].get("d1")):
            reader = config[name]
            reader["stream"] = ""
            reader["timer"] = None
            reader["name"] = name
            reader["unlocked"] = False
            zone_by_pin[reader["d0"]] = name
            zone_by_pin[reader["d1"]] = name
            GPIO.setup(reader["d0"], GPIO.IN)
            GPIO.setup(reader["d1"], GPIO.IN)
            GPIO.add_event_detect(reader["d0"], GPIO.FALLING,
                                  callback=data_pulse)
            GPIO.add_event_detect(reader["d1"], GPIO.FALLING,
                                  callback=data_pulse)

def load_json(filename):
    file_handle = open(filename)
    config = json.load(file_handle)
    file_handle.close()
    return config

def data_pulse(channel):
    reader = config[zone_by_pin[channel]]
    if channel == reader["d0"]:
        reader["stream"] += "0"
    elif channel == reader["d1"]:
        reader["stream"] += "1"
    kick_timer(reader)

def kick_timer(reader):
    if reader["timer"] is None:
        reader["timer"] = threading.Timer(0.2, wiegand_stream_done,
                                          args=[reader])
        reader["timer"].start()

def wiegand_stream_done(reader):
    if reader["stream"] == "":
        return
    bitstring = reader["stream"]
    reader["stream"] = ""
    reader["timer"] = None
    validate_bits(bitstring)

def validate_bits(bstr):
    print bstr
    if len(bstr) != 35:
        debug("Incorrect string length received: %i" % len(bstr))
        debug(":%s:" % bstr)
        return False
    lparity = int(bstr[2])
    facility = int(bstr[2:14], 2)
    print "facility = ",facility
    user_id = int(bstr[14:34], 2)
    print "card code = ",user_id
    user_id = str(user_id)+ "\n"
    try:
		os.write(pipeout, user_id)
    except IOError:
		pass

    rparity = int(bstr[34])

# Globalize some variables for later
zone = None
users = None
config = None
locker = None
last_name = None
lockerzone = None
zone_by_pin = {}
repeat_read_count = 0
repeat_read_timeout = time.time()

initialize()
while True:
    # The main thread should open a command socket or something
    time.sleep(1000)
