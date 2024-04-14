from queue import Queue
from select import select
from socket import socket, socketpair, AF_INET, SOCK_DGRAM
from direct.stdpy.threading import Thread, Lock

from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder


class UDPConnectionThread(Thread):
    """ Thread class comes from panda3d - beware incompatibilities! """
    def __init__(self, addr, port, server=False):
        super().__init__()
        self.addr = addr
        self.port = port

        # set up a way to safely communicate between threads
        # incoming = transfer received from clients
        # outgoing = queued transfers to send
        self.lock = Lock()
        self.incoming: list[NetworkTransfer] = []
        self.outgoing: Queue[NetworkTransfer] = Queue()

        # smart way to handle both incoming and outgoing transfers
        # pipe_in sends control signal to pipe_out which is selected
        # along with data from clients to handle both cases in one waiting loop
        self.pipe_out_socket, self.pipe_in_socket = socketpair()

        # set up IP sockets
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        if server:
            self.udp_socket.bind((self.addr, self.port))
        self.network_transfer_builder = NetworkTransferBuilder()

    def get_queued_transfers(self):
        self.lock.acquire()
        cpy = self.incoming.copy()
        self.incoming = []
        self.lock.release()
        return [transfer for transfer in cpy]

    def enqueue_transfer(self, transfer: NetworkTransfer):
        self.lock.acquire()
        self.outgoing.put(transfer)
        self.lock.release()
        # control message to send data out to client
        self.pipe_in_socket.send(b"\x00")

    def run(self):
        while True:
            # handle incoming or outgoing depending on which socket got data first
            ready_sockets, _, _ = select([self.udp_socket, self.pipe_out_socket], [], [])
            if self.udp_socket in ready_sockets:
                payload, addr = self.udp_socket.recvfrom(10240)
                self.lock.acquire()
                self.network_transfer_builder.set_source(addr)
                self.incoming.append(self.network_transfer_builder.decode(payload))
                self.lock.release()
            elif not self.outgoing.empty():
                self.pipe_out_socket.recv(1)
                self.lock.acquire()
                transfer = self.outgoing.get()
                self.lock.release()
                self.udp_socket.sendto(transfer.get_payload(), transfer.get_destination())
