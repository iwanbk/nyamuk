import sys

import bee

class Subscription: 
    '''Class yang merepresentasikan subscription oleh sebuah client.'''
    def __init__(self, bee, topic, qos):
        self.topic = topic
        self.bee = bee
        self.qos = qos
        self.id = bee.id + str(qos)
    
    def dump(self):
        print "- bee.id = ",self.bee.id," qos = ", self.qos
        
class SubscriptionManager:
    '''MQTT Subscription Manager.
    
    Me-manage subscription di mqtt server
    '''
    
    def __init__(self):
        self.dict = {}
    
    def add(self, bee, topic, qos):
        ''' add topic to subscription list of some bee.'''
        if topic not in self.dict:
            self.dict[topic] = {}
        
        sub = Subscription(bee, topic, qos)
        topic_dict = self.dict[topic]
        
        if sub.id not in self.dict[topic]:
            topic_dict[sub.id] = sub
        
        print "---ALL SUBSCRIBER OF TOPIC ", topic
        self.print_subscriber(topic)
        
    def get_subscriber(self, topic):
        """Get subscriber of some topic."""
        list_subscriber = []
        
        if topic not in self.dict:
            return list_subscriber
        
        topic_dict = self.dict[topic]
        for k,sub in topic_dict.iteritems():
            list_subscriber.append(sub)
        
        return list_subscriber
    def print_subscriber(self, topic):
        """Print all subscriber of some topic."""
        ls = self.get_subscriber(topic)
        
        for s in ls:
            s.dump()
    
    def get_hier_list(self, topic):
        """Get list of topic hierarchi."""
        hier_list = topic.split("/")
        
        #TODO : cek hasil splitan :)
        
        return hier_list