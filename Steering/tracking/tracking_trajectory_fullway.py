import time
from numpy import angle
import math  
import serial
import pynmea2
import utm 
import csv 
import pandas as pd 
import numpy as np 
import os
import can

#====== Port conection =============
port1 = "COM38"                                 #port usb that connect rover in your computer for gnss f9p
# port2 = "COM17"                                 #port usb that connect steering rs232
ser = serial.Serial(port1, baudrate = 115200)    
# ser2 = serial.Serial(
#     port2, 
#     baudrate = 115200,
#     parity = serial.PARITY_NONE,
#     stopbits = serial.STOPBITS_ONE,
#     bytesize = serial.EIGHTBITS
# )
# ser2.isOpen()

#======Param variable ==============
# WAYPOINTS_file = 'refLinear_utm.csv'            #put file record waypoint that reference for tracking 
WAYPOINTS_file = pd.read_csv('/home/autonomous/car_ws/src/autonomous_v/src/tracking/ref3_20_round_1.csv')
L = 1.68                                        #m wheel base of vehicle
Kp = 52                                         #best tune in linear waypoint kp ki kd == 50 0.21 18
Ki = 0.18                                       #best tune in linear_Curve waypoint kp ki kd == 
Kd = 18                                                                                                                                                                                                                                                   #not tune
sum_error_cte=0
prev_error_cte=0
error_positive_negative=0
yaw_expect=0
yaw_control =0
#=====================================================================================================#
def cte_current(x_car,y_car,A,B,C):
    cross_track_error = abs((A*x_car)+(B*y_car)+C)/math.sqrt(A**2+B**2)

    return cross_track_error

def cte_positive_negative(y_east,error_cte):
    r = y_east
    
    #======== Linear North to East linear1 =========== move forward on north 150xxx decrease //cte on 661xxx
    global error_positive_negative,cte_previous
    
    cte_previous = error_positive_negative
    
    if y_east >= 661487.3613 and  y_east <= 661487.4377 :      #cte range 0.77m -1.226195m      เริ่มตรง - สุดท้าย
        error_positive_negative = error_cte
    elif y_east<= 661487.4377 and y_east >=  661487.2793:    #cte 0.85m - -1.283984 m           สุดทางตรง - เริ่มโค้ง
        error_positive_negative = (-1)*error_cte    
    
    # !! Curve !!
        #======== Linear2 North to east =========== move forward on north 150xxx cte on 661xxx
    if y_east >= 661485.2925 and  y_east <= 661487.0427:      #cte range 0.77m -1.226195m   เริ่มเอียงซ้าย-ซ้ายสูงสุด
        error_positive_negative = error_cte
    elif y_east<= 661484.0059  and y_east >=  661483.3563:    #cte 0.85m - -1.283984 m      เริ่มเอียงขวา-ขวาสูงสุด
        error_positive_negative = (-1)*error_cte
        #======== Linear3 North to east ===========
    if y_east >= 661485.2925 and  y_east <= 661487.0427:      #cte range 0.77m -1.226195m   เริ่มเอียงซ้าย-ซ้ายสูงสุด
        error_positive_negative = error_cte
    elif y_east<= 661484.0059  and y_east >=  661483.3563:    #cte 0.85m - -1.283984 m      เริ่มเอียงขวา-ขวาสูงสุด
        error_positive_negative = (-1)*error_cte
        
    #!!! Curve to linear !!!
    #======== Linear4 west to east =========== move forward on east 660xx increase // cte with north sourth 150xxx
    if y_east >= 1509586.6563329294 and  y_east <= 1509588.8436516593:      #cte+ range 0.77m -1.226195m
        error_positive_negative = error_cte
    elif y_east<= 1509586.3165312603 and y_east >= 1509584.0089640797:    #cte- 0.85m - -1.283984 m
        error_positive_negative = (-1)*error_cte
        
    return error_positive_negative
    
 
#    #======== Linear North to East =========== move forward on north 150xxx decrease //cte on 661xxx
#     global error_positive_negative,cte_previous
#     cte_previous = error_positive_negative
#     if y_east >= 661486.90607257 and  y_east <= 661488.9361700793 :      #cte range 0.77m -1.226195m
#         error_positive_negative = error_cte
#     elif y_east<= 661486.7770239009 and y_east >=  661485.0655856021:    #cte 0.85m - -1.283984 m
#         error_positive_negative = (-1)*error_cte
#     # else:
#     #     error_positive_negative = error_cte
    
