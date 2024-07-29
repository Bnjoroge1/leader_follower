import sys
import threading
import time
import signal
import os

sys.path.append('/home/pi/TurboPi/')
import Camera

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)
sys.path.append(os.path.join(current_dir, 'functionality_classes'))

from functionality_classes.LineFollowing import LineFollowing
from functionality_classes.UltrasonicSensor import Sonar
from functionality_classes.AprilTag import AprilTagSensor

def ultrasonic_sensor():
    s = Sonar()
    s.startSymphony()
    while True:
        time.sleep(1)
        distance = s.getDistance()
        print(distance)

def line_following(lf_event):
    lf = LineFollowing()
    lf.start()
    signal.signal(signal.SIGINT, lf.manual_stop)
    
    while not lf_event.is_set():
        time.sleep(0.01)

    lf.stop()

def apriltag_sensor(lf_event):
    at = AprilTagSensor()
    at.init()
    at.start()

    while True:
        img = at.camera.frame
        if img is not None:
            frame = img.copy()
            tags = at.run(frame)
            
            for tag in tags:
                if tag.tag_id in at.tag_ids:
                    # testing output from apriltag; also being output in functionality_classes/AprilTag.py
                    # print(f"Detected AprilTag ID: {tag.tag_id}")
                    continue
                elif tag.tag_id == at.turn_tag_id:
                    # print(f"Detected AprilTag ID: {tag.tag_id}, stopping line following and turning.")
                    lf_event.set()  # Stop line following
                    time.sleep(1)  # Allow some time for the turn to complete
                    lf_event.clear()  # Resume line following

        else:
            time.sleep(0.01)

    at.camera.camera_close()

if __name__ == '__main__':
    lf_event = threading.Event()
    
    ultrasonic_thread = threading.Thread(target=ultrasonic_sensor)
    line_following_thread = threading.Thread(target=line_following, args=(lf_event,))
    apriltag_sensor_thread = threading.Thread(target=apriltag_sensor, args=(lf_event,))

    ultrasonic_thread.start()
    line_following_thread.start()
    apriltag_sensor_thread.start()

    ultrasonic_thread.join()
    line_following_thread.join()
    apriltag_sensor_thread.join()