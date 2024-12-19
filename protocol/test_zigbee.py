from zigbee_network import ZigbeeTransceiver
from time import sleep
def sending_test():
    transceiver = ZigbeeTransceiver()
    msg = 12345678
    try:
        transceiver.send(msg)
        print("Send successful")
    except Exception as exc:
        print("ERROR: ", exc)

def receiving_test():
    transceiver = ZigbeeTransceiver()
    print('waiting')
    sleep(5)
    print('starting')
    try:
        msg = transceiver.receive(60)
        print("Received message:", msg)
    except Exception as exc:
        print("ERROR:", exc)

if __name__ == '__main__':
    # get send to work w no errors first 
    #sending_test()
    # then get receive to run w no errors (but not receiving msg)
    receiving_test()
    # once both run without errors, get two devices and have one run send and other run receive