#     # !! Curve !!
#         #======== Linear2 North to east =========== move forward on north 150xxx cte on 661xxx
#     if y_east >= 661486.90607257 and  y_east <= 661488.9361700793 :      #cte range 0.77m -1.226195m
#         error_positive_negative = error_cte
#     elif y_east<= 661486.7770239009 and y_east >=  661485.0655856021:    #cte 0.85m - -1.283984 m
#         error_positive_negative = (-1)*error_cte
#         #======== Linear3 North to east ===========
#     if y_east >= 661486.90607257 and  y_east <= 661488.9361700793 :      #cte range 0.77m -1.226195m
#         error_positive_negative = error_cte
#     elif y_east<= 661486.7770239009 and y_east >=  661485.0655856021:    #cte 0.85m - -1.283984 m
#         error_positive_negative = (-1)*error_cte
          
#     #!!! Curve to linear !!!
#     #======== Linear4 west to east =========== move forward on east 660xx increase // cte with north sourth 150xxx
#     if y_east >= 1509586.6563329294 and  y_east <= 1509588.8436516593 :      #cte+ range 0.77m -1.226195m
#         error_positive_negative = error_cte
#     elif y_east<= 1509586.3165312603 and y_east >=  1509584.0089640797:    #cte- 0.85m - -1.283984 m
#         error_positive_negative = (-1)*error_cte
        
#     return error_positive_negative

def Previous_state():
    
    return cte_previous

def pid_angle(cte_p_n,cte_prev):
    global sum_error_cte
    global yaw_expect,prev_error_cte,yaw_previous
    yaw_previous = yaw_expect
    sum_error_cte += cte_p_n 
    #=============================                         #error range [-1.28,1.28] yaw output [-300,300] so gain [-234,234]
    P = Kp*cte_p_n
    I = Ki*sum_error_cte
    D = Kd*((cte_p_n-cte_prev))
    yaw_expect = -1*(P+D+I)
    
    
    return yaw_expect
    
def Control(self):

    os.system('sudo ifconfig can0 down')
    os.system('sudo ip link set can0 type can bitrate 250000')
    os.system("sudo ifconfig can0 txqueuelen 250000")
    os.system('sudo ifconfig can0 up')

    self.can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan')
    self.msg_init = can.Message(arbitration_id=0x06000001, data=[0x23,0x0d,0x20,0x01,0x00,0x00,0x00,0x00])
    self.can0.send(self.msg_init)
    # time.sleep(1)

    print("Message sent on Enable state data: {}".format(self.msg_init)) 
         
    while not self.can0.shutdown():
        print("Angle_sent: %s",self.agn)         
        self.Sent(self.agn)

def Sent(self,msg):                                       

    self.elec_angle_dec = self.agn*27
    # rospy.loginfo("Electrical angle (Dec) = ",self.elec_angle_dec)

    self.elec_angle_hex = ('{:0>8X}'.format(int(self.elec_angle_dec) & (2**32-1)))       #i = 45 = 45*27 = 1215, --> data = 000004BF(hex)
    #print('Electrical Angle (Hex) = ',self.elec_angle_hex)
    
    DATA_Hh = ((int(self.elec_angle_hex[0:2],16))) #0x00 #0xFF
    DATA_Hl = ((int(self.elec_angle_hex[2:4],16))) #0x00 #0xFF
    DATA_Lh = ((int(self.elec_angle_hex[4:6],16)))
    DATA_Ll = ((int(self.elec_angle_hex[6:8],16)))

    #print("Electrical Angle (Dec of 2 Byte Hex Data low) = : ",(DATA_Lh), (DATA_Ll), (DATA_Hh), (DATA_Hl))

    self.msg_sent = can.Message(arbitration_id=0x06000001, data=[0x23, 0x02, 0x20, 0x01, (DATA_Lh), (DATA_Ll), (DATA_Hh), (DATA_Hl)])
    print("Message sent on data frame: %s",self.msg_sent)
    self.can0.send(self.msg_sent)     
 
def Previous_state_yaw():
    
    return yaw_previous

def angle_controlMotor(cte_pos_neg,yaw_expect,yaw_prev):
    global yaw_control 
    if cte_pos_neg > 0.15 :
        yaw = abs(yaw_expect - yaw_prev)
        if yaw >= 0.25:
            yaw_control = yaw_expect
       

    elif cte_pos_neg < -0.15:
        yaw = abs(yaw_expect - yaw_prev)
        if yaw >= 0.25:
            yaw_control = yaw_expect
       
    # else:
    #     yaw_control = 5 
                                       #cte + left side yaw -   and cte - right side yaw +
    return yaw_control

