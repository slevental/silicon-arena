# **VeriGym: Architecting an Autonomous Hardware Verification Ecosystem via R2E-Gym and Group Relative Policy Optimization**

## **1\. Executive Summary**

The semiconductor industry stands at a critical juncture where the complexity of hardware designs—measured in transistor counts approaching the trillions—far outstrips the capacity of human verification teams. The prevailing methodology, Constrained Random Verification (CRV), while effective, relies heavily on manual constraint authoring and functional coverage definition. This report proposes a paradigm shift toward **Autonomous Verification Agents** capable of self-directed exploration, rigorous reasoning, and iterative design correction.

We present a comprehensive research blueprint for **VeriGym**, a specialized fork of the **R2E-Gym** framework originally designed for software engineering agents. By adapting R2E-Gym to the Electronic Design Automation (EDA) domain, we create an environment where Large Language Model (LLM) agents can interact directly with industry-standard tools—specifically Verilator for simulation and SymbiYosys for formal verification—within a sandboxed filesystem.

The core contribution of this research is a dual-agent architecture powered by **rLLM** (Reinforcement Learning for Language Models) and optimized using **Group Relative Policy Optimization (GRPO)**. Unlike traditional Proximal Policy Optimization (PPO), GRPO eliminates the need for a value function, making it uniquely suited for the high-dimensional, token-rich environment of Verilog code generation. We define two distinct agent pairs:

1. **The Stimulus-Coverage Pair:** An agent dedicated to the "Coverage vs. Stimulus" task, learning to generate Python/Cocotb testbenches that maximize functional coverage on a RISC-V ALU.  
2. **The Architect-Verifier Pair:** An adversarial system where an "Architect" agent synthesizes RTL from natural language specifications, and a "Verifier" agent generates SystemVerilog Assertions (SVA) to mathematically prove or disprove the design's correctness.

To support "Claude Code-level" capability, we integrate a **Voyager-style Skill Library** backed by vector databases, enabling agents to persist learned verification strategies (e.g., "how to verify an overflow flag") across episodes. This report details the theoretical foundations, algorithmic specifications, loss function derivations, and concrete implementation steps required to realize this Proof of Concept (PoC).

## ---

**2\. The Verification Crisis and the Agentic Solution**

### **2.1 The Limitations of Current Methodologies**

Functional verification currently consumes nearly 70% of the hardware design cycle. The industry standard, Universal Verification Methodology (UVM), provides a structured framework for reusability but imposes a steep learning curve and high verbosity. More critically, UVM testbenches are static; they do not "learn" from their execution history in the way a human engineer does. If a random seed fails to hit a corner case today, the testbench does not inherently improve its probability of hitting it tomorrow without human intervention to modify constraints.

The "Coverage Closure" problem—the asymptotic difficulty of hitting the last 1% of unverified state space—remains the primary bottleneck. Agents trained via Reinforcement Learning (RL) offer a solution by treating coverage closure as an optimization problem. By observing the "missed bins" in a coverage report, an RL agent can adjust its stimulus generation policy to target those specific areas, effectively automating the "directed" phase of directed-random testing.

### **2.2 R2E-Gym as the Foundation**

**R2E-Gym (Repository-to-Environment Gym)** 1 represents a significant advancement in training agents for software tasks. Its core philosophy treats a code repository not as a static text corpus, but as a dynamic environment where file edits trigger execution (unit tests), and execution results (logs, errors) form the observation space. This "Repository-Level" approach is essential for hardware, where a single module (ALU.v) cannot be verified in isolation but depends on a constellation of files: Makefiles, pin constraints, testbench drivers, and simulation libraries.

However, R2E-Gym in its native state is insufficient for EDA. It lacks understanding of temporal simulation (waveforms), requires modification to support EDA toolchains (Verilator, Yosys), and its reward mechanisms are tuned for software "pass/fail" rather than the continuous "coverage percentage" metric used in hardware. The **VeriGym** fork addresses these deficits.

### **2.3 The Vision: "Claude Code" for Verification**

