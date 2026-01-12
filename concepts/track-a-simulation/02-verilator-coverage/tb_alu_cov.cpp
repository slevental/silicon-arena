// Verilator C++ Testbench with Coverage
// Task ID: silicon-arena-6g7.5
// Spec Reference: File 2 - "Coverage tracking via Verilator --coverage"

#include <stdlib.h>
#include <iostream>
#include <verilated.h>
#include <verilated_cov.h>
#include "Valu.h"

// Operation codes matching RTL
enum AluOp {
    OP_ADD = 0b000,
    OP_SUB = 0b001,
    OP_AND = 0b010,
    OP_OR  = 0b011,
    OP_XOR = 0b100,
    OP_NOT = 0b101,
    OP_SHL = 0b110,
    OP_SHR = 0b111
};

const char* op_name(int op) {
    switch(op) {
        case OP_ADD: return "ADD";
        case OP_SUB: return "SUB";
        case OP_AND: return "AND";
        case OP_OR:  return "OR";
        case OP_XOR: return "XOR";
        case OP_NOT: return "NOT";
        case OP_SHL: return "SHL";
        case OP_SHR: return "SHR";
        default:     return "???";
    }
}

void run_test(Valu* dut, uint8_t a, uint8_t b, uint8_t op) {
    dut->a = a;
    dut->b = b;
    dut->op = op;
    dut->eval();
}

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);

    // Create DUT instance
    Valu* dut = new Valu;

    std::cout << "=== ALU Coverage Testbench ===" << std::endl;

    // Run limited tests to demonstrate coverage gaps
    // This intentionally does NOT cover all operations

    std::cout << "\n[Phase 1] Testing ADD operation only..." << std::endl;
    for (int i = 0; i < 10; i++) {
        run_test(dut, i, i+1, OP_ADD);
    }

    std::cout << "[Phase 2] Testing SUB operation..." << std::endl;
    for (int i = 0; i < 5; i++) {
        run_test(dut, 10, i, OP_SUB);
    }

    std::cout << "[Phase 3] Testing AND operation..." << std::endl;
    run_test(dut, 0xFF, 0x0F, OP_AND);
    run_test(dut, 0xAA, 0x55, OP_AND);

    // Note: OR, XOR, NOT, SHL, SHR are NOT tested
    // This creates coverage holes for the concept demonstration

    std::cout << "\n=== Test Summary ===" << std::endl;
    std::cout << "Operations tested: ADD, SUB, AND" << std::endl;
    std::cout << "Operations NOT tested: OR, XOR, NOT, SHL, SHR" << std::endl;
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
