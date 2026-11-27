---
slug: electronics-hardware
title: Electronics & Hardware Basics
icon: 🔋
level: Beginner
order: 15
desc: Ohm's law and power, pull-ups, GPIO modes, LEDs, level shifting, decoupling, LDO vs buck, ADC/DAC, Nyquist, filters, oscillators, MOSFETs, flyback diodes, ESD, signal integrity, low power, schematics and bring-up.
---
Firmware engineers are expected to read schematics, bring up boards and talk to hardware engineers. These are the basics that come up, each with a short answer, the numbers to know and the follow-ups.

### What are Ohm's law and the power formula, and how do you use them on a board? {E}
Ohm's law relates voltage, current and resistance: V = IR. Electrical power is P = VI = I²R = V²/R for a resistor.

#### 1. Board calculation
A 3.3 V output drives a 1 kΩ resistor to ground. The current is 3.3 mA and the resistor dissipates 10.89 mW. Check that the GPIO can supply that current and that the resistor's power rating includes adequate margin.

#### 2. Debugging application
Measure the voltage across a known series resistor and calculate current using I = V/R. If a board draws unexpectedly high current, inspect the affected power rail for shorts, incorrect components or improperly configured outputs.

**Interview takeaway:** Use these equations to size components and validate measured values; do not treat a GPIO as an unlimited voltage source.

### What are pull-up and pull-down resistors? {E}
Pull-up and pull-down resistors establish a predictable logic level when no active driver is present.

```text
3.3 V                     GPIO
  |                         |
  R (pull-up)               R (pull-down)
  |                         |
GPIO ---- switch ---- GND  GND
```

#### 1. Example
With a pull-up, an open switch reads high and a closed switch reads low. With a 10 kΩ pull-up to 3.3 V, pressing the switch draws approximately 0.33 mA.

#### 2. Selecting resistance
A weaker pull saves current but increases the RC rise time and susceptibility to leakage/noise. A stronger pull switches faster but consumes more current when driven low. Internal pulls are convenient but have relatively wide tolerance.

**Interview takeaway:** A floating input is not reliably zero or one. I²C specifically needs pull-ups because devices drive the bus low and release it for high.

### What are the GPIO output modes (push-pull vs open-drain) and input options? {E}
GPIO configuration controls the pad's electrical behavior as well as its logical function.

| Mode | Behavior | Typical use |
|---|---|---|
| Push-pull | Actively drives high and low | LED, SPI clock |
| Open-drain | Drives low or releases line | I²C, shared interrupt |
| Input | High impedance, optionally with pull | Button, sensor IRQ |
| Alternate function | Peripheral controls pad | UART, SPI |
| Analog | Digital input path disabled where supported | ADC, low leakage |

#### Example
Two open-drain devices can share a line with a pull-up: either can pull it low without opposing a high-side output driver. Connecting opposing push-pull outputs can cause damaging contention.

**Interview takeaway:** Check pin multiplexing, voltage tolerance, drive strength, slew rate and external pulls. A correct GPIO register value alone does not guarantee a valid signal.

### How do you calculate the current-limiting resistor for an LED? {E}
Use R = (V_supply − V_forward)/I_LED to limit LED current.

#### Example
For a red LED with 2 V forward voltage, a 3.3 V supply and 5 mA target current, R = 260 Ω. Choose a standard 270 Ω resistor, giving approximately 4.8 mA.

```text
GPIO HIGH --- 270 ohm --- LED ---> GND
```

The resistor dissipates about I²R = 6.3 mW. Confirm the LED's forward voltage range and GPIO output voltage at the selected current. For larger loads use a transistor or dedicated driver.

**Interview takeaway:** Always account for GPIO current limits and worst-case forward voltage; the LED does not regulate its own current.

### How do you interface a 3.3 V MCU with a 5 V device? {M}
A voltage-domain mismatch must be resolved using the receiver's absolute maximum ratings and logic thresholds.

