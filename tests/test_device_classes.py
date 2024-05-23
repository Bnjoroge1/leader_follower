import unittest
import sys
sys.path.append('../protocol')

from device_classes import Device, ThisDevice, DeviceList

class TestDeviceClass(unittest.TestCase):
    def setUp(self):
        pass

    def testContructorId(self):
        pass

    # TODO: test potential getter/setter edge cases if necessary (negatives)

class TestThisDevice(unittest.TestCase):
    def setUp(self):
        pass

    # below tests will be based on communication channel model created 
    # TODO: test send function

    # TODO: test receive function

    # TODO: test setup function

class TestDeviceList(unittest.TestCase):
    def setUp(self):
        pass

    # TODO: test basic funcs: tostring, add, remove

    # TODO: test unused tasks - edge cases to think about: tasks assigned out of order

    # TODO: test update tasks - check all exceptions added

if __name__ == '__main__':
    unittest.main()