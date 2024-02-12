import numpy as np

from rom import ROM


class Bus:
    RAM_START = 0x0000
    RAM_SIZE = 0x800
    RAM_MIRRORS_END = 0x1FFF
    PPU_REGS_START = 0x2000
    PPU_REGS_SIZE = 0x8
    PPU_REGS_MIRRORS_END = 0x3FFF
    PRG_ROM_START = 0x8000
    PRG_ROM_SIZE = 0x4000
    PRG_ROM_MIRRORS_END = 0xFFFF

    def __init__(self):
        self.cpu_vram = RAM(self.RAM_SIZE)
        self.fake_io = FakeIO()

    def load_rom(self, filepath: str):
        self.rom = ROM(filepath)
        self.PRG_ROM_SIZE = self.rom.number_prg_rom_banks * 0x4000
        self.prg_rom = RAM(self.PRG_ROM_SIZE)
        # self.chr_rom = RAM(self.CHR_ROM_SIZE)

        self.prg_rom.write_chunk(0x0000, self.rom.prg_rom_data)
        # self.chr_rom.write_chunk(0x0000, self.rom.chr_rom_data)

    def read(self, address: np.uint16):
        component, address = self._memory_map(address)
        if address is None:
            return component.read()
        return component.read(address)

    def read16(self, address: np.uint16, page_wrap: bool = False):
        component, address = self._memory_map(address)
        # TODO: check if no other component has this feature but CPU RAM
        return component.read16(address, page_wrap=page_wrap)

    def read_chunk(self, address: np.uint16, size: np.uint16):
        component, address = self._memory_map(address)
        return component.read_chunk(address, size)

    def write(self, address: np.uint16, data: np.uint8):
        component, address = self._memory_map(address)
        if address is None:
            component.write(data)
        else:
            component.write(address, data)

    def write16(self, address, data):
        component, address = self._memory_map(address)
        # TODO: check if no other component has this feature but CPU RAM
        component.write16(address, data)

    def write_chunk(self, address: np.uint16, data: np.ndarray):
        component, address = self._memory_map(address)
        component.write_chunk(address, data)

    def _memory_map(self, address):
        if self.RAM_START <= address <= self.RAM_MIRRORS_END:
            address -= self.RAM_START
            address &= np.uint16(self.RAM_SIZE - 1)
            return self.cpu_vram, address
        elif self.PPU_REGS_START <= address <= self.PPU_REGS_MIRRORS_END:
            address -= self.PPU_REGS_START
            address &= np.uint16(self.PPU_REGS_SIZE - 1)
            print("PPU not supported yet")
            return self.fake_io, None
        elif self.PRG_ROM_START <= address <= self.PRG_ROM_MIRRORS_END:
            address -= self.PRG_ROM_START
            address &= np.uint16(self.PRG_ROM_SIZE - 1)
            return self.prg_rom, address
        else:
            print(f"Ignoring mem access at {hex(address)}")
            return self.fake_io, None


class RAM:
    def __init__(self, size):
        self.data = np.zeros((size,), dtype=np.uint8)

    def load_program(self, program: np.ndarray[np.uint8]):
        self.write_chunk(0x8000, program)

    def read_chunk(self, address, size):
        return self.data[address : address + size].copy()

    def read(self, address):
        return self.data[address].copy()

    def read16(self, address, page_wrap=False):
        address = np.uint16(address)
        if page_wrap and np.uint8(address) == 0xFF:
            page = np.uint8(address >> 8)
            lo = self.data[self._uint16_from_2bytes(np.uint8(0xFF), page)]
            hi = self.data[self._uint16_from_2bytes(np.uint8(0x00), page)]
        else:
            lo, hi = self.data[address : address + 2]
        return self._uint16_from_2bytes(lo, hi)

    def write_chunk(self, address, data):
        self.data[address : address + data.shape[0]] = data

    def write(self, address, data):
        self.data[address] = data

    def write16(self, address, data):
        data = np.uint16(data)
        lo = (data & 0xFF).astype(np.uint8)
        hi = ((data >> 8) & 0xFF).astype(np.uint8)
        self.data[address] = lo
        self.data[address + 1] = hi

    @staticmethod
    def _uint16_from_2bytes(lo, hi):
        return np.uint16((hi.astype(np.uint16) << 8) + lo.astype(np.uint16))


class FakeIO:
    def read(*args, **kwargs):
        ...

    def write(*args, **kwargs):
        ...


if __name__ == "__main__":
    bus = Bus()
    bus.load_rom("snake.nes")