#### 1. Common cases
- 5 V push-pull output into a 3.3 V input: use a suitable translator, or a resistor divider for a slow unidirectional signal if its impedance and timing are acceptable.
- 3.3 V output into 5 V input: direct connection is acceptable only if the receiver's VIH specification is satisfied.
- Open-drain I²C: use a bidirectional open-drain level translator with appropriate pull-ups on each side.

#### 2. Example
A 10 kΩ upper resistor and 20 kΩ lower resistor divide 5 V to about 3.33 V, assuming negligible load. This is not a universal solution for high-speed or bidirectional signals.

**Interview takeaway:** Check tolerance when either device is unpowered, power sequencing, propagation delay and contention. Do not rely on protection diodes to absorb continuous overvoltage.

### What is a decoupling capacitor and where should it be placed? {E}
A decoupling capacitor supplies transient current locally and reduces supply disturbances caused by rapidly switching circuits.

```text
Power rail ----+---- IC VDD
               |
             100 nF
               |
Ground --------+---- IC GND
```

#### Placement
Place the high-frequency ceramic capacitor close to the supply and ground pins with a short, low-inductance loop. Larger bulk capacitors help with slower load changes; exact values and ESR must follow the IC or regulator datasheet.

#### Example
A processor switching many outputs simultaneously can cause supply droop. Local capacitors reduce the transient current that must travel through long PCB traces.

**Interview takeaway:** Capacitance, ESR, ESL and layout all matter. A large capacitor far from the chip cannot replace proper local decoupling.

### What is the difference between a linear regulator (LDO) and a switching regulator? {M}
An LDO regulates voltage by dissipating excess energy in a series pass device. A switching regulator transfers energy using switched inductors/capacitors and can be more efficient.

| LDO | Switching regulator |
|---|---|
| Low noise, simpler circuit | Higher efficiency at large voltage differences |
| Output below input | Buck, boost or buck-boost |
| Heat proportional to voltage drop | Switching ripple and layout concerns |

#### Example
Converting 5 V to 3.3 V at 200 mA with an idealized LDO dissipates (5 − 3.3) × 0.2 = 0.34 W. Efficiency ignoring quiescent current is 66%. A buck at 90% efficiency dissipates about 73 mW for the same output power.

**Interview takeaway:** Select using input range, load, noise, thermal budget, quiescent current and transient response—not efficiency alone.

### How does an ADC work, and what are resolution, reference and sampling time? {M}
**Short answer:** An ADC converts an analog voltage into a number: `code = V_in / V_ref × (2^N − 1)` for an N-bit converter (often written × 2^N). **Resolution** is the number of bits (a 12-bit ADC with a 3.3 V reference has an LSB of 3.3 / 4096 ≈ 0.8 mV). The **reference voltage** sets full scale, so its accuracy and noise directly limit the measurement. MCU ADCs are mostly **SAR** (successive approximation) converters that first charge an internal **sampling capacitor** during the sampling time; if the source impedance is high, the capacitor does not charge fully and the reading is wrong.

**Converting a reading**

```c
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    const float vref = 3.3f;
    uint16_t raw = 2482;                                 /* 12-bit reading */
    float v = raw * vref / 4095.0f;                      /* ≈ 2.000 V */
    uint32_t mv = (uint32_t)raw * 3300u / 4095u;         /* integer version: 2000 mV */
    printf("%.3f V, %lu mV\n", v, (unsigned long)mv);
    return 0;
}
```

**Accuracy vs resolution:** a 12-bit ADC rarely gives 12 accurate bits: offset, gain error, integral/differential non-linearity (INL/DNL) and noise reduce the **effective number of bits (ENOB)** to maybe 10–11. Calibrate (many MCUs have a self-calibration routine and factory calibration values, e.g. for the internal reference VREFINT and temperature sensor).

**Sampling time and source impedance:** the SAR ADC's sample-and-hold capacitor (a few pF) must charge to within ½ LSB during the sampling time. A high source impedance (e.g. a 100 kΩ divider) needs a longer sampling time, a capacitor at the ADC pin (e.g. 10–100 nF acting as a charge reservoir), or an op-amp buffer.

**Improving measurements**

