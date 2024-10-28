# test on robots between 10/29-11/4
from RobotBase import MainThread

class QuadrantNavigator:
    def __init__(self):
        self.main_thread = MainThread()

    def navigate_to_quadrant(self, quadrant_num):
        self.main_thread.run(quadrant_num)

if __name__ == '__main__':
    navigator = QuadrantNavigator()

    # this is manual input of a quadrant number for testing purposes
    quadrant_number = int(input("Enter the quadrant number (1-4): "))
    navigator.navigate_to_quadrant(quadrant_number)