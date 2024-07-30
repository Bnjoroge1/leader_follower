#!/usr/bin/python3
# coding=utf8
import sys
import time
import os
import cv2
import apriltag

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

class MainTester:
    def __init__(self):
        self.car = mecanum.MecanumChassis()
        self.camera = Camera.Camera()
        self.camera.camera_open(correction=True)
        self.detector = apriltag.Detector()
        self.running = True

    def move_straight(self, distance_inches):
        duration = distance_inches * 0.5  # Adjust the multiplier as needed
        self.car.set_velocity(35, 90, 0)
        time.sleep(duration)
        self.car.set_velocity(0, 90, 0)  # Stop after moving

    def turn_right(self):
        self.car.set_velocity(0, 90, 0.5)  # Adjust turning speed and direction as needed
        time.sleep(1)  # Duration for the turn (adjust as needed)
        self.car.set_velocity(0, 90, 0)  # Stop turning

    def turn_left(self):
        self.car.set_velocity(0, 90, -0.5)  # Adjust turning speed and direction as needed
        time.sleep(1)  # Duration for the turn (adjust as needed)
        self.car.set_velocity(0, 90, 0)  # Stop turning

    def run(self):
        try:
            # Move straight for 8 inches
            self.move_straight(8)
            
            # Make a 90° right turn
            self.turn_right()
            
            # Move straight until tag 4 is detected
            while self.running:
                img = self.camera.frame
                if img is None or img.size == 0:
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                tags = self.detector.detect(gray)

                tag_4_detected = False
                for tag in tags:
                    tag_id = tag.tag_id
                    if tag_id == 4:
                        print("Tag 4 detected. Setting turn flag.")
                        tag_4_detected = True
                        break  # Exit the loop after detecting tag 4

                if tag_4_detected:
                    # Make a 90° left turn
                    self.turn_left()
                    break  # Exit the loop after completing the turn

                # Continue moving straight until tag 4 is detected
                self.car.set_velocity(35, 90, 0)
        except KeyboardInterrupt:
            print("Program interrupted.")
            self.running = False
        finally:
            self.camera.camera_close()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    tester = MainTester()
    tester.run()