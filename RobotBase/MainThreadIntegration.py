import os
import sys

if 'pi' in os.uname().nodename:
    sys.path.append('/home/pi/Desktop/dev/leader_follower')
else: 
    sys.path.append('/Users/alexbattikha/Desktop/dev/robotics/jhu-2024/leader_follower')

from RobotBase.MainThread import MainThread


class MessageNav:
    def __init__(self, quadrant_num):
        self.main_thread = MainThread(quadrant_num)

    def navigate_to_quadrant(self, quadrant_num):
        self.main_thread = MainThread(quadrant_num)
        self.main_thread.run()

    def stop(self):
        print("Stopping after the current tag is completed")
        self.main_thread.stop_after_tag()

    def swap_quadrants(self, from_quadrant, to_quadrant):
        # placeholder
        print("Swapping robot in Quadrant " + from_quadrant + " with robot in Quadrant " + to_quadrant)

if __name__ == '__main__':
    # this is manual input of a quadrant number for testing purposes
    # replace with protocol message of leader assigning quadrants
    quadrant_number = int(input("Enter the quadrant number (1-4): ").strip())
    navigator = MessageNav(quadrant_number)

    navigator.navigate_to_quadrant(quadrant_number)

    # replace with protocol message of leader telling a robot in a specific quadrant to stop
    stop_input = input("Enter 'stop' to stop robot movement after the current tag: ").strip().lower()
    if stop_input == 'stop':
        navigator.stop()

    # replace with protocol message of leader telling a robot to switch quadrants; come back to quadrant swap at a later time
    # swap_input = input("Enter two quadrant numbers to swap (e.g., '2 3'): ").strip()
    # try:
    #     from_quadrant, to_quadrant = map(int, swap_input.split())
    #     navigator.swap_quadrants(from_quadrant, to_quadrant)
    # except ValueError:
    #     print("Invalid input. Please enter two integers separated by a space.")