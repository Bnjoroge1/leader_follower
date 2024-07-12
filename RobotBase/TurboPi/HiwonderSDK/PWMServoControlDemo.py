#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/TurboPi/')
import time
import signal
import threading
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)
    
print('''
**********************************************************
********功能:幻尔科技树莓派扩展板，PWM舵机控制例程 PWM Servo Control **********
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！ Press Ctrl+C to exit the program, please try few more times if fail to exit!
----------------------------------------------------------
''')

start = True
#关闭前处理 Processing before exit 
def Stop(signum, frame):
    global start

    start = False
    print('关闭中...')

signal.signal(signal.SIGINT, Stop)

if __name__ == '__main__':
    
    while True:
        Board.setPWMServoPulse(1, 1500, 1000) # 设置1号舵机脉宽为1500，运行时间为1000毫秒  The pulse width of No.1 servo is set as 1500 and the running time is set as 1000ms.
        time.sleep(1)
        Board.setPWMServoPulse(1, 2500, 1000) # 设置1号舵机脉宽为2500，运行时间为1000毫秒 The pulse width of No.1 servo is set as 2500 and the running time is set as 1000ms.
        time.sleep(1)
        
        if not start:
            Board.setPWMServoPulse(1, 1500, 1000) # 设置1号舵机脉宽为1500，运行时间为1000毫秒  The pulse width of No.1 servo is set as 1500 and the running time is set as 1000ms.
            time.sleep(1)
            print('Closed')
            break
    
    
        