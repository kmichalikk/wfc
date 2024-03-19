import os

from direct.showbase.ShowBase import ShowBase

from server import Server

if __name__ == "__main__":
    server = Server()
    base = ShowBase(windowType="none")
    server.listen(os.environ.get("PORT", 7654))
    base.run()
