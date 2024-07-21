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

from functionality_classes.ColorSensingMove import ColorSensingMove
from functionality_classes.LineFollowing import LineFollowing
from functionality_classes.UltrasonicSensor import Sonar

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

def color_sensor(lf_event):
    cs = ColorSensingMove()
    cs.init()
    cs.start()
    camera = Camera()
    camera.camera_open(correction=True)

    while True:
        img = camera.frame
        if img is not None:
            frame = img.copy()
            cs.run(frame)
            
            detected_color = cs.get_detected_color()
            
            if detected_color == 'green':
                print("Detected green color, stopping line following and turning.")
                lf_event.set()  # Stop line following
                time.sleep(1)  # Allow some time for the turn to complete
                lf_event.clear()  # Resume line following

        else:
            time.sleep(0.01)

    camera.camera_close()

if __name__ == '__main__':
    lf_event = threading.Event()
    
    ultrasonic_thread = threading.Thread(target=ultrasonic_sensor)
    line_following_thread = threading.Thread(target=line_following, args=(lf_event,))
    color_sensor_thread = threading.Thread(target=color_sensor, args=(lf_event,))

    ultrasonic_thread.start()
    line_following_thread.start()
    color_sensor_thread.start()

    ultrasonic_thread.join()
    line_following_thread.join()
    color_sensor_thread.join()