The user requirement envisions a system analogous to "Claude Code"—an autonomous coding assistant—but specialized for verification. This implies distinct capabilities:

* **Embodiment:** The agent must "live" in the filesystem.2 It does not just output code snippets; it creates directories, manages Makefiles, and executes shell commands.  
* **Tool Proficiency:** It must know how to invoke verilator \--cc, parse results.xml 3, and interpret VCD (Value Change Dump) waveforms.4  
* **Persistence:** It must not suffer from catastrophic forgetting. If it learns how to verify a FIFO in Episode 1, it should recall that skill in Episode 50\.

## ---

**3\. Architecture of the VeriGym Fork**

To transform R2E-Gym into VeriGym, we must re-architect the environment interface, the observation space, and the execution engine. This section details the structural changes required in the source code.

### **3.1 The RTLEnv Class Structure**

The standard RepoEnv in R2E-Gym assumes a Python/Java test runner. We introduce RTLEnv, a subclass specifically designed to wrap the EDA simulation loop.

Class Definition Strategy:  
The RTLEnv must manage the lifecycle of a simulation. Unlike a software function call which returns immediately, a hardware simulation has a setup phase (compilation), a run phase (simulation), and a teardown phase (coverage extraction).

| Component | R2E-Gym RepoEnv | VeriGym RTLEnv |
| :---- | :---- | :---- |
| **Workspace** | Git Repository | Docker Volume with EDA Tools |
| **Action Space** | Edit File, Run Pytest | Edit Verilog/Python, Run Makefile, SymbiYosys |
| **Observation** | Stdout/Stderr | Stdout, Simulation Log, Coverage XML, VCD Snippet |
| **Reward** | Binary (Pass/Fail) | Continuous (Coverage %), Binary (Syntax), Sparse (Bug Found) |
| **State** | File Contents | File Contents \+ Waveform State \+ Coverage State |

#### **3.1.1 Dockerization and Toolchain**

We leverage **TerminalBench** 2 to provide a consistent execution environment. The agent operates within a Docker container defined by a specialized Dockerfile.

**VeriGym Dockerfile Specification:**

Dockerfile

FROM ubuntu:22.04

\# Install Essentials  
RUN apt-get update && apt-get install \-y \\  
    build-essential git python3.11 python3-pip \\  
    verilator gtkwave yosys \\  
    && rm \-rf /var/lib/apt/lists/\*

\# Install Python Verification Stack  
RUN pip install cocotb cocotb-test cocotb-coverage \\  
    scipy numpy pyvcd xmltodict

\# Install SymbiYosys (Formal Verification)  
RUN git clone https://github.com/YosysHQ/SymbiYosys.git \\  
    && cd SymbiYosys && make install

\# Setup Workspace  
WORKDIR /workspace  
ENV PYTHONPATH=/workspace

This container ensures that when the agent invokes make, the underlying tools (Verilator 5.0+, Yosys) are present and correctly versioned. The cocotb-coverage library 6 is critical as it bridges the gap between Python stimulus and coverage collection.

### **3.2 Observation Space Design**

The "text-only" observation space of standard LLMs is insufficient for hardware debugging. When a simulation fails, the error is often buried in a megabyte-sized log file or, worse, visible only as a glitch in a waveform.

**Enhanced Observation Pipeline:**

1. **Log Truncation & Summarization:** The RTLEnv captures stdout from Verilator. If the log exceeds 200 lines, it uses a heuristic to extract the "Error" section (lines starting with %Error or assert failed).  
2. **Coverage Parsing:** The environment parses the coverage.xml generated by Cocotb. It extracts two key metrics:  
   * **Total Coverage %:** The scalar reward signal.  
   * **Missed Bins List:** A textual list (e.g., Cross(Op=SUB, Result=Zero) NOT HIT). This is fed back to the agent as a "Hint," guiding the CoT reasoning.  
