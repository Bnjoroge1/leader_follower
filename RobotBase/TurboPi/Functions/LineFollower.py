#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import cv2
import time
import math
import signal
import Camera
import threading
import numpy as np
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class LineFollower:
    def __init__(self):
        self.car = mecanum.MecanumChassis()
        self.line = infrared.FourInfrared()

        self.servo1 = 1500
        self.servo2 = 1500
        self.car_stop = False
        self.color_list = []
        self.size = (640, 480)
        self.__isRunning = False
        self.detect_color = 'None'
        self.target_color = ('red', 'green')

        self.lab_data = None
        self.servo_data = None

        self.th = threading.Thread(target=self.move)
        self.th.setDaemon(True)
        self.th.start()
   
    def load_config(self):
        # global lab_data, servo_data
        
        self.lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path) or {}
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path) or {"servo1": 1500, "servo2": 1500}

    def initMove(self):
        self.car.set_velocity(0,90,0)
        Board.setPWMServoPulse(1, self.servo1, 1000)
        Board.setPWMServoPulse(2, self.servo2, 1000)

    def setBuzzer(timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)

    range_rgb = {
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'black': (0, 0, 0),
        'white': (255, 255, 255),
    }

    draw_color = range_rgb["black"]

    def reset(self): 
        # global car_stop
        # global color_list
        # global detect_color
        # global start_pick_up
        # global servo1, servo2
        
        self.car_stop = False
        self.color_list = []
        self.detect_color = 'None'
        self.servo1 = self.servo_data['servo1']
        self.servo2 = self.servo_data['servo2']

    def init(self):
        print("LineFollower Init")
        self.load_config()
        self.reset()
        self.initMove()

    def start(self):
        # global __isRunning
        self.reset()
        self.__isRunning = True
        self.car.set_velocity(35,90,0)
        print("LineFollower Start")

    def stop(self):
        # global car_stop
        # global __isRunning
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Stop")
    
    def exit(self):
        # global car_stop
        # global __isRunning
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Exit")

    def setTargetColor(self, color):
        # global target_color

        self.xtarget_color = color
        return (True, ())

    def set_rgb(self, color):
        if color == "red":
            Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
            Board.RGB.show()
        elif color == "green":
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
            Board.RGB.show()
        elif color == "blue":
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
            Board.RGB.show()
        else:
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
            Board.RGB.show()

    def getAreaMaxContour(contours):
        contour_area_temp = 0
        contour_area_max = 0
        area_max_contour = None

        for c in contours:  # 历遍所有轮廓 Loop over the contours
            contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积 Calculate the contour area 
            if contour_area_temp > contour_area_max:
                contour_area_max = contour_area_temp
                if contour_area_temp > 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰 Only when the area is greater than 300, the maximum contour takes effect to filter the interference
                    area_max_contour = c

        return area_max_contour, contour_area_max  # 返回最大的轮廓 Return the maximum contour


    def move(self):
        global car_stop
        global __isRunning
        global detect_color    

        while True:
            if __isRunning:
                if detect_color != 'red':
                    self.set_rgb(detect_color) 
                    sensor_data = self.line.readData()
                    # 2，3号传感器检测到黑线 The black line is detected by No.2 and No.3 sensors 
                    if not sensor_data[0] and sensor_data[1] and sensor_data[2] and not sensor_data[3]:
                        self.car.set_velocity(35,90,0) # 机器人向前移动,线速度35(0~100)，方向角90(0~360)，偏航角速度0(-2~2)   Robot moves forward. The linear velocity is 0 (0~100), the direction velocity is 90(0~360), and the yaw velocity is 0(-2~2).
                        car_stop = True
                    # 3号传感器检测到黑线 The black is detected by No.3 sensor
                    elif not sensor_data[0] and not sensor_data[1] and sensor_data[2] and not sensor_data[3]:
                        self.car.set_velocity(35,90,0.03) # 机器人小右转 Robot turns right
                        car_stop = True 
                    # 2号传感器检测到黑线  The black is detected by No.2 sensor
                    elif not sensor_data[0] and  sensor_data[1] and not sensor_data[2] and not sensor_data[3]:
                        self.car.set_velocity(35,90,-0.03) # 机器人小左转  Robot makes a large left turn
                        car_stop = True
                    # 4号传感器检测到黑线  The black is detected by No.4 sensor
                    elif not sensor_data[0] and not sensor_data[1] and not sensor_data[2] and sensor_data[3]:
                        self.car.set_velocity(35,90,0.3) # 机器人大右转  Robot makes a large right turn
                        car_stop = True
                    # 1号传感器检测到黑线 The black is detected by No.1 sensor
                    elif sensor_data[0] and not sensor_data[1] and not sensor_data[2] and not sensor_data[3]:
                        self.car.set_velocity(35,90,-0.3) # 机器人大左转  Robot turns left
                        car_stop = True
                    
                    elif sensor_data[0] and sensor_data[1] and sensor_data[2] and sensor_data[3]:
                        if car_stop:
                            self.car.set_velocity(0,90,0) # 机器人停止移动 stop moving
                            car_stop = False
                        time.sleep(0.01)
                        
                    if detect_color == 'green': # 检测到绿色 green is detected
                        if not car_stop:
                            self.car.set_velocity(35,90,0) # 机器人向前移动 robot moves forward
                            car_stop = True

                else:
                    if car_stop:
                        self.setBuzzer(0.1)        
                        self.set_rgb(detect_color) 
                        self.car.set_velocity(0,90,0)
                        car_stop = False
                    time.sleep(0.01)
                        
            else:
                if car_stop:
                    self.car.set_velocity(0,90,0) 
                    car_stop = False
                time.sleep(0.01)

    

    def run(self, img):
        global __isRunning
        global detect_color, draw_color, color_list
        
        if not __isRunning:  # 检测是否开启玩法，没有开启则返回原图像 Detect whether the game is started, if not, the orginal image will be returned
            return img
        
        img_copy = img.copy()
        img_h, img_w = img.shape[:2]
        
        frame_resize = cv2.resize(img_copy, self.size, interpolation=cv2.INTER_NEAREST)
        frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)
        frame_lab = cv2.cvtColor(frame_gb, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间 Convert image into LAB space

        max_area = 0
        color_area_max = None
        areaMaxContour_max = 0
        for i in target_color:
            if i in lab_data:
                frame_mask = cv2.inRange(frame_lab,
                                            (lab_data[i]['min'][0],
                                            lab_data[i]['min'][1],
                                            lab_data[i]['min'][2]),
                                            (lab_data[i]['max'][0],
                                            lab_data[i]['max'][1],
                                            lab_data[i]['max'][2]))  #对原图像和掩模进行位运算 Bitwise operation of the original image and mask
                opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # 开运算 Opening 
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # 闭运算 Closing
                contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]  # 找出轮廓 Find contour
                areaMaxContour, area_max = self.getAreaMaxContour(contours)  # 找出最大轮廓 Find the maximum contour
                if areaMaxContour is not None:
                    if area_max > max_area:  # 找最大面积 Find the maximum area
                        max_area = area_max
                        color_area_max = i
                        areaMaxContour_max = areaMaxContour
        if max_area > 2500:  # 有找到最大面积 The maximum area is found
            rect = cv2.minAreaRect(areaMaxContour_max)
            box = np.int0(cv2.boxPoints(rect))
            cv2.drawContours(img, [box], -1, self.range_rgb[color_area_max], 2)
            
            if color_area_max == 'red':  # 红色最大 Red occupies the maxmium area
                color = 1
            elif color_area_max == 'green':  # 绿色最大 Green occupies the maxmium area
                color = 2
            else:
                color = 0
            color_list.append(color)
            
            if len(color_list) == 3:  # 多次判断  Multiple judgements 
                color = np.mean(np.array(color_list))# 取平均值 Take average
                color_list = []
                start_pick_up = True
                if color == 1:
                    detect_color = 'red'
                    draw_color = self.range_rgb["red"]
                elif color == 2:
                    detect_color = 'green'
                    draw_color = self.range_rgb["green"]
                else:
                    detect_color = 'None'
                    draw_color = self.range_rgb["black"]
        else:
            detect_color = 'None'
            draw_color = self.range_rgb["black"]
                    
        cv2.putText(img, "Color: " + detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, draw_color, 2) # 把检测到的颜色打印在画面上
        
        return img


    #关闭前处理 Processing before exit
    def manualcar_stop(self, signum, frame):
        global __isRunning
        
        print('关闭中...')
        __isRunning = False
        self.car.set_velocity(0,90,0)  # 关闭所有电机 Turn off all motors


    if __name__ == '__main__':
        init()
        start()
        camera = Camera.Camera()
        camera.camera_open(correction=True) # 开启畸变矫正,默认不开启 Enable distortion correction which is not enabled by default
        signal.signal(signal.SIGINT, manualcar_stop)
        while __isRunning:
            img = camera.frame
            if img is not None:
                frame = img.copy()
                Frame = run(frame)  
                frame_resize = cv2.resize(Frame, (320, 240))
                cv2.imshow('frame', frame_resize)
                key = cv2.waitKey(1)
                if key == 27:
                    break
            else:
                time.sleep(0.01)
        camera.camera_close()
        cv2.destroyAllWindows()