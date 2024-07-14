import sys
import threading
import time
import signal
sys.path.append('../functionality_clases')
from UltrasonicSensor import Sonar
from LineFollowing import LineFollowing

def UltrasonicSensorTest():
    s = Sonar()
    s.startSequence()
    s.startSymphony()
    while True:
        time.sleep(1)
        distance = s.getDistance()
        print(distance)

def LineFollowingTest():
    lf = LineFollowing()
    lf.start()
    signal.signal(signal.SIGINT, lf.manual_stop)
    while lf.__isRunning:
        time.sleep(0.01)

if __name__ == '__main__':
    ultrasonic_thread = threading.Thread(target=UltrasonicSensorTest)
    line_following_thread = threading.Thread(target=LineFollowingTest)

    ultrasonic_thread.start()
    line_following_thread.start()

    ultrasonic_thread.join()
    line_following_thread.join()
