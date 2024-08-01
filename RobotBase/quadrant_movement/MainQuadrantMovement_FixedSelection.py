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

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class MainQuadrantMovementFixedSelection:
    def __init__(self):
        self.car = mecanum.MecanumChassis()
        self.camera = Camera.Camera()
        self.camera.camera_open(correction=True)
        self.detector = apriltag.Detector()
        self.running = True
        self.detected_tag_after_turn = None
        self.mapSelection = [1, 2, 3]
        self.map1dist = 1
        self.map2dist = 13
        self.map3dist = 20
        self.current_distance = 0

        # this variable is being used to define the number of iterations to loop through all tags
        # TODO: replace with stopping by recieving message from protocol 
        self.fullIterations = 3

    def move_straight(self, distance_inches):
        duration = distance_inches * 0.13 
        print(f"Moving straight for {distance_inches} inches.")
        self.car.set_velocity(35, 90, 0)
        time.sleep(duration)
        self.car.set_velocity(0, 90, 0) 

    def move_straight_reverse(self, distance_inches):
        duration = distance_inches * 0.13 
        print(f"Moving straight for {distance_inches} inches in reverse.")
        self.car.set_velocity(-35, 90, 0)
        time.sleep(duration)
        self.car.set_velocity(0, 90, 0) 

    def turn_right(self):
        self.car.set_velocity(0, 90, 0.5) 
        time.sleep(0.55) 
        self.car.set_velocity(0, 90, 0)

    def turn_left(self):
        self.car.set_velocity(0, 90, -0.5)  
        time.sleep(0.55)  
        self.car.set_velocity(0, 90, 0)  

    def run(self):
        try:
            for i in range(self.fullIterations):
                for map in range(len(self.mapSelection)):
                    print("Beginning Task!")
                    current_tag = self.mapSelection[map]
                    print("Current Tag Selection: " + str(current_tag))

                    self.turn_right()

                    time.sleep(1)

                    if current_tag == 1:
                        self.current_distance = self.map1dist
                    elif current_tag == 2:
                        self.current_distance = self.map2dist
                    elif current_tag == 3:
                        self.current_distance = self.map3dist

                    self.move_straight(self.current_distance)

                    time.sleep(0.5)

                    self.turn_left()

                    time.sleep(1)

                    while self.running:
                        img = self.camera.frame
                        if img is None or img.size == 0:
                            print("No image captured. Skipping frame.")
                            continue

                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        tags = self.detector.detect(gray)

                        # Check for any tag detection
                        for tag in tags:
                            tag_id = tag.tag_id
                            if tag_id in [1, 2, 3]:
                                self.detected_tag_after_turn = tag_id
                                print(f"Detected tag: {self.detected_tag_after_turn}")
                                break

                        if self.detected_tag_after_turn is not None:
                            self.turn_right()
                            time.sleep(0.5)
                            self.move_straight_reverse(self.current_distance)
                            time.sleep(0.5)
                            
                            # TODO: change this
                            if current_tag == 1:
                                self.turn_left()
                            elif current_tag == 2:
                                self.turn_left()
                                time.sleep(0.2)
                                self.turn_left()
                            else:
                                self.turn_right()

                            break
                    print("Task Completed!")
                    time.sleep(5)

        except KeyboardInterrupt:
            print("Program interrupted.")
            self.running = False
        finally:
            print("Shutting down.")
            self.camera.camera_close()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    tester = MainQuadrantMovementFixedSelection()
    tester.run()