3. **Waveform Parsing (The "Visual" Cortex):** For advanced debugging, we implement a VCD parser.4 If a test fails, the environment extracts the signal values at the timestamp of failure ($T\_{fail}$) and presents them as a state table:  
   * Time: 150ns | A: 0xFF | B: 0x01 | Op: ADD | Result: 0x00 | Overflow: 0  
   * This textual representation mimics what a human sees in GTKWave.

### **3.3 Integration with rLLM**

**rLLM** 7 provides the training loop. We utilize its AgentExecutionEngine to parallelize trajectory collection.

* **Decoupled Architecture:** rLLM separates the *Actor* (the agent generating code) from the *Environment* (VeriGym). This allows us to run 50+ Docker containers in parallel, collecting distinct trajectories for the same task.  
* **Trajectory Storage:** Each interaction is stored as (Prompt, Code\_Patch, Simulation\_Result, Reward). These trajectories form the dataset for the GRPO update step.

## ---

**4\. The Stimulus Agent: Solving "Coverage vs. Stimulus"**

The primary task for the PoC is "Coverage vs. Stimulus." The agent acts as a Verification Engineer tasked with verifying the ALU.v module.

### **4.1 The Markov Decision Process (MDP) Formulation**

To apply Reinforcement Learning, we must rigorously define the verification task as an MDP.

* **State ($S\_t$):** The current contents of the testbench file test\_alu.py, the cumulative coverage report $C\_t$, and the feedback from the last simulation run $L\_t$.  
* **Action ($A\_t$):** An edit operation on the filesystem. This can be:  
  * WriteFile(path, content): Overwriting the testbench.  
  * PatchFile(path, diff): Modifying specific constraints.  
  * RunCommand(cmd): Triggering the simulation.  
* **Transition ($T$):** The deterministic execution of the compiler and simulator.  
* **Reward ($R\_t$):** A function of the coverage gain $\\Delta C$.

### **4.2 Reward Shaping for Coverage**

Defining the reward function is the most critical step in RL. A naive "1 for 100% coverage, 0 otherwise" is too sparse.

The VeriGym Reward Function:

$$R(S\_t, A\_t) \= R\_{syntax} \+ R\_{runtime} \+ R\_{coverage} \+ R\_{efficiency}$$

1. **$R\_{syntax}$ (The Gatekeeper):**  
   * If compilation fails (Verilog syntax error or Python syntax error): $R \= \-1.0$.  
   * *Rationale:* Syntax errors provide zero information about the design. We must heavily penalize the agent for wasting a simulation cycle on un-runnable code.  
2. **$R\_{runtime}$ (The Stability Check):**  
   * If simulation hangs (timeout) or crashes (segmentation fault): $R \= \-0.5$.  
   * If simulation completes successfully: $R \= \+0.1$.  
3. **$R\_{coverage}$ (The Core Objective):**  
   * We utilize **Delta Coverage** to encourage exploration.  
   * Let $Cov\_t$ be the set of unique bins hit up to time $t$.  
   * $R\_{coverage} \= \\alpha \\times \\frac{|Cov\_t| \- |Cov\_{t-1}|}{|TotalBins|}$.  
   * Where $\\alpha$ is a scaling factor (e.g., 10.0).  
   * *Insight:* This rewards the discovery of *new* states. Retesting known states yields zero reward.  
4. **$R\_{efficiency}$ (The Constraint):**  
   * $R\_{efficiency} \= \-\\lambda \\times \\text{SimulationTime}$.  
   * This penalizes inefficient testbenches that run for millions of cycles to hit a bin that could be hit in ten cycles with better constraints.

### **4.3 The Agent's Policy: Constrained Random Generation**

The agent learns to use the cocotb.crv (Constrained Random Verification) library.9 The policy $\\pi\_\\theta$ maps the observation of "Missed Bins" to Python code constraints.

**Example Trajectory:**

