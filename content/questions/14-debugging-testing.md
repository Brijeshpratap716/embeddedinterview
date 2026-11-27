---
slug: debugging-testing
title: Debugging, Testing & Tools
icon: 🐞
level: Intermediate
order: 16
desc: Debugging intermittent bugs, HardFault analysis, JTAG/SWD, GDB, breakpoints and watchpoints, printf vs trace (ITM/SWO/RTT), memory corruption, unit testing and mocking, HIL and CI, coverage, static analysis, build systems, map files, code size and git bisect.
---
Interviewers often finish with "tell me about the hardest bug you fixed". These questions give you the vocabulary and the toolbox to answer well. Each answer gives the short version first, then the details and follow-ups.

### How do you debug firmware that crashes only occasionally? {M}
Intermittent crashes require preserving evidence rather than repeatedly restarting the target.

#### Workflow
1. Record firmware build, board revision, workload, temperature and reset cause.
2. Capture timestamped events in a bounded RAM ring buffer or persistent crash record.
3. On failure save PC, LR, SP, fault registers, task identity and relevant peripheral state.
4. Resolve addresses against the exact ELF; examine the failing instruction and call stack.
5. Stress the suspected race, stack boundary, DMA transfer or power condition independently.

Use hardware watchpoints for corrupted addresses and trace when halting affects timing. Enable assertions, stack guards and host-side sanitizers where possible.

**Interview takeaway:** Distinguish the instruction that crashes from the earlier operation that caused corruption. Preserve reproducible evidence.

### How do you analyse a HardFault on a Cortex-M? {H}
On Cortex-M, HardFault indicates a fault that is directly routed or escalated to the HardFault handler. On cores that implement configurable faults, inspect their status registers to identify the original exception.

#### 1. Capture the exception frame
```text
Stacked frame: R0 R1 R2 R3 R12 LR PC xPSR
                   ^
      MSP or PSP selected by EXC_RETURN
```

Capture EXC_RETURN before a compiler prologue changes context. Account for extended floating-point frames and stack alignment where applicable.

#### 2. Decode the cause
Read HFSR and CFSR on supporting cores. MMFAR and BFAR are meaningful only if their corresponding valid bits are set. FORCED in HFSR indicates escalation. A precise bus fault may identify the exact instruction; an imprecise fault may not.

#### 3. Debug
```bash
arm-none-eabi-addr2line -e firmware.elf -f -C 0x08001234
arm-none-eabi-objdump -d firmware.elf
```
Replace the address with the captured PC. Validate stack memory before dereferencing it.

**Interview takeaway:** A fault during exception stacking may invalidate the saved frame. Capture the evidence and use a controlled recovery policy rather than blindly returning.

### What is the difference between JTAG and SWD, and what can a debug probe do? {E}
JTAG and SWD are hardware debug transports. A debug probe bridges the host debugger to the target's debug access infrastructure.

| JTAG | SWD |
|---|---|
| TCK, TMS, TDI, TDO (+ optional reset) | SWCLK and bidirectional SWDIO |
| Can support multiple TAPs and boundary scan | Compact Arm debug connection |
| More pins | Fewer pins |

Both can support halting, stepping, register/memory access and flash programming when the target and probe support them. SWO is an optional trace output, not required for SWD.

**Interview takeaway:** Debug access may be locked by security configuration or power domains. Do not confuse JTAG boundary scan with CPU instruction debugging.

### What is the difference between a breakpoint and a watchpoint? {E}
A breakpoint stops execution at an instruction address. A watchpoint stops on access to a selected data address.

```text
(gdb) break process_packet
(gdb) watch state
(gdb) awatch *0x20001000
```

Hardware breakpoints compare instruction addresses; software breakpoints replace instructions with a trap where permitted. Hardware watchpoints use limited data-address comparators and may have alignment/size restrictions.

#### Example
When a variable is corrupted unexpectedly, watch its address rather than breaking wherever it is read. The debugger can identify the CPU instruction responsible.

**Interview takeaway:** CPU watchpoints do not necessarily detect writes from DMA or other bus masters. Check hardware support and comparator limits.

### What are the essential GDB commands for embedded debugging? {E}
GDB lets you inspect a halted target using symbols from the matching ELF file.

