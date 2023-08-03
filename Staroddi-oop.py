#!/usr/bin/env python3
import serial
import logging,csv
from datetime import datetime

def now():
    return datetime.now().isoformat().replace(':','')[:-7]

class staroddi:
    #Calibration Constants
    #Temperature
    Tc0=137.210166872518
    Tc1=-0.183332418015418
    Tc2=0.00015708789289189
    Tc3=-8.22634930412193E-8
    Tc4= 2.23922024886135E-11
    Tc5=-2.55368930401915E-15
    #Pressure
    Pc0=-28.098691186332
    Pc1=0.0841268734871915
    Pc2=1.49909737216056E-6
    Pc3=-7.52418875342399E-10
    Pc4=1.41966472969949E-13
    Pc5=-9.24169810009204E-18
    #Pressure Temperature Correction
    PtC1=-1.17814498824353
    PtC2= 0.115440105414346
    PtC3=-0.00717023213872395
    PtC4= 0.000176332306255193
    PtC5=-1.5366028019708E-6
    #Pressure Temperature calibration reference
    Tpr=21.2977901891416
    #Conductivity
    CondC0=271.189887316909
    CondC1=-0.614045003449875
    CondC2=0.000732414521026033
    CondC3=-5.11435241542634E-7
    CondC4=2.16451102332944E-10
    CondC5=-5.46467725982402E-14
    CondC6=7.56799969612034E-18
    CondC7=-4.42192064674217E-22
    #Conductivity Temperature Correction Low
    CtcC1=-1.44453249281451
    CtcC2=-0.0848917808771628
    CtcC3=0.00479042710477045
    CtcC4=-0.000118002968547826
    CtcC5=1.11071512305244E-6
    #Conductivity Temperature Correction High
    Ctc1C1=-3.14472666811779
    Ctc1C2=0.0536356144176906
    Ctc1C3=-0.00506830666117654
    Ctc1C4=0.000153810635302959
    Ctc1C5=-1.50470651035196E-6

    Tcr=26.83   #Conductivity Temerature calibration reference
    L=1188      #Conductivity Low loadrange inner value
    H=3020      #COnductivity High load range inner value

    #salinity constants
    a0 = 0.008
    a1 =-0.1692
    a2 = 25.3851
    a3 = 14.0941
    a4 = -7.0261
    a5 = 2.7081
    b0 = 0.0005
    b1 = -0.0056
    b2 = -0.0066
    b3 = -0.0375
    b4 = 0.0636
    b5 = -0.0144
    k = 0.0162
    A1 = 2.070E-5
    A2 = -6.370E-10
    A3 = 3.989E-15
    B4 = -3.107E-3
    B1 = 3.426E-2
    B2 = 4.464E-4
    B3 = 4.215E-1
    c0 = 6.766097E-1
    c1 = 2.00564E-2
    c2 = 1.104259E-4
    c3 = -6.9698E-7
    c4 = 1.0031E-9
    Temp=[]
    Depth=[]
    Sal=[]
    state=True
    
    def __init__(self):
        self.ser=serial.Serial(baudrate=4800, bytesize=8, stopbits=serial.STOPBITS_ONE, timeout=2,)
        #self.ser.port='COM5'             #windows
        self.ser.port='/dev/ttyUSB0'    #pi
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO,format='%(asctime)s: %(levelname)s  %(message)s')
        
    def connection(self):
        self.ser.open()
        self.ser.write(serial.to_bytes([0x00]))      #wake up
        self.ser.readline()                 #takes output from sensor
        self.ser.write(serial.to_bytes([0x0c]))      #set to computer mode
        self.ser.readline()
    
    def datacollection(self):
        self.ser.write(serial.to_bytes([0x02]))
        self.ser.readline()
        self.ser.write(serial.to_bytes([0x55]))
        output=self.ser.readline()
        if len(output)==6:
            self.tl=output[0]
            self.th=output[1]
            self.pl=output[2]
            self.ph=output[3]
            self.cl=output[4]
            self.ch=output[5]
            
    def calculation(self):
        T=self.tl+self.th*256
        P=self.pl+self.ph*256
        C=self.cl+self.ch*256
        
        #conversion to units
        #Temp
        Tv=self.Tc0+(self.Tc1*T)+(self.Tc2*T**2)+(self.Tc3*T**3)+(self.Tc4*T**4)+(self.Tc5*T**5) #Degrees Celcius
        
        #Pressure
        Pc=P+(self.PtC1*self.Tpr)+(self.PtC2*self.Tpr**2)+(self.PtC3*self.Tpr**3)+(self.PtC4*self.Tpr**4)+(self.PtC5*self.Tpr**5)-((self.PtC1*Tv)+(self.PtC2*Tv**2)+(self.PtC3*Tv**3)+(self.PtC4*Tv**4)+(self.PtC5*Tv**5))
        Pv=self.Pc0+(self.Pc1*Pc)+(self.Pc2*Pc**2)+(self.Pc3*Pc**3)+(self.Pc4*Pc**4)+(self.Pc5*Pc**5)
        
        D=Pv*10.19716/1.026     #   10.19716=gravity conversion constant   1.026=seawater density
        
        #Conductivity
        Cc0= C+(self.CtcC1*self.Tcr)+(self.CtcC2*self.Tcr**2)+(self.CtcC3*self.Tcr**3)+(self.CtcC4*self.Tcr**4)+(self.CtcC5*self.Tcr**5)-((self.CtcC1*Tv)+(self.CtcC2*Tv**2)+(self.CtcC3*Tv**3)+(self.CtcC4*Tv**4)+(self.CtcC5*Tv**5))
        Cc1=C+(self.Ctc1C1*self.Tcr)+(self.Ctc1C2*self.Tcr**2)+(self.Ctc1C3*self.Tcr**3)+(self.Ctc1C4*self.Tcr**4)+(self.Ctc1C5*self.Tcr**5)-((self.Ctc1C1*Tv)+(self.Ctc1C2*Tv**2)+(self.Ctc1C3*Tv**3)+(self.Ctc1C4*Tv**4)+(self.Ctc1C5*Tv**5))
        A=(Cc1-Cc0)/(self.H-self.L)
        B=Cc0-A*self.L
        Cc=B+A*C
        Cv=self.CondC0+(self.CondC1*Cc)+(self.CondC2*Cc**2)+(self.CondC3*Cc**3)+(self.CondC4*Cc**4)+(self.CondC5*Cc**5)+(self.CondC6*Cc**6)+(self.CondC7*Cc*7)
        
        Pvda=abs(Pv*10)
        
        R=Cv/42.914
        RP=1+(self.A1*Pvda+self.A2*Pvda**2+self.A3*Pvda**3)/(1+self.B1*Tv+self.B2*Tv**2+self.B3*R+self.B4*Tv*R)
        rT=self.c0+self.c1*Tv+self.c2*Tv**2+self.c3*Tv**3+self.c4*Tv**4
        RT=R/(rT*RP)
        S=self.a0+self.a1*RT**.5+self.a2*RT+self.a3*RT**1.5+self.a4*RT**2+self.a5*RT**2.5+(Tv-15)/(1+self.k*(T-15))*(self.b0+self.b1*RT**.5+self.b2*RT+self.b3*RT**1.5+self.b4*RT**2+self.b5*RT**2.5)
        
        #print ("%.2f" % Tv,'°C',"%.2f" % D,'m',"%.2f" % S,'psu')
        logging.info('%.2f °C, %.2f m, %.2f psu', Tv, D, S)
        #logging.info("%.2f" % Tv,'°C',"%.2f" % D,'m',"%.2f" % S,'psu')
        
    def end(self):
        self.ser.close()
        
    def run(self):
        try:
            self.connection()
            while self.state:
                self.datacollection()
                self.calculation()
            self.end()
        except KeyboardInterrupt:
            self.end()
            
            
staroddi().run()
