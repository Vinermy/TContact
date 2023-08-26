from ConnectionManager import TContactConnectionManager


class Server:
    def __init__(self):
        self.CM = TContactConnectionManager()

    def run(self):
        self.CM.start_listening()
