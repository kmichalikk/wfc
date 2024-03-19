import panda3d.core as p3d
from direct.distributed.PyDatagram import PyDatagram


class Client:
    def __init__(self):
        self.connection_manager = p3d.QueuedConnectionManager()
        self.connection_reader = p3d.QueuedConnectionReader(self.connection_manager, 0)
        self.connection_writer = p3d.ConnectionWriter(self.connection_manager, 0)
        self.connection = None

    def connect(self, ip: str, port: int):
        self.connection = self.connection_manager.open_TCP_client_connection(ip, port, 3000)
        if self.connection:
            self.connection_reader.add_connection(self.connection)
            test = PyDatagram()
            test.addString("Hello World!")
            self.connection_writer.send(test, self.connection)
