import time

class PacketLossCalculator:
    def __init__(self, plr_sec: int):
        self.fCnt = 0  # Last frame count
        self.totalpl = 0  # Total packet loss
        self.pckcount = 0  # Total packets received
        self.plr_sec = plr_sec # rate of plr calculation in seconds, 1 hour = 3600 seconds
        self.last_calculation_time = time.time()  # Track the last calculation time

    def process_packet(self, fCnt):
        """Process the packet to calculate packet loss and packet loss rate based on a time interval"""
        # Initialize fCnt if not already set
        if fCnt and self.fCnt == 0:
            self.fCnt = fCnt

        # Calculate packet loss based on fCnt difference
        if fCnt > self.fCnt:
            pl = (fCnt - self.fCnt - 1)
            self.totalpl += pl

        # Update the last received fCnt
        self.fCnt = fCnt

        # Increment packet count
        self.pckcount += 1

        # Calculate packet loss rate every hour
        current_time = time.time()
        if current_time - self.last_calculation_time >= self.plr_sec:
            plr = self.totalpl / (self.pckcount + self.totalpl) if (self.pckcount + self.totalpl) > 0 else 0
            plr = plr * 100
            
            # Reset for the next hour
            self.totalpl = 0
            self.pckcount = 0
            self.last_calculation_time = current_time

            return (pl,plr)
        return (pl,None)
