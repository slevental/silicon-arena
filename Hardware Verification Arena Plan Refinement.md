# **VerifyGym Ultra: Architectural Audit, Theoretical Framework, and Strategic Implementation Report**

## **Executive Summary**

The proposal for **VerifyGym Ultra** outlines a sophisticated, adversarial environment designed to revolutionize hardware verification through the application of Multi-Agent Reinforcement Learning (MARL). By framing verification as a zero-sum game between **Generators** (Constructors/Verifiers) and **Adversaries** (Auditors/Mutators), the system aims to automate the discovery of corner-case bugs that traditional constrained-random verification methodologies often miss. The architectural choices of **TerminalBench** for the execution substrate and **rLLM** for the training backbone provide a theoretically sound starting point, leveraging state-of-the-art infrastructure for agentic workflows and verifiable rewards.

However, a rigorous audit of the proposed plan reveals significant latent risks and architectural gaps that, if unaddressed, could lead to training divergence, reward hacking, or system non-convergence. Specifically, the "Bit-Driven" methodology lacks the granularity required to guide agents through the steep learning curve of formal logic; the proposed reward functions are vulnerable to vacuity exploitation; and the integration of strictly zero-sum dynamics into frameworks optimized for cooperative tasks requires substantial engineering of the orchestration layer. Furthermore, the exclusion of human-in-the-loop debugging tools for waveform analysis threatens the practical usability of the system.

This report serves as a comprehensive design specification and critical analysis. It deconstructs the initial vision, identifies fragility in the toolchain integration, and proposes a **"Byte-Driven" Maturity Model**, a **Proof-Depth Reward Manifold**, and a **Hypervisor-Based Adversarial Orchestrator**. Drawing upon the latest research in formal methods, automated program repair, and agentic reinforcement learning, this document provides the detailed technical roadmap necessary to elevate VerifyGym Ultra from a concept to an industrial-grade verification arena.

## ---

**1\. Vision & Architecture: The Adversarial Paradigm**

The core premise of VerifyGym Ultra represents a paradigm shift from static, heuristic-based testing to dynamic, adversarial agentic workflows. In traditional verification, engineers write static tests to catch dynamic bugs. In the VerifyGym paradigm, the tests themselves are dynamic agents that evolve in response to the design's hardening. This mirrors the "Red Team / Blue Team" dynamic in cybersecurity but applied to the rigorous mathematical domain of Register Transfer Level (RTL) design.

### **1.1 The Technological Substrate**

The selection of the technology stack is critical for the stability of long-horizon RL training. The proposed stack—TerminalBench for the body and rLLM for the brain—is viable but requires specific optimizations for the EDA (Electronic Design Automation) domain.

#### **1.1.1 The OS (Body): TerminalBench Enhanced**

**TerminalBench** provides a robust, sandboxed environment for executing command-line tasks, which is essential for EDA tools that often rely on complex, interdependent binaries and environment variables. Unlike web-based agents that operate in high-level APIs, a hardware agent must interact with the gritty reality of the Linux command line—managing file descriptors, parsing stderr streams, and handling exit codes from solvers like Z3 or Yices.

The proposal correctly identifies the need for a persistent, sandboxed terminal. However, standard TerminalBench configurations are often ephemeral. For hardware verification, where a single formal proof can take minutes or hours, the environment must support **long-running, stateful sessions**. The integration of a persistent container architecture, as seen in advanced deployments of TerminalBench, enables the agent to maintain context across multi-turn reasoning loops. This persistence allows for "debugging sessions" where an agent runs a simulation, observes a waveform, modifies the code, and re-runs the simulation without losing the shell history or the build artifacts.

#### **1.1.2 The Brain (Training): rLLM & Adversarial Flows**

**rLLM** (Reinforcement Learning for Language Models) is chosen as the training framework. rLLM is designed for post-training language agents via reinforcement learning, specifically optimizing for verifiable rewards (RLVR). Its AgentWorkflowEngine enables the definition of complex, multi-step reasoning loops (Chain-of-Thought) and the management of trajectory generation.

