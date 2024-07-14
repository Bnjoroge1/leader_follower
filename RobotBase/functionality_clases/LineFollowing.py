import time
import threading
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
import HiwonderSDK.FourInfrared as infrared
import yaml_handle

from LineFollowing import LineFollowing

class LineFollowing:
    def __init__(self):
        self.car = mecanum.MecanumChassis()
        self.line = infrared.FourInfrared()
        self.servo_data = None
        self.__isRunning = False
        self.car_stop = False
        self.target_color = None
        self.detect_color = 'None'
        self.range_rgb = {
            'red': (0, 0, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
        }
        self.draw_color = self.range_rgb["black"]
        self.load_config()
        self.initMove()

        self.th = threading.Thread(target=self.move)
        self.th.setDaemon(True)
        self.th.start()

    def load_config(self):
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)

    def initMove(self):
        self.car.set_velocity(0, 90, 0)
        Board.setPWMServoPulse(1, self.servo_data['servo1'], 1000)
        Board.setPWMServoPulse(2, self.servo_data['servo2'], 1000)

    def setBuzzer(self, timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)

    def reset(self):
        self.car_stop = False
        self.detect_color = 'None'
        self.__isRunning = False

    def start(self):
        self.reset()
        self.__isRunning = True
        self.car.set_velocity(35, 90, 0)
        print("LineFollower Start")

    def stop(self):
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Stop")

    def exit(self):
        self.car_stop = True
        self.__isRunning = False
        self.set_rgb('None')
        print("LineFollower Exit")

    def setTargetColor(self, color):
        self.target_color = color
        return True, ()

    def set_rgb(self, color):
        if color in self.range_rgb:
            rgb_color = self.range_rgb[color]
            Board.RGB.setPixelColor(0, Board.PixelColor(*rgb_color))
            Board.RGB.setPixelColor(1, Board.PixelColor(*rgb_color))
            Board.RGB.show()
        else:
            Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
            Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
            Board.RGB.show()

    def move(self):
        while True:
            if self.__isRunning:
                try:
                    sensor_data = self.line.readData()
                    if not sensor_data[0] and sensor_data[1] and sensor_data[2] and not sensor_data[3]:
                        print("Detected black line with sensors 2 and 3")
                        self.car.set_velocity(35, 90, 0)
                        self.car_stop = True
                    elif not sensor_data[0] and not sensor_data[1] and sensor_data[2] and not sensor_data[3]:
                        print("Detected black line with sensor 3")
                        self.car.set_velocity(35, 90, 0.03)
                        self.car_stop = True
                    elif not sensor_data[0] and sensor_data[1] and not sensor_data[2] and not sensor_data[3]:
                        print("Detected black line with sensor 2")
                        self.car.set_velocity(35, 90, -0.03)
                        self.car_stop = True
                    elif not sensor_data[0] and not sensor_data[1] and not sensor_data[2] and sensor_data[3]:
                        print("Detected black line with sensor 4")
                        self.car.set_velocity(35, 90, 0.3)
                        self.car_stop = True
                    elif sensor_data[0] and not sensor_data[1] and not sensor_data[2] and not sensor_data[3]:
                        print("Detected black line with sensor 1")
                        self.car.set_velocity(35, 90, -0.3)
                        self.car_stop = True
                    elif sensor_data[0] and sensor_data[1] and sensor_data[2] and sensor_data[3]:
                        if not self.car_stop:
                            print("Detected all sensors")
                            self.car.set_velocity(0, 90, 0)
                            self.car_stop = True
                        time.sleep(0.01)

                    if self.detect_color == 'green':
                        if not self.car_stop:
                            print("Detected green color")
                            self.car.set_velocity(35, 90, 0)
                            self.car_stop = True

                except OSError as e:
                    print(f"I/O Error: {e}")
            else:
                if not self.car_stop:
                    print("Stopping movement")
                    self.car.set_velocity(0, 90, 0)
                    self.car_stop = True
                time.sleep(0.01)

    def run(self, img):
        if not self.__isRunning:
            return img

        self.detect_color = 'None'
        self.draw_color = self.range_rgb["black"]
        cv2.putText(img, "Color: " + self.detect_color, (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, self.draw_color, 2)
        return img

    def manual_stop(self, signum, frame):
        print('Manual Stop')
        self.__isRunning = False
        self.car.set_velocity(0, 90, 0)

if __name__ == '__main__':
    lf = LineFollowing()
    lf.start()
    import signal
    signal.signal(signal.SIGINT, lf.manual_stop)
    while lf.__isRunning:
        time.sleep(0.01)
