import os
import time
from message_classes import Message, Action
#from abstract_network import AbstractTransceiver
from zigbee_network import ZigbeeTransceiver
from typing import Any, Dict, List, Set
from pathlib import Path
import csv
from device_classes import ThisDevice, Device, TAKEOVER_DURATION
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import multiprocessing
import asyncio

class UserInterface(ThisDevice):
    """ Contains backend logic for user interface """

    def __init__(self, transceiver: ZigbeeTransceiver, id=-1):
        super().__init__(transceiver=transceiver, id=id)
        plt.ion()
        
        fig, self.axs = plt.subplots(2,3, figsize=(10, 6))
        fig.canvas.manager.set_window_title("Leader Follower Protocol Demo")
        self.axs[1, 0].text(0.2,.9, "Channel updates:", size=20, ha="center", va="center", )
        self.axs[0, 1].text(0.5,0.1, "A", size=30, ha="center", va="center", color='b')
        self.axs[0, 2].text(0.5,0.1, "C", size=30, ha="center", va="center", color='b')
        self.axs[1, 1].text(0.5,0.1, "B", size=30, ha="center", va="center", color='b')
        self.axs[1, 2].text(0.5,0.1, "D", size=30, ha="center", va="center", color='b') 
        self.axs[0, 0].set_axis_off()
        self.axs[0, 1].set_axis_off()
        self.axs[0, 2].set_axis_off()
        self.axs[1, 0].set_axis_off()
        self.axs[1, 1].set_axis_off()
        self.axs[1, 2].set_axis_off()
        r1 = patches.Rectangle((0,0.01), .99, .99, edgecolor='b', facecolor='none')
        self.axs[0, 1].add_patch(r1)
        plt.draw()
        plt.pause(0.05) 
        r2 = patches.Rectangle((0,0.01), .99, .99, edgecolor='b', facecolor='none')
        self.axs[0, 2].add_patch(r2)
        plt.draw()
        plt.pause(0.05) 
        r3 = patches.Rectangle((0,0.01), .99, .99, edgecolor='b', facecolor='none')
        self.axs[1, 1].add_patch(r3)
        plt.draw()
        plt.pause(0.05) 
        r4 = patches.Rectangle((0,0.01), .99, .99, edgecolor='b', facecolor='none')
        self.axs[1, 2].add_patch(r4)
        plt.draw()
        plt.pause(0.05) 
        
        l1 = patches.Rectangle((0,0.1), .05, .05, edgecolor='red', facecolor='red')
        self.axs[1, 0].add_patch(l1)
        self.axs[1, 0].text(0.07,0.1, "= leader", size=10)
        plt.draw()
        plt.pause(0.05) 
        l2 = patches.Rectangle((0,0), .05, .05, edgecolor='purple', facecolor='purple')
        self.axs[1, 0].add_patch(l2)
        self.axs[1, 0].text(0.07,0, "= follower", size=10)
        plt.draw()
        plt.pause(0.05) 
        
        self.robot_num = 1
        self.leader = False
        self.devices = {}
        self.quadrants = {1: 'C', 2: 'D', 3: 'A', 4: 'B'}
        
        

    async def main(self):
        while True:
            self.rcvd = self.transceiver.receive(60)
            if self.rcvd:
                action = self.received_action()
                leader = self.received_leader_id()
                follow = self.received_follower_id()
                payload = self.received_payload()
                if not self.leader and action == 6:
                    self.leader = True
                    self.leader_id = leader
                    p, rnum, n = self.new_robot(True, leader)
                    self.devices[leader] = [None, n, p, rnum]
                elif action == 2 and (follow not in self.devices):
                    p, rnum, n = self.new_robot(False, follow)
                    self.devices[follow] = [None, n, p, rnum]
                elif action == 3 and (self.devices[follow][0] == None):
                    self.devices[follow][0] = payload
                    p, rnum = self.move_robot(follow, payload)
                    self.devices[follow][2] = p
                    self.devices[follow][3] = rnum
                elif action == 5:
                    self.delete_robot(follow)
                    del self.devices[follow]
                elif self.leader and action == 6:
                    self.delete_robot(self.leader_id)
                    self.leader_id = leader
                    self.make_leader(leader)
                
    # when robot first responds to attendance -> make blue robot appear in corner
    def new_robot(self, leader, robot_id):
        alert = self.axs[1, 0].text(0.5,0.5, f"New Robot Joined!", size=20, ha="center", va="center")
        color = 'purple'
        if leader:
            color = 'red'
        robot = patches.Rectangle((0.3,0.3), .4, .4, edgecolor=color, facecolor=color)
        rnum = self.axs[0, 0].text(0.5,0.5, f"{self.robot_num}", size=20, ha="center", va="center")
        self.axs[0, 0].add_patch(robot)
        plt.draw()
        plt.pause(4) 
        self.robot_num += 1
        alert.remove()
        plt.draw()
        plt.pause(0.05) 
        return robot, rnum, self.robot_num - 1
    
    # when task gets assigned to robot -> arrow appears with quadrant number
    # wait 5 seconds then move robot to quadrant  
    def move_robot(self, robot_id, payload):
        assign = self.axs[1, 0].text(0.5,0.5, f" Robot {self.devices[robot_id][1]}: \nAssigned Quadrant {self.quadrants[payload]}", size=20, ha="center", va="center")
        plt.draw()
        plt.pause(4)
        self.devices[robot_id][2].remove()
        self.devices[robot_id][3].remove()
        plt.draw()
        plt.pause(0.05)
        color = 'purple'
        if robot_id == self.leader_id:
            color = 'red'
        
        if payload == 1:
            robot = patches.Rectangle((0.3,0.3), .4, .4, edgecolor=color, facecolor=color)
            rnum = self.axs[0, 2].text(0.5,0.5, f"{self.devices[robot_id][1]}", size=20, ha="center", va="center")
            self.axs[0, 2].add_patch(robot)
        
        elif payload == 2:
            robot = patches.Rectangle((0.3,0.3), .4, .4, edgecolor=color, facecolor=color)
            rnum = self.axs[1, 2].text(0.5,0.5, f"{self.devices[robot_id][1]}", size=20, ha="center", va="center")
            self.axs[1, 2].add_patch(robot)
        elif payload == 3:
            robot = patches.Rectangle((0.3,0.3), .4, .4, edgecolor=color, facecolor=color)
            rnum = self.axs[0, 1].text(0.5,0.5, f"{self.devices[robot_id][1]}", size=20, ha="center", va="center")
            self.axs[0, 1].add_patch(robot)
        elif payload == 4:
            robot = patches.Rectangle((0.3,0.3), .4, .4, edgecolor=color, facecolor=color)
            rnum = self.axs[1, 1].text(0.5,0.5, f"{self.devices[robot_id][1]}", size=20, ha="center", va="center")
            self.axs[1, 1].add_patch(robot)
        plt.draw()
        plt.pause(1) 
        assign.remove()
        plt.draw()
        plt.pause(0.05)
        return robot, rnum

    # either takeover recognized or delete message sent
    def delete_robot(self, robot_id):
        alert = self.axs[1, 0].text(0.5,0.5, f" Robot {self.devices[robot_id][1]}: \nDisconnected", size=20, ha="center", va="center")
        plt.draw()
        plt.pause(1)
        self.devices[robot_id][2].remove()
        self.devices[robot_id][3].remove()
        plt.draw()
        plt.pause(4) 
        alert.remove()
        plt.draw()
        plt.pause(0.05)
   
    def make_leader(self, robot_id):
        alert = self.axs[1, 0].text(0.5,0.5, f" Robot {self.devices[robot_id][1]}: \nBecame Leader", size=20, ha="center", va="center")
        plt.draw()
        plt.pause(1)
        self.devices[robot_id][2].set_facecolor('red')
        plt.draw()
        plt.pause(0.05)
        
        plt.draw()
        plt.pause(4) 
        alert.remove()
        plt.draw()
        plt.pause(0.05)
        return robot, rnum
        
    def received_action(self):
        """
        :return: action bit of last received message
        :raise: ValueError if no message was received
        """
        if not self.rcvd:
            raise ValueError("No message was received")
        return self.rcvd // int(1e10)
        
    def received_leader_id(self) -> int:
        """
        :return: leader id of last received message
        :raise: ValueError if no message was received
        """
        if not self.rcvd:
            raise ValueError("No message was received")
        return self.rcvd % int(1e8) // int(1e4)

    def received_follower_id(self) -> int:
        """
        :return: follower id of last received message
        :raise: ValueError if no message was received
        """
        if not self.rcvd:
            raise ValueError("No message was received")
        return self.rcvd % int(1e4)

    def received_payload(self) -> int:
        """
        :return: payload of last received message
        :raise: ValueError if no message was received
        """
        if not self.rcvd:
            raise ValueError("No message was received")
        return self.rcvd % int(1e10) // int(1e8)  
            
if __name__ == "__main__":
    ui = UserInterface(transceiver=ZigbeeTransceiver(broker_address='192.168.68.89', broker_port=1883, active= multiprocessing.Value('i', 2)))
    asyncio.run(ui.main())
