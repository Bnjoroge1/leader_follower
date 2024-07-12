#!/usr/bin/python3
#coding:utf8

#HW_WIFI_MODE = 1                     #wifi的工作模式， 1为AP模式， 2为STA模式/ WiFi mode. 1 refers to AP mode and 2 refers to STA mode.
#HW_WIFI_AP_SSID = 'ssid_name'        #AP模式下的SSID。字符和数字构成/ SSID under AP mode consists of character and number 
#HW_WIFI_AP_PASSWORD = 'password'     #AP模式下的WIFI密码,字符和数字构成/ The WIFI password under AP mode consists of character and number.
#HW_WIFI_AP_GATEWAY = '192.168.149.1' #AP模式下的本机IP, 默认为192.168.149.1, 若修改了本项，手机APP上会无法进入wifi配置界面 /The local IP under AP mode is 192.168.149.1 by default. If this part is modified, app fails to enter WIFI configuration interface.
HW_WIFI_FREQ_BAND = 5                 #AP模式下的wifi频率， 直接赋值为 2.4 或 5 对应2.4G和5G/ WiFi frequency under AP mode is 2.4 or 5 corresponding to 2.4G and 5G.
HW_WIFI_CHANNEL = 149                 #AP模式下的wifi信道，5G下目前测试可用的有 149, 153, 157, 161/ The wifi channel in AP mode, currently available in 5G testing are 149, 153, 157, 161
#HW_WIFI_STA_SSID = 'ssid_name'       #STA模式下的SSID/ SSID under STA mode 
#HW_WIFI_STA_PASSWORD = 'password'    #STA模式下的WIFI密码/ The WIFI password under STA mode 
#HW_WIFI_TIMEOUT  = 30                #STA连接到wifi热点时的超时时间， 超过时间未成功连接则认为连接失败，默认为 30秒/ The default timeout of WIFI connection is 30s.
#HW_WIFI_LED  = True                  #是否使用LED指示灯， 默认为True， 使用LED指示灯 /Whether to use LED indicator. "True" by default.
#HW_WIFI_RESET_NOW = False            #清除所有配置文件， 默认为False，当设置为True时，程序会清除所有配置， 恢复初始状态， 包括手机配置的和手动编辑配置文件的。/Clear all configuration files. The default setting is False. When it is "True", program will clear all configuration and retore to the initial status, including phone configuration files and manual coding files
