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
**Short answer:** **JTAG** (IEEE 1149.1) is a 4/5-wire debug and boundary-scan interface (TCK, TMS, TDI, TDO, optional TRST) that can daisy-chain several devices. **SWD** (Serial Wire Debug) is Arm's 2-wire alternative (SWCLK, SWDIO) that gives the same debug access to Cortex cores with fewer pins; it is the default on Cortex-M. Both connect a debug probe (J-Link, ST-LINK, CMSIS-DAP/DAPLink, Lauterbach) to the chip's debug access port, which lets the host flash memory, halt and step the CPU, read and write memory and registers while running, set hardware breakpoints and watchpoints, and receive trace.

| | JTAG | SWD |
|---|---|---|
| Pins | TCK, TMS, TDI, TDO (+ nTRST) | SWCLK, SWDIO (+ optional SWO for trace) |
| Daisy chain | yes (several chips on one chain) | no (point to point; SWD multi-drop exists in v2) |
| Boundary scan (testing board connections) | yes | no |
| Cores | any JTAG-capable chip (Arm, RISC-V, FPGAs, DSPs) | Arm Cortex |

**Debug connector advice:** always route SWD (plus nRESET and the SWO pin) to a standard 10-pin Cortex debug header or Tag-Connect footprint, plus a UART console. Many teams also keep the debug port usable in production for failure analysis, protected with readout protection and authenticated debug.

**Common connection problems:** firmware reconfigures the SWD pins as GPIOs or enters a low-power mode that disables the debug clock (connect under reset, enable DBGMCU low-power debug bits during development); readout protection blocks access (a mass erase may be the only way back); wrong target voltage reference on the probe.

**Security:** lock debug access in production (RDP levels on STM32, APPROTECT on nRF, debug authentication on Armv8-M) because an open debug port gives full access to memory and keys.

### What is the difference between a breakpoint and a watchpoint? {E}
**Short answer:** A **breakpoint** stops execution when the CPU reaches a particular **instruction address**. A **watchpoint** (data breakpoint) stops execution when a particular **data address** is read or written (or both), possibly only when the value matches. Watchpoints are the fastest way to find out who corrupts a variable. In flash-based MCUs, breakpoints use a limited number of **hardware comparators** (Cortex-M3/M4: 6 instruction comparators in the FPB, 4 data watchpoints in the DWT; Cortex-M0: 4 and 2).

| | Breakpoint | Watchpoint |
|---|---|---|
| Triggers on | executing an instruction address | reading/writing a data address |
| Hardware unit (Cortex-M) | FPB (Flash Patch and Breakpoint) | DWT (Data Watchpoint and Trace) |
| Typical count | 2–8 | 1–4 |
| GDB command | `break file.c:42`, `hbreak` | `watch var`, `rwatch`, `awatch` |
| Software version | `BKPT` instruction (RAM code only, or flash patching by the probe) | single-stepping and comparing (extremely slow) |

**Useful variants**

- **Conditional breakpoints:** `break foo if len > 512` (the debugger halts every time and checks, which can be slow; prefer a code-level `if (...) __BKPT(0);` in hot paths).
- **Watchpoint with a value:** some DWT implementations can match on data value, e.g. stop when a variable becomes 0.
- **Tracepoints / logpoints:** record or print without stopping (GDB `dprintf`, IDE logpoints).
- **`__BKPT(0)`** in code: an explicit breakpoint (e.g. in an assertion handler); without a debugger attached it causes a HardFault, so guard it with a "debugger attached" check (`CoreDebug->DHCSR & C_DEBUGEN`).

**Watchpoint example:** a global `config.mode` is randomly overwritten. Set `watch config.mode` (or `watch *(uint32_t *)0x20001234`), run, and the CPU halts on the instruction that writes it; `bt` shows the culprit, often a buffer overrun in a neighbouring array.

### What are the essential GDB commands for embedded debugging? {E}
**Short answer:** Connect to the probe's GDB server with `target extended-remote :3333` (OpenOCD) or `:2331` (J-Link), then `load` to flash the ELF, `monitor reset halt` to reset, `break`/`hbreak` and `watch` to stop, `continue`/`next`/`step`/`finish` to run, `bt` for the call stack, `info registers`, `print`/`p/x` and `x/16wx addr` to inspect data and memory, `frame N` to switch stack frames, and `set var x = 5` to change values.

