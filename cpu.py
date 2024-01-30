import warnings

import numpy as np

# https://skilldrick.github.io/easy6502/
# https://bugzmanov.github.io/nes_ebook/
# https://medium.com/@guilospanck/the-journey-of-writing-a-nes-emulator-part-i-the-cpu-6e83b50baa37
# https://www.copetti.org/writings/consoles/nes/
# https://codeburst.io/how-do-processors-actually-work-91dce24fbb44
# np.seterr(over="raise")


class CPU:
    def __init__(self):
        self.accumulator = Register()
        self.register_x = Register()
        self.register_y = Register()
        self.stack_pointer = Register()
        self.program_counter = Register(dtype=np.uint16)
        self.status = Status()
        # self.data_bus = Bus(size=1)
        # self.address_bus = Bus(size=2)
        self.ram = RAM()

    def main_loop(self):
        while True:
            opcode = self.ram.read16(self.program_counter.read())
            self.operation(opcode)
            self.program_counter.increment()

    def reset(self):
        self.accumulator.write(0)
        self.register_x.write(0)
        self.register_y.write(0)
        self.status.reset()
        self.program_counter = self.ram.read16(0xFFFC)
        self.stack_pointer.write(0xFF)

    def stack_push(self, data: np.uint8):
        if self.stack_pointer.read() == np.uint8(0x00):
            raise MemoryError("Stack Overflow")
        self.ram.write(np.uint16(0x100) + self.stack_pointer.read(), data)
        self.stack_pointer.decrement()

    def stack_pull(self) -> np.uint8:
        if self.stack_pointer.read() == np.uint8(0xFF):
            raise MemoryError("Stack Underflow")
        data = self.ram.read(np.uint16(0x100) + self.stack_pointer.read())
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
                self.jsr("absolute")

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
                self.nop()

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
                self.sbc("absolute_Y")
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

    def load_operation_arg(self, addressing_mode):
        match addressing_mode:
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
                    + self.register_x
                )
                self.program_counter.increment()
                return address
            case "absolute_y":
                self.program_counter.increment()
                address = (
                    self.ram.read16(self.program_counter.read())
                    + self.register_x
                )
                self.program_counter.increment()
                return address
            case "indirect":
                self.program_counter.increment()
                reference = self.ram.read16(self.program_counter.read())
                address = self.ram.read16(reference)
                self.program_counter.increment()
                return address
            case "indirect_x":
                self.program_counter.increment()
                reference = (
                    self.ram.read(self.program_counter.read())
                    + self.register_x.read()
                )
                address = self.ram.read16(reference)
                return address
            case "indirect_y":
                self.program_counter.increment()
                reference = self.ram.read(self.program_counter.read())
                address = self.ram.read16(reference) + self.register_y.read()
                return address
            case _:
                raise ValueError(f"Invalid addressing mode {addressing_mode}")

    def adc(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self._add(self.accumulator.read(), data)
        self.accumulator.write(result)

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
            data = self.ram.read(self.load_operation_arg(mode))
            result = self._left_shift(data)
            self.ram.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

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
        self.status.break_command = True

    def bvc(self):
        self._branch_if(not self.status.overflow_flag)

    def bvs(self):
        self._branch_if(self.status.overflow_flag)

    def clc(self):
        self.status.carry_flag = False

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
        # TODO: An original 6502 does not correctly fetch the target address if
        # the indirect vector falls on a page boundary (e.g. $xxFF where xx is
        # any value from $00 to $FF). In this case fetches the LSB from $xxFF
        # as expected but takes the MSB from $xx00.
        self.program_counter = address

    def jsr(self):
        address = self.load_operation_arg("absolute")
        self.stack_push(self.program_counter.read())
        self.program_counter.write(address)

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
            data = self.ram.read(self.load_operation_arg(mode))
            result = self._right_shift(data)
            self.ram.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def nop(self):
        ...

    def ora(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = self.accumulator.read() | data

        self._update_zero_and_neg_flags(result)

    def pha(self):
        self.stack_push(self.accumulator.read())

    def php(self):
        self.stack_push(self.status.read())

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
            data = self.ram.read(self.load_operation_arg(mode))
            result = self._left_rotate(data)
            self.ram.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def ror(self, mode):
        if mode == "accumulator":
            data = self.accumulator.read()
            result = self._right_rotate(data)
            self.accumulator.write(result)
        else:
            data = self.ram.read(self.load_operation_arg(mode))
            result = self._right_rotate(data)
            self.ram.write(result)

        self._update_zero_flag(self.accumulator.read())
        self._update_neg_flag(result)

    def rti(self):
        data = self.stack_pull()
        self.status.write(data)
        address = self.stack_pull()
        self.program_counter.write(address)

    def rts(self):
        address = self.stack_pull()
        self.program_counter.write(address)

    def sbc(self, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        twos_comp_data = np.uint8(int(np.binary_repr(data, width=8), base=2))
        result = self._add(self.accumulator.read(), twos_comp_data)
        self.accumulator.write(result)

        self._update_zero_and_neg_flags(result)

    def sec(self):
        self.status.carry_flag = True

    def sed(self):
        # decimal operation, it doesn't work in 2A03
        ...

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

        self._update_zero_and_neg_flags(data)

    def tya(self):
        data = self.register_y.read()
        self.accumulator.write(data)

        self._update_zero_and_neg_flags(data)

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

    def _add(self, arg1, arg2):
        result = sum([arg1, arg2])
        self.status.overflow_flag = (
            self._is_negative(arg1)
            and self._is_negative(arg2)
            and self._is_negative(result)
        ) or (
            not self._is_negative(arg1)
            and not self._is_negative(arg2)
            and not self._is_negative(result)
        )
        self.status.carry_flag = bool(result // 256)
        return np.uint8(result % 256)

    def _left_shift(self, data):
        result = data << 8
        self.status.carry_flag = self._is_negative(data)
        return np.uint8(result % 256)

    def _branch_if(self, condition):
        data = self.ram.read(self.load_operation_arg("relative"))
        offset = data.astype(np.int8)
        if condition:
            self.program_counter += offset

    def _compare(self, register, mode):
        data = self.ram.read(self.load_operation_arg(mode))
        result = register.read() - data

        self.status.carry_flag = result >= 0
        self._update_zero_and_neg_flags(result)

    def _right_shift(self, data):
        result = data >> 8
        self.status.carry_flag = not (data % 2)
        return np.uint8(result % 256)

    def _left_rotate(self, data):
        result = data << 8
        result = self._copy_bit(result, 0, int(self.status.carry_flag))
        self.status.carry_flag = self._is_negative(data)
        return result

    def _right_rotate(self, data):
        result = data >> 8
        result = self._copy_bit(result, 7, int(self.status.carry_flag))
        self.status.carry_flag = not (data % 2)
        return result

    @staticmethod
    def _copy_bit(data: np.uint8, index: int, value: bool):
        mask = 1 << index
        data |= mask
        data ^= (not value) * mask
        return np.uint8(data)


class Register:
    def __init__(self, dtype=np.uint8):
        self.dtype = dtype
        self.data = dtype(0)

    def read(self) -> np.uint8 | np.uint16:
        return self.value.copy()

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
        self.interrupt_flag = False
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
                False,  # decimal flag
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
        self.break_command = bin_data[-5] == "1"
        self.overflow_flag = bin_data[-7] == "1"
        self.negative_flag = bin_data[-8] == "1"


class RAM:
    def __init__(self):
        self.data = np.zeros((0xFFFF,), dtype=np.uint8)

    def load_program(self, program):
        self.write(0x8000, program, len(program))

    def read(self, address):
        return self.data[address].copy()

    def read16(self, address):
        lo, hi = self.data[address : address + 1]
        return (hi.astype(np.uint16) << 8) + lo.astype(np.uint16)

    def write(self, address, data):
        self.data[address] = data

    def write16(self, address, data):
        lo = (data & 0xFF).astype(np.uint8)
        hi = ((data >> 8) & 0xFF).astype(np.uint8)
        self.data[address] = lo
        self.data[address + 1] = hi
