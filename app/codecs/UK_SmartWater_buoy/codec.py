"""
UK SmartWater Buoy codec for LoRaWAN Listener.
8 bytes, big-endian u16 fields
-> battery_voltage_v, temperature_c (from Kelvin), fec (TDS), turbidity.
"""
import struct


class Codec:
    """Decoder for UK SmartWater Buoy payloads (8 bytes, big-endian)."""

    def decode(self, payload_bytes: bytes) -> dict:
        """
        Decode raw payload bytes into a flat dict of name -> value.
        Format: 2 bytes vbat, 2 bytes temp (K×100), 2 bytes TDS, 2 bytes turbidity (all big-endian u16).
        """
        if len(payload_bytes) < 8:
            return {}
        try:
            vbat_raw = struct.unpack_from(">H", payload_bytes, 0)[0]
            temp_raw = struct.unpack_from(">H", payload_bytes, 2)[0]
            tds_raw = struct.unpack_from(">H", payload_bytes, 4)[0]
            turb_raw = struct.unpack_from(">H", payload_bytes, 6)[0]

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
        except struct.error:
            return {}