However, rLLM is primarily architected for single-agent optimization or cooperative multi-agent flows (e.g., Solver-Judge). The VerifyGym Ultra proposal introduces a **competitive, zero-sum dynamics**, which introduces non-stationarity into the learning environment. If Agent A (The Verifier) improves, Agent B (The Adversary) sees its reward drop, potentially destabilizing the training signal. To mitigate this, the architecture must implement **League Training** or **Fictitious Self-Play** (FSP), mechanisms not native to the basic rLLM examples but essential for adversarial convergence. This report will detail the implementation of a custom AdversarialWorkflowEngine that extends rLLM to handle these dynamics.

### **1.2 The Input Data: Alignment with Industry Standards**

The reliance on SWE-Bench formatted datasets (VerilogEval, CVDP) is a strategic choice. SWE-Bench has emerged as the de facto standard for evaluating coding agents, creating a unified schema for problem statements, code repositories, and patch verification. By aligning VerifyGym Ultra with this format, the project ensures that its datasets are interoperable with the broader AI research community. This allows for the seamless import of new tasks and the export of "Golden Verified" trajectories that can be used to fine-tune other coding models.

## ---

**2\. Methodology: From Bit-Driven to Byte-Driven Development**

The initial proposal suggests a "Bit-Driven" (BD) development methodology with a 4-bit progress tracker. While agile, this 4-step progression is insufficiently granular for the complexity of formal verification. A binary "works/doesn't work" metric fails to capture the subtle gradations of competence required to master hardware design—such as syntax correctness, synthesis viability, simulation passing, formal safety, and liveness properties.

### **2.1 The Byte-Driven (ByD) Capability Matrix**

To provide a robust curriculum and precise progress tracking, we propose expanding the methodology to a **64-bit Capability Matrix**, organized into "Bytes" of competency. This matrix serves as both a development roadmap and a curriculum schedule for the RL agents. Agents must demonstrate mastery of lower-order bytes before being exposed to higher-order adversarial challenges, preventing the "collapse to noise" phenomenon where agents learn to exploit environment fragility rather than solving the task.

| Byte Index | Domain | Bit 0 (LSB) Criteria | Bit 7 (MSB) Criteria |
| :---- | :---- | :---- | :---- |
| **0x00** | **Infrastructure** | Docker container boots and executes sby \--version. | Toolchain end-to-end latency \< 500ms for "Hello World". |
| **0x01** | **Syntax & Lint** | Verilator lints clean (no syntax errors). | Design synthesizes via Yosys without latch inferences. |
| **0x02** | **Simulation** | Testbench compiles without error. | Self-checking testbench passes 100% of directed vectors. |
| **0x03** | **Formal (Safety)** | SymbiYosys (SBY) parses SystemVerilog Assertions (SVA). | Bounded Model Checking (BMC) depth \> 20 cycles passes. |
| **0x04** | **Formal (Liveness)** | Liveness properties (s\_eventually) defined. | K-Induction proof completes successfully. |
| **0x05** | **Coverage** | Line coverage \> 0% verified by Verilator/Cocotb. | Mutation Coverage (MCY) \> 95% kill ratio on standard faults. |
| **0x06** | **Adversarial** | Auditor detects a trivial, injected bug. | Auditor generates a bug that survives 10 adversarial rounds. |
| **0x07** | **System Stability** | Multi-agent loop executes 100 steps without crashing. | RLVR convergence: Policy entropy stabilizes below threshold. |

### **2.2 Curriculum Learning Implication**

This matrix dictates the **Curriculum Schedule**. During the initial training phases (Phase 1 & 2), the Adversary is disabled, and the Generator is trained solely on Bytes 0x00 through 0x04. Only once the agent consistently achieves "Formal Safety" (Byte 0x03) is the Adversarial Arena (Byte 0x06) unlocked. This ensures that the Generator has a baseline of competence before facing an active opponent, mirroring the progression from "learning the rules" to "sparring" in human mastery.

## ---

**3\. Phase 1: The Agent OS (TerminalBench \+ Docker)**

The physical layer of the simulation—the "Body"—is where the agent interacts with reality. The proposal to fork TerminalBench and create a Dockerfile.eda is the correct approach, but the implementation details determine the system's determinism and reproducibility.

### **3.1 Step 1.1: The Hardware Image Architecture**

A simple apt-get install approach is insufficient for a rigorous verification environment. EDA tools are notoriously sensitive to version mismatches; a discrepancy between the Yosys version used for synthesis and the SymbiYosys version used for formal proofs can lead to undefined behavior or vacuous rewards.