- Oversample and average (each 4× oversampling adds about 1 bit of resolution if noise is present).
- Measure VREFINT to compensate for a varying VDD reference.
- Separate analog supply (VDDA) and reference with filtering; keep analog traces away from switching signals.
- Trigger conversions from a timer (exact sample rate) and transfer with DMA.

**Other ADC types:** sigma-delta (high resolution, slow: precision sensors, audio), pipelined and flash (very fast: video, oscilloscopes).

### What is the Nyquist theorem and what is aliasing? {E}
**Short answer:** The Nyquist–Shannon sampling theorem says a signal must be sampled at **more than twice its highest frequency component** to be reconstructed without loss. If frequencies above half the sample rate (the **Nyquist frequency**, f_s/2) are present, they fold back and appear as false lower frequencies — **aliasing** — which cannot be removed after sampling. That is why an **anti-aliasing low-pass filter** is placed before the ADC.

**Aliasing example:** sampling at 1 kHz, a 900 Hz signal appears at |900 − 1000| = **100 Hz**. Mains hum (50/60 Hz) harmonics and switching-regulator noise commonly alias into sensor readings this way.

**Practical rules**

- Sample at 5–10× the highest frequency of interest when possible; this relaxes the anti-aliasing filter (a simple RC filter rolls off slowly: only −20 dB/decade).
- Put the filter's cut-off at or below the band of interest and well below f_s/2.
- Use oversampling + digital filtering + decimation: sample fast with a simple analog filter, then filter and downsample digitally (sigma-delta ADCs do this internally).
- For slow sensors, choose a sampling rate that rejects mains: averaging over exactly 20 ms (50 Hz) or 16.67 ms (60 Hz), or 100 ms for both.

**Related:** quantisation noise (from finite resolution) is different from aliasing; dithering and oversampling can reduce its effect.

### What is a low-pass RC filter and how do you find its cut-off frequency? {E}
**Short answer:** A resistor in series with the signal and a capacitor to ground form a first-order low-pass filter: low frequencies pass, high frequencies are attenuated at −20 dB per decade above the cut-off frequency **f_c = 1 / (2π R C)**, where the output is −3 dB (about 70.7% of the input amplitude). Example: R = 10 kΩ, C = 100 nF → f_c = 1 / (2π × 10⁴ × 10⁻⁷) ≈ **159 Hz**.

**Time domain:** the time constant τ = R × C (1 ms in the example); after a step, the output reaches 63% after τ and ~99% after 5τ. This matters for debounce circuits and for how fast an ADC input settles after switching channels.

**Uses on a board**

- Anti-aliasing before ADCs.
- Button debouncing (often with a Schmitt-trigger input).
- Smoothing PWM into a DC voltage (cheap DAC): choose f_c well below the PWM frequency; ripple falls as the PWM frequency rises.
- Filtering noise on reset lines and slow control signals.

**Design trade-offs**

- A large R reduces current but raises output impedance (the load, e.g. an ADC sampling capacitor, can disturb the filter) and thermal noise.
- Higher-order filters (two RC stages, active Sallen-Key filters) give a steeper roll-off.
- High-pass RC (capacitor in series, resistor to ground) blocks DC: same f_c formula.

**Digital equivalent:** the first-order IIR (exponential moving average) `y += α (x − y)` with α ≈ 2π f_c / f_s for f_c ≪ f_s.

### What is a DAC, and how can you generate an analog voltage with PWM? {E}
**Short answer:** A DAC (digital-to-analog converter) produces an output voltage proportional to a digital code: `V_out = code / (2^N − 1) × V_ref`. Many MCUs have 12-bit DACs for waveform generation, audio, biasing and setpoints. Without a DAC, a **PWM output followed by a low-pass filter** gives an average voltage `V_out = duty × V_high`; resolution comes from the PWM timer's counts and the ripple from the filter.

**PWM-DAC numbers**

