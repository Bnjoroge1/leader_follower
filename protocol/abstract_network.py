from abc import abstractmethod, ABCMeta

class AbstractNode(metaclass=ABCMeta):

    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def join(self):
        pass

    @abstractmethod
    def set_outgoing_channel(self, target_node_id, queue):
        pass

    @abstractmethod
    def set_incoming_channel(self, target_node_id, queue):
        pass


class AbstractTransceiver(metaclass=ABCMeta):

    @abstractmethod
    def set_outgoing_channel(self, node_id, queue):
        pass

    @abstractmethod
    def set_incoming_channel(self, node_id, queue):
        pass

    @abstractmethod
    def send(self, msg):
        pass

    @abstractmethod
    def receive(self, timeout):
        pass

    @abstractmethod
    def clear(self):
        pass