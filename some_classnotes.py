import sys

#Holds bytes
#A big array of bytes. Address/Index/Location/Pointer to where things are stored.

#"opcode" == instruction byte
#"operands" == arguments to the instruction
#Add some symbolic numbers

PRINT_BEEJ = 1
HALT = 2
SAVE_REG = 3
PRINT_REG = 4

memory = [
    1, # PRINT_BEEJ
    3, # SAVE_REG R1, 37
    1, #Index
    37, #value
    4, # PRINT_Reg
    1, #Place in register
    1, # PRINT_BEEJ
    2 # HALT
]

#Start execution at Address 0

register = [0] * 8 #These act like variables.

# Keep track of the address of the currently-executing instruction.
pc = 0 #Program Counter, pointer to the instruction we're executing.

halted = False

while not halted:
    instruction = memory[pc]

    if instruction == PRINT_BEEJ:
        print("Beej!")
        pc += 1

    elif instruction == HALT:
        halted = True
        pc += 1
    
    elif instruction == SAVE_REG:
        reg_num = memory[pc + 1]
        value = memory[pc + 2]
        register[reg_num] = value
        #print(register)
        pc += 3
    
    elif instruction == PRINT_REG:
        reg_num = memory[pc + 1]
        print(register[reg_num])
        pc += 2

    else:
        print(f'Unknown instruction {instruction}')
        sys.exit(1)


# for instruction in memory:
#     if instruction == 1:
#         print("Beej!")
#     if instruction == 2:
#         break