- Resolution: a timer clocked at 84 MHz with a period of 4096 counts gives 12-bit resolution at 84 MHz / 4096 ≈ **20.5 kHz** PWM frequency.
- Filter: an RC filter with f_c ≈ 200 Hz attenuates the 20 kHz ripple by about 40 dB (100×); a two-stage filter gives more.
- Trade-off: higher resolution means a lower PWM frequency (for a fixed timer clock), which needs more filtering and slows the response.

**Generating waveforms:** use a timer to trigger DAC updates and DMA to feed a sine table (e.g. 64 samples per period) for exact frequencies without CPU load.

**Other DAC concepts:** settling time, glitch energy at major code transitions, output buffer drive capability, and R-2R ladder or resistor-string architectures.

### What is the difference between a crystal and an RC oscillator? {E}
**Short answer:** A **quartz crystal** (or crystal oscillator module) gives an accurate and stable frequency, typically ±10–50 ppm, needed for UART at high baud rates, USB, CAN, Ethernet, radio and real-time clocks. An internal **RC oscillator** costs nothing, starts quickly and saves pins and board space, but its accuracy is typically ±1–3% over temperature and voltage (factory-trimmed parts can be much better at room temperature), which is too inaccurate for USB, CAN or Ethernet and risky for fast UARTs.

| | Crystal (HSE, LSE) | Internal RC (HSI, MSI, LSI) |
|---|---|---|
| Accuracy | ±10–50 ppm | ±0.5–3% (worse over temperature) |
| Start-up | ms (32 kHz crystals: up to seconds) | µs |
| Cost/pins | crystal + 2 load caps, 2 pins | none |
| Uses | USB, CAN, Ethernet, radios, RTC timekeeping | general CPU clock, low-power wake-up, watchdogs (LSI) |

**Error examples:** 1% error on a clock means 14 minutes per day for an RTC, while a 20 ppm crystal drifts about 1.7 s per day. For a UART, 1% error per side is acceptable for 8N1; 3% may not be.

**Board design points**

- Load capacitors: `C_load = (C1 × C2)/(C1 + C2) + C_stray`; for a crystal rated C_L = 12 pF with ~3 pF stray, C1 = C2 ≈ 18 pF. Wrong values shift the frequency.
- Keep the crystal close to the MCU, with a ground guard and no signals routed underneath.
- Check the oscillator's drive level and the MCU's recommended crystal ESR; low-power 32.768 kHz crystals are sensitive to leakage (flux residue) and layout.

**Firmware:** enable clock security system (CSS) to fall back to the internal oscillator if the crystal fails; trim the RC oscillator against the crystal or USB SOF (clock recovery system) where available; add timeouts when waiting for the crystal to start.

### What is a MOSFET and how do you use one to switch a load? {M}
**Short answer:** A MOSFET is a voltage-controlled transistor: the gate-source voltage (V_GS) controls the resistance between drain and source. To switch a load from an MCU, use an **N-channel MOSFET as a low-side switch**: load between the supply and the drain, source to ground, GPIO to the gate through a small resistor, and a pull-down from gate to source. Choose a **logic-level** MOSFET whose R_DS(on) is specified at the GPIO voltage (e.g. V_GS = 2.5 V or 3.3 V), with enough drain-source voltage and current rating. Inductive loads need a flyback diode.

```
      +12 V
        │
      [Load]  ◄── flyback diode across the load (cathode to +12 V) if inductive
        │
        D
GPIO ─[100 Ω]─ G   N-MOSFET (e.g. logic-level, R_DS(on) spec'd at 2.5 V)
        │      S
     [100 kΩ]  │
        │      │
       GND ────┘
```

**Key parameters**

| Parameter | Why it matters |
|---|---|
| V_GS(th) | voltage where it **starts** to conduct — not where it is fully on; use R_DS(on) at your V_GS instead |
| R_DS(on) at your V_GS | conduction loss P = I² × R_DS(on) (2 A × 2 A × 50 mΩ = 0.2 W) |
| V_DS(max) | must exceed the supply plus any inductive spikes |
| I_D, thermal resistance | current and heat limits; check the derating curves |
| Gate charge Q_g | how fast it switches; matters for PWM (a GPIO can only source a few mA, so high-frequency PWM of big MOSFETs needs a gate driver) |

