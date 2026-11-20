---
slug: debugging-testing
title: Debugging, Testing & Tools
icon: 🐞
level: Intermediate
order: 16
desc: GDB, JTAG/SWD, printf vs trace, unit testing firmware, static analysis, build systems and version control.
---
Interviewers often finish with "tell me about the hardest bug you fixed". These questions give you the vocabulary and the toolbox to answer well.

### How do you debug firmware that crashes only occasionally? {M}
1. **Capture state**: a fault handler that saves registers, the stacked PC/LR and the fault status into a no-init RAM area or flash, then reports it after reset.
2. **Add cheap tracing**: a ring buffer of events with timestamps, ITM/SWO or Segger RTT output, which costs far less than UART `printf`.
3. **Look for timing-sensitive causes**: races with ISRs, stack overflow, missing `volatile`, uninitialised variables, DMA overwriting buffers.
4. **Make it reproducible**: stress tests, fault injection, and varying optimisation level or timing.
5. Use **watchpoints** (data breakpoints) on the corrupted variable to catch the writer in the act.

### What is the difference between a breakpoint and a watchpoint? {E}
A **breakpoint** halts execution when the CPU reaches a specific instruction address. A **watchpoint** halts when a specific memory location is read or written, which is how you find what corrupts a variable. Cortex-M has a limited number of each in hardware (typically 4–8 breakpoints in the FPB and 2–4 watchpoints in the DWT); software breakpoints in RAM are unlimited.

### What are the essential GDB commands for embedded debugging? {E}
- `target extended-remote :3333` (OpenOCD) or `:2331` (J-Link GDB server), then `load` and `monitor reset halt`.
- `break`, `tbreak`, `watch var`, `rwatch`, `info breakpoints`.
- `continue`, `step`, `next`, `finish`, `until`.
- `bt` (backtrace), `frame n`, `info locals`, `print var`, `print/x reg`, `x/16wx addr` (examine memory).
- `info registers`, `display`, and `set var x = 5` to modify state.

### Why can printf debugging change program behaviour? {M}
`printf` over UART is slow (about 87 µs per character at 115200 baud), may block, uses a lot of stack, and is often not reentrant. Adding it changes timing, so race conditions can disappear ("Heisenbugs") or new ones appear, and calling it from an ISR can deadlock or corrupt output. Faster alternatives: Segger RTT, ITM/SWO trace, writing to a RAM log buffer, or toggling a GPIO and watching it on a scope or logic analyser.

### How do you unit test embedded C code? {M}
Separate hardware-independent logic (protocol parsing, state machines, algorithms) from hardware access behind a thin hardware abstraction layer. Then compile and test that logic **on the host** with a framework such as Unity + CMock (Ceedling), CppUTest or GoogleTest, replacing the HAL with mocks or fakes. Run the tests in CI on every commit. Add hardware-in-the-loop (HIL) tests on real boards for drivers and timing. Test-driven development works well for firmware logic.

### What is static analysis and which tools are used? {E}
Static analysis checks source code without running it, finding bugs such as NULL dereferences, buffer overflows, uninitialised variables, dead code and coding-standard violations (MISRA, CERT C). Tools: compiler warnings (`-Wall -Wextra -Werror`), `clang-tidy`, `cppcheck`, Coverity, PC-lint Plus, Polyspace, CodeSonar. The Linux kernel uses `sparse`, `smatch` and `checkpatch.pl`. Run them in CI so issues are caught before review.

### What is the difference between Make and CMake? {E}
**Make** reads a Makefile of targets, dependencies and commands and rebuilds what is out of date. **CMake** is a build-system generator: you describe targets in `CMakeLists.txt` and it generates Makefiles or Ninja files for a given toolchain. CMake with toolchain files is now common for MCU projects (Zephyr, STM32CubeMX, nRF Connect SDK, Pico SDK), while the Linux kernel and U-Boot use Make with Kbuild.

### What does a map file tell you? {M}
The linker map file lists every section, its address and size, which object file each symbol came from, and the memory usage of each region. Use it to find what is eating flash or RAM, to check that code landed in the right section (RAM functions, bootloader boundaries), and to translate a crash address to a function. `arm-none-eabi-size`, `nm --size-sort` and tools like Puncover summarise it.

### How do you reduce firmware code size? {M}
- Optimise for size (`-Os` or `-Oz`) and enable **LTO** (`-flto`).
- Remove unused code with `-ffunction-sections -fdata-sections` and `-Wl,--gc-sections`.
- Use `newlib-nano` (`--specs=nano.specs`) and avoid floating-point `printf`.
- Replace heavy library calls and vendor HAL functions with direct register code where needed.
- Make tables `const` so they stay in flash, and review the largest symbols in the map file.
- Avoid C++ exceptions, RTTI and template bloat.

### What is git bisect and how does it help? {E}
`git bisect` performs a binary search through commit history to find which commit introduced a bug. You mark one known good and one known bad commit; git checks out the midpoint, you test and mark it good or bad, and it repeats. With 1000 commits you need about 10 tests. `git bisect run ./test.sh` automates it if the test can be scripted, which works well with hardware-in-the-loop tests.

### What is a logic analyser and when do you use it instead of an oscilloscope? {E}
A logic analyser captures many digital channels as 0/1 levels over a long time window and decodes protocols (I2C, SPI, UART, CAN) into bytes. Use it to check what is being sent and when. An **oscilloscope** shows the analog waveform of a few channels: rise times, ringing, voltage levels and noise. Use it when the question is whether the signal is electrically good. Many bugs need both: the analyser shows a NACK, and the scope shows a slow rising edge from a weak pull-up.
