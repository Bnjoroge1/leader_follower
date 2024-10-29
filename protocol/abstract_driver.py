from abc import abstractmethod, ABCMeta


class AbstractDriver(abc=ABCMeta):

    @abstractmethod
    async def main():
        pass