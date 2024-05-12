from common.transfer.network_transfer import NetworkTransfer
from common.typings import Messages
from server.chain_of_responsibility.abstract_handler import AbstractHandler
from server.typings import HandlerContext


class HelloHandler(AbstractHandler):
    def __init__(self):
        super().__init__()

    def handle(self, context: HandlerContext) -> list[NetworkTransfer]:
        if context.message != Messages.HELLO:
            return self.pass_to_next(context)

        print("[INFO] New player")

        return []