1. **Obs:** Missed: ALU\_Overflow.  
2. **Internal Thought (CoT):** "Overflow occurs when adding two large positive numbers yields a negative result. I need to constrain A and B to be large positive integers."  
3. **Action (Code Generation):**  
   Python  
   class ALUOp(Randomized):  
       def \_\_init\_\_(self):  
           self.a \= 0  
           self.b \= 0  
           self.op \= 0  
           \# Constraint for Positive Overflow  
           self.add\_constraint(lambda a, b: a \> 0x70000000 and b \> 0x70000000)

4. **Outcome:** The simulation hits the bin. $R\_{coverage}$ is positive. The policy is reinforced.

## ---

**5\. Algorithmic Core: GRPO and Loss Functions**

The user request specifically asks for "very specific algorithms and loss function suggestions." We select **Group Relative Policy Optimization (GRPO)** 10 as the engine for VeriGym.

### **5.1 Why GRPO over PPO?**

Standard PPO (Proximal Policy Optimization) utilizes an Actor-Critic architecture. The Critic (Value Function $V(s)$) estimates the expected future reward.

* **The Problem:** In code generation, the state space (source code) is discrete and high-dimensional. Two testbenches differing by a single semicolon can have vastly different values (Syntax Error vs. 100% Coverage). Learning a smooth Value Function on this landscape is notoriously difficult and computationally expensive.  
* **The GRPO Solution:** GRPO eliminates the Critic. Instead of comparing the reward to a learned baseline $V(s)$, it compares the reward to the **average reward of a group of parallel samples**.

### **5.2 Mathematical Derivation of the GRPO Loss**

Let the verification query be $q$ (e.g., "Write a test for ALU").  
The policy $\\pi\_{\\theta\_{old}}$ generates a group of $G$ outputs $\\{o\_1, o\_2,..., o\_G\\}$.  
We execute all $G$ outputs in the VeriGym environment, obtaining rewards $\\{r\_1, r\_2,..., r\_G\\}$.  
Step 1: Compute Advantages  
The advantage $\\hat{A}\_i$ for the $i$-th output is calculated relative to the group statistics:

$$\\hat{A}\_i \= \\frac{r\_i \- \\text{mean}(\\mathbf{r})}{\\text{std}(\\mathbf{r}) \+ \\epsilon}$$

This effectively normalizes the rewards. If the group average was 50% coverage, and $o\_1$ achieved 80%, its advantage is positive. If $o\_2$ achieved 20%, its advantage is negative.  
Step 2: The Surrogate Objective  
We optimize the policy $\\pi\_\\theta$ to maximize the advantage of the generated tokens, subject to a KL divergence constraint to prevent the model from drifting too far from the base language model (which ensures code readability).  
The objective function $J\_{GRPO}(\\theta)$ is:

$$J(\\theta) \= \\mathbb{E}\_{q \\sim P(Q), \\{o\_i\\} \\sim \\pi\_{\\theta\_{old}}} \\left$$  
Where the clipped loss $\\mathcal{L}^{clip}\_i$ is derived from PPO:

$$\\mathcal{L}^{clip}\_i \= \\frac{1}{|o\_i|} \\sum\_{t=1}^{|o\_i|} \\min \\left( \\frac{\\pi\_\\theta(o\_{i,t}|...)}{\\pi\_{\\theta\_{old}}(o\_{i,t}|...)} \\hat{A}\_i, \\text{clip}\\left(\\frac{\\pi\_\\theta}{\\pi\_{\\theta\_{old}}}, 1-\\epsilon, 1+\\epsilon\\right) \\hat{A}\_i \\right)$$

### **5.3 Implementation in rLLM**

To implement this in the R2E-Gym fork, we modify the AgentTrainer module of rLLM.

Python