```gdb
target remote localhost:3333
monitor reset halt
break main
continue
next
step
finish
bt
info registers
print variable
x/16wx 0x20000000
disassemble /m main
watch variable
```

The remote server and monitor commands depend on the probe/server implementation. Use backtrace, registers and disassembly together when optimized code makes source-level stepping confusing.

**Interview takeaway:** Compile with debug information and keep the exact ELF for every deployed firmware build. Symbols do not require disabling all optimization.

### Why can printf debugging change program behaviour? {M}
Printf debugging can change the behavior of timing-sensitive firmware. Formatting, locking, buffering and UART transmission consume CPU time and may change scheduling or interrupt timing.

#### Example
At 115200 baud with 8N1 framing, transmitting 100 bytes takes approximately 8.7 ms on the wire. A blocking logging call can delay a task with a 1 ms deadline.

#### Alternatives
Use a bounded non-blocking ring buffer, hardware trace, GPIO timing pulses or deferred logging. Avoid heavy formatting in ISRs and record dropped-message counts.

**Interview takeaway:** A bug that disappears after adding logging is not necessarily fixed. The instrumentation may have changed the race or timing.

### What are ITM, SWO, ETM and RTT, and when do you use trace? {M}
Trace provides observability without stopping the CPU, subject to bandwidth and hardware limits.

| Mechanism | Purpose |
|---|---|
| ITM | Software instrumentation and supported hardware events |
| SWO | Serial trace output path, where available |
| ETM | Hardware instruction trace on supported cores |
| RTT | RAM-buffer communication read through a debug probe |

#### Selection
Use ITM/SWO or RTT for low-overhead events and timestamps. Use ETM when the execution history before a fault is required and suitable trace capture is available.

**Interview takeaway:** Trace is not infinitely fast. Check buffer overflow, timestamp accuracy, target support and whether the implementation can block.

### How do you find memory corruption and stack overflows in firmware? {M}
Memory corruption occurs when code writes outside an object's valid storage, uses freed memory or exceeds a stack boundary.

#### Investigation
- Enable compiler warnings, AddressSanitizer and UndefinedBehaviorSanitizer in host tests.
- Add canaries, guard regions or MPU stack protection where supported.
- Fill unused stack with a known pattern and measure the high-water mark.
- Set a hardware watchpoint on a damaged location.
- Verify DMA buffer size, ownership, alignment and cache maintenance.

#### Example
A task with a 512-byte stack declares a 600-byte local buffer. Increase or redesign the stack only after inspecting the actual call chain and worst-case nesting.

**Interview takeaway:** Stack watermarking estimates observed usage, not a mathematical worst-case guarantee. Test interrupt nesting and fault paths as well.

### How do you unit test embedded C code? {M}
Unit testing verifies small software components in isolation with repeatable inputs and expected outputs.

#### Separate logic from hardware
```c
bool temperature_alarm(int value, int limit)
{
    return value >= limit;
}
```
Test below, at and above the threshold on the host. For hardware-dependent code, inject an interface and replace register/bus operations with fakes or mocks.

#### Workflow
Use frameworks such as Unity/Ceedling or a project-specific test harness. Check success, errors, boundaries, timeouts and state transitions. Run with sanitizers on the host and add target tests for real hardware behavior.

**Interview takeaway:** Unit tests do not prove electrical timing or register side effects; complement them with integration and hardware tests.

### What is hardware-in-the-loop (HIL) testing, and how do you set up CI for firmware? {M}
Hardware-in-the-loop testing runs production or representative firmware on physical hardware while a test system supplies controlled inputs and checks outputs.

```text
CI runner -> flash DUT -> stimulus generator
                |            |
                +-> UART / GPIO / bus capture -> assertions
```

#### Pipeline
1. Build and run host unit tests.
2. Reserve a board and flash the artifact.
3. Reset/power-cycle through a fixture.
4. Inject protocol traffic, timing events or sensor stimuli.
5. Assert response, latency and recovery; upload logs and waveforms.

Provide timeouts, fixture health checks and exclusive board ownership. Separate flaky infrastructure from product defects.

**Interview takeaway:** HIL verifies real integration and timing; keep tests repeatable and retain the exact binary and board revision.

### What is code coverage, and what coverage levels do safety standards require? {M}
Code coverage measures what parts of a program were exercised by tests, not whether the tests were correct.

