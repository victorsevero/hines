import numpy as np


class ROM:
    def __init__(self, filepath):
        with open(filepath, "rb") as file:
            header = file.read(16)
            self._parse_ines_header(header)
            self._load_prg_rom(file)

    def _parse_ines_header(self, header):
        assert header[:4] == b"NES\x1a", "Invalid iNES ROM file."

        self.number_prg_rom_banks = header[4]
        self.number_chr_rom_banks = header[5]
        self._parse_control_byte1(header[6])
        self._parse_control_byte2(header[7])
        self._parse_mapper()

    def _parse_control_byte1(self, byte):
        bits = np.binary_repr(byte, width=8)
        vertical_mirroring = bool(bits[-1])
        self.battery_ram = bool(bits[-2])
        self.trainer = bool(bits[-3])
        four_screen_vram = bool(bits[-4])
        self.lower_mapper = bits[-8:-4]

        mirroring = (vertical_mirroring, four_screen_vram)
        match mirroring:
            case True, _:
                self.mirroring = "four_screen"
            case False, True:
                self.mirroring = "vertical"
            case False, False:
                self.mirroring = "horizontal"

    def _parse_control_byte2(self, byte):
        bits = np.binary_repr(byte, width=8)
        assert (
            int(bits[-4:-2], base=2) == 0
        ), "iNES different than v1.0 not supported"
        self.upper_mapper = bits[-8:-4]

    def _parse_mapper(self):
        self.mapper = int(self.upper_mapper + self.lower_mapper)
        assert self.mapper == 0, f"Mapper {self.mapper} not supported"

    def _load_prg_rom(self, file):
        prg_rom_size = self.number_prg_rom_banks * 16 * 1024  # 16KB per bank
        prg_rom_data = file.read(prg_rom_size)
        prg_rom_data = np.frombuffer(prg_rom_data, dtype=np.uint8)
        self.prg_rom_data = prg_rom_data

        chr_rom_size = self.number_chr_rom_banks * 8 * 1024  # 8KB per bank
        chr_rom_data = file.read(chr_rom_size)
        chr_rom_data = np.frombuffer(chr_rom_data, dtype=np.uint8)
        self.chr_rom_data = chr_rom_data