\# Pseudocode for GRPO Loss Implementation  
def grpo\_loss(batch, policy\_model, ref\_model, beta=0.01):  
    prompts \= batch\['prompts'\]  
    outputs \= batch\['outputs'\] \# Group of G outputs per prompt  
    rewards \= batch\['rewards'\] \# Computed from VeriGym  
      
    \# 1\. Compute Group Stats  
    mean\_rewards \= rewards.mean(dim=1, keepdim=True)  
    std\_rewards \= rewards.std(dim=1, keepdim=True)  
    advantages \= (rewards \- mean\_rewards) / (std\_rewards \+ 1e-6)  
      
    \# 2\. Forward Pass (Log Probabilities)  
    log\_probs \= policy\_model(prompts, outputs)  
    old\_log\_probs \= batch\['old\_log\_probs'\]  
      
    \# 3\. Ratio and Clipping  
    ratios \= torch.exp(log\_probs \- old\_log\_probs)  
    surr1 \= ratios \* advantages  
    surr2 \= torch.clamp(ratios, 1\-epsilon, 1\+epsilon) \* advantages  
      
    \# 4\. KL Penalty (Token-level)  
    ref\_log\_probs \= ref\_model(prompts, outputs)  
    kl\_div \= torch.exp(ref\_log\_probs \- log\_probs) \- (ref\_log\_probs \- log\_probs) \- 1  
      
    loss \= \-torch.min(surr1, surr2) \+ beta \* kl\_div  
    return loss.mean()

**Insight:** The KL term is crucial for verification. Without it, the agent learns to "game" the simulator by finding weird syntax that technically passes but is unmaintainable. The $\\pi\_{ref}$ (usually the base DeepSeek-Coder or Llama-3 model) anchors the agent to human-readable coding styles.

## ---

**6\. The Architect and The Verifier: Spec-to-RTL Agent Pair**

The user explicitly requests a second pair of agents: one to write RTL from specs, and another to verify it. This creates a "Self-Play" dynamic analogous to GANs (Generative Adversarial Networks), but in the domain of logic design.

### **6.1 Agent A: The Architect (Spec-to-RTL)**

Role: Synthesize Verilog code from ALU\_spec.md.  
Input: Natural language specification (e.g., "Implement a 32-bit ALU with opcode 0x1 for ADD").  
Output: ALU.v.  
Chain-of-Thought (CoT) Prompting Strategy:  
The Architect is prompted to plan before coding:

1. **Interface Definition:** List inputs (A, B, Op) and outputs (Result, Zero, Overflow).  
2. **Opcode Mapping:** Create a parameter list parameter ADD \= 4'b0000;.  
3. **Datapath Design:** Define the arithmetic logic.  
4. **Control Logic:** Define the case statement.  
5. **Status Flags:** Logic for Zero (result \== 0\) and Overflow.

### **6.2 Agent B: The Verifier (The Formal Critic)**

Role: Prove the Architect's design is correct using Formal Verification.  
Tool: SymbiYosys.12  
Unlike the Stimulus Agent which uses dynamic simulation, the Verifier Agent generates **SystemVerilog Assertions (SVA)**. Formal verification provides a mathematical guarantee of correctness, which is rigorous validation for the Architect.

**The Verifier's Workflow:**

1. **Read Spec:** Identify invariants. "The Zero flag must be high IF AND ONLY IF the result is 0."  
2. **Generate SVA:**  
   Code snippet  
   // Agent Generated Property  
   property zero\_flag\_check;  
       @(posedge clk) (result \== 0\) \<-\> zero;  
   endproperty  
   assert property (zero\_flag\_check);

3. **Run SymbiYosys:** The agent creates a .sby file and runs it.  
4. **Parse Trace:** If the proof fails, SymbiYosys generates a counter-example trace.

### **6.3 The Adversarial Feedback Loop**

The interaction between Architect and Verifier forms a powerful learning loop:

1. **Round 1:** Architect writes ALU.v.  
2. **Round 1:** Verifier writes ALU.sby and finds a bug (e.g., Overflow logic is wrong for signed numbers).  
3. **Feedback:** The Verifier passes the *Counter-Example Trace* back to the Architect.  
   * *Trace:* "At t=10, A=MAX, B=1, Op=ADD, Overflow=0 (Expected 1)."  
4. **Round 2:** Architect analyzes the trace, reasons about signed arithmetic, and fixes the Verilog.  
5. **Round 2:** Verifier re-runs the proof. Result: PASS.

