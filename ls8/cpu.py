"""CPU functionality."""

#import msvcrt
import sys
import os.path
from datetime import datetime

HLT  = 0b00000001
LDI  = 0b10000010
PRN  = 0b01000111
MUL  = 0b10100010
PUSH = 0b01000101
POP  = 0b01000110
CALL = 0b01010000
RET  = 0b00010001
ADD  = 0b10100000
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110
CMP = 0b10100111
AST = 0b01001111 #Raw creation. 1 operations (01). Not ALU (0). Not pointer(0).1111 for ease.
SUB = 0b10100001
DIV = 0b10100011
MOD = 0b10100100
OR = 0b10101010
XOR = 0b10101011
NOT = 0b01101001
SHL = 0b10101100
SHR = 0b10101101
ADDI = 0b10100101
AND = 0b10101000
ST = 0b10000100 #TODO
PRA = 0b01001000 #TODO
IRET = 0b00010011 #TODO
IINT = 0b01010010 #TODO

IM = 5
IS = 6
SP = 7


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
        self.mdr = 0 #Memory Data Register: holds the value to write or the value to read.
        self.fl = 0b00000000 #Flag Register: holds the current flags status *might change
        self.halted = False

        #Initialize the Stack Pointer
        #SP points at the value at the top of the stack (most recently pushed), or at address F4.
        self.reg[7] = 0xF4

        #Test case for interrupts to be functioning.
        self.interrupts_enabled = True

        #Set up Branch Table (will add more as we go):
        self.branchtable = {}
        self.branchtable[HLT] = self.execute_HLT
        self.branchtable[LDI] = self.execute_LDI
        self.branchtable[PRN] = self.execute_PRN
        self.branchtable[MUL] = self.execute_MUL
        self.branchtable[PUSH] = self.execute_PUSH
        self.branchtable[POP] = self.execute_POP
        self.branchtable[CALL] = self.execute_CALL
        self.branchtable[RET] = self.execute_RET
        self.branchtable[ADD] = self.execute_ADD
        self.branchtable[CMP] = self.execute_CMP
        self.branchtable[JMP] = self.execute_JMP
        self.branchtable[JEQ] = self.execute_JEQ
        self.branchtable[JNE] = self.execute_JNE
        self.branchtable[AST] = self.execute_AST
        self.branchtable[SUB] = self.execute_SUB
        self.branchtable[DIV] = self.execute_DIV
        self.branchtable[MOD] = self.execute_MOD
        self.branchtable[OR] = self.execute_OR
        self.branchtable[XOR] = self.execute_XOR
        self.branchtable[NOT] = self.execute_NOT
        self.branchtable[SHL] = self.execute_SHL
        self.branchtable[SHR] = self.execute_SHR
        self.branchtable[ADDI] = self.execute_ADDI
        self.branchtable[AND] = self.execute_AND
        self.branchtable[IRET] = self.execute_IRET
        self.branchtable[PRA] = self.execute_PRA
        self.branchtable[ST] = self.execute_ST

    # Property wrapper is very powerful to set/get function.
    @property
    def sp(self): #Gets Stack Pointer
        return self.reg[7]
    
    @sp.setter
    def sp(self, a): #Sets Stack Pointer
        self.reg[7] = a & 0xFF

    @property
    def operand_a(self): #Sets operand_a when necessary.
        return self.ram_read(self.pc + 1)
    
    @property
    def operand_b(self): #Sets operand_b when necessary.
        return self.ram_read(self.pc + 2)
    
    @property
    def instruction_size(self): #Taken from lecture short-hand. 
        #The first 2 places of the command are how many instructions to do.
        return ((self.ir >> 6) & 0b11) + 1 
    
    @property
    def instruction_sets_pc(self): #Taken from lecture short-hand.
        #From instruction layout- place 4 determines if this sets the PC.
        return ((self.ir >> 4) & 0b0001) == 1


    #Base CPU Methods.

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
        """Load a program into memory.
        """
        if len(sys.argv) != 2:
            print('Invalid number of args')
            sys.exit(1)
        
        try:
            with open(f'examples/{sys.argv[1]}') as f:
                address = 0
                for line in f:
                    line = line.strip()
                    if line == '' or line[0] == "#":
                        continue
                    num = line.split('#')[0].strip()
                    try:
                        instruction = int(num, 2)
                        self.ram[address] = instruction
                        address += 1
                    except:
                        print("Can't convert string to number")
                        continue
        except:
            print(f"Could not find file named: {sys.argv[1]}")
            sys.exit(1)


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
            
        elif op == 'MUL':
            self.reg[reg_a] *= self.reg[reg_b]

        elif op == "CMP":
            if self.reg[reg_a] == self.reg[reg_b]:
                self.fl = 0b00000001
               
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl = 0b00000010

            elif self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b000000100
        
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]

        elif op == "DIV":
            self.reg[reg_a] /= self.reg[reg_b]
        
        elif op == "OR":
            self.reg[reg_a] = self.reg[reg_a] | self.reg[reg_b]
        
        elif op == "XOR":
            self.reg[reg_a] = self.reg[reg_a] ^ self.reg[reg_b]
        
        elif op == "NOT":
            self.reg[reg_a] = ~self.reg[reg_a]
        
        elif op == "SHL":
            self.reg[reg_a] = self.reg[reg_a] << self.reg[reg_b]
        
        elif op == "SHR":
            self.reg[reg_a] = self.reg[reg_a] >> self.reg[reg_b]
        
        elif op == "MOD":
            self.reg[reg_a] = self.reg[reg_a] % self.reg[reg_b]
        
        elif op == "AND":
            self.reg[reg_a] = self.reg[reg_a] & self.reg[reg_b]

        elif op == "ADDI":
            self.reg[reg_a] += reg_b

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.fl,
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
        #prev_time = datetime.now()
        while self.halted is False: #Presumes activation
            
            # new_time = datetime.now()
            # if (new_time - prev_time).total_seconds() >= 1:
            #     prev_time = new_time
            #     self.reg[IS] = self.reg[IS] | 0b00000001
            
            # if msvcrt.kbhit():
            #     self.ram_write(ord(msvcrt.getch()), 0xF4)
            #     self.reg[IS] = self.reg[IS] | 0b00000010
            
            # interrupt_happened = False
            # if self.interrupts_enabled and self.reg[IM] != 0:
            #     masked_interrupts = self.reg[IM] & self.reg[IS]
            #     for i in range(8):
            #         interrupt_happened = ((masked_interrupts >> i) & 1) == 1
            #         if interrupt_happened:
            #             self.interrupts_enabled = False
            #             self.reg[IS] = self.reg[IS] & (0b11111110 << i)
            #             self.execute_PUSHI(self.pc)
            #             self.execute_PUSHI(self.fl)

            #             for j in range(7):
            #                 self.execute_PUSH
                        
            #             self.pc = self.ram[0xF8 + i]
            #             self.ir = self.ram_read(self.pc)


            #Collects next instruction
            self.ir = self.ram_read(self.pc) #Instruction register

            if self.ir in self.branchtable:
                self.branchtable[self.ir]()
            else:
                print(f"Error: Could not find instruction {self.ir} in branchtable.")
                sys.exit(1)
            if not self.instruction_sets_pc:
                self.pc += self.instruction_size
    
    #Branchtable Commands. Might be a way to use the ALU.
    def execute_HLT(self):
        #Runs the HLT command.
        self.halted = True
    
    def execute_LDI(self):
        #Write ram command, only targets register.
        self.reg[self.operand_a] = self.operand_b

    def execute_PRN(self):
        #Prints item from register.
        print(self.reg[self.operand_a])
    
    def execute_MUL(self):
        #Multiplies the operand_a and operand_b values.
        #self.reg[self.operand_a] *= self.reg[self.operand_b]
        self.alu("MUL", self.operand_a, self.operand_b)
    
    def execute_PUSH(self):
        #Takes something from the register and moves it to ram.
        #Stack pointer becomes the address.
        self.sp -= 1
        self.mdr = self.reg[self.operand_a]
        self.ram_write(self.sp, self.mdr)

    def execute_PUSHI(self, value):
        self.sp -= 1
        self.ram_write(value, self.reg[self.sp])

    def execute_POP(self):
        #Changes item in register from ram value.
        #Stack pointer is ram address.
        self.mdr = self.ram_read(self.sp)
        self.reg[self.operand_a] = self.mdr 
        self.sp += 1

    def execute_POPI(self):
        #Pops value at the top of the stack and returns it directly.
        self.reg[self.sp] +=1
        return self.ram_read(self.reg[self.sp] -1)

    def execute_ST(self):
        #Stores value in registerb in the address stored in registera
        self.ram[self.reg[self.operand_a]] = self.reg[self.operand_b]

    def execute_CALL(self):
        #Writes item to ram from stack pointer value. Program counter + instruction_size is value.
        #Iterates the program counter by the value at register operand_a
        self.sp -= 1
        self.ram_write(self.sp, self.pc + self.instruction_size)
        self.pc = self.reg[self.operand_a]

    def execute_RET(self):
        #Sets program counter to ram value at stack counter address.
        self.pc = self.ram_read(self.sp)
        self.sp += 1

    def execute_ADD(self):
        #Adds operand_a and operand_b together.
        #self.reg[self.operand_a] += self.reg[self.operand_b]
        self.alu("ADD", self.operand_a, self.operand_b)

    def execute_SUB(self):
        #Subracts operand_b from operand_a
        self.alu("SUB", self.operand_a, self.operand_b)

    def execute_DIV(self):
        #Divides operand_a by operand_b
        self.alu("DIV", self.operand_a, self.operand_b)
    
    def execute_MOD(self):
        #Takes the modular of operand_a by operand_b
        self.alu("MOD", self.operand_a, self.operand_b)

    def execute_OR(self):
        #Performs OR function on operand_a by operand_b
        self.alu("OR", self.operand_a, self.operand_b)

    def execute_XOR(self):
        #Takes the modular of operand_a by operand_b
        self.alu("XOR", self.operand_a, self.operand_b)

    def execute_NOT(self):
        #Takes the modular of operand_a by operand_b
        self.alu("NOT", self.operand_a, self.operand_b)

    def execute_SHL(self):
        #Takes the modular of operand_a by operand_b
        self.alu("SHL", self.operand_a, self.operand_b)

    def execute_SHR(self):
        #Takes the modular of operand_a by operand_b
        self.alu("SHR", self.operand_a, self.operand_b)

    def execute_ADDI(self):
        #Increases the contents of the given register by the given value.
        self.alu("SHR", self.operand_a, self.operand_b)

    def execute_AND(self):
        #Performs and function on operand_a and operand_b
        self.alu("AND", self.operand_a, self.operand_b)

    def execute_JMP(self):
        #Causes to program counter to go to the operand_a value in memory.
        self.pc = self.reg[self.operand_a]
    
    def execute_JEQ(self):
        #If the equal flag is set to true, jump.
        if self.fl == 0b00000001:
            self.execute_JMP()
        else:
            self.pc += 2
        
    def execute_JNE(self):
        #If the equal flag isn't true, jump.
        if self.fl != 0b00000001:
            self.execute_JMP()
        else:
            self.pc += 2

    def execute_CMP(self):
        #Compare two values. Set a flag with answer.
        self.alu("CMP", self.operand_a, self.operand_b)

    def execute_IRET(self):
        #Returns from interrupt handler.
        print("IRET")
        for _ in reversed(range(7)):
            self.execute_POP()
        self.fl = self.execute_POPI()
        self.pc = self.execute_POPI()
        self.interrupts_enabled = True

    def execute_PRA(self):
        #Print alpha character stored in the given register
        print(chr(self.reg[self.operand_a]), end='', flush=True)
    
    def execute_AST(self):
        asts = ''
        for _ in range(self.reg[self.operand_a]):
            asts += '*'
        print(asts)

