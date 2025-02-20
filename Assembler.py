def reg_value(s):
    abi = ["zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6", "fp"]
    for i in range(32):
        if s == abi[i]:
            if i<32:
                return i
            else:
                return 8

def binary_conv(n, x):
    s = "0"+str(x)+"b"
    return format(n% (1 << x), s)

def sep_command(comm, label_dict=None, pc=0):
    parts = comm.replace(",", " ").split()
    while len(parts) < 4:
        parts.append("0")
    result = []
    instruction = parts[0]
    result.append(instruction)
    if instruction == "jal":
        result.append(parts[1])
        if label_dict and parts[2] in label_dict:
            imm = label_dict[parts[2]] - pc
            result.append(str(imm))
        else:
            result.append(parts[2])
    elif instruction in ["bne", "beq", "blt"]:
        result.append(parts[1])
        result.append(parts[2])
        if label_dict and parts[3] in label_dict:
            imm = label_dict[parts[3]] - pc
            result.append(str(imm))
        else:
            result.append(parts[3])
    elif instruction in ["addi", "lw", "sw"]:
        result.append(parts[1])
        result.append(parts[2])
        result.append(parts[3])
    else:
        result.extend(parts[1:])
    return result

def r_type(l):

    a = ["", "", "", "", "", ""]
    if l[0] == "add":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "000"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0000000"
    elif l[0] == "sub":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "000"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0100000"
    elif l[0] == "slt":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "010"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0000000"
    elif l[0] == "srl":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "101"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0000000"
    elif l[0]=="or":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "110"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0000000"
    elif l[0] == "and":
        rs1 = reg_value(l[2])
        rs2 = reg_value(l[3])
        rd = reg_value(l[1])
        a[0] = "0110011"
        a[1] = binary_conv(rd, 5)
        a[2] = "111"
        a[3] = binary_conv(rs1, 5)
        a[4] = binary_conv(rs2, 5)
        a[5] = "0000000"
    val = ""
    for i in range(5, -1, -1):
        val += a[i]
    return val
def encode_b_type(instruction, label_dict, pc):
    parts = sep_command(instruction, label_dict, pc)
    opcode = "1100011"
    funct3_dict = {"beq": "000", "bne": "001", "blt": "100"}
    funct3 = funct3_dict.get(parts[0], "000")
    rs1 = binary_conv(reg_value(parts[1]), 5)
    rs2 = binary_conv(reg_value(parts[2]), 5)
    imm = binary_conv(int(parts[3]), 13)
    imm_bin=imm[::-1]
    imm_final = imm_bin[12] + imm_bin[10:4:-1] + imm_bin[4:0:-1] + imm_bin[11]
    return imm_final[0:7:1] + rs2 + rs1 + funct3 + imm_final[7:13:1] + opcode

def process_and_write_output(input_filename, output_filename):
    instructions, label_dict = process_input_file(input_filename)
    
    with open(output_filename, 'w') as output_file:
        for pc, instr in enumerate(instructions):
            parts = sep_command(instr, label_dict, pc * 4)
            if parts[0] in ["addi", "jalr"]:
                binary_instr = encode_i_type(parts[0], parts[1], parts[2], parts[3])
            elif parts[0] in ["lw"]:
                l_new = for_lw(parts[2])
                binary_instr = encode_i_type(parts[0], parts[1], l_new[1], l_new[0])
            elif parts[0] in ["add", "sub", "slt", "srl", "or", "and"]:
                binary_instr = r_type(parts)
            elif parts[0] in ["sw"]:
                binary_instr = encode_s_type(instr)
            elif parts[0] in ["beq", "bne", "blt"]:
                binary_instr = encode_b_type(instr, label_dict, pc * 4)
            elif parts[0] in ["jal"]:
                binary_instr = j_type(parts)
            else:
                binary_instr = "Unsupported instruction"
            
            output_file.write(binary_instr + '\n')

input_filename = input("Enter the name of input file : ")
output_filename = input("Enter the name of output file : ")
process_and_write_output(input_filename, output_filename)
print("Binary output written to", output_filename)