| Metric | Measures |
|---|---|
| Statement | Executed statements |
| Branch/decision | Outcomes of decisions |
| Condition | Individual Boolean conditions |
| MC/DC | Each condition's independent effect on a decision |

#### Safety context
Requirements depend on the applicable standard, edition, assurance/integrity level and approved verification plan. For example, DO-178C uses structural coverage objectives of statement for Level C, decision for Level B and MC/DC for Level A. ISO 26262 has its own methods and ASIL-dependent recommendations.

**Interview takeaway:** Coverage is evidence of test completeness relative to code structure, not proof of correctness. Investigate uncovered code and trace tests to requirements.

### What is static analysis and which tools are used? {E}
**Short answer:** Static analysis examines source code without running it to find bugs and rule violations: NULL dereferences, buffer overruns, uninitialised variables, integer overflow, resource leaks, dead code, concurrency issues and violations of coding standards such as MISRA C. It runs in CI on every change and catches issues that tests miss because they occur only on rare paths.

| Tool | Type |
|---|---|
| Compiler warnings (`-Wall -Wextra -Wshadow -Wconversion -Wcast-align -Werror`), GCC `-fanalyzer` | free, first line of defence |
| clang-tidy, Clang Static Analyzer (`scan-build`) | free, deep path analysis |
| cppcheck | free, low false positives, MISRA addon |
| Coverity, Klocwork, Polyspace, PC-lint Plus, Parasoft C/C++test, Helix QAC | commercial, MISRA/CERT checking, certification support |
| CodeQL, SonarQube | queries, dashboards |
| Polyspace Code Prover, Frama-C, Astrée | abstract interpretation: prove absence of some run-time errors |
| Stack analysis (`-fstack-usage`, puncover), WCET tools (aiT) | resource bounds |

**Coding standards:** MISRA C:2012/2023 (automotive, industrial; rules with mandatory/required/advisory categories and a deviation process), CERT C (security), AUTOSAR C++14 / MISRA C++:2023, and the Barr Group Embedded C Coding Standard.

**Making it work in practice:** start with compiler warnings as errors; add one analyser to CI; fix or explicitly suppress (with a justification) each finding so the baseline stays clean; run analysis on new code first for legacy codebases.

**Dynamic analysis complements it:** sanitizers (ASan, UBSan, TSan) and Valgrind on host builds, fuzzing (libFuzzer, AFL++) for parsers and protocol handlers.

### What is the difference between Make and CMake? {E}
**Short answer:** **Make** is a build tool that executes rules from a Makefile: targets, their dependencies and the commands to build them, rebuilding only what changed. **CMake** is a build-system **generator**: you describe targets, sources, include paths and options in `CMakeLists.txt`, and CMake generates Makefiles or Ninja files (or IDE projects) for the chosen toolchain. CMake handles cross-platform details, dependencies and configuration better, so most modern embedded projects (Zephyr, Pico SDK, ESP-IDF, STM32 CMake projects) use it, often with Ninja for speed.

**Minimal cross-compilation setup**

```cmake
# arm-gcc-toolchain.cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(blinky C ASM)
add_executable(blinky.elf src/main.c src/startup_stm32f4.s)
target_compile_options(blinky.elf PRIVATE -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16
                       -Os -ffunction-sections -fdata-sections -Wall -Wextra)
target_link_options(blinky.elf PRIVATE -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16
                    -T${CMAKE_SOURCE_DIR}/stm32f4.ld -Wl,--gc-sections -Wl,-Map=blinky.map --specs=nano.specs)
add_custom_command(TARGET blinky.elf POST_BUILD
                   COMMAND arm-none-eabi-objcopy -O binary blinky.elf blinky.bin
                   COMMAND arm-none-eabi-size blinky.elf)
```

```sh
cmake -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=arm-gcc-toolchain.cmake
cmake --build build
```

**Make basics interviewers ask:** targets, prerequisites, recipes (tab-indented), automatic variables (`$@` target, `$<` first prerequisite, `$^` all prerequisites), pattern rules (`%.o: %.c`), `.PHONY`, and dependency generation with `-MMD -MP` so header changes trigger rebuilds.

