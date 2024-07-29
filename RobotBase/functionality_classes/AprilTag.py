#!/usr/bin/python3
import sys
sys.path.append('/home/pi/TurboPi/')
import cv2
import time
import signal
import threading
import numpy as np
import apriltag
import Camera
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class AprilTagSensor:
    def __init__(self):
        self.is_running = False
        self.camera = Camera.Camera()
        self.detector = apriltag.Detector()

        self.tag_ids = [1, 2, 3] # IDs 1-3 used for quadrant movement
        self.turn_tag_id = 4  # ID for turning

    def init(self):
        print("AprilTag Detection Init")

    def start(self):
        self.is_running = True
        print("AprilTag Detection Start")
        self.camera.camera_open(correction=True)

    def stop(self):
        self.is_running = False
        print("AprilTag Detection Stop")
        self.camera.camera_close()

    def exit(self):
        self.is_running = False
        print("AprilTag Detection Exit")
        self.camera.camera_close()

    def detect_april_tags(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tags = self.detector.detect(gray)
        return tags

    def process_tag(self, tag):
        if tag.tag_id in self.tag_ids or tag.tag_id == self.turn_tag_id:
            print(f"Detected tag ID: {tag.tag_id}")

    def run(self, img):
        if not self.is_running:
            return img
        
        tags = self.detect_april_tags(img)
        for tag in tags:
            self.process_tag(tag)
        return img

    def manual_stop(self, signum, frame):
        print('Closing...')
        self.is_running = False
        self.camera.camera_close()

if __name__ == '__main__':
    tag_sensor = AprilTagSensor()
    tag_sensor.init()
    tag_sensor.start()
    signal.signal(signal.SIGINT, tag_sensor.manual_stop)
    while tag_sensor.is_running:
        img = tag_sensor.camera.frame
        if img is not None:
            frame = img.copy()
            tag_sensor.run(frame)  
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    tag_sensor.camera.camera_close()
    cv2.destroyAllWindows()