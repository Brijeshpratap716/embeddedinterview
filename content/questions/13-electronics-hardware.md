---
slug: electronics-hardware
title: Electronics & Hardware Basics
icon: 🔋
level: Beginner
order: 13
desc: Ohm's law, pull-ups, level shifting, ADC and filters, power supplies, signal integrity and reading schematics.
---
Firmware engineers are expected to read schematics, bring up boards and talk to hardware engineers. These are the basics that come up.

### What are pull-up and pull-down resistors? {E}
A pull-up connects a signal to the supply through a resistor so it reads a defined high when nothing drives it; a pull-down connects it to ground for a defined low. Without them, an unconnected input "floats" and picks up noise, reading random values and wasting power. Typical values are 4.7 kΩ to 100 kΩ; lower values give faster edges and better noise immunity but more current when the line is driven low. Most MCUs have selectable internal pulls of roughly 30–50 kΩ.

### How do you calculate the current-limiting resistor for an LED? {E}
R = (Vsupply − Vf) / I. For a 3.3 V GPIO driving a red LED with Vf ≈ 2.0 V at 5 mA: R = (3.3 − 2.0) / 0.005 = 260 Ω, so use 270 Ω. Check that the GPIO can source or sink that current and that the total current for the port stays within the datasheet limit.

### How do you interface a 3.3 V MCU with a 5 V device? {M}
- **5 V output into a 3.3 V input**: use a resistor divider, a level-shifter IC, or a pin that is explicitly **5 V tolerant** (check the datasheet "FT" pins).
- **3.3 V output into a 5 V input**: often works if the 5 V device's VIH is ≤ about 2.5 V (TTL-compatible inputs, e.g. 74HCT); otherwise use a buffer or level shifter.
- **Bidirectional open-drain (I2C)**: a MOSFET-based shifter (BSS138 circuit) or a dedicated I2C level translator.

Never feed 5 V into a non-tolerant pin; the internal clamp diodes can conduct and back-power the MCU.

### What is a decoupling capacitor and where should it be placed? {E}
A small capacitor (typically 100 nF ceramic, plus a 1–10 µF bulk capacitor) between each supply pin and ground that supplies fast current spikes locally and filters high-frequency noise. It must be placed as **close as possible** to the pin with a short path to ground, because trace inductance makes a distant capacitor ineffective. Missing or badly placed decoupling causes resets, ADC noise and unreliable high-speed interfaces.

### What is the difference between a linear regulator (LDO) and a switching regulator? {M}
- **LDO**: drops the excess voltage across a pass transistor. Simple, quiet, cheap, but efficiency is roughly Vout/Vin, so power is wasted as heat (P = (Vin − Vout) × I). Good for small currents, noise-sensitive analog rails, or small voltage drops.
- **Switching (buck/boost)**: switches an inductor at high frequency, with 80–95% efficiency over large voltage differences. More components, and it produces switching ripple and EMI that may need filtering.

Battery products usually use a buck converter for the main rail and an LDO after it for analog sections.

### What is the Nyquist theorem and what is aliasing? {E}
To reconstruct a signal from samples, you must sample at more than **twice its highest frequency component**. Frequencies above half the sample rate (the Nyquist frequency) fold back and appear as false lower frequencies, called **aliasing**. A low-pass **anti-aliasing filter** before the ADC removes them. In practice sample at 5–10× the bandwidth of interest to make the filter realistic.

### What is a low-pass RC filter and how do you find its cut-off frequency? {E}
A resistor in series with a capacitor to ground passes low frequencies and attenuates high ones. The cut-off (−3 dB) frequency is f = 1 / (2πRC). For R = 1 kΩ and C = 100 nF, f ≈ 1.6 kHz. Above the cut-off, a first-order filter attenuates by 20 dB per decade. It is used before ADC inputs and to smooth PWM into an analog voltage.

### What is the difference between a crystal and an RC oscillator? {E}
A **crystal** (or ceramic resonator) uses a piezoelectric quartz resonator for an accurate, stable frequency (typically ±10–50 ppm), needed for USB, CAN, Ethernet, high baud rates and RTCs. It needs correctly sized load capacitors and takes milliseconds to start. An **internal RC oscillator** needs no external parts and starts quickly, but is only accurate to about ±1–2% across temperature and voltage unless trimmed or calibrated.

### What is a MOSFET and how do you use one to switch a load? {M}
A MOSFET is a voltage-controlled switch. For a **low-side switch**, use an N-channel MOSFET between the load and ground: driving the gate above its threshold turns it on. Choose a logic-level part whose **Rds(on)** is specified at your gate voltage (e.g. 2.5 V or 3.3 V). Add a gate resistor (10–100 Ω) to limit ringing and a pull-down (10–100 kΩ) so the load stays off during reset when the GPIO is floating. For inductive loads (relays, motors), add a **flyback diode** across the load.

### What is a flyback diode and why is it needed? {E}
When current through an inductor (relay coil, motor, solenoid) is switched off, the inductor generates a large reverse voltage spike (V = L·di/dt) that can destroy the switching transistor. A diode placed across the coil, reverse-biased in normal operation, gives the current a path to decay safely. A Zener or TVS in series makes relays release faster.

### What is ESD and how do you protect a board? {M}
Electrostatic discharge is a sudden high-voltage, high-current pulse when a charged object (often a person) touches a circuit; it can damage or latch up ICs. Protect exposed connectors and buttons with **TVS diodes** close to the connector, series resistors, ferrites, good ground design and enclosures. Products are tested to IEC 61000-4-2 (e.g. ±8 kV contact discharge). Handle boards with wrist straps and ESD mats.

### What is signal integrity and what causes ringing? {H}
Signal integrity is how well a signal keeps its shape as it travels. Fast edges on long traces behave like transmission lines; if the trace impedance does not match the driver and receiver, reflections cause **ringing**, overshoot and false edges. Causes include long unterminated traces, poor return paths (gaps in the ground plane), crosstalk between parallel traces and too-fast slew rates. Fixes: series termination resistors (22–33 Ω near the driver), controlled-impedance routing, solid ground planes, and using the slowest GPIO speed setting that works.

### How do you read a datasheet efficiently? {E}
1. **Front page and block diagram** for what the part does.
2. **Absolute maximum ratings** (never exceed) and **recommended operating conditions**.
3. **Electrical characteristics** with their test conditions: VIH/VIL, supply current, timing.
4. **Timing diagrams** for the interface (setup/hold, clock limits, power-up sequence).
5. **Register map** and the application section, with reference schematics and layout guidance.
6. Always read the **errata** sheet for silicon bugs.

### What tools do you use for board bring-up? {E}
A **multimeter** for rails and continuity; an **oscilloscope** for clocks, power ripple, reset timing and signal shape; a **logic analyser** (Saleae, sigrok) with protocol decoders for UART/SPI/I2C/CAN; a **debug probe** (J-Link, ST-LINK) for flashing and stepping; a **bench power supply** with current limit to catch shorts; and a **current/power analyser** (Nordic PPK2, Joulescope) for low-power work. Bring-up order: power rails, clocks, reset, debug connection, then a blinking LED and a UART console.