This loop is implemented within the VeriGym environment by managing the message passing between the two agents.

## ---

**7\. Persistent Knowledge: The Voyager-Style Skill Library**

To achieve "Claude Code" capabilities, the agent must learn skills that persist beyond a single episode. We implement a mechanism inspired by **Voyager** 14, which used GPT-4 to curate a library of Minecraft skills.

### **7.1 Architecture of the Skill Library**

The Skill Library is a persistent database residing on the filesystem (and indexed in a vector DB).

**Schema:**

* **Skill Name:** verify\_overflow\_signed  
* **Description:** "Cocotb coroutine to verify signed overflow for 32-bit addition."  
* **Code:** The Python function source.  
* **Embedding:** A vector representation of the description (using sentence-transformers).  
* **Success Rate:** Metadata tracking how often this skill effectively found bugs.

### **7.2 The Learning Process**

1. **Discovery:** In Episode N, the agent successfully writes a complex constraint to verify the ALU Overflow. The Reward is high.  
2. **Curation:** The environment triggers a "Curator Agent" (an LLM call).  
   * *Prompt:* "Extract the reusable logic from this successful testbench and wrap it in a generic Python function."  
3. **Indexing:** The resulting function check\_overflow(a, b, result) is saved to skills/math\_checks.py and indexed in the Vector DB (e.g., ChromaDB).

### **7.3 Skill Retrieval**

In Episode N+1, the agent is tasked with verifying a Multiplier.

1. **Query:** The agent "thinks": "I need to check for overflow in multiplication."  
2. **Search:** It queries the Skill Library with "overflow check".  
3. **Retrieval:** The system returns the check\_overflow function learned from the ALU task.  
4. **Reuse:** The agent imports this function instead of rewriting it from scratch, significantly accelerating the verification process.

## ---

**8\. Proof of Concept: RISC-V ALU Implementation**

This section provides the concrete implementation details for the "Simple PoC" requested.

### **8.1 The Target RTL (Inferred Spec)**

Based on the standard RV32I ISA 16, the ALU spec is defined as follows:

| Opcode | Operation | Description |
| :---- | :---- | :---- |
| 0000 | ADD | A \+ B |
| 1000 | SUB | A \- B |
| 0010 | SLT | Set Less Than (Signed) |
| 0011 | SLTU | Set Less Than (Unsigned) |
| 0100 | XOR | Bitwise XOR |
| 0110 | OR | Bitwise OR |
| 0111 | AND | Bitwise AND |
| 0001 | SLL | Shift Left Logical |
| 0101 | SRL | Shift Right Logical |
| 1101 | SRA | Shift Right Arithmetic |

**Outputs:**

* result \[31:0\]: Computation output.  
* zero: Asserted if result is 0\.  
* overflow: Asserted if signed add/sub overflows.

### **8.2 The Filesystem Layout**

The VeriGym environment initializes the workspace with this structure:  
/workspace  
├── rtl/  
│ └── ALU.v \# (Initially empty for Architect, or populated for Stimulus)  
├── tb/  
│ ├── test\_alu.py \# (Agent writes this)  
│ └── Makefile \# (Pre-configured for Verilator)  
├── specs/  
│ └── ALU\_spec.md \# (Read-only input)  
├── skills/ \# (Voyager Library)  
└── logs/ \# (Simulation artifacts)

### **8.3 The Makefile Harness**

To enable the agent to "run simulators," we provide a robust Makefile wrapper around Cocotb and Verilator.

Makefile

\# Makefile  
SIM?= verilator  
TOPLEVEL\_LANG?= verilog

VERILOG\_SOURCES \+= $(PWD)/../rtl/ALU.v  
TOPLEVEL \= ALU  
MODULE \= test\_alu

\# Enable Coverage  
EXTRA\_ARGS \+= \--coverage \--trace  
COMPILE\_ARGS \+= \-Wno-fatal

include $(shell cocotb-config \--makefiles)/Makefile.sim

The agent simply runs os.system("make"). The environment handles the complexity of invoking the simulator.

