import time
import Board

print('''
**********************************************************
********功能:幻尔科技树莓派扩展板，蜂鸣器控制例程 Control Buzzer*********
**********************************************************
----------------------------------------------------------
Official website:https://www.hiwonder.com
Online mall:https://hiwonder.tmall.com
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可关闭此次程序运行，若失败请多次尝试！ Press Ctrl+C to exit the program, please try few more times if fail to exit!
----------------------------------------------------------
''')

Board.setBuzzer(0) # 关闭 OFF

Board.setBuzzer(1) # 打开 ON
time.sleep(0.1) # 延时 Delay
Board.setBuzzer(0) #关闭 OFF

time.sleep(1) # 延时 Delay

Board.setBuzzer(1)
time.sleep(0.5)
Board.setBuzzer(0)