from abc import abstractmethod, ABCMeta
import websockets
import multiprocessing
import device_classes as dc

class AbstractNode(metaclass=ABCMeta):

    def setup(self, node_id, target_func = None, target_args = None, active: multiprocessing.Value = None):  # type: ignore
        self.node_id = node_id
        self.thisDevice = dc.ThisDevice(self.__hash__() % 10000, self.transceiver)  # replace with MAC or IEEE
        if not target_func:
            target_func = self.thisDevice.device_main
        if target_args:
            target_args = (self.transceiver, self.node_id)
            self.process = multiprocessing.Process(target=target_func, args=target_args)
        else:
            self.process = multiprocessing.Process(target=target_func)

    def start(self):
        self.process.start()
    
    @abstractmethod
    def stop(self):
        self.process.terminate()

    @abstractmethod
    def join(self):
        self.process.join()


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

    @abstractmethod
    def log(self, data: str):
        pass