```text
$ arm-none-eabi-gdb build/app.elf
(gdb) target extended-remote :3333        # OpenOCD GDB server
(gdb) monitor reset halt
(gdb) load                                # program flash from the ELF
(gdb) hbreak main
(gdb) continue
(gdb) next / step / finish                # over, into, out of a function
(gdb) bt                                  # backtrace
(gdb) frame 2                             # select a caller's frame
(gdb) info locals
(gdb) p/x *((GPIO_TypeDef *)0x40020000)   # peripheral registers as a struct
(gdb) x/8wx 0x20000000                    # 8 words of RAM in hex
(gdb) watch rx_count                      # stop when written
(gdb) info registers                      # r0-r15, xPSR
(gdb) p $pc ; p/x $sp
(gdb) set var debug_level = 3
(gdb) display/x status                    # show after every stop
(gdb) monitor reset                       # probe-specific commands
```

**Productivity tips**

- Build with `-g3` (macros available in GDB) and keep the exact ELF for every release so you can debug field crash dumps.
- `-Og` or `-O1` makes stepping more predictable than `-O2`; "value optimized out" means the variable lives only in registers at that point.
- A `.gdbinit` file automates connection and common commands; GDB's Python API can pretty-print RTOS structures.
- Use RTOS-aware debugging (OpenOCD `-rtos auto`, J-Link RTOS plugins) to list tasks and their stacks.
- Post-mortem: load a RAM dump into GDB, or analyse a core dump with tools like Memfault or `CrashDebug`.
- `arm-none-eabi-addr2line -e app.elf 0x0800abcd` converts a crash PC to a source line without a debugger.

### Why can printf debugging change program behaviour? {M}
**Short answer:** `printf` is slow (formatting plus a blocking UART at 115200 baud takes about 87 µs per character, so a 40-character line costs ~3.5 ms), uses a lot of stack (often 0.5–1 KB or more with floating-point formatting), may allocate memory or take locks, and is usually not safe to call from interrupts. Adding it changes timing, stack usage and memory layout, so race conditions and timing bugs may disappear or new ones may appear (a "Heisenbug").

**Better ways to get information out**

| Technique | Cost | Notes |
|---|---|---|
| GPIO toggle + scope/logic analyser | ~10 ns | best for timing, ISR entry/exit, latency |
| RAM trace buffer (event ID + timestamp + value) | a few cycles | dump later with the debugger or over a link |
| SEGGER RTT | ~1 µs per message, no blocking | writes to a RAM ring buffer read by the J-Link while running |
| ITM/SWO (`ITM_SendChar`) | fast, single-wire | requires an SWO pin and probe support |
| Deferred logging (log IDs + arguments, formatted on the host) | very low | e.g. Trice, defmt (Rust), Zephyr dictionary logging |
| Asynchronous log task with a queue | moderate | formatting happens later, at low priority |

**If you must use printf**

- Use a non-blocking, buffered implementation with DMA, and never call it from ISRs.
- Retarget `_write` (newlib) to your UART or RTT; use newlib-nano and avoid `%f` (or enable `-u _printf_float` only if needed).
- Remember that disabling printf in release builds also changes timing — test the release configuration.

### What are ITM, SWO, ETM and RTT, and when do you use trace? {M}
**Short answer:** They are ways to get data out of a running Cortex-M without stopping it. **ITM** (Instrumentation Trace Macrocell) sends software messages (printf-style output, event IDs) and hardware events (DWT data trace, PC sampling, exception entry/exit) over the single-wire **SWO** pin. **ETM** (Embedded Trace Macrocell) streams every executed instruction through a parallel trace port (or into an on-chip buffer like the ETB/MTB), giving a full execution history for timing analysis and code coverage. **RTT** (SEGGER Real-Time Transfer) uses ring buffers in RAM that the debug probe reads in the background, so it works on any core with just SWD.

| | ITM/SWO | ETM (+ trace port) | MTB (Cortex-M0+) | RTT |
|---|---|---|---|---|
| Data | software messages, PC samples, exception trace, data watch trace | full instruction trace | recent branches in RAM | software messages, bidirectional |
| Pins | 1 (SWO) | 4–5 (TRACECLK, TRACEDATA[3:0]) | none | none (SWD) |
| Probe | most probes | trace probes (J-Trace, Lauterbach, ULINKpro) | any | J-Link (and some others) |
| Use | logging, profiling, ISR timing | "what happened before the crash", coverage, WCET | post-mortem branch history | fast logging, shell |

**Uses of trace**

