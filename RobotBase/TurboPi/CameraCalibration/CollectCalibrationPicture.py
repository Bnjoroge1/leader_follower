#!/usr/bin/env python3
# encoding:utf-8
# Data:2021/05/25
# Author:Aiden
# Function: collect calibration picture
import os
import cv2
import time
from CalibrationConfig import *

print('Press "Space" on keyboard to save picture. Press "Esc" to exit')
cap = cv2.VideoCapture(-1)

pictures_list = []
#If the calib folder doesn't exist, create a new one.
if not os.path.exists(save_path):
    os.mkdir(save_path)
else:
    for i in os.listdir(save_path):
        pictures_list.append(i[:-4])

#calculate the number of the saved picture
num = 0
while True:
    ret, frame = cap.read()
    if ret:
        Frame = frame.copy()
        cv2.putText(Frame, str(num), (10, 50), cv2.FONT_HERSHEY_COMPLEX, 2.0, (0, 0, 255), 5)
        cv2.imshow("Frame", Frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
        if key == 32:
            while True:
                num += 1
                if num not in pictures_list:
                    #The format of the picture file name: the number of the current pictures.jpg
                    cv2.imwrite(save_path + str(num) + ".jpg", frame)
                    break
    else:
        time.sleep(0.01)

cap.release()
cv2.destroyAllWindows()
