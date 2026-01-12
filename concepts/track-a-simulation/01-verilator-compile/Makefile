# Makefile for Verilator ALU Compilation Concept
# Task ID: silicon-arena-6g7.4
# Spec Reference: File 2 - "verilator --cc"

# Paths
RTL_DIR = ../../rtl/alu_8bit
RTL_SRC = $(RTL_DIR)/alu.v
TB_SRC  = tb_alu.cpp

# Verilator settings
VERILATOR = verilator
VERILATOR_FLAGS = --cc --exe --build -Wall
VERILATOR_FLAGS += --trace           # Enable VCD tracing
VERILATOR_FLAGS += -CFLAGS "-g"      # Debug symbols

# Output
TOP_MODULE = alu
OBJ_DIR = obj_dir
EXECUTABLE = $(OBJ_DIR)/V$(TOP_MODULE)

.PHONY: all clean run trace

all: $(EXECUTABLE)

$(EXECUTABLE): $(RTL_SRC) $(TB_SRC)
	@echo "=== Compiling with Verilator ==="
	$(VERILATOR) $(VERILATOR_FLAGS) $(RTL_SRC) $(TB_SRC) --top-module $(TOP_MODULE)
	@echo "=== Build complete ==="

run: $(EXECUTABLE)
	@echo "=== Running simulation ==="
	./$(EXECUTABLE)

trace: run
	@echo "=== Opening waveform viewer ==="
	@if command -v gtkwave > /dev/null; then \
		gtkwave alu_waveform.vcd &; \
	else \
		echo "gtkwave not found. VCD file: alu_waveform.vcd"; \
	fi

clean:
	rm -rf $(OBJ_DIR) alu_waveform.vcd

# Show Verilator version
version:
	$(VERILATOR) --version

# Lint only (no build)
lint:
	$(VERILATOR) --lint-only -Wall $(RTL_SRC)

help:
	@echo "Targets:"
	@echo "  all     - Build the simulation executable"
	@echo "  run     - Build and run the simulation"
	@echo "  trace   - Run and open waveform viewer"
	@echo "  clean   - Remove build artifacts"
	@echo "  lint    - Run Verilator lint checks"
	@echo "  version - Show Verilator version"
