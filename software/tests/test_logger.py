import unittest
import os
import tempfile
from mpp_tracker.logger import DataLogger

class TestDataLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = DataLogger(base_path=self.temp_dir)
        
    def test_log_mpp_data(self):
        self.logger.log_mpp_data(
            "test_channel",
            "2024-01-01T00:00:00",
            1.0,  # voltage
            0.5,  # current
            100,  # dac_value
            2,    # adc_gain_v
            16    # adc_gain_c
        )
        expected_file = os.path.join(self.temp_dir, 'test_channel_data.csv')
        self.assertTrue(os.path.exists(expected_file))
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)