import pickle
import panda3d.core as p3d
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.showbase.DirectObject import DirectObject
from direct.task.TaskManagerGlobal import taskMgr
from common.typings import Messages


class Connection(DirectObject):
    def __init__(self):
        super().__init__()
        self.connection_manager = p3d.QueuedConnectionManager()
        self.connection_reader = p3d.QueuedConnectionReader(self.connection_manager, 0)
        self.connection_writer = p3d.ConnectionWriter(self.connection_manager, 0)
        self.connection = None
        self.tiles = None

    def initialize(self, ip: str, port: int):
        self.connection = self.connection_manager.open_TCP_client_connection(ip, port, 3000)
        if self.connection:
            self.connection_reader.add_connection(self.connection)

    def find_room(self, callback):
        def poll(task):
            if not self.connection_reader.data_available():
                return task.cont

            datagram = p3d.NetDatagram()
            if not self.connection_reader.get_data(datagram):
                return task.cont

            data = PyDatagramIterator(datagram)
            message = data.get_uint8()
            if message == Messages.FIND_ROOM_OK:
                accept_datagram = PyDatagram()
                accept_datagram.add_uint8(Messages.ACCEPT_ROOM)
                self.connection_writer.send(accept_datagram, self.connection)
            elif message == Messages.ACCEPT_ROOM_OK:
                self.tiles = pickle.loads(data.get_blob())
                callback()
                return task.done

            return task.cont

        join_datagram = PyDatagram()
        join_datagram.add_uint8(Messages.FIND_ROOM)
        self.connection_writer.send(join_datagram, self.connection)
        taskMgr.add(poll, "find room")

    def poll_reader(self, task):
        if self.connection_reader.data_available():
            datagram = p3d.NetDatagram()
            if self.connection_reader.get_data(datagram):
                print("[INFO] Received datagram", datagram)
        return task.cont
