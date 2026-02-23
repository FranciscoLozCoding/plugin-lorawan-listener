"""
Example codec for LoRaWAN Listener codec fallback.
The listener expects a class Codec with a method decode(payload_bytes) that returns
a flat dict of measurement name -> value. The listener will convert this to the
internal measurements format and normalize names (e.g. clean_string).
"""
import struct


class Codec:
    """Example decoder: expects at least 6 bytes -> temperature (int16, 0.1°C) and humidity (uint16, 0.01%)."""

    def decode(self, payload_bytes: bytes) -> dict:
        """
        Decode raw payload bytes into a flat dict of name -> value.
        Example format: 2 bytes temp (signed, 0.1°C), 2 bytes humidity (0.01%).
        """
        if len(payload_bytes) < 4:
            return {}
        try:
            temp_raw = struct.unpack_from("<h", payload_bytes, 0)[0]
            humidity_raw = struct.unpack_from("<H", payload_bytes, 2)[0]
            temperature = temp_raw / 10.0
            humidity = humidity_raw / 100.0
            return {
                "temperature": temperature,
                "humidity": humidity,
            }
        except struct.error:
            return {}