**Other build systems:** Meson, Bazel, SCons; Kbuild/Kconfig for the Linux kernel; Yocto/BitBake and Buildroot for whole Linux distributions; vendor IDE projects (convertible to CMake for CI).

### What does a map file tell you? {M}
**Short answer:** The linker map file (`-Wl,-Map=app.map`) shows where everything ended up in memory: the memory regions and how full they are, the address and size of every section (`.text`, `.rodata`, `.data`, `.bss`, stacks, heap), which object files and library members contributed to each section, the address of every symbol, which sections were discarded by `--gc-sections`, and why library objects were pulled in. It is the primary tool for understanding and reducing flash and RAM usage and for mapping crash addresses to functions.

**What to look for**

| Question | Where in the map |
|---|---|
| How much flash/RAM is used? | memory configuration and the end addresses of sections (or `arm-none-eabi-size`) |
| What is using all the flash? | sizes per input section/object under `.text` and `.rodata` |
| Why is `printf`/float code present? | "archive member included to satisfy reference by file (symbol)" lines at the top |
| Where is a variable or function? | symbol addresses (for watchpoints, crash analysis) |
| Is a buffer in the right RAM (DTCM, non-cacheable, backup SRAM)? | output section placement |
| Initialised data cost | `.data` takes space in **both** flash (initial values) and RAM |

**Helpful tools:** `arm-none-eabi-nm --size-sort -S -C app.elf | tail -30` (largest symbols), `bloaty`, puncover (per-function code and stack size in a web view), Amap / MapViewer GUIs, and `size -A` for per-section totals.

**Interview example:** "Flash grew by 20 KB after a small change; the map file showed `_dtoa_r` and floating-point emulation pulled in by a `%f` in one debug message. Removing it (or using a fixed-point print) recovered the space."

### How do you reduce firmware code size? {M}
**Short answer:** Measure first (map file, `nm --size-sort`, bloaty), then: compile with `-Os` (or `-Oz` with Clang), enable `-ffunction-sections -fdata-sections` with `-Wl,--gc-sections` so unused functions are removed, use link-time optimisation (`-flto`), use newlib-nano (`--specs=nano.specs`) and avoid heavy library functions (`printf` with floats, `sscanf`, `iostream`), remove unused vendor HAL code or switch to LL/register-level drivers, move constant tables to compact formats, and avoid code duplication from macros and templates.

**Techniques ranked by typical impact**

| Technique | Typical saving |
|---|---|
| Remove floating-point `printf`/`scanf`, use integer formatting | 10–20+ KB |
| `--gc-sections` with function/data sections | large if libraries are linked whole |
| `-Os` vs `-O2` | 10–30% of code |
| LTO | 5–15% (cross-module inlining, dead code removal) |
| newlib-nano | several KB |
| Replace vendor HAL with LL drivers | often 10–30 KB in HAL-heavy projects |
| Thumb-2 (default on Cortex-M) vs ARM state on Cortex-A/R | ~25–30% |
| Compress assets (fonts, images), store tables as `const` | depends |
| Avoid inline expansion of large macros/inline functions in many places | depends |
| Logging with IDs instead of strings (deferred logging) | string data |

**Be careful:** size optimisation can make code slower (`-Os` disables some loop unrolling) — keep hot paths fast with function attributes (`__attribute__((optimize("O2")))` sparingly) or by placing them in RAM; aggressive optimisation can expose latent undefined behaviour, so run the full test suite on the optimised build.

**RAM reduction:** check `.bss` and `.data` in the map file, size stacks from measured high-water marks, shrink buffers to measured needs, use `const` so tables stay in flash, and share buffers between features that never run at the same time (unions or overlays, carefully).

### What is git bisect and how does it help? {E}
**Short answer:** `git bisect` performs a binary search through the commit history to find the commit that introduced a bug. You mark a known-good and a known-bad commit; git checks out the commit halfway between; you test it and mark it good or bad; git repeats until it identifies the first bad commit. 1,000 commits take only about 10 steps. With a test script that returns 0 (good) or non-zero (bad), `git bisect run` automates the whole search, even including flashing and testing on hardware.