Advanced Docker Layering Strategy:  
To ensure absolute determinism, the Dockerfile.eda must be constructed using a multi-stage build process that pins specific commit hashes of the core tools.

1. **Layer 0: The Base (Canonical Ubuntu)**  
   * Start with ubuntu:22.04 (Jammy Jellyfish) for broad compatibility.  
   * Install essential build dependencies: build-essential, clang, bison, flex, libreadline-dev, gawk, tcl-dev, libffi-dev, git, graphviz, xdot, pkg-config, python3, libboost-system-dev, libboost-python-dev, libboost-filesystem-dev, zlib1g-dev.  
2. **Layer 1: The Solver Stack (Pre-Computation)**  
   * Compiling solvers from source is time-consuming. This layer should fetch pre-compiled binaries or strictly versioned source tarballs of the formal solvers.  
   * **Z3:** The standard SMT solver. Version 4.12.2 is recommended for stability.  
   * **Boolector:** Often faster than Z3 for bit-vector logic (hardware). Version 3.2.2.  
   * **Yices 2:** A strong alternative solver for specific logic types.  
   * **Super\_prove:** For advanced inductive proofs (optional, but powerful).  
3. **Layer 2: The EDA Core (Yosys & Verilator)**  
   * **Verilator:** Must be compiled with CFLAGS="-O3" to maximize simulation performance. This is critical because the Mutation Oracle will run thousands of simulations per training step.  
   * **Yosys:** Clone from the YosysHQ repository and pin to a specific stable release tag (e.g., yosys-0.39). This ensures that the JSON netlist generation used for the "Structural Oracle" remains consistent across the project lifecycle.  
   * **SymbiYosys (SBY):** The front-end driver for formal verification. It must be configured to prioritize smtbmc (the SMT-based bounded model checker) as the default engine for speed.  
4. **Layer 3: The Python Shim (Agent Interface)**  
   * Install cocotb for Python-based testbenching.  
   * Install pylint and verilog-mode for code quality checks.  
   * Install custom wrapper scripts (discussed in Step 1.2) that sanitize tool output for the LLM.

Verification Step:  
The build process must conclude with a self-test script that not only runs sby \--version but also executes a "Golden Reference" proof—a simple counter module with a known assertion. This confirms that the entire stack (Solver \-\> SBY \-\> Yosys \-\> OS) is functionally integrated.

### **3.2 Step 1.2: The Hardware Environment Wrapper (HEW)**

The proposal suggests subclassing TerminalBench to add tool-use actions. This is necessary but insufficient. Raw output from EDA tools is notoriously verbose. An LLM consuming raw verilator logs will quickly exhaust its context window with meaningless compilation artifacts, reducing its ability to reason about the actual error.

Structured Observation Wrappers (SOW):  
We must implement a layer of "middleware" scripts that intercept the stdout/stderr of the EDA tools and parse them into a structured, token-efficient format before passing them to the agent.

* **The Problem:** Running verilator \--lint-only my\_design.v might produce 200 lines of text, including warnings about unused signals, copyright headers, and verbose path information.  
* **The SOW Solution:** The wrapper script executes the command, parses the output using regex, and returns a JSON object:  
  JSON  
  {  
    "status": "FAILED",  
    "error\_count": 2,  
    "warning\_count": 1,  
    "errors":  
  }

This **Semantic Information Density** approach allows the agent to focus on the *logic* of the error rather than the *parsing* of the log file. It essentially provides the agent with the "Intellisense" experience of a modern IDE.

State Tracking: VFS vs. Git  
The proposal suggests git init and committing every step. While robust, Git operations can be slow, especially as the repository grows. For high-throughput RL training, latency is the enemy.

* **Recommendation:** Use a **Virtual Filesystem (VFS)** or an overlay filesystem (like overlayfs or a Python in-memory simulation). The environment wrapper tracks the "current state" of the files in memory or a temporary directory. Snapshots are managed by the TerminalBench infrastructure. Git should be reserved for saving the *final* trajectory of a successful episode, not for the inner loop of the RL step.

### **3.3 Step 1.3: The Structural Oracle (The Map)**

The proposal uses write\_json to give the agent structure. This is a brilliant insight but risky. A synthesized netlist for a complex module can be enormous (megabytes of JSON), far exceeding the token limit of even large-context LLMs.

