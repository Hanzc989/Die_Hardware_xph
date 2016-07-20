from pynq import Overlay

ol = Overlay("audiovideo.bit")
ol.download()

from time import sleep
from pynq.video import Frame, vga
from IPython.display import Image
from pynq.board import Switch
import numpy as np
import time
from pynq.board import Button
import os
import pylab as p
import sys
import cv2 
from pynq.pmods import PMOD_OLED

#oled configuration
oled = PMOD_OLED(1)
stream = ''

# get the Zybo switches
switches = [Switch(i) for i in range(4)]

# monitor configuration
video_out_res_mode = 0 # 640x480 @ 60Hz
frame_out_w = 1920
frame_out_h = 1080

# camera configuration
frame_in_req_w = 300
frame_in_req_h = 300

# initialize camera
videoIn = cv2.VideoCapture(0)
videoIn.set(cv2.CAP_PROP_FRAME_WIDTH, frame_in_req_w);
videoIn.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_in_req_h);

# initialize monitor
videoOut = vga.VGA('out')
resolution = videoOut.mode(video_out_res_mode)
print("selected video resolution: " + resolution)
videoOut.start()
videoOut.frame_index(0)

# initialize support variables
npFrame = np.zeros(frame_out_w*frame_out_h*3, dtype=np.uint8)
frameOut = videoOut.frame(0)
frameCount = 0
start = time.time()
i = 0
acq = 1
c = []
keyboard = cv2.imread("frame/pynq.png")
#keyboard_p = cv2.image("frame/tostiera_p.png")
#keyboard_y = cv2.image("frame/tostiera_y.png")
#keyboard_n = cv2.image("frame/tostiera_n.png")
#keyboard_q = cv2.image("frame/tostiera_q.png")
kern = cv2.imread("frame/temp_rosso.jpg")
shape_kern = kern.shape
row = shape_kern[0]
col = shape_kern[1]
read=0
b, g, r = cv2.split(kern)
kern = r
#for ro in range (0,row):
#    for co in range (0,col):
#        if kern[ro][co]==255:
#            kern[ro][co]=-1
flag=0
################
#print(len(keyboard))
#shape_key = keyboard.shape
#print(shape_key)
try:

    while(True):
        # capture frame
        frame_prev = None
        while(frame_prev is None):
            ret, frame_prev = videoIn.read()
        #print(len(frame_prev))
        #shape = frame_prev.shape
        #print(shape)
        frame = np.concatenate((frame_prev,keyboard), axis=1)
        
        
        if(ret):
            # get frame dimension
            shape = frame.shape
            #print(shape)
            frame_w = shape[1]
            frame_h = shape[0]

                
            # apply requested filters
            zeros = np.zeros(frame_h*frame_w).resize(frame_h,frame_w)
            if(switches[0].read()):
                frame[0:frame_h,0:frame_w,0] = 0
            if(switches[1].read()):
                frame[0:frame_h,0:frame_w,1] = 0
            if(switches[2].read()):
                frame[0:frame_h,0:frame_w,2] = 0
            if(switches[3].read()):
                frame = cv2.Laplacian(frame, cv2.CV_8U) 
                
            cv2.rectangle(frame,(140,110),(210,180),(255,0,0),2)

            
            immaginee = frame[110:180, 140:210]
            b1, g1, r1 = cv2.split(immaginee)
            tmp = cv2.matchTemplate(r1, kern, cv2.TM_CCORR_NORMED)
            tmp = tmp * 254

            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(tmp)
            y_quad = maxLoc[1] + 8
            x_quad = maxLoc[0] + 8
            cv2.circle(frame, (x_quad + 140, y_quad + 110), 1, (255, 0, 0),  2)
            reset=Button(3)
             
            #CALIBRATION
            button = Button(1)
            if button.read() and acq:
                
                b,g,r = cv2.split(frame[110:180,140:210])
                r=cv2.GaussianBlur(r,(5,5),0)
                r=cv2.Laplacian(r,cv2.CV_8U)
                r=cv2.medianBlur(r,3)
            
                circles=cv2.HoughCircles(r,cv2.HOUGH_GRADIENT,2,400,200,10,20)
                for j in circles[0,:]:

                    j[0]=j[0]+140
                    j[1]=j[1]+110
                    cv2.circle(frame,(j[0],j[1]),j[2],(0,0,255),)
                    cv2.circle(frame,(j[0],j[1]),1,(0,255,0),1)
                    c.append([j[0], j[1]])
                dist_init_y = -y_quad + j[1]
                dist_init_x = -x_quad + j[0]
                #x_center_init = j[0]
                flag=1
                cv2.imwrite("output_to_be_processed/frame" + str(i) + ".jpg", frame[110:180,140:210])
                i = i + 1
                if i>0:
                    acq=0
                    cv2.rectangle(frame,(140,110),(210,180),(0,0,255),2)
                while button.read() :
                    sleep(0.000001)
                        
            #ACQUISITION
            button = Button(1)
            if button.read() and not acq:
                cv2.rectangle(frame,(140,110),(210,180),(0,128,128),2)
                quadrante=[1,1,1,1]
                b,g,r = cv2.split(frame[110:180,140:210])
                r=cv2.GaussianBlur(r,(5,5),0)
                r=cv2.Laplacian(r,cv2.CV_8U)
                r=cv2.medianBlur(r,3)
                circles=cv2.HoughCircles(r,cv2.HOUGH_GRADIENT,2,400,200,10,20)
                                            
                for j in circles[0,:]:
                    j[0]=j[0]+140
                    j[1]=j[1]+110
                    cv2.circle(frame,(j[0],j[1]),j[2],(0,0,255),)
                    cv2.circle(frame,(j[0],j[1]),1,(0,255,0),1)
                    
                    #distance
                    dist_y = j[1] - y_quad
                    delt_dist_y = dist_y - dist_init_y
                    
                    dist_x = j[0] - x_quad
                  
                    if dist_y > dist_init_y and dist_x > dist_init_x:
                        stream=stream+'N'
                        print(stream)
                        read=3
                    if dist_y > dist_init_y and dist_x < dist_init_x: 
                        stream=stream+'Q'
                        print(stream)
                        read=4
                    if dist_y < dist_init_y and dist_x > dist_init_x:
                        stream=stream+'P'
                        print(stream)
                        read=1
                    if dist_y < dist_init_y and dist_x < dist_init_x:
                        stream=stream+'Y'
                        print(stream)
                        read=2

                    oled.clear()
                    oled.write(stream)
                   
                while button.read() :
                    sleep(0.000001)
                                            
                #cv2.imwrite("output_to_be_processed/frame" + str(i) + "_" + str(k) + ".jpg", frame[110:180,140:210])
                i = i + 1
#            if flag:
#                cv2.circle(frame, (int(x_quad  - dist_init_x), int(y_quad  - dist_init_y)),2,(255,255,255),2)

            # write frame to video output
            frame.resize(frame_w*frame_h*3)
            for y in range(frame_h):
                frameOut.frame[y*frame_out_w*3:y*frame_out_w*3+frame_w*3] = frame.data[y*frame_w*3:(y+1)*frame_w*3]
                
            videoOut.frame(0, frameOut)
            frameCount = frameCount + 1 
            if reset.read():
                acq=1
                stream=''
                                            
except KeyboardInterrupt:
    # end gracefully if the kernel is interrupted
    pass

# release camera and monitor
videoIn.release()
videoOut.stop()