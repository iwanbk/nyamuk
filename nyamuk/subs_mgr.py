import sys

import bee

class Subscription: 
    '''Class yang merepresentasikan subscription oleh sebuah client.'''
    def __init__(self, bee, topic, qos):
        self.topic = topic
        self.bee = bee
        self.qos = qos
        
class SubscriptionManager:
    '''MQTT Subscription Manager.
    
    Me-manage subscription di mqtt server
    '''
    
    def __init__(self):
        self.dict = {}
    
    def add(self, bee, topic, qos):
        ''' add topic to subscription list of some bee.'''
        if bee.id not in self.dict:
            self.dict[bee.id] = []
        
        sub = Subscription(bee, topic, qos)
        
        if topic not in self.dict[bee.id]:
            self.dict[bee.id].append(topic)
    
    def check(self, bee, topic):
        '''Chek if a bee already listed on some topic.'''
        if bee.id not in self.dict:
            return False
        if topic not in self.dict[bee.id]:
            return False
        return True
    