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
from os import path, popen
import scipy.optimize as optimize
import sqlite3 as sql
import signal

def connect_db(filename):
    if filename[-3:]!=".db":
        filename += ".db"
    filename = path.normpath(filename)
    calibration_dir = path.normpath("calibration")
    filepath = path.join(calibration_dir, filename)
    return sql.connect(filepath) # create db

def setup_calibration(filename):
    """Initial setup of the calibration db"""
    # add file extension if not there
    if filename[-3:]!=".db":
        filename += ".db"
    ilename = path.normpath(filename)
    calibration_dir = path.normpath("calibration")
    # create directory if it does not exist
    if not path.exists(calibration_dir):
        makedirs(calibration_dir)
    # create filepath
    filepath = path.join(calibration_dir, filename)

    # does db already exist, if not, create db.
    if path.isfile(filepath): 
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

##def write_to_calibration(That, Tpi, Treal, filename="calibration"):
##    """Write pihat and input temperature"""
##    db = connect_db(filename)
##    datetime = dt.datetime.now()
##    db.cursor()
##    values = (datetime, That, Tpi, Treal)
##    db.execute("INSERT INTO calibration VALUES (?,?,?,?)", values)
##    db.commit()
##    db.close()

def read_all_calibration(filename="calibration"):
    """Read all calibration data"""
    db = connect_db(filename)
    db.cursor()
    values = db.execute("SELECT * FROM calibration").fetchall()
    db.close()
    return values

def readAvgTempCalibration(filename="calibration.db"):
    """Returns userT and piAvgT from calibration file"""
    x = []
    y = []
    db = connect_db(filename)
    db.cursor()
    try:
        values = db.execute("SELECT Tavg, Treal FROM calibration").fetchall()
        for row in values:
            x.append(row[0])
            y.append(row[1])
    except ValueError:
        print ("Calibration database empty")
    db.close()
    return x, y

def readHumCalibration(filename="calibration"):
    """Returns userT and piAvgT from calibration file"""
    piH = []
    realH = []
    db = connect_db(filename)
    db.cursor()
    try:
        values = db.execute("SELECT Hum, Hreal FROM calibration").fetchall()
        for row in values:
            piH.append(row[0])
            realH.append(row[1])
    except ValueError:
        print ("Calibration database empty")
    db.close()
    return [piH, realH]

def polyfit_3(x, y):
    if len(x) > 9: # what min values of points makes 3rd order ok?
        fit = np.polyfit(x, y, 3)
    elif len(x) == 0: # no calibration data, just return x
        fit = np.poly1d([1,0])
    else:
        # too few points, use linear
        fit = np.polyfit(x, y, 1)
    fit_object = np.poly1d(fit)
    return fit_object


## pihat environment ##

def getpitemp():
    """Gets the temperature of the Pi chip"""
    resline=popen("vcgencmd measure_temp").readline()
    res = resline.replace("temp=","").replace("'C\n","")
    return(float(res))

def getenvirodata(senseHat):
    """Gets temp from humidity and pressure, and humidity and pressure"""
    ht=senseHat.get_temperature()
    pt=senseHat.get_temperature_from_pressure()
    hu=senseHat.get_humidity()
    pr=senseHat.get_pressure() #in millibar

    return ht,pt,hu,pr

def printenvirodata(senseHat, Tem, Hum, Pres):
    r = (255, 0, 0)
    g = (0, 255, 0)
    b = (0, 0, 255)
    senseHat.low_light = True
    if Tem != None:
        if Tem >= 25:
            senseHat.show_message("T= " + str(round(Tem,1)),
                                  scroll_speed = 0.07,
                                  text_colour = r)
        if 19 < Tem < 25:
            senseHat.show_message("T= " + str(round(Tem,1)),
                                  scroll_speed = 0.07,
                                  text_colour = g)
        if Tem <= 19:
            senseHat.show_message("T= " + str(round(Tem,1)),
                                  scroll_speed = 0.07,
                                  text_colour = b)
    if Hum!=None:
        senseHat.show_message("H= " + str(round(Hum,1)),
                              scroll_speed = 0.07)
    if Pres!=None:
        senseHat.show_message("P= " + str(round(Pres,1)),
                              scroll_speed = 0.07)
    senseHat.low_light=False
    return


def run(interval = 30, total_time = 120, display=True):
    """
    Run program

    Input
    -----
    interval: float.
        time between readings.

    total_time: float.
        Maximum time of experiment
    """
    # initial run often returns 0
    sense = SenseHat()
    htemp,ptemp,humidity,pressure = getenvirodata(sense) 
    chiptemp = getpitemp()

    start_time = time.time()

    # get calibration fits
    [piT, realT] = readAvgTempCalibration()
    Tfit = polyfit_3(piT, realT)

    [piH, realH] = readHumCalibration()
    Hfit = polyfit_3(piH, realH)

    # loop until quit
    
    while ((time.time()-start_time) < total_time):
        t_now = time.time()
        # measure temperature
        htemp,ptemp,humidity,pressure = getenvirodata(sense) 
        chiptemp = getpitemp()
        avg_piT = np.divide((htemp + ptemp),2)
        temp = np.around(Tfit(avg_piT),1)
        print("T: " + str(temp))
        humid = np.around(Hfit(humidity),1)
        print("H: " + str(humid))
        if display:
            printenvirodata(sense, temp, humid, pressure)
        time.sleep(interval - (time.time() - t_now))

def setup_run():
    while True:
        try:
            total_time = input("Total time (s): ")
            if total_time == "":
                total_time = 120
            total_time = int(total_time)
            if total_time <= 0:
                print("Invalid time")
                raise
            break
        except:
            continue
                             
    while True:
        try:
            interval = input("Intervale(s): ")
            if interval == "":
                interval = 30
            interval= int(interval)
            if ((interval <= 0) or (interval>total_time)):
                print("Invalid Interval")
                raise
            break
        except:
            continue
                             
    run(interval = interval, total_time = total_time, display=True)

if __name__ == "__main__":
##    [x, y] = readAvgTempCalibration()
##    Tfit = polyfit_3(x, y)
##    print(Tfit(x[0]))
#    run()
    setup_run()