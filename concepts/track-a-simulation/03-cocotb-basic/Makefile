# Cocotb Makefile for ALU testbench
# Task ID: silicon-arena-6g7.7
# Spec Reference: File 2 - "Cocotb testbenches"

# Simulator selection
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

# Source files
VERILOG_SOURCES = $(PWD)/../../rtl/alu_8bit/alu.v

# Top level module
TOPLEVEL = alu

# Python test module
MODULE = test_alu

# Verilator-specific settings
EXTRA_ARGS += --trace --trace-structs
EXTRA_ARGS += -Wno-fatal

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
