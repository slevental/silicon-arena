# Makefile for Verilator Coverage Concept
# Task ID: silicon-arena-6g7.5
# Spec Reference: File 2 - "Coverage tracking via Verilator --coverage"

# Paths - Using 32-bit IEEE-754 FP ALU
RTL_DIR = ../../rtl/fp_alu_32bit/rtl
RTL_SRC = $(RTL_DIR)/ALU.v
TB_SRC  = tb_alu_cov.cpp

# Verilator settings
VERILATOR = verilator
VERILATOR_FLAGS = --cc --exe --build -j 0
VERILATOR_FLAGS += --coverage          # Enable all coverage types
VERILATOR_FLAGS += --coverage-line     # Line coverage
VERILATOR_FLAGS += --coverage-toggle   # Toggle coverage
VERILATOR_FLAGS += -CFLAGS "-g"        # Debug symbols
# Suppress warnings for tristate logic (FP ALU uses multi-driven outputs)
VERILATOR_FLAGS += -Wno-fatal -Wno-MULTIDRIVEN -Wno-IMPLICIT -Wno-CASEX
VERILATOR_FLAGS += -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC -Wno-UNOPTFLAT -Wno-CASEINCOMPLETE

# Output
TOP_MODULE = ALU
OBJ_DIR = obj_dir
EXECUTABLE = $(OBJ_DIR)/V$(TOP_MODULE)

# Coverage outputs
COV_DAT = coverage.dat
COV_INFO = coverage.info
COV_ANNOTATE_DIR = annotated
COV_HTML_DIR = coverage_html

.PHONY: all clean run coverage annotate html report

all: $(EXECUTABLE)

$(EXECUTABLE): $(RTL_SRC) $(TB_SRC)
	@echo "=== Compiling with Verilator (coverage enabled) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) $(RTL_SRC) $(TB_SRC) --top-module $(TOP_MODULE)
	@echo "=== Build complete ==="

run: $(EXECUTABLE)
	@echo "=== Running simulation ==="
	./$(EXECUTABLE)

# Generate annotated source files
annotate: run
	@echo "=== Generating annotated source files ==="
	verilator_coverage --annotate $(COV_ANNOTATE_DIR) --annotate-all $(COV_DAT)
	@echo "Annotated files in: $(COV_ANNOTATE_DIR)/"
	@echo ""
	@echo "=== Coverage annotation legend ==="
	@echo "  ' ' = All coverage points hit >= threshold"
	@echo "  '%' = Below threshold"
	@echo "  '~' = Mixed (some above, some below)"
	@echo "  '+' = Above threshold with point details"
	@echo "  '-' = Below threshold with point details"

# Generate lcov info file
info: run
	@echo "=== Generating lcov info file ==="
	verilator_coverage --write-info $(COV_INFO) $(COV_DAT)
	@echo "Info file: $(COV_INFO)"

# Generate HTML report (requires lcov/genhtml)
html: info
	@echo "=== Generating HTML coverage report ==="
	@if command -v genhtml > /dev/null; then \
		genhtml $(COV_INFO) --output-directory $(COV_HTML_DIR); \
		echo "HTML report: $(COV_HTML_DIR)/index.html"; \
	else \
		echo "genhtml not found. Install lcov package."; \
		echo "On macOS: brew install lcov"; \
		echo "On Ubuntu: apt install lcov"; \
	fi

# Full coverage report
report: annotate info
	@echo ""
	@echo "=== Coverage Report Summary ==="
	@echo "Coverage data: $(COV_DAT)"
	@echo "Annotated sources: $(COV_ANNOTATE_DIR)/"
	@echo "LCOV info: $(COV_INFO)"
	@echo ""
	@echo "To view annotated ALU source:"
	@echo "  cat $(COV_ANNOTATE_DIR)/ALU.v"

# Show coverage statistics
stats: run
	@echo "=== Coverage Statistics ==="
	@verilator_coverage --rank $(COV_DAT) 2>/dev/null || echo "Rank not available"

clean:
	rm -rf $(OBJ_DIR) $(COV_DAT) $(COV_INFO) $(COV_ANNOTATE_DIR) $(COV_HTML_DIR)

# Show Verilator version
version:
	$(VERILATOR) --version

help:
	@echo "Targets:"
	@echo "  all      - Build the simulation executable with coverage"
	@echo "  run      - Build and run simulation (generates coverage.dat)"
	@echo "  annotate - Generate annotated source files"
	@echo "  info     - Generate lcov .info file"
	@echo "  html     - Generate HTML coverage report (requires genhtml)"
	@echo "  report   - Generate all coverage reports"
	@echo "  stats    - Show coverage statistics"
	@echo "  clean    - Remove build artifacts"
	@echo "  version  - Show Verilator version"