The Graph-Text Serializer:  
Instead of feeding the raw JSON to the agent, we must implement a Netlist Summarizer. This tool parses the Yosys JSON output and generates a condensed textual representation that highlights the architectural features without the gate-level noise.

* **Extraction:** Yosys generates hierarchy.json.  
* **Condensation:** A Python script walks the JSON tree.  
  * **Modules:** Lists inputs, outputs, and parameters.  
  * **Hierarchy:** "Module A instantiates Module B and C."  
  * **Connectivity:** "Signal req in Module A connects to valid in Module B."  
  * **State:** "Found 4 registers and 1 memory block."  
* **Presentation:** This summary is provided to the agent as part of the observation. If the agent needs more detail, it can issue an inspect\_module(name) action to get the full interface of a specific submodule. This implements a "Zoom-In" mechanic, mirroring how human engineers debug complex systems.

## ---

**4\. Phase 2: The Reward Engine (RLVR)**

The Reward Engine is the physics engine of this universe. In RLVR, "You get what you measure." A poorly designed reward function will lead to **Reward Hacking**, where agents find shortcuts that satisfy the metric without solving the problem (e.g., writing verification properties that are always true, known as "vacuity").

### **4.1 Step 2.1: The Formal Oracle (SBY)**

The proposal suggests a binary reward: \+1.0 for Pass, \-1.0 for Fail. This is mathematically sound but provides a "sparse reward" signal. In the early stages of training, the agent may fail repeatedly, receiving only \-1.0, which gives no gradient information on *how close* it was to succeeding.

The Proof-Depth Reward Manifold:  
We must introduce a dense reward signal based on Bounded Model Checking (BMC) Depth. When a proof fails or times out, the depth to which it did verify is a proxy for correctness.

* Reward Equation:

  $$R\_{formal} \= \\begin{cases} 1.0 & \\text{if Proven (Induction success)} \\\\ \\alpha \\cdot \\frac{d\_{current}}{d\_{target}} & \\text{if Timeout/Unknown (Partial Depth)} \\\\ \-1.0 & \\text{if Fails (Counter-example found)} \\end{cases}$$  
  Where $d\_{current}$ is the number of cycles the property held true before the solver timed out or found a violation, and $d\_{target}$ is the goal depth (e.g., 20 cycles). $\\alpha$ is a scaling factor (e.g., 0.5) to ensure partial success is never worth as much as full success.

Trace Narration:  
When SBY fails, it generates a VCD (Value Change Dump) trace file (engine\_0/trace.vcd). This file contains the exact sequence of events leading to the failure.

* **The Narrator:** We need a component that parses this VCD and translates it into natural language for the agent.  
  * **Action:** Parse trace.vcd.  
  * **Logic:** Identify the assertion that failed. Backtrack the "Cone of Influence" to find the input signals that triggered the failure.  
  * Output: "Assertion fifo\_full\_check failed at timestamp 45ns. The failure occurred because wr\_en was high and data\_count was 16, but full was low."  
    This feedback loop is critical for the agent's Self-Correction capability.

### **4.2 Step 2.2: The Mutation Oracle (MCY) optimization**

Running mcy (generating 10 mutants and running simulations against all of them) inside the RL loop is extremely computationally expensive. A single step could take minutes, drastically reducing the training throughput (Tokens Per Second).

The Surrogate Mutant Model:  
To optimize this, we introduce a Stochastic Surrogate Model.

1. **Offline Pre-computation:** Generate a large pool of "Hard Mutants" for standard components (FIFOs, Arbiters, ALUs) using SWE-Smith logic. These are mutants that are known to be difficult to catch.  
2. **Online Sampling:** During the RL loop, the agent's testbench is not run against *all* mutants. Instead, it is run against a random subsample (e.g., 3 mutants).  
3. **Probabilistic Reward:** If the testbench catches these 3 mutants, we infer a high probability of catching the rest.  
4. **Periodic Calibration:** Every N steps, run the full MCY suite to validate the surrogate metric and update the mutant pool. This balances the need for rigorous evaluation with the need for training speed.

## ---

**5\. Phase 3: The Adversarial Games (Arenas)**

