from lb_logger import logger
import unittest
from labelbox import Client
import logging
import os

api_key = os.environ['apikey']

class TestLoggerMessages(unittest.TestCase):
    "Test that the logger's out put will match the expected levels set by logger"

    def setUp(self):
        self.msg = "Test message"
        self.test_logger = logger
    
    def test_info_msg(self) -> None: 
        with self.assertLogs(self.test_logger) as assert_log:
            self.test_logger.info(self.msg)
        self.assertEqual(assert_log.output, ['INFO:lb_logger:%s' %(self.msg)])

    def test_warning_msg(self) -> None: 
        with self.assertLogs(self.test_logger) as assert_log:
            self.test_logger.warning(self.msg)
        self.assertEqual(assert_log.output, ['WARNING:lb_logger:%s' %(self.msg)])    

    def test_error_msg(self) -> None: 
        with self.assertLogs(self.test_logger) as assert_log:
            self.test_logger.error(self.msg)
        self.assertEqual(assert_log.output, ['ERROR:lb_logger:%s' %(self.msg)])    

    def test_critical_msg(self) -> None:      
        with self.assertLogs(self.test_logger) as assert_log:
            self.test_logger.critical(self.msg)
        self.assertEqual(assert_log.output, ['CRITICAL:lb_logger:%s' %(self.msg)])     

    def test_verbosity(self) -> None:     
        assert self.test_logger.level == logging.NOTSET
        client = Client(api_key=api_key, verbose=True)
        assert self.test_logger.level == logging.INFO 