**High-side switching:** switching the positive supply (so the load stays grounded) uses a P-channel MOSFET (gate pulled to the supply to turn off, pulled low to turn on; needs a small NPN/N-MOSFET level shifter if the supply is above the GPIO voltage) or an N-channel with a gate driver/charge pump; integrated "high-side switches" add current limiting and diagnostics (common in automotive).

**Resistor roles:** the series gate resistor (10–100 Ω) limits ringing and the GPIO current spike charging the gate capacitance; the pull-down keeps the MOSFET off while the MCU is in reset with its pins floating.

**BJT alternative:** an NPN transistor needs a base current (I_B ≈ I_C / 10 for saturation) through a base resistor; fine for small loads (relays, LEDs), but MOSFETs are more efficient for higher currents.

### What is a flyback diode and why is it needed? {E}
**Short answer:** When current through an inductive load (relay coil, motor, solenoid) is switched off suddenly, the inductor's stored energy produces a large voltage spike (V = L × di/dt, often hundreds of volts) that can destroy the switching transistor or MCU pin. A **flyback (freewheeling) diode** across the load, reverse-biased in normal operation (cathode to the positive supply), gives the current a path to circulate and decay safely, clamping the spike to about one diode drop above the supply.

**Trade-off: release time.** A plain diode lets the current decay slowly, so a relay opens more slowly (and motors keep spinning). For faster release, add a Zener or TVS in series with the diode (clamps at a higher voltage, dissipating energy faster) while keeping the voltage below the transistor's rating.

