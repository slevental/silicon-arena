# Cocotb Makefile for FP ALU testbench (32-bit IEEE-754)
# Task ID: silicon-arena-6g7.7
# Spec Reference: File 2 - "Cocotb testbenches"

# Simulator selection
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

# Source files - Using 32-bit IEEE-754 FP ALU
VERILOG_SOURCES = $(PWD)/../../rtl/fp_alu_32bit/rtl/ALU.v

# Top level module
TOPLEVEL = ALU

# Python test module
MODULE = test_alu

# Verilator-specific settings
EXTRA_ARGS += --trace --trace-structs
# Suppress warnings for tristate logic (FP ALU uses multi-driven outputs)
EXTRA_ARGS += -Wno-fatal -Wno-MULTIDRIVEN -Wno-IMPLICIT -Wno-CASEX
EXTRA_ARGS += -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC -Wno-UNOPTFLAT -Wno-CASEINCOMPLETE -Wno-LATCH

# Enable coverage (optional)
# EXTRA_ARGS += --coverage --coverage-line --coverage-toggle

# Include cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim

# Additional targets
.PHONY: waves clean-all

waves: sim
	gtkwave dump.vcd &

clean-all: clean
	rm -rf __pycache__ *.vcd *.xml cocotb_coverage.json results.xml