```sh
git bisect start
git bisect bad                 # current HEAD has the bug
git bisect good v2.3.0         # this release was fine
# build, flash, test... then:
git bisect good                # or: git bisect bad, or: git bisect skip (doesn't build)
# ...repeat until git prints "<sha> is the first bad commit"
git bisect reset               # return to where you started

# automated, e.g. with a HIL test script
git bisect run ./ci/flash_and_test.sh
```

**Tips:** small, focused commits make the result meaningful; every commit should build (otherwise use `git bisect skip`); for intermittent bugs, make the test repeat enough times to be confident a "good" verdict is really good; and bisecting configuration or dependency changes (toolchain, SDK versions) is also possible by bisecting the commits that changed them.

**Related git tools:** `git log -S "symbol"` (find commits that added or removed text), `git blame` (who changed a line and why), `git log -p --follow file`.

### What is a logic analyser and when do you use it instead of an oscilloscope? {E}
**Short answer:** A **logic analyser** captures many digital signals (8–32+ channels) as 1s and 0s over long periods and **decodes protocols** (SPI, I2C, UART, CAN, 1-Wire, I2S, SWD), so it answers "what data was sent, in what order and with what timing between events". An **oscilloscope** shows the **analog** waveform of a few channels — voltage levels, rise times, ringing, noise, power-supply ripple — so it answers "is this signal electrically correct". Use the logic analyser for protocol and timing logic; use the oscilloscope when you suspect signal integrity, power or analog problems.

| | Logic analyser | Oscilloscope |
|---|---|---|
| Channels | 8–34+ | 2–8 |
| Shows | logic levels vs time, decoded protocols | real voltage waveform |
| Capture length | long (seconds to minutes, streaming) | short at high sample rates (deep memory helps) |
| Finds | wrong commands, missing ACKs, CS timing, ISR timing (with GPIO markers), sequence errors | ringing, slow edges, glitches, wrong levels, noise, supply dips, crosstalk |
| Typical tools | Saleae Logic, DSLogic, sigrok/PulseView with cheap analysers | Rigol, Siglent, Keysight, Tektronix; mixed-signal scopes (MSO) combine both |

**Typical workflow:** the logic analyser shows that an I2C sensor sometimes NACKs; the oscilloscope then shows that SDA's rising edge is too slow because the pull-up is too weak — two tools, one bug.

**Timing measurements:** toggle GPIOs at points in firmware (ISR entry/exit, task start, DMA complete) and capture them with the logic analyser alongside the bus signals to measure latency, execution time and jitter precisely without debugger interference.

### How do you design logging and diagnostics for devices in the field? {M}
**Short answer:** Make failures reportable after the fact: store a persistent **crash record** (fault registers, PC/LR, stack snippet, task name, firmware version and reset reason) in no-init RAM or flash, keep a compact **ring-buffer event log** with timestamps and severity levels, maintain **counters and health metrics** (resets by cause, communication errors, watchdog events, minimum free stack/heap, battery), and upload them when connectivity is available or expose them over a service interface. Keep logging cheap (binary records or log IDs instead of formatted strings), rate-limited and safe to call from any context.

**Design elements**

| Element | Detail |
|---|---|
| Log levels | ERROR / WARN / INFO / DEBUG, configurable at run time per module |
| Format | binary records: {timestamp, module, event ID, args}; decoded on the host using the build's string table (keeps flash small and logging fast) |
| Storage | RAM ring buffer, flushed to flash in batches (wear levelling, power-fail safe), with a bounded size |
| Context safety | ISR-safe enqueue (lock-free SPSC or a short critical section); formatting and I/O in a low-priority task |
| Crash path | minimal code that does not depend on the heap, RTOS or peripherals that may have failed |
| Versioning | firmware version, build ID (hash of the ELF) in every report so addresses can be symbolised |
| Privacy/security | no secrets or personal data in logs; authenticate the upload channel |

**Reset-cause handling at boot:** read the reset-cause register (POR, BOR, watchdog, software, pin), log it, check for a crash record from the previous run, then clear both.

**Tools/services:** Memfault, Zephyr's logging and coredump subsystems, AWS IoT Device Defender, or a custom backend; on embedded Linux, journald, `pstore`/ramoops, and kdump.

**Interview point:** "Without field diagnostics, an intermittent bug that happens once a month on 1 in 1,000 devices is nearly impossible to fix; with a crash record and the matching ELF file, it is often a 10-minute job."
