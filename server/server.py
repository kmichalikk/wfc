import panda3d.core as p3d
from direct.task.TaskManagerGlobal import taskMgr


class Server:
    def __init__(self):
        self.connection_manager = p3d.QueuedConnectionManager()
        self.connection_listener = p3d.QueuedConnectionListener(self.connection_manager, 0)
        self.connection_reader = p3d.QueuedConnectionReader(self.connection_manager, 0)
        self.connection_writer = p3d.ConnectionWriter(self.connection_manager, 0)
        self.active_connections = []

    def listen(self, port):
        tcp_socket = self.connection_manager.open_TCP_server_rendezvous(port, 1000)
        self.connection_listener.add_connection(tcp_socket)
        taskMgr.add(self.poll_listener, "poll the connection listener", -39)
        taskMgr.add(self.poll_reader, "poll the connection reader", -40)
        print(f"[INFO] Server started on port {port}")

    def poll_listener(self, task):
        if self.connection_listener.new_connection_available():
            print("[INFO] New connection")
            rendezvous = p3d.PointerToConnection()
            net_address = p3d.NetAddress()
            new_connection = p3d.PointerToConnection()
            if self.connection_listener.get_new_connection(rendezvous, net_address, new_connection):
                new_connection = new_connection.p()
                self.active_connections.append(new_connection)
                self.connection_reader.add_connection(new_connection)
        return task.cont

    def poll_reader(self, task):
        if self.connection_reader.data_available():
            datagram = p3d.NetDatagram()
            if self.connection_reader.get_data(datagram):
                print("[INFO] Received datagram", datagram)
        return task.cont