This section defines the "Gameplay" of the environment. We must formalize the roles and the payoff matrices to ensure the game has a stable Nash Equilibrium.

### **5.1 Arena A: The Specification Game (Spec-War)**

* **Role 1: The Designer (Blue Team).** Writes RTL code to implement a feature.  
* **Role 2: The Verifier (Red Team).** Writes SystemVerilog Assertions (SVA) to constrain the design.  
* **The Game:**  
  1. Designer submits RTL.  
  2. Verifier submits SVA.  
  3. **Payoff:**  
     * Designer gains points if RTL satisfies the SVA.  
     * Verifier gains points if the SVA is *non-vacuous* and effectively constrains the state space.  
* **The Vacuity Trap:** A lazy Verifier could write assert(1) (Always True). This passes but is useless.  
* **The Vacuity Breaker:** To counter this, the environment itself acts as a third "Chaos Agent." It injects a blatant bug into the RTL (e.g., inverting an output).  
  * If the SVA *still passes* despite the blatant bug, the SVA is declared **Vacuous**.  
  * The Verifier receives a massive penalty ($-10.0$).  
  * This forces the Verifier to write tight, meaningful constraints that distinguish between correct and incorrect behavior.

### **5.2 Arena B: The Implementation Game (Bug-War)**

* **Role 1: The Coder.** Writes RTL to match a "Golden Spec."  
* **Role 2: The Hacker.** Injects a single-line mutation (e.g., changing a \+ b to a \- b, or if (x) to if (\!x)).  
* **Role 3: The Auditor.** Writes a test vector to expose the bug.  
* **The Game:**  
  * Hacker wins if the mutation changes the output (is not equivalent) BUT the Coder's existing testbench passes (Silent Corruption).  
  * Coder wins if their testbench fails (Caught Bug).  
  * This dynamic creates a strong evolutionary pressure for the Coder to write robust, high-coverage testbenches that are resilient to subtle logic errors.

## ---

**6\. Phase 4: Training with rLLM & Multi-Agent Orchestration**

The integration of rllm provides the framework for training, but the adversarial nature of VerifyGym Ultra requires specific extensions to the standard workflow.

### **6.1 The Adversarial Workflow Engine**

We must extend rllm.AgentWorkflowEngine to support **Turn-Based Markov Games**. The standard engine assumes a single agent interacting with an environment. Here, the "Environment" for Agent A includes the actions of Agent B.

**Workflow Logic:**

1. **Initialization:** The environment loads a task (e.g., "Design an SPI Controller").  
2. **Turn 1 (Generator):** The Generator Agent receives the prompt and outputs RTL.  
3. **Turn 2 (Adversary):** The Adversary Agent receives the RTL and outputs a Mutation or an Assertion.  
4. **Adjudication:** The Environment (TerminalBench) runs the tools (SBY/MCY) to determine the outcome.  
5. **Reward Distribution:** Rewards are assigned zero-sum. If the Adversary exposes a bug, Adversary gets \+1, Generator gets \-1.  
6. **Update:** Both agents update their policies using the collected trajectories.

### **6.2 Training Stability: Fictitious Self-Play (FSP)**

Naive alternating updates in adversarial RL can lead to **Cycling**, where Agent A learns to beat Agent B's current strategy, Agent B adapts to beat A, and Agent A reverts to an old strategy, creating a loop rather than general competence.

The League System:  
To prevent this, we implement Fictitious Self-Play.

* **The Pool:** We maintain a pool of past versions of all agents (checkpoints).  
* **The Matchmaking:** In each training episode, the current agent does not just play against the *current* opponent. It plays against a mixture:  
  * 80% probability: The latest opponent (to learn new strategies).  
  * 20% probability: A random past opponent (to prevent catastrophic forgetting of how to beat old strategies).  
* This ensures the agent becomes robust against the entire history of strategies, leading to a more general and powerful verification capability.

## ---

**7\. Data Logger & Strategic Tooling**

### **7.1 Dataset Alignment: The "Verified-RTL" Schema**

To maximize the impact of VerifyGym Ultra, the data generated must be reusable by the community. We align the output schema with SWE-Bench.

**JSONL Schema:**

JSON