### **8.4 Implementation of the Agent Loop (Python)**

The following Python snippet demonstrates the core loop of the Stimulus Agent.

Python

def agent\_loop(env, agent\_model):  
    obs \= env.reset()  
    done \= False  
      
    while not done:  
        \# 1\. Perception  
        coverage\_report \= obs\['coverage'\]  
        last\_error \= obs\['error\_log'\]  
          
        \# 2\. Reasoning (Context Management)  
        \# We construct a prompt including the feedback  
        prompt \= f"""  
        Task: Verify ALU.v  
        Current Coverage: {coverage\_report\['total'\]}%  
        Missed Bins: {coverage\_report\['missed\_bins'\]\[:5\]}  
        Last Error: {last\_error}  
          
        Write a Cocotb test to target the missed bins.  
        """  
          
        \# 3\. Action Generation (GRPO Policy)  
        \# The model generates code tokens  
        code\_action \= agent\_model.generate(prompt)  
          
        \# 4\. Execution  
        obs, reward, done, info \= env.step({  
            'type': 'edit\_and\_run',  
            'file': 'tb/test\_alu.py',  
            'content': code\_action  
        })  
          
        \# 5\. Learning happens asynchronously via rLLM trainer

## ---

**9\. Conclusion and Future Directions**

The **VeriGym** framework represents a robust architecture for bringing autonomous agents into the hardware verification loop. By forking R2E-Gym and specializing it with EDA toolchains, we bridge the gap between software-centric LLM research and the rigorous demands of silicon design.

The integration of **GRPO** addresses the fundamental challenge of training on non-differentiable objectives (code coverage) without the computational overhead of a critic network. The **Architect-Verifier** agent pair introduces a self-correcting dynamic that mimics human engineering teams, while the **Voyager-style Skill Library** ensures that the agents accumulate wisdom over time, evolving from novice coders to expert verification engineers.

**Immediate Next Steps for the PoC:**

1. **Base Image Build:** Create the Docker image containing Verilator 5.0 and Cocotb.  
2. **Environment Wrapper:** Implement RTLEnv inheriting from R2E-Gym's RepoEnv.  
3. **Training Run:** Execute a 500-episode training run on the RISC-V ALU task using the GRPO loss function defined in Section 5.3.

This research blueprint provides all the necessary algorithmic and architectural details to build the "Claude Code for Verification," potentially reducing verification costs by orders of magnitude through automation.

### ---

**Key Research Snippet References**

* **R2E-Gym & SWE Agents:** 1  
* **rLLM & GRPO:** 7  
* **TerminalBench & Docker:** 2  
* **Voyager & Skills:** 14  
* **Formal Verification (SymbiYosys):** 12  
* **Cocotb & Coverage:** 6  
* **RISC-V ALU Spec:** 16

#### **Works cited**

