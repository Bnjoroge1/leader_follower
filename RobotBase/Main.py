import sys
import threading
import time
import signal
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, '../functionality_clases'))

from functionality_clases.LineFollowing import LineFollowing
from UltrasonicSensor import Sonar
from ColorSensor import ColorSensor

def ultrasonic_sensor():
    s = Sonar()
    s.startSequence()
    s.startSymphony()
    while True:
        time.sleep(1)
        distance = s.getDistance()
        print(distance)

def line_following():
    lf = LineFollowing()
    lf.start()
    signal.signal(signal.SIGINT, lf.manual_stop)
    while lf.__isRunning:
        time.sleep(0.01)

def color_sensor():
    cs = ColorSensor()
    cs.init()
    cs.start()
    camera = Camera.Camera()
    camera.camera_open(correction=True)
    while True:
        img = camera.frame
        if img is not None:
            frame = img.copy()
            cs.run(frame)
            time.sleep(1)  # Add a delay to control the frame rate and avoid excessive prints
        else:
            time.sleep(0.01)

if __name__ == '__main__':
    ultrasonic_thread = threading.Thread(target=ultrasonic_sensor)
    line_following_thread = threading.Thread(target=line_following)
    color_sensor_thread = threading.Thread(target=color_sensor)

    ultrasonic_thread.start()
    line_following_thread.start()
    color_sensor_thread.start()

    ultrasonic_thread.join()
    line_following_thread.join()
    color_sensor_thread.join()