{  
  "instance\_id": "cvdp\_001\_fifo\_sync",  
  "repo": "nvidia/cvdp",  
  "base\_commit": "sha256...",  
  "problem\_statement": "Design a synchronous FIFO with Depth=16...",  
  "patch": "module fifo...",  // The Gold Solution (RTL)  
  "test\_patch": "module tb...", // The Verification Logic (TB/SVA)  
  "verification\_metadata": {  
    "sby\_config": "fifo.sby",  
    "proof\_depth": 20,  
    "mutation\_score": 0.98,  
    "adversarial\_trace": "engine\_0/trace.vcd" // The hardest counter-example  
  }  
}

This schema allows researchers to use standard load\_dataset calls to ingest the data, facilitating the training of future Super-Verifier models.

### **7.2 Human-in-the-Loop: The Surfer Integration**

While the primary loop is automated, human insight is often required to understand *why* an agent is failing. Viewing VCD text logs is painful.

The "Surfer" Link:  
We integrate Surfer, a modern, web-based waveform viewer.

* **Mechanism:** When the Environment generates a failure trace (trace.vcd), it automatically generates a URL or a local launch command for Surfer.  
* **User Experience:** The human user clicks a link in the log, and a browser window opens rendering the waveform. They can visually inspect the signal transitions, clocks, and resets.  
* **Feedback:** This allows the human to spot "obvious" errors that the reward function might be missing (e.g., the clock never toggled) and refine the prompt or the environment setup accordingly.

## ---

**8\. Implementation Roadmap: The "Ultra" Plan**

### **Phase 1: Foundation (Weeks 1-3)**

* Build docker/Dockerfile.eda with pinned Yosys/Verilator/SBY versions.  
* Implement HardwareEnv with Structured Observation Wrappers (SOW).  
* Develop the **Graph-Text Serializer** for netlist summarization.  
* **Deliverable:** A Docker container where an agent can take a prompt, write Verilog, and see structured error logs.

### **Phase 2: Single-Player Mastery (Weeks 4-6)**

* Integrate rllm with the HardwareEnv.  
* Implement the **Proof-Depth Reward** logic.  
* Implement the **Trace Narrator** (VCD to Text).  
* Train the Generator on VerilogEval-Human.  
* **Deliverable:** An agent achieving \>50% Pass@1 on VerilogEval using RLVR.

### **Phase 3: The Arena Opens (Weeks 7-10)**

* Implement the AdversarialWorkflowEngine in rllm.  
* Develop the **Surrogate Mutant Model** to optimize MCY speed.  
* Implement the **Vacuity Breaker** logic to penalize lazy verification.  
* **Deliverable:** Operational "Spec-War" and "Bug-War" arenas.

### **Phase 4: League & Scale (Weeks 11-14)**

* Implement **Fictitious Self-Play (League)** training.  
* Scale training to the full CVDP dataset (782 problems).  
* **Deliverable:** Release of the VerifyGym-Ultra dataset and the pre-trained Agent League.

## ---

**9\. Conclusion**

VerifyGym Ultra represents the convergence of two powerful streams: the rigor of Formal Verification and the adaptability of Agentic AI. By addressing the architectural fragility of the initial proposal—specifically through the **Byte-Driven Maturity Model**, the **Proof-Depth Reward**, and the **Fictitious Self-Play** mechanism—this project transforms from a theoretical experiment into a robust platform for generating provably correct hardware. The shift from "testing" to "adversarial verification" is the key to unlocking superhuman capabilities in chip design, ensuring that the hardware of the future is as intelligent as the software running on it.

### ---

**Appendix: Tool Configuration Table**

| Tool | Version (Recommended) | Function | Configuration Note |
| :---- | :---- | :---- | :---- |
| **Yosys** | 0.39 | Synthesis & JSON Dump | Use \-p "write\_json" for structure oracle. |
| **Verilator** | v5.020+ | Simulation & Linting | Compile with \-O3 for MCY speed. |
| **SymbiYosys** | latest | Formal Driver | Default to smtbmc engine. |
| **Boolector** | 3.2.2 | SMT Solver (Hardware) | Preferred backend for SBY. |
| **Z3** | 4.12.2 | SMT Solver (General) | Fallback for complex arithmetic. |
| **Cocotb** | 1.9.0 | Python Testbench | Use for Arena A verification. |
| **Surfer** | latest (WASM) | Waveform Viewer | Web-based visualization. |