- Finding the code path just before a HardFault (ETM/MTB history).
- Statistical profiling: PC sampling every N cycles shows where CPU time goes.
- RTOS event trace: Percepio Tracealyzer and SEGGER SystemView record context switches, ISRs and API calls (via RTT or a RAM buffer) and display timelines.
- Code coverage on target with ETM, without instrumentation.

**DWT cycle counter:** `DWT->CYCCNT` (enable with `CoreDebug->DEMCR |= TRCENA; DWT->CTRL |= 1`) gives cycle-accurate timing of code sections, available on Cortex-M3 and above.

### How do you find memory corruption and stack overflows in firmware? {M}
**Short answer:** Detect them as close to the cause as possible: **stack overflows** with MPU guard regions below each stack (immediate MemManage fault), the Armv8-M stack limit registers (MSPLIM/PSPLIM), RTOS stack checking (canary patterns checked at context switches), and high-water marks from stack painting; **memory corruption** with data watchpoints on the corrupted variable, canary values around buffers and heap blocks, MPU regions that make code and constant data read-only and catch NULL pointer access, and host-side tools (AddressSanitizer, Valgrind) by running the same code in unit tests on a PC.

**Stack painting and high-water mark**

```c
#include <stdint.h>
#include <stddef.h>

#define STACK_WORDS 512
static uint32_t task_stack[STACK_WORDS];              /* grows down from the top */

void stack_paint(void) { for (size_t i = 0; i < STACK_WORDS; i++) task_stack[i] = 0xA5A5A5A5u; }

size_t stack_free_words(void)                         /* words never touched since painting */
{
    size_t n = 0;
    while (n < STACK_WORDS && task_stack[n] == 0xA5A5A5A5u) n++;
    return n;
}
```

**Typical sources of corruption**

| Source | How to catch it |
|---|---|
| Buffer overrun (array index, `strcpy`, missing length check on received data) | watchpoints, canaries, bounds-checked functions, static analysis |
| Stack overflow into adjacent RAM (other stacks, globals) | MPU guard, PSPLIM, RTOS checks, large margins |
| Use after free / double free | pools with poisoning (fill freed blocks with a pattern), heap integrity checks, ASan on host |
| DMA writing beyond its buffer or into a freed buffer | check DMA lengths, MPU, guard patterns after DMA buffers |
| Cache maintenance errors (Cortex-M7) | aligned DMA buffers, invalidate/clean correctly or use non-cacheable regions |
| ISR and task race on shared structures | critical sections, review all ISR-shared data |
| Wild pointers (uninitialised, stale function pointers) | initialise everything, `-Wall -Wextra`, static analysis |

**Linker tricks:** place stacks at the **bottom** of RAM (below globals) so an overflow runs into non-existent memory or a guard region and faults immediately, rather than silently overwriting variables.

### How do you unit test embedded C code? {M}
**Short answer:** Separate hardware access from logic behind thin interfaces (HAL functions, function pointers or link-time substitution), then compile and run the logic **on the host PC** with a test framework (Unity, CppUTest, GoogleTest, CMocka), replacing hardware functions with **fakes or mocks** (CMock, FFF, hand-written fakes). Run the tests on every commit in CI, measure coverage, and add on-target and hardware-in-the-loop tests for what only real hardware can show.

**Example: testing a debounce module with Unity**

```c
/* debounce.h */
#include <stdbool.h>
#include <stdint.h>
typedef struct { uint8_t count; bool state; } debounce_t;
bool debounce_update(debounce_t *d, bool raw);       /* call every 1 ms; returns stable state */

/* debounce.c */
bool debounce_update(debounce_t *d, bool raw)
{
    if (raw == d->state) { d->count = 0; return d->state; }
    if (++d->count >= 5) { d->state = raw; d->count = 0; }   /* 5 consecutive samples */
    return d->state;
}

/* test_debounce.c — runs on the PC */
#include "unity.h"
#include "debounce.h"

void setUp(void) {}
void tearDown(void) {}

void test_glitch_is_ignored(void)
{
    debounce_t d = {0};
    debounce_update(&d, true);  debounce_update(&d, true);
    debounce_update(&d, false);                      /* bounce back */
    for (int i = 0; i < 4; i++) TEST_ASSERT_FALSE(debounce_update(&d, true));
    TEST_ASSERT_TRUE(debounce_update(&d, true));     /* 5th consecutive sample */
}

int main(void) { UNITY_BEGIN(); RUN_TEST(test_glitch_is_ignored); return UNITY_END(); }
```

