import unittest
import sys
sys.path.append('../protocol')

from message_classes import Message


class TestMessageClass(unittest.TestCase):

    def setUp(self):
        pass

    def test_constructor(self):
        basic_msg = Message(1, 0, 0, 0, 0)
        corr_msg = 1e26
        message = "Basic constructor message not equal to 1e26"
        self.assertEqual(basic_msg.msg, corr_msg, message)

if __name__ == '__main__':
    unittest.main()
    

    

    