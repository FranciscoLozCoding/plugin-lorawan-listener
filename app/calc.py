"""
Packet loss and packet loss rate (PLR) calculator.

Tracks frame counts per device and computes packet loss and PLR over a configurable
time interval. Used by the shared publish pipeline for signal metrics (signal.pl, signal.plr).
"""
import time
from typing import Any, Dict, Optional, Tuple


class PacketLossCalculator:
    """Computes packet loss and PLR per device over a sliding time window."""

    def __init__(self, plr_sec: int) -> None:
        """
        plr_sec: Time interval in seconds over which PLR is computed (e.g. 3600 for hourly).
        """
        self.devices: Dict[Any, Dict[str, Any]] = {}
        self.plr_sec = plr_sec

    def process_packet(
        self, deveui: Any, fCnt: Optional[int]
    ) -> Tuple[int, Optional[float]]:
        """
        Process a packet from a device and update packet loss state.

        Returns (pl, plr): pl is packet loss for this packet; plr is the current
        PLR percentage for the interval if the interval has elapsed, else None.
        """
        # Initialize device data if not already present
        if deveui not in self.devices:
            self.devices[deveui] = {
                "fCnt": 0,  # Last frame count
                "totalpl": 0,  # Total packet loss
                "pckcount": 0,  # Total packets received
                "last_calculation_time": time.time()  # Last PLR calculation time
            }

        # Reference device data
        device = self.devices[deveui]

        # Initialize fCnt if not already set
        if fCnt and device["fCnt"] == 0:
            device["fCnt"] = fCnt

        # Calculate packet loss for this packet
        pl = 0
        if fCnt > device["fCnt"]:
            pl = (fCnt - device["fCnt"] - 1)
            device["totalpl"] += pl

        # Update the last received fCnt
        device["fCnt"] = fCnt

        # Increment packet count
        device["pckcount"] += 1

        # Calculate PLR for this device if the time interval has passed
        current_time = time.time()
        if current_time - device["last_calculation_time"] >= self.plr_sec:
            total_packets = device["pckcount"] + device["totalpl"]
            plr = (device["totalpl"] / total_packets * 100) if total_packets > 0 else 0
            plr = round(plr, 2)#Format PLR to two decimal places

            # Reset the counters for the next interval
            device["totalpl"] = 0
            device["pckcount"] = 0
            device["last_calculation_time"] = current_time

            return (pl, plr)
        return (pl, None)