**Motors driven in both directions (H-bridges)** have four freewheeling diodes (often the MOSFETs' body diodes, or synchronous rectification by switching on the opposite MOSFETs).

**Choosing the diode:** reverse voltage above the supply, current rating at least the load current (for the decay time), fast or Schottky types for PWM-driven loads.

**Firmware symptom of a missing or failed diode:** the MCU resets or a GPIO dies when a relay switches; noise on ADC readings at each motor commutation.

### What is ESD and how do you protect a board? {M}
**Short answer:** Electrostatic discharge is a fast, high-voltage pulse (thousands of volts, nanosecond rise times, amps of peak current) when a charged person or object touches a connector or pin. It can destroy or weaken ICs immediately or cause latent damage and glitches (resets, lock-ups, corrupted registers). Protect external interfaces with **TVS diodes** placed right at the connector with a short path to ground, add series resistors or ferrites on signals, use proper grounding and enclosure design, and design firmware to recover from glitches.

**Hardware measures**

- TVS/ESD diode arrays on every externally accessible line (USB, buttons, Ethernet, CAN, debug headers), chosen with low capacitance for fast signals (USB HS, HDMI).
- Place protection **between the connector and anything else**, with a very short, wide ground connection; route the discharge current away from the MCU.
- Series resistors (e.g. 22–100 Ω) limit current into IC pins; RC filters on slow inputs.
- Solid ground planes, chassis ground connections at connectors, and spark gaps/shielding where required.
- Test to IEC 61000-4-2 levels (e.g. ±8 kV contact, ±15 kV air discharge) for products.

**Handling:** ESD-safe work areas (wrist straps, mats, ionisers), and shipping boards in anti-static packaging.

**Firmware robustness against ESD and EMC events**

- Watchdog enabled and serviced from a supervisory task.
- Periodically re-write critical configuration registers (GPIO modes, peripheral settings) or verify them.
- Detect and recover from communication errors (I2C bus recovery, re-initialising peripherals), and use CRCs on data.
- Brown-out reset enabled; log reset causes to diagnose field issues.

### What is signal integrity and what causes ringing? {H}
**Short answer:** Signal integrity is about whether a digital signal arrives at the receiver with clean edges and correct levels and timing. **Ringing** — overshoot and oscillation after an edge — happens when a fast edge travels along a trace that behaves as a transmission line whose impedance is not matched at the ends, so energy reflects back and forth; it can also come from parasitic inductance and capacitance forming a resonant circuit. Problems appear when the **edge rise time** is short compared with the trace's propagation delay (roughly when the trace length exceeds about 1/6 of the distance the edge travels during its rise time), regardless of the clock frequency.

**Rule of thumb:** signals travel about 15 cm/ns on FR-4. An edge with a 1 ns rise time "sees" any trace longer than a few cm as a transmission line. Modern MCU GPIOs with fast slew settings have sub-ns edges even when toggled at only 1 MHz.

**Fixes**

| Problem | Fix |
|---|---|
| Reflections on point-to-point lines (SPI clock, SDRAM) | series termination resistor (22–33 Ω) near the driver, matching driver impedance to the trace impedance |
| Unnecessary fast edges | reduce GPIO slew rate/speed setting |
| Long buses (CAN, RS-485) | parallel termination at both ends matching the cable impedance (120 Ω) |
| High-speed interfaces (USB, Ethernet, DDR, MIPI) | controlled-impedance traces (50 Ω single-ended, 90–100 Ω differential), length matching, continuous reference planes |
| Crosstalk | spacing (3× trace width), ground between sensitive traces, avoid long parallel runs |
| Ground bounce | good decoupling, solid ground plane, short return paths |

**Measuring:** use an oscilloscope with enough bandwidth (5× the signal's knee frequency ≈ 0.35 / rise time) and a short ground connection on the probe (the long ground clip adds inductance and creates fake ringing).

**Firmware-visible symptoms:** double-clocked SPI data (ringing on SCLK crosses the threshold twice), random bit errors at high clock rates that disappear at lower rates, and EMI test failures.

### How do you design firmware and hardware for low power? {M}
**Short answer:** Average current is what drains the battery, so minimise the time spent awake and the current in each state: run fast and sleep (race to idle), use the deepest sleep mode that still meets wake-up latency and retention needs, switch off unused peripherals, clocks and external components, avoid polling, wake on interrupts or low-power timers, configure every GPIO (no floating inputs, no pull-ups fighting outputs), and measure the real current profile with a power analyser.

**MCU power modes (typical Cortex-M)**

| Mode | CPU | Clocks | RAM | Typical current | Wake-up |
|---|---|---|---|---|---|
| Run | on | all | yes | 50–200 µA/MHz | – |
| Sleep (WFI) | stopped | peripherals on | yes | ~30–50% of run | any interrupt, µs |
| Stop / deep sleep | stopped | high-speed clocks off, LSE/RTC on | yes | 1–10 µA | RTC, EXTI, LP UART, ~5–50 µs |
| Standby / shutdown | off | RTC only | lost (except backup) | 0.03–1 µA | reset-like boot, ms |

**Checklist**

1. Power budget: list every state, its current and time; compute the average and battery life.
2. Clock tree: lower frequencies or voltage scaling for steady work; gate clocks of unused peripherals.
3. Peripherals with DMA and low-power features (LPUART wake on character, ADC triggered by a low-power timer, comparator wake-up).
4. RTOS tickless idle to avoid periodic wake-ups.
5. External components: power-gate sensors with a load switch; check regulator quiescent current, pull-up currents, LED indicators, voltage dividers (switch them off between measurements).
6. Radio: batch transmissions, use long connection intervals (BLE), sleep the radio.
7. Debug: the debugger keeps clocks running in sleep modes (disable DBGMCU low-power debug bits in production), and leaky GPIOs often account for the "missing" microamps.

**Measuring:** Nordic PPK2, Joulescope, Otii, or a shunt resistor with an oscilloscope; look at both the average and the peaks (battery internal resistance limits peak current, especially for coin cells).

### How do you read a datasheet efficiently? {E}
**Short answer:** Start with the **front page** (key features, operating range) and the **block diagram**, then the **pin description** and **absolute maximum ratings** (never exceed) vs **recommended operating conditions** (where specifications apply). Read the **electrical characteristics** for the parameters you depend on (min/max, not typical), the **timing diagrams** for the interface you use, the **register map** and the **application circuit/layout guidelines**. Finally, always check the **errata** document for silicon bugs.

**What to extract for firmware work**

| Section | Look for |
|---|---|
| Interface timing | SPI mode and max clock, I2C address and clock stretching, setup/hold times, CS timing |
| Power-up sequence | supply ramp, reset timing, delays before the first command, power-on default register values |
| Register map | reset values, reserved bits (write as read or 0), read-to-clear or write-1-to-clear flags |
| Electrical characteristics | V_IH/V_IL, output drive, supply current in each mode, ADC accuracy |
| Conversion/start-up times | how long to wait before data is valid |
| Application notes | recommended configuration sequences, typical pitfalls |
| Errata | workarounds that firmware must implement |

**Typical vs min/max:** design for the worst case (min/max over temperature and voltage); "typical" values are what you measure on the bench at 25 °C.

**MCU documentation set:** the **datasheet** (pins, electrical specs, package), the **reference manual** (peripherals and registers), the **programming manual** (CPU core, instructions) and the **errata sheet** — you need all four.

### How do you read a schematic as a firmware engineer? {E}
**Short answer:** Find the MCU and trace from each of its pins to what they connect to: which peripherals use which pins (and therefore which alternate functions to configure), pull-up and pull-down resistors (default states), active-low signals (names with a bar, `n`, `#` or `_N`), power domains and enables, reset and boot-mode circuitry, debug connectors, clock sources and any level shifters. Use net names to follow signals across sheets, and keep a pin-mapping table that becomes your board configuration (device tree, pin mux files, CubeMX configuration).

**Checklist when bringing up firmware on a new board**

1. Power rails: which regulators exist, which are enabled by GPIOs (and their default state).
2. Clocks: crystal frequency (HSE/LSE values in the clock configuration).
3. Boot pins and reset: how the board selects boot mode; reset button; watchdog chips.
4. Debug: SWD/JTAG pins, UART console pins and levels.
5. Each peripheral: bus, address (I2C address pins), chip select, interrupt pin (and its polarity, open-drain or push-pull), reset pin, power enable.
6. LEDs and buttons: polarity (active high/low).
7. Analog: dividers (scaling factors for ADC conversion), reference voltage, filters.
8. Protection and level shifting that may limit speed.

**Symbols to recognise:** resistors, capacitors (polarised vs ceramic), inductors/ferrites, diodes (LED, Zener, Schottky, TVS), MOSFETs/BJTs, crystals, test points, net labels and no-connect markers.

**Collaboration tip:** review schematics before layout and ask for test points on key signals, a UART console, SWD, a few spare GPIOs and LEDs; it saves weeks during bring-up.

### What tools do you use for board bring-up? {E}
**Short answer:** A **multimeter** (rail voltages, continuity, current), a **bench power supply** with current limiting (catch shorts before they burn parts), an **oscilloscope** (analog behaviour: clocks, power ripple, edges, reset timing), a **logic analyser** (decoding SPI/I2C/UART/CAN over long captures), a **debug probe** (J-Link, ST-LINK, CMSIS-DAP via SWD/JTAG for flashing and debugging), a **USB-UART adapter** for the console, and sometimes a thermal camera (hot spots from shorts or wrong components).

**Typical bring-up order**

1. Visual inspection (orientation, solder bridges), then check rails for shorts with power off (resistance to ground).
2. Power up with current limiting; measure every rail and check current draw against expectations.
3. Check the crystal/oscillator with a scope and reset lines (MCU out of reset?).
4. Connect the debug probe: read the device ID (`JLinkExe`, `openocd`), erase and flash a minimal program.
5. Blink an LED, then bring up the UART console for logging.
6. Configure the clock tree to full speed and verify with MCO (clock output pin) on the scope.
7. Bring up each peripheral one by one: external memory (run a memory test), I2C scan, SPI device ID reads, then higher-level functions.
8. Measure power in each mode, then run stress and temperature tests.

**Useful habits:** keep a bring-up log, compare against a known-good board or evaluation kit, write small test firmware for each interface, and verify assumptions with measurements rather than with the schematic alone.
