from datetime import datetime

import numpy as np

# https://skilldrick.github.io/easy6502/
# https://bugzmanov.github.io/nes_ebook/
# https://medium.com/@guilospanck/the-journey-of-writing-a-nes-emulator-part-i-the-cpu-6e83b50baa37
# https://www.copetti.org/writings/consoles/nes/
# https://codeburst.io/how-do-processors-actually-work-91dce24fbb44
np.seterr(over="ignore")


class CPU:
    def __init__(self, log=None):
        self.accumulator = Register()
        self.register_x = Register()
        self.register_y = Register()
        self.stack_pointer = Register()
        self.program_counter = Register(dtype=np.uint16)
        self.status = Status()
        # self.data_bus = Bus(size=1)
        # self.address_bus = Bus(size=2)
        self.ram = RAM()
        self.log = log is not None
        if self.log:
            self.log_file = open(
                f"logs/{log}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                "w",
            )

    def main_loop(self):
        while True:
            if self.log:
                curr_pc = np.base_repr(self.program_counter.read(), 16)
                curr_pc = "0" * (4 - len(curr_pc)) + curr_pc
                self.log_file.write(f"{curr_pc}\n")
            opcode = self.ram.read(self.program_counter.read())
            self.operation(opcode)
            self.program_counter.increment()

    def reset(self):
        self.accumulator.write(0)
        self.register_x.write(0)
        self.register_y.write(0)
        self.status.reset()
        self.program_counter.write(self.ram.read16(0xFFFC))
        self.stack_pointer.write(0xFF)

    def load_nes_file(self, filepath):
        with open(filepath, "rb") as fp:
            header = fp.read(16)
            prg_rom_banks, _ = self.parse_ines_header(header)
            self.load_prg_rom(fp, prg_rom_banks)

    @staticmethod
    def parse_ines_header(header):
        if header[:4] != b"NES\x1a":
            raise ValueError("Invalid NES ROM file.")

        prg_rom_banks = header[4]
        chr_rom_banks = header[5]

        return prg_rom_banks, chr_rom_banks

    def load_prg_rom(self, file, prg_rom_banks):
        prg_rom_size = 16 * 1024 * prg_rom_banks  # 16 KB per bank
        prg_rom_data = file.read(prg_rom_size)
        prg_rom_data = np.frombuffer(prg_rom_data, dtype=np.uint8)

        self.ram.write_chunk(0x8000, prg_rom_data)
        if prg_rom_banks == 1:
            # Mirror the data if only one PRG ROM bank
            self.ram.write_chunk(0xC000, prg_rom_data)

    def load_program(self, program: np.ndarray[np.uint8]):
        self.ram.load_program(program)

    def stack_push(self, data: np.uint8):
        if self.stack_pointer.read() == np.uint8(0x00):
            raise MemoryError("Stack Overflow")
        self.ram.write(np.uint16(0x0100) + self.stack_pointer.read(), data)
        self.stack_pointer.decrement()

    def stack_push16(self, data: np.uint16):
        if self.stack_pointer.read() == np.uint8(0x00):
            raise MemoryError("Stack Overflow")
        self.ram.write16(np.uint16(0xFF) + self.stack_pointer.read(), data)
        self.stack_pointer.decrement()
        self.stack_pointer.decrement()

    def stack_pull(self) -> np.uint8:
        if self.stack_pointer.read() == np.uint8(0xFF):
            raise MemoryError("Stack Underflow")
        data = self.ram.read(np.uint16(0x0101) + self.stack_pointer.read())
        self.stack_pointer.increment()
        return data

    def stack_pull16(self) -> np.uint16:
        if self.stack_pointer.read() == np.uint8(0xFF):
            raise MemoryError("Stack Underflow")
        data = self.ram.read16(np.uint16(0x101) + self.stack_pointer.read())
        self.stack_pointer.increment()
        self.stack_pointer.increment()
        return data

    def operation(self, opcode):
        match opcode:
            case 0x69:
                self.adc("immediate")
            case 0x65:
                self.adc("zero_page")
            case 0x75:
                self.adc("zero_page_x")
            case 0x6D:
                self.adc("absolute")
            case 0x7D:
                self.adc("absolute_x")
            case 0x79:
                self.adc("absolute_y")
            case 0x61:
                self.adc("indirect_x")
            case 0x71:
                self.adc("indirect_y")

            case 0x29:
                self.and_("immediate")
            case 0x25:
                self.and_("zero_page")
            case 0x35:
                self.and_("zero_page_x")
            case 0x2D:
                self.and_("absolute")
            case 0x3D:
                self.and_("absolute_x")
            case 0x39:
                self.and_("absolute_y")
            case 0x21:
                self.and_("indirect_x")
            case 0x31:
                self.and_("indirect_y")

            case 0x0A:
                self.asl("accumulator")
            case 0x06:
                self.asl("zero_page")
            case 0x16:
                self.asl("zero_page_x")
            case 0x0E:
                self.asl("absolute")
            case 0x1E:
                self.asl("absolute_x")

            case 0x90:
                self.bcc()

            case 0xB0:
                self.bcs()

            case 0xF0:
                self.beq()

            case 0x24:
                self.bit("zero_page")
            case 0x2C:
                self.bit("absolute")

            case 0x30:
                self.bmi()

            case 0xD0:
                self.bne()

            case 0x10:
                self.bpl()

            case 0x00:
                self.brk()

            case 0x50:
                self.bvc()

            case 0x70:
                self.bvs()

            case 0x18:
                self.clc()

            case 0xD8:
                self.cld()

            case 0x58:
                self.cli()

            case 0xB8:
                self.clv()

            case 0xC9:
                self.cmp("immediate")
            case 0xC5:
                self.cmp("zero_page")
            case 0xD5:
                self.cmp("zero_page_x")
            case 0xCD:
                self.cmp("absolute")
            case 0xDD:
                self.cmp("absolute_x")
            case 0xD9:
                self.cmp("absolute_y")
            case 0xC1:
                self.cmp("indirect_x")
            case 0xD1:
                self.cmp("indirect_y")

            case 0xE0:
                self.cpx("immediate")
            case 0xE4:
                self.cpx("zero_page")
            case 0xEC:
                self.cpx("absolute")

            case 0xC0:
                self.cpy("immediate")
            case 0xC4:
                self.cpy("zero_page")
            case 0xCC:
                self.cpy("absolute")

            case 0xC6:
                self.dec("zero_page")
            case 0xD6:
                self.dec("zero_page_x")
            case 0xCE:
                self.dec("absolute")
            case 0xDE:
                self.dec("absolute_x")

            case 0xCA:
                self.dex()

            case 0x88:
                self.dey()

            case 0x49:
                self.eor("immediate")
            case 0x45:
                self.eor("zero_page")
            case 0x55:
                self.eor("zero_page_x")
            case 0x4D:
                self.eor("absolute")
            case 0x5D:
                self.eor("absolute_x")
            case 0x59:
                self.eor("absolute_y")
            case 0x41:
                self.eor("indirect_x")
            case 0x51:
                self.eor("indirect_y")

            case 0xE6:
                self.inc("zero_page")
            case 0xF6:
                self.inc("zero_page_x")
            case 0xEE:
                self.inc("absolute")
            case 0xFE:
                self.inc("absolute_x")

            case 0xE8:
                self.inx()

            case 0xC8:
                self.iny()

            case 0x4C:
                self.jmp("absolute")
            case 0x6C:
                self.jmp("indirect")

            case 0x20:
                self.jsr()

            case 0xA9:
                self.lda("immediate")
            case 0xA5:
                self.lda("zero_page")
            case 0xB5:
                self.lda("zero_page_x")
            case 0xAD:
                self.lda("absolute")
            case 0xBD:
                self.lda("absolute_x")
            case 0xB9:
                self.lda("absolute_y")
            case 0xA1:
                self.lda("indirect_x")
            case 0xB1:
                self.lda("indirect_y")

            case 0xA2:
                self.ldx("immediate")
            case 0xA6:
                self.ldx("zero_page")
            case 0xB6:
                self.ldx("zero_page_y")
            case 0xAE:
                self.ldx("absolute")
            case 0xBE:
                self.ldx("absolute_y")

            case 0xA0:
                self.ldy("immediate")
            case 0xA4:
                self.ldy("zero_page")
            case 0xB4:
                self.ldy("zero_page_x")
            case 0xAC:
                self.ldy("absolute")
            case 0xBC:
                self.ldy("absolute_x")

            case 0x4A:
                self.lsr("accumulator")
            case 0x46:
                self.lsr("zero_page")
            case 0x56:
                self.lsr("zero_page_x")
            case 0x4E:
                self.lsr("absolute")
            case 0x5E:
                self.lsr("absolute_x")

            case 0xEA:
                self.nop("implied")

            case 0x09:
                self.ora("immediate")
            case 0x05:
                self.ora("zero_page")
            case 0x15:
                self.ora("zero_page_x")
            case 0x0D:
                self.ora("absolute")
            case 0x1D:
                self.ora("absolute_x")
            case 0x19:
                self.ora("absolute_y")
            case 0x01:
                self.ora("indirect_x")
            case 0x11:
                self.ora("indirect_y")

            case 0x48:
                self.pha()

            case 0x08:
                self.php()

            case 0x68:
                self.pla()

            case 0x28:
                self.plp()

            case 0x2A:
                self.rol("accumulator")
            case 0x26:
                self.rol("zero_page")
            case 0x36:
                self.rol("zero_page_x")
            case 0x2E:
                self.rol("absolute")
            case 0x3E:
                self.rol("absolute_x")

            case 0x6A:
                self.ror("accumulator")
            case 0x66:
                self.ror("zero_page")
            case 0x76:
                self.ror("zero_page_x")
            case 0x6E:
                self.ror("absolute")
            case 0x7E:
                self.ror("absolute_x")

            case 0x40:
                self.rti()

            case 0x60:
                self.rts()

            case 0xE9:
                self.sbc("immediate")
            case 0xE5:
                self.sbc("zero_page")
            case 0xF5:
                self.sbc("zero_page_x")
            case 0xED:
                self.sbc("absolute")
            case 0xFD:
                self.sbc("absolute_x")
            case 0xF9:
                self.sbc("absolute_y")
            case 0xE1:
                self.sbc("indirect_x")
            case 0xF1:
                self.sbc("indirect_y")

            case 0x38:
                self.sec()

            case 0xF8:
                self.sed()

            case 0x78:
                self.sei()

            case 0x85:
                self.sta("zero_page")
            case 0x95:
                self.sta("zero_page_x")
            case 0x8D:
                self.sta("absolute")
            case 0x9D:
                self.sta("absolute_x")
            case 0x99:
                self.sta("absolute_y")
            case 0x81:
                self.sta("indirect_x")
            case 0x91:
                self.sta("indirect_y")

            case 0x86:
                self.stx("zero_page")
            case 0x96:
                self.stx("zero_page_y")
            case 0x8E:
                self.stx("absolute")

            case 0x84:
                self.sty("zero_page")
            case 0x94:
                self.sty("zero_page_x")
            case 0x8C:
                self.sty("absolute")

            case 0xAA:
                self.tax()

            case 0xA8:
                self.tay()

            case 0xBA:
                self.tsx()

            case 0x8A:
                self.txa()

            case 0x9A:
                self.txs()

            case 0x98:
                self.tya()

            # all opcodes below are illegal:
            # https://www.nesdev.org/wiki/CPU_unofficial_opcodes
            # https://www.masswerk.at/nowgobang/2021/6502-illegal-opcodes
            # http://www.oxyron.de/html/opcodes02.html

            case 0x4B:
                self.alr("immediate")

            case 0x0B:
                self.anc("immediate")
            case 0x2B:
                self.anc("immediate")

            case 0x8B:
                self.xaa("immediate")

            case 0x6B:
                self.arr("immediate")

            case 0xC7:
                self.dcp("zero_page")
            case 0xD7:
                self.dcp("zero_page_x")
            case 0xCF:
                self.dcp("absolute")
            case 0xDF:
                self.dcp("absolute_x")
            case 0xDB:
                self.dcp("absolute_y")
            case 0xC3:
                self.dcp("indirect_x")
            case 0xD3:
                self.dcp("indirect_y")

            case 0xE7:
                self.isc("zero_page")
            case 0xF7:
                self.isc("zero_page_x")
            case 0xEF:
                self.isc("absolute")
            case 0xFF:
                self.isc("absolute_x")
            case 0xFB:
                self.isc("absolute_y")
            case 0xE3:
                self.isc("indirect_x")
            case 0xF3:
                self.isc("indirect_y")

            case 0xBB:
                self.las("absolute_y")

            case 0xA7:
                self.lax("zero_page")
            case 0xB7:
                self.lax("zero_page_y")
            case 0xAF:
                self.lax("absolute")
            case 0xBF:
                self.lax("absolute_y")
            case 0xA3:
                self.lax("indirect_x")
            case 0xB3:
                self.lax("indirect_y")

            case 0xAB:
                self.lxa("immediate")

            case 0x27:
                self.rla("zero_page")
            case 0x37:
                self.rla("zero_page_x")
            case 0x2F:
                self.rla("absolute")
            case 0x3F:
                self.rla("absolute_x")
            case 0x3B:
                self.rla("absolute_y")
            case 0x23:
                self.rla("indirect_x")
            case 0x33:
                self.rla("indirect_y")

            case 0x67:
                self.rra("zero_page")
            case 0x77:
                self.rra("zero_page_x")
            case 0x6F:
                self.rra("absolute")
            case 0x7F:
                self.rra("absolute_x")
            case 0x7B:
                self.rra("absolute_y")
            case 0x63:
                self.rra("indirect_x")
            case 0x73:
                self.rra("indirect_y")

            case 0x87:
                self.sax("zero_page")
            case 0x97:
                self.sax("zero_page_y")
            case 0x8F:
                self.sax("absolute")
            case 0x83:
                self.sax("indirect_x")

            case 0xCB:
                self.sbx("immediate")

            case 0x9F:
                self.sha("absolute_y")
            case 0x93:
                self.sha("indirect_y")

            case 0x9E:
                self.shx("absolute_y")

            case 0x9C:
                self.shy("absolute_x")

            case 0x07:
                self.slo("zero_page")
            case 0x17:
                self.slo("zero_page_x")
            case 0x0F:
                self.slo("absolute")
            case 0x1F:
                self.slo("absolute_x")
            case 0x1B:
                self.slo("absolute_y")
            case 0x03:
                self.slo("indirect_x")
            case 0x13:
                self.slo("indirect_y")

            case 0x47:
                self.sre("zero_page")
            case 0x57:
                self.sre("zero_page_x")
            case 0x4F:
                self.sre("absolute")
            case 0x5F:
                self.sre("absolute_x")
            case 0x5B:
                self.sre("absolute_y")
            case 0x43:
                self.sre("indirect_x")
            case 0x53:
                self.sre("indirect_y")

            case 0x9B:
                self.tas("immediate")

            case 0xEB:
                self.sbc("immediate")

            case 0x1A:
                self.nop("implied")
            case 0x3A:
                self.nop("implied")
            case 0x5A:
                self.nop("implied")
            case 0x7A:
                self.nop("implied")
            case 0xDA:
                self.nop("implied")
            case 0xFA:
                self.nop("implied")
            case 0x80:
                self.nop("immediate")
            case 0x82:
                self.nop("immediate")
            case 0x89:
                self.nop("immediate")
            case 0xC2:
                self.nop("immediate")
            case 0xE2:
                self.nop("immediate")
            case 0x04:
                self.nop("zero_page")
            case 0x44:
                self.nop("zero_page")
            case 0x64:
                self.nop("zero_page")
            case 0x14:
                self.nop("zero_page_x")
            case 0x34:
                self.nop("zero_page_x")
            case 0x54:
                self.nop("zero_page_x")
            case 0x74:
                self.nop("zero_page_x")
            case 0xD4:
                self.nop("zero_page_x")
            case 0xF4:
                self.nop("zero_page_x")
            case 0x0C:
                self.nop("absolute")
            case 0x1C:
                self.nop("absolute_x")
            case 0x3C:
                self.nop("absolute_x")
            case 0x5C:
                self.nop("absolute_x")
            case 0x7C:
                self.nop("absolute_x")
            case 0xDC:
                self.nop("absolute_x")
            case 0xFC:
                self.nop("absolute_x")

            case 0x02:
                self.jam()
            case 0x12:
                self.jam()
            case 0x22:
                self.jam()
            case 0x32:
                self.jam()
            case 0x42:
                self.jam()
            case 0x52:
                self.jam()
            case 0x62:
                self.jam()
            case 0x72:
                self.jam()
            case 0x92:
                self.jam()
            case 0xB2:
                self.jam()
            case 0xD2:
                self.jam()
            case 0xF2:
                self.jam()

            case _:
                raise ValueError(f"Invalid OpCode {hex(opcode)}")

    def load_operation_arg(self, addressing_mode):
        match addressing_mode:
            case "implied":
                return
            case "immediate":
                self.program_counter.increment()
                address = self.program_counter.read()
                return address
            case "zero_page":
                self.program_counter.increment()
                address = self.ram.read(self.program_counter.read())
                return address
            case "zero_page_x":
                self.program_counter.increment()
                address = (
                    self.ram.read(self.program_counter.read())
                    + self.register_x.read()
                )
                return address
            case "zero_page_y":
                self.program_counter.increment()
                address = (
                    self.ram.read(self.program_counter.read())
                    + self.register_y.read()
                )
                return address
            case "absolute":
                self.program_counter.increment()
                address = self.ram.read16(self.program_counter.read())
                self.program_counter.increment()
                return address
            case "absolute_x":
                self.program_counter.increment()
                address = (
                    self.ram.read16(self.program_counter.read())
                    + self.register_x.read()
                )
                self.program_counter.increment()
                return address
            case "absolute_y":
                self.program_counter.increment()
                address = (
                    self.ram.read16(self.program_counter.read())
                    + self.register_y.read()
                )
                self.program_counter.increment()
                return address
            case "indirect":
                self.program_counter.increment()
                reference = self.ram.read16(self.program_counter.read())
                # bug in original 6502, we'll replicate it here
                address = self.ram.read16(reference, page_wrap=True)
                self.program_counter.increment()
                return address
            case "indirect_x":
                self.program_counter.increment()
                reference = (
                    self.ram.read(self.program_counter.read())
                    + self.register_x.read()
                )
                address = self.ram.read16(reference, page_wrap=True)
                return address
            case "indirect_y":
                self.program_counter.increment()
                reference = self.ram.read(self.program_counter.read())
                address = (
                    self.ram.read16(reference, page_wrap=True)
                    + self.register_y.read()
                )
                return address
            case _:
                raise ValueError(f"Invalid addressing mode {addressing_mode}")

    def adc(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result, overflow = self._add(
            self.accumulator.read(),
            data,
            np.uint8(self.status.carry_flag),
        )
        self.accumulator.write(result)

        self.status.carry_flag = bool(overflow)
        self._update_zero_and_neg_flags(result)

    def and_(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self.accumulator.read() & data
        self.accumulator.write(result)

        self._update_zero_and_neg_flags(result)

    def asl(self, mode):
        if mode == "accumulator":
            data = self.accumulator.read()
            result = self._left_shift(data)
            self.accumulator.write(result)
        else:
            address = self.load_operation_arg(mode)
            data = self.ram.read(address)
            result = self._left_shift(data)
            self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

    def bcc(self):
        self._branch_if(not self.status.carry_flag)

    def bcs(self):
        self._branch_if(self.status.carry_flag)

    def beq(self):
        self._branch_if(self.status.zero_flag)

    def bit(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self.accumulator.read() & data

        self._update_zero_flag(result)
        self.status.overflow_flag = bool(
            int(np.binary_repr(data, width=8)[-7])
        )
        self.status.negative_flag = bool(
            int(np.binary_repr(data, width=8)[-8])
        )

    def bmi(self):
        self._branch_if(self.status.negative_flag)

    def bne(self):
        self._branch_if(not self.status.zero_flag)

    def bpl(self):
        self._branch_if(not self.status.negative_flag)

    def brk(self):
        # TODO:
        # https://www.nesdev.org/the%20'B'%20flag%20&%20BRK%20instruction.txt
        # https://www.nesdev.org/obelisk-6502-guide/reference.html#BRK
        self.status.break_command = True

    def bvc(self):
        self._branch_if(not self.status.overflow_flag)

    def bvs(self):
        self._branch_if(self.status.overflow_flag)

    def clc(self):
        self.status.carry_flag = False

    def cld(self):
        self.status.decimal_flag = False

    def cli(self):
        self.status.interrupt_flag = False

    def clv(self):
        self.status.overflow_flag = False

    def cmp(self, mode):
        self._compare(self.accumulator, mode)

    def cpx(self, mode):
        self._compare(self.register_x, mode)

    def cpy(self, mode):
        self._compare(self.register_y, mode)

    def dec(self, mode):
        address = self.load_operation_arg(mode)
        result = self.ram.read(address) - np.uint8(1)
        self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

    def dex(self):
        result = self.register_x.decrement()

        self._update_zero_and_neg_flags(result)

    def dey(self):
        result = self.register_y.decrement()

        self._update_zero_and_neg_flags(result)

    def eor(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self.accumulator.read() ^ data
        self.accumulator.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def inc(self, mode):
        address = self.load_operation_arg(mode)
        result = self.ram.read(address) + np.uint8(1)
        self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

    def inx(self):
        result = self.register_x.increment()

        self._update_zero_and_neg_flags(result)

    def iny(self):
        result = self.register_y.increment()

        self._update_zero_and_neg_flags(result)

    def jmp(self, mode):
        address = self.load_operation_arg(mode)
        self.program_counter.write(address - np.uint16(1))

    def jsr(self):
        address = self.load_operation_arg("absolute")
        self.stack_push16(self.program_counter.read())
        self.program_counter.write(address - np.uint16(1))

    def lda(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

    def ldx(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        self.register_x.write(data)

        self._update_zero_and_neg_flags(data)

    def ldy(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        self.register_y.write(data)

        self._update_zero_and_neg_flags(data)

    def lsr(self, mode):
        if mode == "accumulator":
            data = self.accumulator.read()
            result = self._right_shift(data)
            self.accumulator.write(result)
        else:
            address = self.load_operation_arg(mode)
            data = self.ram.read(address)
            result = self._right_shift(data)
            self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

    def nop(self, mode):
        self.load_operation_arg(mode)

    def ora(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self.accumulator.read() | data
        self.accumulator.write(result)

        self._update_zero_and_neg_flags(result)

    def pha(self):
        self.stack_push(self.accumulator.read())

    def php(self):
        prev_flag = self.status.break_command
        self.status.break_command = True
        self.stack_push(self.status.read())
        self.status.break_command = prev_flag

    def pla(self):
        data = self.stack_pull()
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

    def plp(self):
        data = self.stack_pull()
        self.status.write(data)

    def rol(self, mode):
        if mode == "accumulator":
            data = self.accumulator.read()
            result = self._left_rotate(data)
            self.accumulator.write(result)
        else:
            address = self.load_operation_arg(mode)
            data = self.ram.read(address)
            result = self._left_rotate(data)
            self.ram.write(address, result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def ror(self, mode):
        if mode == "accumulator":
            data = self.accumulator.read()
            result = self._right_rotate(data)
            self.accumulator.write(result)
        else:
            address = self.load_operation_arg(mode)
            data = self.ram.read(address)
            result = self._right_rotate(data)
            self.ram.write(address, result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def rti(self):
        data = self.stack_pull()
        self.status.write(data)
        address = self.stack_pull16()
        self.program_counter.write(address - np.uint16(1))

    def rts(self):
        address = self.stack_pull16()
        self.program_counter.write(address)

    def sbc(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        twos_comp_data = ~data + np.uint8(1)
        not_carry = np.uint8(not self.status.carry_flag)
        twos_comp_not_carry = ~not_carry + np.uint8(1)
        result, overflow = self._add(
            self.accumulator.read(),
            twos_comp_data,
            twos_comp_not_carry,
        )
        self.accumulator.write(result)

        self.status.carry_flag = overflow
        self._update_zero_and_neg_flags(result)

    def sec(self):
        self.status.carry_flag = True

    def sed(self):
        self.status.decimal_flag = True

    def sei(self):
        self.status.interrupt_flag = True

    def sta(self, mode):
        address = self.load_operation_arg(mode)
        self.ram.write(address, self.accumulator.read())

    def stx(self, mode):
        address = self.load_operation_arg(mode)
        self.ram.write(address, self.register_x.read())

    def sty(self, mode):
        address = self.load_operation_arg(mode)
        self.ram.write(address, self.register_y.read())

    def tax(self):
        data = self.accumulator.read()
        self.register_x.write(data)

        self._update_zero_and_neg_flags(data)

    def tay(self):
        data = self.accumulator.read()
        self.register_y.write(data)

        self._update_zero_and_neg_flags(data)

    def tsx(self):
        data = self.stack_pointer.read()
        self.register_x.write(data)

        self._update_zero_and_neg_flags(data)

    def txa(self):
        data = self.register_x.read()
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

    def txs(self):
        data = self.register_x.read()
        self.stack_pointer.write(data)

    def tya(self):
        data = self.register_y.read()
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

    # illegal opcodes

    def dcp(self, mode):
        # DEC
        address = self.load_operation_arg(mode)
        data = self.ram.read(address) - np.uint8(1)
        self.ram.write(address, data)

        self._update_zero_and_neg_flags(data)

        # CMP
        a_data = self.accumulator.read()
        result = a_data - data

        self.status.carry_flag = a_data >= data
        self._update_zero_and_neg_flags(result)

    def isc(self, mode):
        # INC
        address = self.load_operation_arg(mode)
        data = self.ram.read(address) + np.uint8(1)
        self.ram.write(address, data)

        # self._update_zero_and_neg_flags(data)

        # ISC
        twos_comp_data = ~data + np.uint8(1)
        not_carry = np.uint8(not self.status.carry_flag)
        twos_comp_not_carry = ~not_carry + np.uint8(1)
        result, overflow = self._add(
            self.accumulator.read(),
            twos_comp_data,
            twos_comp_not_carry,
        )
        self.accumulator.write(result)

        self.status.carry_flag = overflow
        self._update_zero_and_neg_flags(result)

    def lax(self, mode):
        # LDA
        data = self.ram.read(self.load_operation_arg(mode))
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

        # LDX
        self.register_x.write(data)

        self._update_zero_and_neg_flags(data)

    def rla(self, mode):
        # ROL
        address = self.load_operation_arg(mode)
        data = self.ram.read(address)
        result = self._left_rotate(data)
        self.ram.write(address, result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

        # AND
        result = self.accumulator.read() & result
        self.accumulator.write(result)

        self._update_zero_and_neg_flags(result)

    def rra(self, mode):
        # ROR
        address = self.load_operation_arg(mode)
        data = self.ram.read(address)
        result = self._right_rotate(data)
        self.ram.write(address, result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

        # ADC
        result, overflow = self._add(
            self.accumulator.read(),
            result,
            np.uint8(self.status.carry_flag),
        )
        self.accumulator.write(result)

        self.status.carry_flag = bool(overflow)
        self._update_zero_and_neg_flags(result)

    def sax(self, mode):
        address = self.load_operation_arg(mode)
        data = self.accumulator.read() & self.register_x.read()
        self.ram.write(address, data)

    def slo(self, mode):
        # ASL
        address = self.load_operation_arg(mode)
        data = self.ram.read(address)
        result = self._left_shift(data)
        self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

        # ORA
        result = self.accumulator.read() | result
        self.accumulator.write(result)

        self._update_zero_and_neg_flags(result)

    def sre(self, mode):
        # LSR
        address = self.load_operation_arg(mode)
        data = self.ram.read(address)
        result = self._right_shift(data)
        self.ram.write(address, result)

        self._update_zero_and_neg_flags(result)

        # EOR
        result = self.accumulator.read() ^ result
        self.accumulator.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    # end of illegal opcodes

    def _update_zero_and_neg_flags(self, data):
        self._update_zero_flag(data)
        self._update_neg_flag(data)

    def _update_zero_flag(self, data):
        self.status.zero_flag = self._is_zero(data)

    def _update_neg_flag(self, data):
        self.status.negative_flag = self._is_negative(data)

    @staticmethod
    def _is_negative(data):
        # return not (data & 1 << 7)
        return data >= 0b1000_0000

    @staticmethod
    def _is_zero(data):
        return not data

    def _add(self, arg1, arg2, carry):
        result = sum([arg1, arg2, carry])
        is_result_neg = self._is_negative(np.uint8(result % 256))
        # complicated edge case, don't ask
        self.status.overflow_flag = (
            bool(arg2) & (~(self._is_negative(arg1) ^ self._is_negative(arg2)))
            | ~arg2
            & ~(self._is_negative(arg1) ^ self._is_negative(arg2 + carry))
        ) & (self._is_negative(arg1) ^ is_result_neg)
        result8 = np.uint8(result % 256)
        return result8, bool(result // 256)

    def _left_shift(self, data):
        result = data << 1
        self.status.carry_flag = self._is_negative(data)
        return np.uint8(result % 256)

    def _branch_if(self, condition):
        # not quite true, addressing mode should be `relative`
        # but let's keep things simple
        data = self.ram.read(self.load_operation_arg("immediate"))
        if condition:
            offset = data.astype(np.int8)
            self.program_counter.write(self.program_counter.read() + offset)

    def _compare(self, register, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        reg_data = register.read()
        result = reg_data - data

        self.status.carry_flag = reg_data >= data
        self._update_zero_and_neg_flags(result)

    def _right_shift(self, data):
        result = data >> 1
        self.status.carry_flag = data % 2
        return np.uint8(result % 256)

    def _left_rotate(self, data):
        result = data << 1
        result = self._copy_bit(result, 0, int(self.status.carry_flag))
        self.status.carry_flag = self._is_negative(data)
        return result

    def _right_rotate(self, data):
        result = data >> 1
        result = self._copy_bit(result, 7, int(self.status.carry_flag))
        self.status.carry_flag = data % 2
        return result

    @staticmethod
    def _copy_bit(data: np.uint8, index: int, value: bool):
        mask = 1 << index
        data |= mask
        data ^= (not value) * mask
        return np.uint8(data)

    def _check_stack(self):
        # debugging purposes
        return self.ram.data[0x100 + self.stack_pointer.read() + 1 : 0x200]


class Register:
    def __init__(self, dtype=np.uint8):
        self.dtype = dtype
        self.data = dtype(0)

    def read(self) -> np.uint8 | np.uint16:
        return self.data.copy()

    def write(self, data: np.uint8 | np.uint16):
        self.data = self.dtype(data)

    def increment(self) -> np.uint8 | np.uint16:
        self.data = self.data + self.dtype(1)
        return self.data

    def decrement(self) -> np.uint8 | np.uint16:
        self.data = self.data - self.dtype(1)
        return self.data


class Status:
    def __init__(self):
        self.reset()

    def reset(self):
        self.carry_flag = False
        self.zero_flag = False
        self.interrupt_flag = True
        self.decimal_flag = False
        # I'm not sure of this, see comment in CPU.brk()
        self.break_command = False
        self.overflow_flag = False
        self.negative_flag = False

    def read(self) -> np.uint8:
        flags_list = [
            int(x)
            for x in (
                self.carry_flag,
                self.zero_flag,
                self.interrupt_flag,
                self.decimal_flag,  # doesn't really matter
                self.break_command,
                True,  # i don't think this is a valid flag in any context
                self.overflow_flag,
                self.negative_flag,
            )
        ]
        result = 0
        for i, flag in enumerate(flags_list):
            result += 2**i * int(flag)
        return np.uint8(result)

    def write(self, data: np.uint8):
        bin_data = np.binary_repr(data, width=8)
        self.carry_flag = bin_data[-1] == "1"
        self.zero_flag = bin_data[-2] == "1"
        self.interrupt_flag = bin_data[-3] == "1"
        self.decimal_flag = bin_data[-4] == "1"
        self.break_command = bin_data[-5] == "1"
        self.overflow_flag = bin_data[-7] == "1"
        self.negative_flag = bin_data[-8] == "1"


class RAM:
    def __init__(self):
        self.data = np.zeros((0x10000,), dtype=np.uint8)

    def load_program(self, program: np.ndarray[np.uint8]):
        self.write_chunk(0x8000, program)

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


if __name__ == "__main__":
    import re

    def hex_format(data, n_bytes=1):
        hex_repr = np.base_repr(data, 16)
        return "0" * (2 * n_bytes - len(hex_repr)) + hex_repr

    def print_binaries(d1, d2):
        # to debug process status register, d1 is str (p variable), d2 is int
        d1 = bin(int(d1, 16))[2:]
        print("0" * (8 - len(d1)) + d1)
        d2 = bin(d2)[2:]
        print("0" * (8 - len(d2)) + d2)

    with open("logs/nestest.log") as fp:
        test_lines = fp.readlines()

    test = [
        {
            "addr": x[:4],
            # "op": re.search(r"  ([0-9A-F]{2})", x).group(1),
            "A": re.search(r"A:([0-9A-F]{2}) ", x).group(1),
            "X": re.search(r"X:([0-9A-F]{2}) ", x).group(1),
            "Y": re.search(r"Y:([0-9A-F]{2}) ", x).group(1),
            "P": re.search(r"P:([0-9A-F]{2}) ", x).group(1),
            "SP": re.search(r"SP:([0-9A-F]{2}) ", x).group(1),
        }
        for x in test_lines
    ]

    cpu = CPU(log="nestest")
    cpu.load_nes_file("nestest.nes")
    cpu.reset()
    cpu.program_counter.write(0xC000)

    # TODO: I don't know why but the SP starts at 0xFD for this ROM
    cpu.stack_push16(0x0000)

    log_str = "{addr}  A:{A} X:{X} Y:{Y} P:{P} SP:{SP}\n"

    i = 0
    while True:
        pc = hex_format(cpu.program_counter.read(), n_bytes=2)
        a = hex_format(cpu.accumulator.read())
        x = hex_format(cpu.register_x.read())
        y = hex_format(cpu.register_y.read())
        p = hex_format(cpu.status.read())
        sp = hex_format(cpu.stack_pointer.read())
        info_dict = {"addr": pc, "A": a, "X": x, "Y": y, "P": p, "SP": sp}

        cpu.log_file.write(log_str.format(**info_dict))
        if info_dict != test[i]:
            break
        opcode = cpu.ram.read(cpu.program_counter.read())
        cpu.operation(opcode)
        # TODO: copy this line to main_loop if this behavior is correct
        cpu.status.break_command = False
        cpu.program_counter.increment()
        i += 1

    cpu.log_file.close()
    print(f"Lines executed: {i}/{len(test)} ({i/len(test):.1%})")
