"""Teensy ile seri haberlesme arayuzu.

firmware/tulpar_teensy'deki I2CBus/DijitalCikis "gercek/mock arayuz" deseniyle
ayni mantik: pyserial bagimliligi sadece GercekSeriPort'ta, testler ve
donanimsiz gelistirme MockSeriPort ile yapilir.
"""

import threading


class SeriPort:
    """Arayuz: yaz(satir) - '\\n' cagiran tarafta eklenmez, burada eklenir."""

    def yaz(self, satir: str) -> None:
        raise NotImplementedError


class GercekSeriPort(SeriPort):
    """Gercek donanim - pyserial (python3-serial) gerektirir."""

    def __init__(self, port: str, baud: int, timeout: float = 1.0):
        import serial  # noqa: PLC0415 - bilerek lazy import, mock testte gerekmiyor

        self._lock = threading.Lock()
        self._ser = serial.Serial(port, baud, timeout=timeout)

    def yaz(self, satir: str) -> None:
        with self._lock:
            self._ser.write((satir + '\n').encode('ascii'))
            self._ser.flush()

    def close(self) -> None:
        with self._lock:
            self._ser.close()


class MockSeriPort(SeriPort):
    """Test icin - yazilan tum satirlari sirayla saklar, gercek port acmaz."""

    def __init__(self):
        self.yazilanlar = []

    def yaz(self, satir: str) -> None:
        self.yazilanlar.append(satir)
