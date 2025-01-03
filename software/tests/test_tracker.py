import unittest
from mpp_tracker.tracker import OBoardManager, OBoard, Channel
from unittest.mock import MagicMock, patch

class TestOBoardManager(unittest.TestCase):
    def setUp(self):
        self.mock_i2c = MagicMock()
        self.mock_i2c.scan.return_value = [32, 72, 96, 97]
        
    @patch('mpp_tracker.tracker.ExtendedI2C')
    def test_setup_boards(self, mock_i2c_class):
        mock_i2c_class.return_value = self.mock_i2c
        manager = OBoardManager(i2c_num=1)
        self.assertTrue(len(manager.oboards) > 0)

class TestOBoard(unittest.TestCase):
    def setUp(self):
        self.mock_i2c = MagicMock()
        
    @patch('mpp_tracker.tracker.ExtendedI2C')
    def test_board_initialization(self, mock_i2c_class):
        mock_i2c_class.return_value = self.mock_i2c
        board = OBoard(i2c_num=1)
        self.assertEqual(len(board.channel), 8)