"""
UK SmartWater Buoy codec for LoRaWAN Listener.
7 or 8 bytes, big-endian u16 fields
-> battery_voltage_v, temperature_c (from Kelvin×100), fec (TDS/10), turbidity (turb/10).
With 7 bytes, the last u16 is (bytes[6]<<8)|0 (JS treats missing byte as 0).
"""
import struct


class Codec:
    """Decoder for UK SmartWater Buoy payloads (7 or 8 bytes, big-endian)."""

    def decode(self, payload_bytes: bytes) -> dict:
        """
        Decode raw payload bytes into a flat dict of name -> value.
        Format: 2 bytes vbat, 2 temp (K×100), 2 TDS, 2 turbidity (big-endian u16).
        Accepts 7 bytes: turbidity u16 is then (high_byte << 8).
        """
        if len(payload_bytes) < 7:
            return {}
        try:
            vbat_raw = struct.unpack_from(">H", payload_bytes, 0)[0]
            temp_raw = struct.unpack_from(">H", payload_bytes, 2)[0]
            tds_raw = struct.unpack_from(">H", payload_bytes, 4)[0]
            if len(payload_bytes) >= 8:
                turb_raw = struct.unpack_from(">H", payload_bytes, 6)[0]
            else:
                turb_raw = (payload_bytes[6] << 8) | 0

            battery_voltage_v = round((vbat_raw * 3.3) / 512, 3)
            temperature_c = round(temp_raw / 100.0 - 273.15, 1)
            fec = round(tds_raw / 10.0, 2)
            turbidity = round(turb_raw / 10.0, 2)

            return {
                "battery_voltage_v": battery_voltage_v,
                "temperature_c": temperature_c,
                "fec": fec,
                "turbidity": turbidity,
            }
        except (struct.error, IndexError):
            return {}
