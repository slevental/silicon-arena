# Silicon Arena EDA Base Image
# Spec Reference: File 2 (RL Verification Gym Architecture.md) - "VeriGym Dockerfile Specification"
# Task ID: silicon-arena-6g7.3

FROM ubuntu:22.04

LABEL maintainer="Silicon Arena Project"
LABEL description="EDA tools for hardware verification: Verilator, Yosys, SymbiYosys, Cocotb"
LABEL version="1.0"

# Prevent interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    build-essential \
    git \
    wget \
    curl \
    ca-certificates \
    # Python
    python3.11 \
    python3.11-venv \
    python3-pip \
    # Verilator dependencies
    autoconf \
    flex \
    bison \
    libfl2 \
    libfl-dev \
    # Yosys dependencies
    clang \
    lld \
    tcl-dev \
    libreadline-dev \
    libffi-dev \
    pkg-config \
    # Formal verification
    z3 \
    yices2 \
    # Waveform viewer
    gtkwave \
    # Misc
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install Verilator from thomasnormal fork (enhanced SystemVerilog/UVM support)
# This fork includes fixes for:
# - Stream expressions with [] selection syntax
# - $past with explicit clock argument
# - Bind with instance list syntax
# - Modport empty expression syntax
# - Soft constraints and other UVM features
ARG VERILATOR_REPO=https://github.com/thomasnormal/verilator.git
ARG VERILATOR_BRANCH=local/combined-features
RUN git clone ${VERILATOR_REPO} /tmp/verilator \
    && cd /tmp/verilator \
    && git checkout ${VERILATOR_BRANCH} \
    && autoconf \
    && ./configure --prefix=/usr/local \
    && make -j$(nproc) \
    && make install \
    && rm -rf /tmp/verilator

# Install Yosys from source
ARG YOSYS_VERSION=yosys-0.40
RUN git clone https://github.com/YosysHQ/yosys.git /tmp/yosys \
    && cd /tmp/yosys \
    && git checkout ${YOSYS_VERSION} \
    && make config-clang \
    && make -j$(nproc) \
    && make install \
    && rm -rf /tmp/yosys

# Install SymbiYosys (formal verification frontend)
RUN git clone https://github.com/YosysHQ/sby.git /tmp/sby \
    && cd /tmp/sby \
    && make install \
    && rm -rf /tmp/sby

# Install Python verification stack
RUN pip3 install --no-cache-dir \
    # Cocotb and extensions
    cocotb>=1.8.0 \
    cocotb-test>=0.2.4 \
    cocotb-coverage>=1.1.0 \
    # VCD/waveform parsing
    pyvcd>=0.3.0 \
    vcdvcd>=2.2.0 \
    # Scientific computing
    numpy>=1.24.0 \
    scipy>=1.11.0 \
    # XML/JSON parsing
    xmltodict>=0.13.0 \
    # Testing
    pytest>=7.4.0 \
    pytest-xdist>=3.3.0 \
    # Utilities
    rich>=13.0.0 \
    typer>=0.9.0

# Install additional formal verification tools
# Boolector (SMT solver)
RUN git clone https://github.com/boolector/boolector.git /tmp/boolector \
    && cd /tmp/boolector \
    && ./contrib/setup-lingeling.sh \
    && ./contrib/setup-btor2tools.sh \
    && ./configure.sh --prefix=/usr/local \
    && cd build && make -j$(nproc) && make install \
    && rm -rf /tmp/boolector

# Create workspace directory
WORKDIR /workspace

# Environment variables
ENV PYTHONPATH=/workspace
ENV VERILATOR_ROOT=/usr/local/share/verilator

# Verify installations
RUN echo "=== Verification ===" \
    && verilator --version \
    && yosys --version \
    && sby --help | head -5 \
    && python3 -c "import cocotb; print(f'cocotb {cocotb.__version__}')" \
    && echo "=== All tools installed ==="

# Default command
CMD ["/bin/bash"]
