import sys

def read_file_to_list(filename):
    with open(filename, 'r') as file:
        lines = [line.strip() for line in file if line.strip()]
    return lines

def to_binary(n, bits=32):
    return '0b' + format(n & ((1 << bits) - 1), f'0{bits}b')

def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

def simulator_write(input_file, output_file):
    lines = read_file_to_list(input_file)
    
    pc = 0
    reg = [0] * 32
    reg[2] = 0x17C  # Initialize reg[2] to 380 (0x17C)
    
    memory = {}
    mem_add = 0x00010000
    for i in range(32):
        memory[mem_add] = 0
        mem_add += 4

    virtual_hault_found = False
    instruction_count = 0
    max_instructions = len(lines)

    with open(output_file, 'w', newline='\n') as f:
        while pc < max_instructions * 4 and not virtual_hault_found:
            instr = lines[pc // 4]
            
            if instr == '00000000000000000000000001100011':
                virtual_hault_found = True
                pc, reg = simulator(instr, pc, reg, memory)
            else:
                pc, reg = simulator(instr, pc, reg, memory)
            
            reg_values = " ".join([to_binary(reg[i]) for i in range(32)]) + " "  # Added trailing space
            f.write(f"{to_binary(pc, 32)} {reg_values}\n")
            instruction_count += 1
            
            if instruction_count > max_instructions * 2:
                break

        for addr in range(0x00010000, 0x00010080, 4):
            mem_key = addr
            f.write(f"0x{mem_key:08X}:{to_binary(memory.get(mem_key, 0), 32)}\n")  # Removed space after ':'
    
    print(f"Output written to {output_file}")
    print(f"Total instructions executed: {instruction_count}")

def simulator(instr, pc, reg, memory):
    opcode = instr[-7:]
    rd = int(instr[20:25], 2)
    funct3 = instr[17:20]
    rs1 = int(instr[12:17], 2)
    rs2 = int(instr[7:12], 2)
    funct7 = instr[:7]
    
    increment_pc = True

    if opcode == '0110011':
        if funct3 == '000':
            if funct7 == '0000000':
                reg[rd] = (reg[rs1] + reg[rs2]) & 0xFFFFFFFF
            elif funct7 == '0100000':
                reg[rd] = (reg[rs1] - reg[rs2]) & 0xFFFFFFFF
        elif funct3 == '001':
            reg[rd] = (reg[rs1] << (reg[rs2] & 0x1F)) & 0xFFFFFFFF
        elif funct3 == '010':
            reg[rd] = 1 if reg[rs1] < reg[rs2] else 0
        elif funct3 == '101':
            if funct7 == '0000000':
                reg[rd] = (reg[rs1] >> (reg[rs2] & 0x1F)) & 0xFFFFFFFF
            elif funct7 == '0100000':
                reg[rd] = (reg[rs1] >> (reg[rs2] & 0x1F)) | ~((1 << (32 - (reg[rs2] & 0x1F))) - 1) if (reg[rs1] >> 31) else 0
        elif funct3 == '110':
            reg[rd] = (reg[rs1] | reg[rs2]) & 0xFFFFFFFF
        elif funct3 == '111':
            reg[rd] = (reg[rs1] & reg[rs2]) & 0xFFFFFFFF

    elif opcode == '0010011':
        imm = sign_extend(int(instr[:12], 2), 12)
        if funct3 == '000':
            reg[rd] = (reg[rs1] + imm) & 0xFFFFFFFF
        elif funct3 == '010':
            reg[rd] = 1 if reg[rs1] < imm else 0
        elif funct3 == '001':
            shamt = int(instr[7:12], 2)
            reg[rd] = (reg[rs1] << shamt) & 0xFFFFFFFF
        elif funct3 == '101':
            shamt = int(instr[7:12], 2)
            if funct7 == '0000000':
                reg[rd] = (reg[rs1] >> shamt) & 0xFFFFFFFF
            elif funct7 == '0100000':
                reg[rd] = (reg[rs1] >> shamt) | (~((1 << (32 - shamt)) - 1)) if (reg[rs1] >> 31) else 0

    elif opcode == '0000011' and funct3 == '010':
        imm = sign_extend(int(instr[:12], 2), 12)
        addr = reg[rs1] + imm
        aligned_addr = addr & ~0x3
        reg[rd] = memory.get(aligned_addr, 0)

    elif opcode == '0100011' and funct3 == '010':
        imm = sign_extend(int(instr[:7] + instr[20:25], 2), 12)
        addr = reg[rs1] + imm
        aligned_addr = addr & ~0x3
        memory[aligned_addr] = reg[rs2] & 0xFFFFFFFF

    elif opcode == '1100011':
        imm = sign_extend(int(instr[0] + instr[24] + instr[1:7] + instr[20:24] + '0', 2), 13)
        if funct3 == '000':
            if reg[rs1] == reg[rs2]:
                pc += imm
                increment_pc = False
        elif funct3 == '001':
            if reg[rs1] != reg[rs2]:
                pc += imm
                increment_pc = False

    elif opcode == '1101111':
        imm = sign_extend(int(instr[0] + instr[12:20] + instr[11] + instr[1:11] + '0', 2), 21)
        reg[rd] = pc + 4
        pc += imm
        increment_pc = False

    reg[0] = 0
    if increment_pc and instr != '00000000000000000000000001100011':
        pc += 4
    return pc, reg

input_file = sys.argv[1]
output_file = sys.argv[2]
simulator_write(input_file, output_file)