if __name__ == '__main__':
    #=============Serial position from rover =================================
    while True:
        data = ser.readline()                           #output = b'$GNGGA,173534.70,1339.04546,N,10029.60344,E,1,12,0.56,6.3,M,-27.8,M,,*63\r\n'
        gngga_data = data.split(b",")
        if gngga_data[0] == b"$GNGGA":
            newmsg=pynmea2.parse(data.decode("utf-8"))
            lat=newmsg.latitude                         #get data from gnss is latitude and longtitude
            lng=newmsg.longitude
            gps = lat,lng
            xy = utm.from_latlon(lat,lng)               #convert data lat lng to utm-xy 
            x_north = xy[1]                             #for check cte 
            y_east = xy[0]                              #for track forward linear
            utem_position = x_north,y_east              #forward move in x-axis north 1509602 data is decease , check error on y-axis east 661487
    #===========================================================================
            # start_time = time.time()                    #บอกเวลา
            # print("time : ", (time.time()-start_time)*1000) #unit = millisecond ไว้บอกเวลาที่ใช้ไปทั้งหมด
    #=== import file path reference to compute====================
            a1,b1,c1 =  -0.0015632756, -1, 663847.0633094484       # linear1 52m -0.0015632756107706199 -1 663847.0633094484
            a2,b2,c2 =  -0.1754903706, -1, 926407.5688121466       ##linear with Curve1 equation of Curve 6.918949 m  -0.1754903706433879 -1 926407.5688121466
            a3,b3,c3 =  -0.9479336077, -1 ,2092481.2061952758      ##linear with Curve2 equation of Curve 7.122931 m -0.9479336077039751 -1 2092481.2061952758
            a4,b4,c4 =  0.006923016, -1 ,1505006.8807523265        #linear2   distance4 is 23.908760 m on east-axis define y1509586.450772019, x661496.8112426052 //0.00692301632478863 -1 1505006.8807523265
    # #cal CTE Condition to select linear Equation
            if x_north <= 1509653.4323676503 and x_north  >= 1509602.340385789:       #car on linear1 move on north to sourth
                error_current1 = cte_current(x_north,y_east,a1,b1,c1)
                cte_pos_neg = cte_positive_negative(y_east,error_current1)    #data can tell cte + -
                ##Curve1##  start min (1509602.0818160048, 661487.0682533941)  stop max (1509591.2600646394, 661487.3151340398) // left 
            if x_north  <= 1509602.3403857893 and x_north >=1509591.2600646394  :       #car on linear1 move on north to sourth
                error_current2 = cte_current(x_north,y_east,a2,b2,c2)
                cte_pos_neg = cte_positive_negative(y_east,error_current2)
                ##Curve2##  max n to s(1509586.3371194396, 661487.3273840717) // on east start (1509586.4012525694, 661494.7559586521)
            if x_north  <= 1509602.0818160048 and x_north >= 1509586.3371194396 and y_east <= 661496.8112426052:       #car on linear1 move on north to sourth
                error_current3 = cte_current(x_north,y_east,a3,b3,c3)
                cte_pos_neg = cte_positive_negative(y_east,error_current3)

            if y_east <= 661496.8112426052:         # if >y  car that on y_east linear2 forward west to east
                error_current4 = cte_current(x_north,y_east,a4,b4,c4)
                cte_pos_neg = cte_positive_negative(y_east,error_current4)
    # # store data previous
            cte_prev = Previous_state()
    # #Cal yaw angle that expect from PID controller
            yaw_expect = pid_angle(cte_pos_neg,cte_prev)
            yaw_prev = Previous_state_yaw()
            yaw_controlSteering = angle_controlMotor(cte_pos_neg,yaw_expect,yaw_prev)
            #print(cte_pos_neg,yaw_controlSteering)

            #======= For write data to file CSV ========================
            test_see = cte_pos_neg,yaw_controlSteering
            
            df = csv.writer('/home/autonomous/car_ws/src/autonomous_v/src/tracking/see_dataPrint.csv')
            df.writerow(test_see)
            
            # with open('/home/autonomous/car_ws/src/autonomous_v/src/tracking/see_dataPrint.csv', 'a', newline='') as f:  
            #     writer = csv.writer(f,delimiter=",")    
            #     writer.writerow(test_see) 

    # #===========input data yaw angle (degree) for control Steering Motor=============
            
            #steer_input(yaw_controlSteering)
            

           