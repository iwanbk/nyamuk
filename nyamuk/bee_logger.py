import logging

class BeeLogger:
    def __init__(self, level):
        logger = logging.Logger("BeeLogger")
        
        self.logger = logging.getLogger("BeeLogger")
        self.logger.setLevel(level)
        
        ch = logging.StreamHandler()
        ch.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        
    
    def debug(self, s):
        self.logger.debug(s)
    
    def warn(self, s):
        self.logger.warn(s)
        
    def error(self, s):
        self.logger.error(s)
    
    def critical(self, s):
        self.logger.critical(s)