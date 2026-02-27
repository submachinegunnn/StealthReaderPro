from pypresence import Presence
import time

class DiscordHandler: # Changed from DiscordPresence to DiscordHandler
    def __init__(self, client_id="123456789012345678"): # Replace with your actual ID
        self.client_id = client_id
        self.rpc = None
        self.start_time = time.time()

    def connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
        except:
            self.rpc = None

    def update_presence(self, state, details):
        if self.rpc:
            try:
                self.rpc.update(
                    state=state,
                    details=details,
                    start=self.start_time,
                    large_image="stealth_logo" 
                )
            except:
                pass