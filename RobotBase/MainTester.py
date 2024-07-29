#!/usr/bin/python3
# coding=utf8
import sys
import time
import threading
import numpy as np
import cv2
import apriltag
sys.path.append('/home/pi/TurboPi/')
import yaml_handle
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared
import LineFollowing
import signal

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class MainTester:
    def __init__(self):
        self.camera = Camera.Camera()
        self.camera.camera_open(correction=True)
        self.detector = apriltag.Detector()
        self.line_follower = LineFollowing.LineFollowing()
        self.lf_event = threading.Event()  
        self.line_follower.init()
        self.line_follower.start()

    def run(self):
        try:
            while True:
                img = self.camera.camera.frame
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                tags = self.detector.detect(gray)

                for tag in tags:
                    tag_id = tag.tag_id
                    if tag_id in [1, 2, 3]:
                        cv2.putText(img, f"Tag ID: {tag_id}", (10, 30 + tag_id * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    elif tag_id == 4:
                        self.lf_event.set()  # trigger turn
                        time.sleep(1)  # allow some time for the turn to complete
                        self.lf_event.clear()  # resume line following

                img = self.line_follower.run(img)
                cv2.imshow("Camera", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.camera.camera_close()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    tester = MainTester()
    tester.run()