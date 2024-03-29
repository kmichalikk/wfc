from queue import Queue
from select import select
from socket import socket, socketpair, AF_INET, SOCK_DGRAM
from direct.stdpy.threading import Thread, Lock

from common.transfer.network_transfer import NetworkTransfer
from common.transfer.network_transfer_builder import NetworkTransferBuilder


class UDPConnectionThread(Thread):
    def __init__(self, addr, port):
        super().__init__()
        self.addr = addr
        self.port = port
        self.lock = Lock()
        self.incoming: list[NetworkTransfer] = []
        self.outgoing: Queue[NetworkTransfer] = Queue()
        self.pipe_out_socket, self.pipe_in_socket = socketpair()
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
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
        self.pipe_in_socket.send(b"\x00")

    def run(self):
        while True:
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
                print("[UDP] Sending {} bytes".format(len(transfer.get_payload())))
                self.udp_socket.sendto(transfer.get_payload(), transfer.get_destination())
