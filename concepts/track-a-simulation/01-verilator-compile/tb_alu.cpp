// Verilator C++ Testbench for 8-bit ALU
// Task ID: silicon-arena-6g7.4
// Spec Reference: File 2 - "verilator --cc" and "RTLEnv wrapper"

#include <stdlib.h>
#include <iostream>
#include <verilated.h>
#include <verilated_vcd_c.h>
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

int main(int argc, char** argv) {
    // Initialize Verilator
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    // Create DUT instance
    Valu* dut = new Valu;

    // Setup VCD tracing
    VerilatedVcdC* trace = new VerilatedVcdC;
    dut->trace(trace, 99);
    trace->open("alu_waveform.vcd");

    // Test vectors: {a, b, op, expected_result}
    struct TestVector {
        uint8_t a;
        uint8_t b;
        uint8_t op;
        uint8_t expected;
        bool check_zero;
        bool expected_zero;
    };

    TestVector tests[] = {
        // ADD tests
        {0x00, 0x00, OP_ADD, 0x00, true, true},    // 0 + 0 = 0, zero=1
        {0x01, 0x01, OP_ADD, 0x02, true, false},   // 1 + 1 = 2
        {0xFF, 0x01, OP_ADD, 0x00, true, true},    // 255 + 1 = 0 (overflow), zero=1
        {0x7F, 0x01, OP_ADD, 0x80, false, false},  // 127 + 1 = 128

        // SUB tests
        {0x05, 0x03, OP_SUB, 0x02, true, false},   // 5 - 3 = 2
        {0x03, 0x03, OP_SUB, 0x00, true, true},    // 3 - 3 = 0, zero=1
        {0x00, 0x01, OP_SUB, 0xFF, true, false},   // 0 - 1 = 255 (underflow)

        // AND tests
        {0xAA, 0x55, OP_AND, 0x00, true, true},    // 1010 & 0101 = 0
        {0xFF, 0x0F, OP_AND, 0x0F, true, false},   // all & low = low

        // OR tests
        {0xAA, 0x55, OP_OR, 0xFF, true, false},    // 1010 | 0101 = 1111
        {0x00, 0x00, OP_OR, 0x00, true, true},     // 0 | 0 = 0

        // XOR tests
        {0xFF, 0xFF, OP_XOR, 0x00, true, true},    // all ^ all = 0
        {0xAA, 0x55, OP_XOR, 0xFF, true, false},   // 1010 ^ 0101 = 1111

        // NOT tests
        {0xAA, 0x00, OP_NOT, 0x55, true, false},   // ~1010 = 0101
        {0xFF, 0x00, OP_NOT, 0x00, true, true},    // ~1111 = 0000

        // Shift tests
        {0x01, 0x04, OP_SHL, 0x10, true, false},   // 1 << 4 = 16
        {0x80, 0x04, OP_SHR, 0x08, true, false},   // 128 >> 4 = 8
        {0x01, 0x00, OP_SHL, 0x01, true, false},   // 1 << 0 = 1
    };

    int num_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0;
    int failed = 0;
    vluint64_t sim_time = 0;

    std::cout << "=== ALU Verilator Testbench ===" << std::endl;
    std::cout << "Running " << num_tests << " test vectors..." << std::endl;
    std::cout << std::endl;

    for (int i = 0; i < num_tests; i++) {
        TestVector& t = tests[i];

        // Apply inputs
        dut->a = t.a;
        dut->b = t.b;
        dut->op = t.op;

        // Evaluate (combinational, no clock)
        dut->eval();

        // Dump to VCD
        trace->dump(sim_time);
        sim_time += 10;

        // Check results
        bool result_ok = (dut->result == t.expected);
        bool zero_ok = !t.check_zero || (dut->zero == t.expected_zero);
        bool test_passed = result_ok && zero_ok;

        if (test_passed) {
            passed++;
        } else {
            failed++;
            std::cout << "[FAIL] Test " << i << ": "
                      << op_name(t.op) << " "
                      << "a=0x" << std::hex << (int)t.a << " "
                      << "b=0x" << std::hex << (int)t.b << std::endl;
            std::cout << "       Expected: result=0x" << std::hex << (int)t.expected;
            if (t.check_zero) std::cout << " zero=" << t.expected_zero;
            std::cout << std::endl;
            std::cout << "       Got:      result=0x" << std::hex << (int)dut->result
                      << " zero=" << (int)dut->zero << std::endl;
        }
    }

    // Final evaluation for VCD
    trace->dump(sim_time);
    trace->close();

    // Print summary
    std::cout << std::endl;
    std::cout << "=== Test Summary ===" << std::endl;
    std::cout << "Passed: " << std::dec << passed << "/" << num_tests << std::endl;
    std::cout << "Failed: " << failed << "/" << num_tests << std::endl;
    std::cout << "VCD written to: alu_waveform.vcd" << std::endl;

    // Cleanup
    delete dut;
    delete trace;

    return (failed == 0) ? 0 : 1;
}