**Techniques for replacing hardware**

| Technique | How | Pros/cons |
|---|---|---|
| Link-time substitution | link `fake_gpio.c` instead of `gpio.c` in the test build | simple, no production code changes |
| Function pointers / interfaces | driver struct with ops, tests pass fakes | flexible, small run-time cost |
| Generated mocks (CMock, FFF) | mocks record calls and return programmed values | verifies interactions; tests can become brittle |
| Register-level fakes | point the peripheral base pointer at a RAM struct | tests driver register logic on the host |
| Emulation | run the firmware in QEMU or Renode | tests whole images, including startup and RTOS |

**Good practices:** test-driven development for logic-heavy modules (parsers, state machines, protocol handling, filters), keep hardware-dependent code thin, run tests with sanitizers (`-fsanitize=address,undefined`) on the host, and track coverage with gcov/lcov. Book: *Test-Driven Development for Embedded C* (James Grenning).

### What is hardware-in-the-loop (HIL) testing, and how do you set up CI for firmware? {M}
**Short answer:** **CI for firmware** builds every configuration and target on each commit, runs static analysis and host unit tests, checks code size, and produces versioned artifacts. **Hardware-in-the-loop** testing then flashes the build onto real boards (or a board farm) connected to test equipment that simulates the environment — sensors, buses, power supplies, network — and runs automated system tests that check behaviour, timing and recovery. Simulation-based testing (QEMU, Renode) sits in between: whole firmware images on virtual hardware, faster and easier to scale than real boards.

**Typical pipeline**

```
commit → build (all boards, debug + release, warnings as errors)
       → static analysis (cppcheck/clang-tidy/MISRA checker), formatting check
       → host unit tests + sanitizers + coverage report
       → size report (fail if flash/RAM grows beyond a budget)
       → simulation tests (Renode/QEMU) for boot, protocols, RTOS behaviour
       → HIL: flash test boards, run system tests (pytest + serial/CAN/SPI tools, power cycling)
       → artifacts: signed images, map files, ELF with symbols, release notes
```

**HIL rig components:** a host PC or Raspberry Pi per rack, debug probes for flashing, USB-controlled relays/power switches for power cycling, programmable supplies (brown-out tests), signal generators or DACs to simulate sensors, CAN/UART/SPI adapters, logic analysers with scripted captures, and a test framework (pytest, Robot Framework, LabGrid, Lava).

**What HIL catches that unit tests cannot:** timing and interrupt interactions, peripheral configuration errors, boot and update procedures (including failed updates and rollbacks), power-loss behaviour, long-duration stability (leaks, counter overflows), and hardware revision differences.

**Tips:** make the firmware testable — a test command shell or RPC over UART/USB, deterministic logs, and version reporting — and keep HIL tests stable (flaky tests get ignored).

### What is code coverage, and what coverage levels do safety standards require? {M}
**Short answer:** Code coverage measures which parts of the code the tests executed. **Statement coverage** checks every line ran; **branch (decision) coverage** checks every `if`/`switch` took each outcome; **MC/DC** (Modified Condition/Decision Coverage) checks that each individual condition in a decision independently affects the outcome. Coverage shows what is **not** tested — it does not prove the tested code is correct. Safety standards require higher levels for more critical software: e.g. DO-178C requires MC/DC for Level A avionics software, and ISO 26262 recommends MC/DC for ASIL D.

**Example: why branch coverage is not enough**

```c
if (speed > LIMIT && !override) brake();
```

Two tests (true/false outcome) give branch coverage, but MC/DC needs tests showing that `speed > LIMIT` alone changes the outcome (with `override` fixed) and that `override` alone changes it: e.g. (T,F)→brake, (F,F)→no brake, (T,T)→no brake.

**Measuring**

- On the host: `gcc --coverage` / gcov + lcov/gcovr reports; LLVM source-based coverage.
- On the target: instrumented builds that dump counters over a debug link (gcov with semihosting or custom dump), or non-intrusive ETM trace (no code changes).
- Commercial tools: VectorCAST, LDRA, Testwell CTC++, Cantata (support MC/DC and certification evidence).

**Practical targets:** for ordinary product firmware, aim for high statement and branch coverage on logic modules (parsers, state machines, safety checks) rather than a single number for the whole codebase; review untested code to decide whether it needs tests, is defensive code, or is dead code.

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
