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
An ADC converts an analog input into a numerical code. A SAR ADC, common in MCUs, samples the voltage and performs successive comparisons against an internal DAC.

#### 1. Resolution
A 12-bit ADC provides 4096 codes. With a 3.3 V reference, one ideal LSB is approximately 0.806 mV. A 1.65 V input maps near code 2048.

#### 2. Sampling
The sampling capacitor must settle through the source impedance before conversion. Excessively short acquisition time produces errors, especially with high-impedance sensors.

#### 3. Firmware example
```c
float voltage = raw * (3.3f / 4096.0f);
```
This estimates voltage using ideal code bins; use the datasheet transfer function and calibration for accuracy.

**Interview takeaway:** Resolution is not accuracy. Reference tolerance, noise, offset, gain error and effective number of bits matter. Timer-triggered ADC with DMA is useful for periodic acquisition.

### What is the Nyquist theorem and what is aliasing? {E}
The Nyquist sampling condition requires a sampling rate greater than twice the highest frequency in a band-limited baseband signal for ideal reconstruction.

#### Example
A 1 kHz sine sampled at 1.5 kHz appears as a 500 Hz component because the sampled sequence cannot distinguish those frequencies.

```text
Analog signal -> anti-alias filter -> ADC -> digital processing
```

Real filters have finite roll-off, so sampling is usually higher than the theoretical minimum and analog frequencies above the usable band are attenuated before conversion.

**Interview takeaway:** Increasing digital filtering after sampling cannot undo aliasing that already occurred at the ADC.

### What is a low-pass RC filter and how do you find its cut-off frequency? {E}
A first-order RC low-pass filter passes low frequencies and attenuates high frequencies. Its cutoff is fc = 1/(2πRC).

```text
Vin --- R ---+--- Vout
             |
             C
             |
            GND
```

#### Example
R = 10 kΩ and C = 100 nF produce a 1 ms time constant and cutoff of approximately 159 Hz. At cutoff the amplitude is about 70.7% of the low-frequency amplitude (−3 dB). The asymptotic attenuation above cutoff is 20 dB per decade.

**Interview takeaway:** Consider ADC input impedance and acquisition time when choosing the resistor; loading changes the ideal response.

### What is a DAC, and how can you generate an analog voltage with PWM? {E}
A DAC converts a digital value into an analog voltage or current. An MCU without a DAC can approximate an analog output using filtered PWM.

```text
PWM GPIO -> RC low-pass filter -> buffer/load
```

For a 0–3.3 V ideal PWM signal, the average is 3.3 × duty cycle. At 25% duty, the average is 0.825 V.

#### Trade-offs
Higher PWM frequency and a lower filter cutoff reduce ripple, but the filter slows response. Timer resolution also limits available duty steps. A high-impedance load or buffer avoids changing the filter characteristics.

**Interview takeaway:** Unfiltered PWM is a digital pulse train, not a true analog voltage. A dedicated DAC may offer lower ripple and better settling behavior.

### What is the difference between a crystal and an RC oscillator? {E}
An RC oscillator derives frequency from resistance and capacitance; a crystal oscillator uses quartz mechanical resonance.

| RC | Crystal |
|---|---|
| Inexpensive, often internal | Generally higher accuracy |
| Fast startup possible | Usually longer startup |
| More temperature and voltage drift | Requires correct load network |

#### Example
An internal RC clock may be adequate for blinking an LED. An accurate RTC or a UART with a tight clock-error budget may require a calibrated oscillator or crystal.

**Interview takeaway:** Choose by frequency tolerance, startup time, power and jitter. A PLL does not eliminate reference frequency error.

### What is a MOSFET and how do you use one to switch a load? {M}
A MOSFET is a voltage-controlled transistor used to switch loads. An N-channel MOSFET is convenient as a low-side switch.

```text
Supply --- Load --- Drain
                     MOSFET
MCU -- Rg -- Gate    Source --- GND
             |
            Rpd
             |
            GND
```

