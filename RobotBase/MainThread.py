#!/usr/bin/python3
# coding=utf8
import sys
import time
import os
import cv2
import apriltag
import random

sys.path.append('/home/pi/TurboPi/')
import Camera
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
from functionality_classes.LineFollowing import LineFollowing

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

if sys.version_info.major == 2:
    # print('Please run this program with python3!')
    sys.exit(0)

class MainThread:
    def __init__(self, quadrant_num):
        self.car = mecanum.MecanumChassis()
        self.line_follower = LineFollowing()
        self.camera = None
        self.running = False
        try:
            self.camera = Camera.Camera()
            self.camera.camera_open(correction=True)
            print("Camera Initialization Successful")
        except Exception as e:
            print(f"Error opening camera: {e}")
            sys.exit(1)
        
        self.detector = apriltag.Detector()
        self.running = True
        self.stop_signal = False
        self.detected_tag_after_turn = None
        self.last_detected_tag = 0
        self.mapSelection = [1, 2, 3]
        self.map1dist = 1
        self.map2dist = 13
        self.map3dist = 20
        self.current_distance = 0
        self.quadrant_num = quadrant_num
        
        # true quad indicates that it is 2/4; false quad is 1/3
        self.quad = True

        # print(f"Initializing with quadrant number: {self.quadrant_num}")
        # self.move_to_quad(self.quadrant_num)
        self.move_to_quad_lf(self.quadrant_num)

    def __del__(self):
        if self.camera:
            self.camera.camera_close()
    
    # called from MessageNav to move robot to correct quadrant and begin tasks (note: assuming all robots start in the same position)
    def move_to_quad(self, quad_num):
        # specific to quadrant 1 and 4
        initialForwardDist = 9.5
        crossForwardDist = 34

        if quad_num == 1:
            self.move_straight(initialForwardDist)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(crossForwardDist)
            time.sleep(0.2)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(44)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(8)
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        elif quad_num == 2:
            self.move_straight(54)
            time.sleep(0.2)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(7)
            time.sleep(0.2)
            self.move_straight_reverse(11.2)
            time.sleep(0.5)
        elif quad_num == 3:
            self.move_straight(41)
            time.sleep(0.2)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(5)
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        elif quad_num == 4:
            self.move_straight(initialForwardDist)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(crossForwardDist)
            time.sleep(0.2)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(35)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(10) # wall allignment
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        
        print(f"Navigated to Quadrant {quad_num}")
        
        self.run()
    
    def move_to_quad_lf(self, quad_num):
        if quad_num == 1:
            self.move_straight(9.5)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(4)
            time.sleep(2)
            self.lf_stop(2)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(8)
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        elif quad_num == 2:
            self.move_straight(9.5)
            time.sleep(2)
            self.lf_stop(2)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(7)
            time.sleep(0.2)
            self.move_straight_reverse(11.2)
            time.sleep(0.5)
        elif quad_num == 3:
            self.move_straight(9.5)
            time.sleep(2)
            self.lf_stop(1)
            self.turn_left()
            time.sleep(0.2)
            self.move_straight(5)
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        elif quad_num == 4:
            self.move_straight(9.5)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(4)
            time.sleep(2)
            self.lf_stop(1)
            time.sleep(0.2)
            self.turn_right()
            time.sleep(0.2)
            self.move_straight(10)
            time.sleep(0.2)
            self.move_straight_reverse(12)
            time.sleep(0.5)
        
        print(f"Navigated to Quadrant {quad_num}")
        
        self.run()

    def lf_stop(self, num):
        self.line_follower.start()

        while True:
            sensor_data = self.line_follower.line.readData()
            self.line_follower.move(num) # this stops running when all chanels are triggered
            time.sleep(0.05)  
            break

        self.car.set_velocity(0,0,0)
        print("Completed Line Following")
        time.sleep(2)

    def nav_home(self, quad_num):
        # PLACEHOLDER -- update this section when everything else is working
        self.move_straight(8)
        time.sleep(0.2)
        self.move_straight_reverse(12)

    def quadrant_init(self, qNum):
        # print(f"Quadrant number: {self.quadrant_num}")
        if (qNum == 2 or qNum == 4):
            self.quad = True
        elif (qNum == 1 or qNum == 3):
            self.quad = False

    def move_straight(self, distance_inches):
        duration = distance_inches * 0.13 
        self.car.set_velocity(35, 90, 0)
        time.sleep(duration)
        self.car.set_velocity(0, 90, 0) 

    def move_straight_reverse(self, distance_inches):
        duration = distance_inches * 0.13 
        self.car.set_velocity(-35, 90, 0)
        time.sleep(duration)
        self.car.set_velocity(0, 90, 0) 

    def turn_right(self):
        self.car.set_velocity(0, 90, 0.55) 
        time.sleep(0.58) # rpi1: 0.55; 11/20: 0.58
        self.car.set_velocity(0, 90, 0)

    def turn_left(self):
        self.car.set_velocity(0, 90, -0.52)  
        time.sleep(0.58) # rpi1: 0.55; 11/20: 0.61
        self.car.set_velocity(0, 90, 0)  

    def handle_last_tag(self):
        # tag0 isn't an actual april tag; it's used to define the initial turn direction
        # print(f"Handling last detected tag: {self.last_detected_tag}")
        if (self.last_detected_tag == 0):
            if (self.quad):
                self.turn_right()
            elif (not self.quad):
                self.turn_left()
        elif (self.last_detected_tag == 1):
            if (self.quad):
                self.turn_right()
            elif (not self.quad):
                self.turn_left()
        elif (self.last_detected_tag == 2):
            if (self.quad):
                self.turn_right()
                time.sleep(1.0)
                self.turn_right()
            elif (not self.quad):
                self.turn_left()
                time.sleep(1.0)
                self.turn_left()
        elif (self.last_detected_tag == 3):
            if (self.quad):
                self.turn_left()
            elif (not self.quad):
                self.turn_right()

    def align_with_tag(self, tag):
        aligned = False
        # print(f"Aligning with tag: {tag}")
        while self.running and not aligned:
            img = self.camera.frame
            if img is None or img.size == 0:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            tags = self.detector.detect(gray)

            for detected_tag in tags:
                if detected_tag.tag_id == tag:
                    # calculates misalignment (offset) from center
                    tag_center_x = detected_tag.center[0]
                    # print("Tag Center X: " + str(tag_center_x))
                    frame_center_x = img.shape[1] / 2
                    # print("Frame Center X: " + str(frame_center_x))
                    offset = tag_center_x - frame_center_x

                    if abs(offset) > 40:  # tolerance threshold
                        if offset > 0:
                            self.car.set_velocity(0, 90, 0.30)
                            print("Offset: " + str(offset))
                            time.sleep(0.1)
                        else:
                            self.car.set_velocity(0, 90, -0.30)
                            time.sleep(0.1)

                        # Stop for 0.5 seconds for recalibration
                        self.car.set_velocity(0, 90, 0)
                        print("Waiting for re-calibration")
                        time.sleep(0.5)
                    else:
                        aligned = True
                        self.car.set_velocity(0, 90, 0)
                        time.sleep(0.2)
                        print("Completed Tag Alignment!")
                        break
        return aligned

    def stop_after_tag(self):
        self.stop_signal = True
        self.nav_home() # verify this is being called

    def run(self):
            try:
                self.quadrant_init(self.quadrant_num)
                while self.running:
                    for map in range(len(self.mapSelection)):
                        if self.stop_signal:

                            self.running = False
                            break

                        current_tag = self.mapSelection[map]

                        time.sleep(0.5)
                        self.handle_last_tag()
                        time.sleep(5)

                        if(self.last_detected_tag == 3 and current_tag == 1):
                            if(not self.quad):
                                self.turn_right()
                                time.sleep(0.5)
                                self.move_straight(16)
                                time.sleep(0.5)
                                self.move_straight_reverse(12)
                                time.sleep(0.5)
                                self.turn_left()
                                time.sleep(0.5)
                            elif(self.quad):
                                self.turn_left()
                                time.sleep(0.25)
                                self.move_straight(16)
                                time.sleep(0.5)
                                self.move_straight_reverse(12)
                                time.sleep(0.5)
                                self.turn_right()
                                time.sleep(0.5)

                        if current_tag == 1:
                            self.lf_stop(1)
                        elif current_tag == 2:
                            self.lf_stop(2)
                        elif current_tag == 3:
                            self.lf_stop(3)

                        time.sleep(0.5)
                        
                        if (self.quad or self.quadrant_num == 0): # self.quadrant_num == 0 used for debugging
                            self.turn_left()
                        elif (not self.quad):
                            self.turn_right()

                        time.sleep(1)

                        if self.align_with_tag(current_tag):
                            time.sleep(0.5)
                            if self.quad:
                                self.turn_right()
                            else:
                                self.turn_left()

                            time.sleep(0.5)    
                            self.move_straight_reverse(self.current_distance)
                            time.sleep(0.5)

                            if current_tag == 1:
                                if (self.quad):
                                    time.sleep(1.0)
                                    self.turn_left()
                                elif (not self.quad):
                                    time.sleep(1.0)
                                    self.turn_right()
                            elif current_tag == 2:
                                if (self.quad):
                                    self.turn_left()
                                    time.sleep(1.0)
                                    self.turn_left()
                                elif (not self.quad):
                                    self.turn_right()
                                    time.sleep(1.0)
                                    self.turn_right()
                            else:
                                if (self.quad):
                                    time.sleep(1.0)
                                    self.turn_right()
                                elif (not self.quad):
                                    time.sleep(1.0)
                                    self.turn_left()
                            
                            self.last_detected_tag = current_tag

                            time.sleep(2.5)

            except KeyboardInterrupt:
                self.running = False
            finally:
                if self.camera:
                    self.camera.camera_close()
                cv2.destroyAllWindows()
                
    # def run(self):
    #     try:
    #         self.quadrant_init(self.quadrant_num)
    #         while self.running:
    #             for map in range(len(self.mapSelection)):
    #                 if self.stop_signal:

    #                     self.running = False
    #                     break

    #                 current_tag = self.mapSelection[map]

    #                 time.sleep(0.5)
    #                 self.handle_last_tag()
    #                 time.sleep(5)

    #                 if(self.last_detected_tag == 3 and current_tag == 1):
    #                     if(not self.quad):
    #                         self.turn_right()
    #                         time.sleep(0.5)
    #                         self.move_straight(16)
    #                         time.sleep(0.5)
    #                         self.move_straight_reverse(12)
    #                         time.sleep(0.5)
    #                         self.turn_left()
    #                         time.sleep(0.5)
    #                     elif(self.quad):
    #                         if(self.quadrant_num == 2):
    #                             self.turn_left()
    #                             time.sleep(0.25)
    #                             self.move_straight(16)
    #                             time.sleep(0.5)
    #                             self.move_straight_reverse(12)
    #                             time.sleep(0.5)
    #                             self.turn_right()
    #                             time.sleep(0.5)
    #                         else:
    #                             self.turn_left()
    #                             time.sleep(0.5)
    #                             self.move_straight(16)
    #                             time.sleep(0.5)
    #                             self.move_straight_reverse(12)
    #                             time.sleep(0.5)
    #                             self.turn_right()
    #                             time.sleep(0.5)

    #                 if current_tag == 1:
    #                     self.current_distance = self.map1dist
    #                 elif current_tag == 2:
    #                     self.current_distance = self.map2dist
    #                 elif current_tag == 3:
    #                     self.current_distance = self.map3dist

    #                 self.move_straight(self.current_distance)
    #                 time.sleep(0.5)
                    
    #                 if (self.quad or self.quadrant_num == 0): # self.quadrant_num == 0 used for debugging
    #                     self.turn_left()
    #                 elif (not self.quad):
    #                     self.turn_right()

    #                 time.sleep(1)

    #                 if self.align_with_tag(current_tag):
    #                     time.sleep(0.5)
    #                     if self.quad:
    #                         self.turn_right()
    #                     else:
    #                         self.turn_left()

    #                     time.sleep(0.5)    
    #                     self.move_straight_reverse(self.current_distance)
    #                     time.sleep(0.5)

    #                     if current_tag == 1:
    #                         if (self.quad):
    #                             time.sleep(1.0)
    #                             self.turn_left()
    #                         elif (not self.quad):
    #                             time.sleep(1.0)
    #                             self.turn_right()
    #                     elif current_tag == 2:
    #                         if (self.quad):
    #                             self.turn_left()
    #                             time.sleep(1.0)
    #                             self.turn_left()
    #                         elif (not self.quad):
    #                             self.turn_right()
    #                             time.sleep(1.0)
    #                             self.turn_right()
    #                     else:
    #                         if (self.quad):
    #                             time.sleep(1.0)
    #                             self.turn_right()
    #                         elif (not self.quad):
    #                             time.sleep(1.0)
    #                             self.turn_left()
                        
    #                     self.last_detected_tag = current_tag

    #                     time.sleep(2.5)

    #     except KeyboardInterrupt:
    #         self.running = False
    #     finally:
    #         if self.camera:
    #             self.camera.camera_close()
    #         cv2.destroyAllWindows()

if __name__ == '__main__':
    quadrant_num = int(sys.argv[1])

    main = MainThread(quadrant_num)
    main.run()