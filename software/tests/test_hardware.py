import unittest
from mpp_tracker.hardware import ExtendedI2C, Softdac
from unittest.mock import MagicMock, patch

class TestExtendedI2C(unittest.TestCase):
    @patch('os.path.exists')
    def test_i2c_initialization(self, mock_exists):
        mock_exists.return_value = True
        i2c = ExtendedI2C(1)
        self.assertIsNotNone(i2c)

class TestSoftdac(unittest.TestCase):
    def setUp(self):
        self.mock_mux = MagicMock()
        self.softdac = Softdac(self.mock_mux)
    
    def test_gain_setting(self):
        self.softdac.gain = 1
        self.assertEqual(self.softdac.gain, 1)