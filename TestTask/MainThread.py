#!/usr/bin/python3
# coding=utf8
import sys
import time
import os
#import cv2

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class MainThread:
    def __init__(self, quadrant_num):
        self.quad = quadrant_num
        print(f"Main thread initialized")
        
    def run(self):
        print(f"Quadrant task: {self.quad}")       

if __name__ == '__main__':
    quadrant_num = int(sys.argv[1])
    
    # testing only
    # quadrant_num = int(1)

    main = MainThread(quadrant_num)
    main.run()


# note from 12/12: if there's extra time, address the issue where if no tag is detected then the robot begins to navigate to quadrant again (can be solved offline)
