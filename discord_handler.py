from pypresence import Presence
import time

class DiscordPresence:
    def __init__(self, client_id):
        self.client_id = client_id
        self.rpc = None
        self.start_time = time.time()

    def connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.update("System Standby")
        except:
            self.rpc = None

    def update(self, details):
        if self.rpc:
            self.rpc.update(
                state="Stealth Reader Pro",
                details=details,
                start=self.start_time,
                large_image="stealth_logo" 
            )