1. R2E-Gym/R2E-Gym: \[COLM 2025\] Official repository for ... \- GitHub, accessed January 11, 2026, [https://github.com/R2E-Gym/R2E-Gym](https://github.com/R2E-Gym/R2E-Gym)  
2. Introduction \- Terminal-Bench, accessed January 11, 2026, [https://www.tbench.ai/docs](https://www.tbench.ai/docs)  
3. cocotb\_tools.check\_results — cocotb 2.1.0.dev0+5c8f43a documentation, accessed January 11, 2026, [https://docs.cocotb.org/en/development/\_modules/cocotb\_tools/check\_results.html](https://docs.cocotb.org/en/development/_modules/cocotb_tools/check_results.html)  
4. vcd\_parser.py, accessed January 11, 2026, [https://cs.colby.edu/courses/F20/cs232-labs/vcd\_parser.py](https://cs.colby.edu/courses/F20/cs232-labs/vcd_parser.py)  
5. Terminal-Bench 2.0 | EvalScope \- Read the Docs, accessed January 11, 2026, [https://evalscope.readthedocs.io/en/latest/third\_party/terminal\_bench.html](https://evalscope.readthedocs.io/en/latest/third_party/terminal_bench.html)  
6. cocotb-coverage/documentation/source/introduction.rst at master \- GitHub, accessed January 11, 2026, [https://github.com/mciepluc/cocotb-coverage/blob/master/documentation/source/introduction.rst](https://github.com/mciepluc/cocotb-coverage/blob/master/documentation/source/introduction.rst)  
7. rllm-org/rllm: Democratizing Reinforcement Learning for LLMs \- GitHub, accessed January 11, 2026, [https://github.com/rllm-org/rllm](https://github.com/rllm-org/rllm)  
8. rLLM, accessed January 11, 2026, [https://rllm-project.readthedocs.io/](https://rllm-project.readthedocs.io/)  
9. cocotb-coverage \- PyPI, accessed January 11, 2026, [https://pypi.org/project/cocotb-coverage/](https://pypi.org/project/cocotb-coverage/)  
10. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models \- GitHub, accessed January 11, 2026, [https://github.com/deepseek-ai/DeepSeek-Math](https://github.com/deepseek-ai/DeepSeek-Math)  
11. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models \- arXiv, accessed January 11, 2026, [https://arxiv.org/html/2402.03300v3](https://arxiv.org/html/2402.03300v3)  
12. RISC-V Formal Verification Framework Extension for Synopsys VC Formal \- YosysHQ Blog, accessed January 11, 2026, [https://blog.yosyshq.com/p/risc-v-formal-verification-framework-extension-for-synopsys-vc-formal/](https://blog.yosyshq.com/p/risc-v-formal-verification-framework-extension-for-synopsys-vc-formal/)  
13. SymbiYosys \- Read the Docs, accessed January 11, 2026, [https://symbiyosys.readthedocs.io/](https://symbiyosys.readthedocs.io/)  
14. Voyager: An Open-Ended Embodied Agent with Large Language Models \- OpenReview, accessed January 11, 2026, [https://openreview.net/forum?id=ehfRiF0R3a](https://openreview.net/forum?id=ehfRiF0R3a)  
15. MineDojo/Voyager: An Open-Ended Embodied Agent with Large Language Models \- GitHub, accessed January 11, 2026, [https://github.com/MineDojo/Voyager](https://github.com/MineDojo/Voyager)  
16. DESIGN AND SIMULATE RISC-V PROCESOR USING VERILOG DAVID NGU TECK JOUNG MASTER OF ENGINEERING IN ELECTRONIC SYSTEMS FACULTY OF EN, accessed January 11, 2026, [http://eprints.utar.edu.my/5966/1/David\_Ngu\_Teck\_Joung\_21AGM06719.pdf](http://eprints.utar.edu.my/5966/1/David_Ngu_Teck_Joung_21AGM06719.pdf)  
17. Design and Implementation of RISC-V Processor ALU using Multiplexers and LUT. \- IJNRD, accessed January 11, 2026, [https://www.ijnrd.org/papers/IJNRD2309039.pdf](https://www.ijnrd.org/papers/IJNRD2309039.pdf)  
18. R2E-Gym \- GitHub, accessed January 11, 2026, [https://github.com/R2E-Gym](https://github.com/R2E-Gym)  
19. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models \- arXiv, accessed January 11, 2026, [https://arxiv.org/pdf/2402.03300](https://arxiv.org/pdf/2402.03300)  
20. laude-institute/terminal-bench: A benchmark for LLMs on complicated tasks in the terminal \- GitHub, accessed January 11, 2026, [https://github.com/laude-institute/terminal-bench](https://github.com/laude-institute/terminal-bench)  
21. Voyager | An Open-Ended Embodied Agent with Large Language Models, accessed January 11, 2026, [https://voyager.minedojo.org/](https://voyager.minedojo.org/)  
22. Reference Documentation — cocotb\_coverage 1.0 documentation \- cocotb-coverage, accessed January 11, 2026, [https://cocotb-coverage.readthedocs.io/en/latest/reference.html](https://cocotb-coverage.readthedocs.io/en/latest/reference.html)