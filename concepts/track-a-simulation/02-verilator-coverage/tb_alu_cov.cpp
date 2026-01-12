// Verilator C++ Testbench with Coverage
// Task ID: silicon-arena-6g7.5
// Spec Reference: File 2 - "Coverage tracking via Verilator --coverage"
//
// Updated to use 32-bit IEEE-754 FP ALU

#include <stdlib.h>
#include <iostream>
#include <cstring>
#include <verilated.h>
#include <verilated_cov.h>
#include "VALU.h"

// Operation codes matching FP ALU RTL
enum FpAluOp {
    OP_MUL       = 1,   // Multiplication
    OP_DIV       = 2,   // Division
    OP_SUB       = 3,   // Subtraction
    OP_OR        = 4,   // Bitwise OR
    OP_AND       = 5,   // Bitwise AND
    OP_XOR       = 6,   // Bitwise XOR
    OP_SHL       = 7,   // Left Shift (by 1)
    OP_SHR       = 8,   // Right Shift (by 1)
    OP_FP2INT    = 9,   // FP to Integer
    OP_ADD       = 10,  // Addition
    OP_COMPL     = 11   // Complement
};

const char* op_name(int op) {
    switch(op) {
        case OP_MUL:    return "MUL";
        case OP_DIV:    return "DIV";
        case OP_SUB:    return "SUB";
        case OP_OR:     return "OR";
        case OP_AND:    return "AND";
        case OP_XOR:    return "XOR";
        case OP_SHL:    return "SHL";
        case OP_SHR:    return "SHR";
        case OP_FP2INT: return "FP2INT";
        case OP_ADD:    return "ADD";
        case OP_COMPL:  return "COMPL";
        default:        return "???";
    }
}

// Convert float to IEEE-754 32-bit representation
uint32_t float_to_ieee754(float f) {
    uint32_t result;
    memcpy(&result, &f, sizeof(result));
    return result;
}

void run_test(VALU* dut, uint32_t a, uint32_t b, uint8_t op) {
    dut->a_operand = a;
    dut->b_operand = b;
    dut->Operation = op;
    dut->eval();
}

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);

    // Create DUT instance
    VALU* dut = new VALU;

    std::cout << "=== FP ALU (32-bit IEEE-754) Coverage Testbench ===" << std::endl;
    std::cout << "Note: This design uses tristate logic which Verilator" << std::endl;
    std::cout << "      doesn't fully support. Coverage is still collected." << std::endl;

    // Run limited tests to demonstrate coverage gaps
    // This intentionally does NOT cover all operations

    std::cout << "\n[Phase 1] Testing ADD operation (op=10)..." << std::endl;
    run_test(dut, float_to_ieee754(1.0f), float_to_ieee754(2.0f), OP_ADD);
    run_test(dut, float_to_ieee754(3.5f), float_to_ieee754(2.5f), OP_ADD);
    run_test(dut, float_to_ieee754(100.0f), float_to_ieee754(0.5f), OP_ADD);
    run_test(dut, float_to_ieee754(-5.0f), float_to_ieee754(3.0f), OP_ADD);
    run_test(dut, float_to_ieee754(0.0f), float_to_ieee754(0.0f), OP_ADD);

    std::cout << "[Phase 2] Testing SUB operation (op=3)..." << std::endl;
    run_test(dut, float_to_ieee754(10.0f), float_to_ieee754(5.0f), OP_SUB);
    run_test(dut, float_to_ieee754(100.0f), float_to_ieee754(50.0f), OP_SUB);
    run_test(dut, float_to_ieee754(1.0f), float_to_ieee754(1.0f), OP_SUB);

    std::cout << "[Phase 3] Testing AND operation (op=5)..." << std::endl;
    run_test(dut, 0xFFFF0000, 0x0000FFFF, OP_AND);
    run_test(dut, 0xAAAAAAAA, 0x55555555, OP_AND);

    // Note: MUL, DIV, OR, XOR, SHL, SHR, FP2INT, COMPL are NOT tested
    // This creates coverage holes for the concept demonstration

    std::cout << "\n=== Test Summary ===" << std::endl;
    std::cout << "Operations tested: ADD (10), SUB (3), AND (5)" << std::endl;
    std::cout << "Operations NOT tested: MUL (1), DIV (2), OR (4), XOR (6)," << std::endl;
    std::cout << "                       SHL (7), SHR (8), FP2INT (9), COMPL (11)" << std::endl;
    std::cout << "This intentionally creates coverage gaps for demonstration." << std::endl;

    // Write coverage data
    std::cout << "\n[Writing coverage data to coverage.dat]" << std::endl;
    VerilatedCov::write("coverage.dat");

    // Cleanup
    delete dut;

    std::cout << "\n=== Coverage data written ===" << std::endl;
    std::cout << "Use verilator_coverage to analyze:" << std::endl;
    std::cout << "  verilator_coverage --annotate annotated coverage.dat" << std::endl;
    std::cout << "  verilator_coverage --write-info coverage.info coverage.dat" << std::endl;

    return 0;
}
