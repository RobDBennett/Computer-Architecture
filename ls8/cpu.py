"""CPU functionality."""

import sys
import os.path

HLT  = 0b00000001
LDI  = 0b10000010
PRN  = 0b01000111
MUL  = 0b10100010
PUSH = 0b01000101
POP  = 0b01000110
CALL = 0b01010000
RET  = 0b00010001
ADD  = 0b10100000

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # 256-byte RAM, each element is 1 byte. Can only store integers 0-255
        self.ram = [0] *256

        #R0-R7: 8-bit registers.
        #R5= interrupt mask (IM)
        #R6= Interrupt status (IS)
        #R7= stack pointer (SP)
        self.reg = [0] * 8

        # Internal Registers
        self.pc = 0 #Program Counter: address of currently executing instruction
        self.ir = 0 #Instruction Register: contains a copy of the currently executing instruction
        self.mar = 0 #Memory Address Register: holds the memory address we're read/writing.
        self.mdr = 0 #Memory Data RegisterL holds the value to write or the value to read.
        self.fl = 0 #Flag Register: holds the current flags status
        self.halted = False

        #Initialize the Stack Pointer
        #SP points at the value at the top of the stack (most recently pushed), or at address F4.
        self.reg[7] = 0xF4

    def ram_read(self, mar):
        if mar >= 0 and mar < len(self.ram):
            return self.ram[mar]
        else:
            print(f'Error: attempted to read from memory address: {mar}, which is outside of the memory.')
            return -1

    def ram_write(self, mar, mdr):
        if mar >= 0 and mar < len(self.ram):
            self.ram[mar] = mdr #& 0xFF
        else:
            print(f'Error: attempted to write to memory address: {mar}, which is outside the memory.')

    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010, # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111, # PRN R0
            0b00000000,
            0b00000001, # HLT
        ]

        for instruction in program:
            self.ram[address] = instruction
            address += 1


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        while self.halted is False:
            ir = self.ram_read(self.pc) #Instruction register
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)
            if ir == HLT:
                self.halted = True
                self.pc += 1
            elif ir == PRN:
                print(self.reg[operand_a])
                self.pc += 2
            elif ir == LDI:
                self.reg[operand_a] = operand_b
                self.pc += 3