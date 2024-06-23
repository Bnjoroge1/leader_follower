import unittest
import sys
from base_test import PROTOCOL_DIR
sys.path.append(str(PROTOCOL_DIR))
import device_classes as dc

class TestDeviceClass(unittest.TestCase):
    def setUp(self):
        pass

    # waiting till after hash function made then will stress test
    def testContructorId(self):
        pass

    def testSetNegativeTask(self):
        pass

    # TODO: test potential getter/setter edge cases if necessary (negatives)

class TestThisDevice(unittest.TestCase):
    def setUp(self):
        pass

    # below tests will be based on communication channel model created 
    # TODO: test send function
    def sendStressTest(self):
        pass
        
    # TODO: test receive function
    def receiveStressTest(self):
        pass
    # TODO: test setup function



class TestDeviceList(unittest.TestCase):
    def setUp(self):
        pass

    # TODO: test basic funcs: tostring, add, remove

    # TODO: test unused tasks - edge cases to think about: tasks assigned out of order

    # TODO: test update tasks - check all exceptions added

if __name__ == '__main__':
    unittest.main()