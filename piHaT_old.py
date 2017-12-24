###display temperature on sense###
from sense_hat import SenseHat
sense=SenseHat()
from pixelcolours import *
import snumbers as snum
import time
import numpy as np
import os

totaltime=float(input("Enter total run time in seconds: ")) #total time for the experiment
filename=input("Enter a file name: ")
printQ=" "
while printQ not in ["y","n"]:
    printQ=input("Would you like to enable hat display? y or n: ")
    printQ=printQ.lower()

filepath="/home/pi/"+filename+".txt"


tsign=[
    e,e,e,e,w,e,e,e,
    w,w,w,e,e,e,e,e,
    e,w,e,e,e,w,w,w,
    e,w,e,e,e,w,e,e,
    e,w,e,e,e,w,e,e,
    e,w,e,e,e,w,w,w,
    e,e,e,e,e,e,e,e,
    e,e,e,e,e,e,e,e
    ]
initialtime=time.time()
np_Pitemp=np.array([])
np_temp=np.array([])
np_ptemp=np.array([])
np_humidity=np.array([])
np_pressure=np.array([])
np_time=np.array([])

def getpitemp():
    """Gets the temperature of the Pi chip"""
    resline=os.popen("vcgencmd measure_temp").readline()
    res=resline.replace("temp=","").replace("'C\n","")
    return(float(res))

def getenvirodata():
    """Gets temp from humidity and pressure, and humidity and pressure"""
    ht=sense.get_temperature()
    pt=sense.get_temperature_from_pressure()
    hu=sense.get_humidity()
    pr=sense.get_pressure() #in millibar
    if pr<1: #sometimes first attempt =0
        pr=sense.get_pressure() #in millibar
        pt=sense.get_temperature_from_pressure()
        
    return ht,pt,hu,pr

def printenvirodata(Tem,Hum,Pres):
    if Tem!=None:
        if Tem>=25:
            sense.show_message("T= "+str(round(Tem,1)),scroll_speed=0.07,text_colour=r)
        if 19<Tem<25:
            sense.show_message("T= "+str(round(Tem,1)),scroll_speed=0.07,text_colour=g)
        if Tem<=19:
            sense.show_message("T= "+str(round(Tem,1)),scroll_speed=0.07,text_colour=b)
    if Hum!=None:
        sense.show_message("H= "+str(round(Hum,1)),scroll_speed=0.07)
    if Pres!=None:
        sense.show_message("P= "+str(round(Pres,1)),scroll_speed=0.07)
    return
i=3
while(time.time()<(initialtime+totaltime+5)):
    starttime=time.time()
                           
    htemp,ptemp,humidity,pressure=getenvirodata()
    chiptemp=getpitemp()

    np_Pitemp=np.append(np_Pitemp,chiptemp)     
    np_time=np.append(np_time,int(time.time()-initialtime))
    np_temp=np.append(np_temp,htemp)
    np_ptemp=np.append(np_ptemp,ptemp)
    np_humidity=np.append(np_humidity,humidity)
    np_pressure=np.append(np_pressure,pressure)
    avgPiT=(np_Pitemp.sum()/len(np_Pitemp))
    TcalcH=np_temp+(0.201*avgPiT)-13.965 
    TcalcP=np_ptemp+(0.145*avgPiT)-9.812
    Tcalc=((TcalcH+TcalcP)/2)-1 #i don't know why it seems to be 1 out
                           
    if i==3 and printQ=="y": #every 4th measurement it prints
        printenvirodata(Tcalc[-1],humidity,pressure)
        i=0
    else:
        i+=1

    print("t="+str(np_time[-1])+
          " Th="+str(round(TcalcH[-1],1))+
          " Tp="+str(round(TcalcP[-1],1))+
          " Tcalc="+str(round(Tcalc[-1],1))+
          " H="+str(round(humidity,1))+
          " P="+str(round(pressure,0)))
    
    medtime=time.time()
    waittime=30-(medtime-starttime)
    time.sleep(waittime)

finaldata=np.array([np_time,Tcalc,np_Pitemp,np_temp,np_ptemp,np_humidity,np_pressure])



np.savetxt(filepath,finaldata,delimiter=",")

    
print("measurement finished")



