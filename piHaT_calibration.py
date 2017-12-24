"""
piHaT
A program to measure and display the humidity and
temperature using a RaspberryPi2 and sensehat.
Author: Scot Wheeler
"""
__version__ = 2.0

from sense_hat import SenseHat
import time
import datetime as dt
import numpy as np
import os
import scipy.optimize as optimize
import sqlite3 as sql
import signal

## calibration database ##

def connect_db(filename):
    if filename[-3:]!=".db":
        filename += ".db"
    calibration_dir = "/home/pi/piHaT/calibration/"
    filepath = os.path.normpath(calibration_dir
                                + filename)
    return sql.connect(filepath) # create db

def setup_calibration(filename):
    """Initial setup of the calibration db"""
    # add file extension if not there
    if filename[-3:]!=".db":
        filename += ".db"
    calibration_dir = "/home/pi/piHaT/calibration/"
    # create directory if it does not exist
    if not os.path.exists(calibration_dir):
        os.makedirs(calibration_dir)
    # create filepath
    filepath = os.path.normpath(calibration_dir
                                + filename)

    # does db already exist, if not, create db.
    if os.path.isfile(filepath): 
        print("Calibration file exists")
        db = connect_db(filename)
    else:
        print("Creating calibration file")
        db = sql.connect(filepath) # create db
    # does calibration table exist?
     
    db.cursor()
    db.execute("""
                CREATE TABLE IF NOT EXISTS calibration (
                    datatime TIMESTAMP,
                    Thum FLOAT,
                    Tpres FLOAT,
                    Tavg FLOAT,
                    Tpi FLOAT,
                    Hum FLOAT,
                    Treal FLOAT,
                    Hreal FLOAT
                    )
                """)
    db.commit()
    db.close()       
    
    return

def recreate_calibration(filename="calibration"):
    db = connect_db(filename)
    db.cursor()
    db.execute("DROP TABLE calibration")
    db.commit()
    db.close()
    setup_calibration(filename)
    print("Calibration database has been reset")

def write_to_calibration(Thum, Tpres, Tavg, Tpi, Hum,
                         Treal, Hreal,
                         filename="calibration"):
    """
    Write pihat and input temperature
    """
    db = connect_db(filename)
    datetime = dt.datetime.now()
    db.cursor()
    values = (datetime, Thum, Tpres, Tavg, Tpi, Hum, Treal, Hreal)
    db.execute("INSERT INTO calibration VALUES (?,?,?,?,?,?,?,?)", values)
    db.commit()
    db.close()
    print("Write to database successful")

def read_all_calibration(filename="calibration"):
    """Read all calibration data"""
    db = connect_db(filename)
    db.cursor()
    values = db.execute("SELECT * FROM calibration").fetchall()
    db.close()
    return values

## pihat environment ##

def getpitemp():
    """Gets the temperature of the Pi chip"""
    resline=os.popen("vcgencmd measure_temp").readline()
    res = resline.replace("temp=","").replace("'C\n","")
    return(float(res))

def getenvirodata(senseHat):
    """Gets temp from humidity and pressure, and humidity and pressure"""
    ht=senseHat.get_temperature()
    pt=senseHat.get_temperature_from_pressure()
    hu=senseHat.get_humidity()
    pr=senseHat.get_pressure() #in millibar

    return ht,pt,hu,pr

def new_calibration():
    setup_calibration("calibration")
    while True:
        userT = input("Input current temperature: ")
        try:
            userT = float(userT)
            break
        except:
            print("Not a valid number")
    while True:
        userH = input("Input current humidity: ")
        try:
            userH = float(userH)
            break
        except:
            print("Not a valid number")

    # initial run often returns 0
    sense = SenseHat()
    htemp,ptemp,humidity,pressure = getenvirodata(sense) 
    chiptemp = getpitemp()

    # get pi data
    htemp,ptemp,humidity,pressure = getenvirodata(sense) 
    chiptemp = getpitemp()
    avg_piT = np.divide((htemp + ptemp),2)

    # update calibration database
    write_to_calibration(htemp,ptemp, avg_piT, chiptemp, humidity,
                         userT, userH)

    
            




if __name__ == "__main__":
    new_calibration()
##    recreate_calibration()
##    print(read_all_calibration())
    pass