Select a logic-level device with RDS(on) specified at the actual gate voltage, adequate voltage/current ratings and thermal margin. The pull-down keeps it off during reset.

At 1 A and RDS(on) = 50 mΩ, conduction loss is 50 mW, excluding switching losses.

**Interview takeaway:** Gate threshold is not the full-enhancement voltage. Inductive loads require an appropriate flyback or clamp path.

### What is a flyback diode and why is it needed? {E}
An inductor opposes a sudden change in current. Opening a relay-coil switch can produce a high voltage and damage the driver. Connect a flyback diode across the coil, cathode to supply and anode to the low-side switch.

```text
+V ----- Coil -----+---- switch ---- GND
 |                 |
 +-----|<|---------+
     flyback diode
```

During normal operation the diode is reverse-biased. When the switch opens, coil current circulates through the diode.

**Interview takeaway:** A simple diode limits voltage but slows relay release. A suitably designed TVS clamp can speed turn-off within the switch ratings.

### What is ESD and how do you protect a board? {M}
Electrostatic discharge (ESD) is a brief transfer of stored charge that can damage semiconductor inputs or cause resets.

#### Hardware protection
Use suitable TVS diodes near external connectors, short return paths, controlled grounding and appropriate series resistance or filtering. Handle assemblies using grounded ESD-safe equipment.

#### Firmware resilience
Watchdog recovery, reset-cause logs and retries can help with transient disturbances, but cannot substitute for electrical protection.

**Interview takeaway:** Component-level ESD ratings are different from finished-product immunity tests. Verify protection on the actual assembly.

### What is signal integrity and what causes ringing? {H}
Signal integrity means preserving valid waveforms and timing. Fast edges on PCB traces and cables can behave as transmission-line events even at low clock frequencies.

#### Ringing
Impedance discontinuities reflect traveling edges. Reflections and parasitic capacitance/inductance cause overshoot, undershoot and repeated threshold crossings.

#### Debugging
Use a suitable scope probe with short ground connection. Compare source and receiver waveforms. Inspect return paths, stubs, drive strength and termination. A source-series resistor can reduce SPI clock ringing when chosen for the actual trace and driver impedance.

**Interview takeaway:** Edge rate and electrical length matter more than clock frequency alone.

### How do you design firmware and hardware for low power? {M}
Low-power design minimizes energy over the complete duty cycle.

#### Firmware
Use interrupts and DMA instead of busy polling, clock-gate unused peripherals, batch work, configure wake sources and restore peripheral state correctly after sleep.

#### Hardware
Choose low-quiescent-current regulators, avoid leakage through unpowered peripherals, switch sensors off when possible and minimize unnecessary pull-resistor current.

#### Example
10 mA for 10 ms per second plus 10 µA for 990 ms gives an average of about 110 µA, ignoring transition overhead.

**Interview takeaway:** Measure the current waveform across active, sleep and wake states; account for transition energy and worst-case conditions.

### How do you read a datasheet efficiently? {E}
Read the exact part's datasheet and errata with a specific question in mind.

1. Identify revision, package and operating conditions.
2. Separate absolute maximum ratings from recommended conditions.
3. Locate pinout, power sequencing, interface timing and electrical characteristics.
4. Find register descriptions, reset values and interrupt behavior.
5. Check errata and initialization examples.

For an I²C sensor, verify address straps, power-up delay, supported bus rate, identification register and repeated-START requirements.

**Interview takeaway:** Use the reference manual for register programming and the errata for hardware limitations. Never guess register meanings.

### How do you read a schematic as a firmware engineer? {E}
A schematic maps firmware configuration to real electrical connectivity.

#### Workflow
Start at power rails and reset. Follow net names to MCU pins, pull resistors, address straps, interrupt polarity, enables, clocks and level translators.

#### Example
For an I²C device, identify the actual SCL/SDA controller, pull-up voltage, address pins, reset and power-enable GPIOs. Configure pinmux and device-tree resources to match.

**Interview takeaway:** Correct driver code can still fail when the board uses a different bus, voltage domain, polarity or reset sequence.

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
