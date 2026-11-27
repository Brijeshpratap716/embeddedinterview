---
slug: communication-protocols
title: Communication Protocols
icon: 📡
level: Intermediate
order: 7
desc: UART, RS-232/RS-485, SPI, I2C, I3C, I2S, CAN, CAN FD, LIN, USB, Modbus, Ethernet, TCP/UDP, MQTT, BLE and wireless IoT. Frames, timing, arbitration, error handling and how to choose.
---
You will almost certainly be asked to compare UART, SPI and I2C, then pushed on one of them in detail. Automotive roles add CAN and LIN; Linux roles add USB and Ethernet; IoT roles add MQTT and wireless. Each answer gives the short version first, then the details and the follow-ups interviewers ask.

### Compare UART, SPI and I2C. {E}
UART, SPI and I2C are serial communication interfaces widely used to connect microcontrollers to sensors, displays, memory and other devices.

| Feature | UART | SPI | I2C |
|---|---|---|---|
| Clock | Asynchronous | Shared SCLK | Shared SCL |
| Signals | TX, RX | SCLK, MOSI, MISO, CS | SDA, SCL |
| Addressing | Not inherent | Chip-select signal | Device address |
| Duplex | Usually full | Usually full in standard four-wire form | Shared bidirectional data |
| Typical use | Console, serial modules | Flash, displays, fast ADC | Sensors, configuration |

#### 1. Wiring example

```text
UART: MCU TX --> device RX
      MCU RX <-- device TX

SPI:  MCU SCLK, MOSI, CS --> target
      MCU MISO          <-- target

I2C:  controller and targets share SDA and SCL
      both lines have pull-ups
```

A common ground and compatible voltage levels are also required.

#### 2. Practical selection

Use UART for an asynchronous debug console, SPI for high-throughput flash or display transfers, and I2C when multiple addressed low-speed devices share two signal wires.

**Interview takeaway:** UART needs matching serial settings, SPI needs matching mode and chip select, and I2C needs addressing, pull-ups and transaction acknowledgment. Actual throughput depends on clock rate and protocol overhead.

### How do you choose between UART, SPI and I2C for a project? {M}
Choose a serial interface by considering required throughput, pin count, number of devices, cable length, voltage levels and software complexity.

#### 1. Example design

| Requirement | Suitable starting choice |
|---|---|
| Debug console | UART |
| High-rate display pixel data | SPI or dedicated display interface |
| Several low-rate sensors | I2C |
| Fast serial flash | SPI/QSPI |
| Long noisy industrial cable | UART protocol with suitable transceiver, e.g. RS-485 |

#### 2. Throughput calculation

A UART configured at 115200 baud using 8N1 transfers ten bits per eight-bit data byte, giving at most 11,520 bytes/s before application overhead.

A standard SPI link clocked at 10 MHz transfers up to 1.25 MB/s per data line direction during continuous transfer. I2C at 400 kHz needs address, ACK and transaction overhead, so its application throughput is below the raw clock rate.

#### 3. Other constraints

Check target-supported speeds, electrical timing, bus loading, error handling, controller support and pin availability. I2C address conflicts may need an address strap or mux; SPI may require more chip-select pins.

**Interview takeaway:** Select the interface for the actual payload and hardware constraints, not solely the maximum advertised bit rate.

### What does a UART frame look like? {E}
A UART frame sends one character asynchronously using a start bit, data bits, optional parity and one or more stop bits.

#### 1. Example: 8N1

8 data bits, no parity, 1 stop bit. Standard UART idles high and starts a frame with a low bit. Data is commonly sent least significant bit first.

<div style="max-width:700px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 109" width="100%" role="img" aria-label="8N1 UART frame for 0xA5, start low, data LSB first, stop high">
<path d="M8 26 h27 V61" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M8 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="21.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">Idle</text><path d="M35 61 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M35 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="48.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">Start</text><path d="M62 26 h27 V61" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M62 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="75.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D0</text><path d="M89 61 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M89 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="102.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D1</text><path d="M116 26 h27 V61" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M116 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="129.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D2</text><path d="M143 61 h27 V61" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M143 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="156.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D3</text><path d="M170 61 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M170 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="183.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D4</text><path d="M197 26 h27 V61" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M197 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="210.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D5</text><path d="M224 61 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M224 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="237.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D6</text><path d="M251 26 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M251 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="264.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">D7</text><path d="M278 26 h27 V26" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M278 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="291.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">Stop</text><path d="M305 26 h27" stroke="#3b82f6" stroke-width="2" fill="none"/><path d="M305 20 V69" stroke="currentColor" stroke-opacity=".15"/><text x="318.5" y="84" font-size="9" text-anchor="middle" fill="currentColor">Idle</text><text x="170" y="103" font-size="10" text-anchor="middle" fill="currentColor">One bit period per interval; example 0xA5.</text></svg></div>

#### 2. Bit duration

At 9600 baud, one bit lasts approximately 104.17 microseconds. A ten-bit 8N1 frame lasts about 1.04 ms.

#### 3. Configuration

Both endpoints must agree on baud rate, data length, parity and stop configuration. A UART frame does not provide packet boundaries, addresses or strong error detection; higher-level protocols add these features.

**Interview takeaway:** The start edge synchronizes the receiver for each frame. Baud rate counts transmitted symbols, including framing overhead.

### How does a UART receiver sample bits, and how much baud-rate error is tolerated? {M}
A UART receiver detects the start-bit edge and samples the following bits using its own baud-rate clock. It often oversamples the input to locate bit centers and reject noise.

#### 1. Typical receive sequence

1. Detect a falling edge from idle high.
2. Validate the start bit near its center.
3. Sample successive data bits near their centers.
4. Check parity when enabled and verify the stop bit.

A receiver using 16× oversampling has 16 sampling-clock cycles per nominal bit, but the precise sampling/voting algorithm depends on the UART.

#### 2. Baud mismatch

Without a shared clock, transmitter and receiver timing errors accumulate across the frame. An idealized 8N1 receiver sampling the stop bit near 9.5 bit times has roughly half a bit of margin, giving an order-of-magnitude combined mismatch limit near 5% under ideal assumptions.

Real hardware has start-detection error, oversampling uncertainty, noise and clock tolerance; use the datasheet's specified limit, commonly much tighter than the ideal calculation.

#### 3. Example

At 115200 baud, the nominal bit interval is approximately 8.68 microseconds. A logic analyzer can measure transmitted bit width and compare against the configured rate.

**Interview takeaway:** UART resynchronizes at each start bit. Allowable baud error is a combined transmitter/receiver timing budget, not a universal fixed percentage.

### What are UART framing, parity and overrun errors? {M}
UART hardware reports receive errors when the received frame or software service behavior violates its expectations.

| Error | Meaning | Common cause |
|---|---|---|
| Framing | Expected stop bit not observed correctly | Wrong baud/configuration, noise, break |
| Parity | Received parity disagrees with calculated parity | Bit error, configuration mismatch |
| Overrun | New receive data cannot be stored because prior data was not serviced | ISR latency, FIFO full, slow consumer |

#### 1. Example ISR logic

```c
void uart_irq(void)
{
    uint32_t status = uart_read_status();

    if (status & ERROR_MASK)
        uart_handle_errors(status);

    while (uart_rx_ready())
        rx_push(uart_read_byte());
}
```

This is illustrative: register read/clear order and FIFO behavior depend on the UART. Bound ISR work and handle software-buffer overflow.

#### 2. Debugging

Verify baud, parity and stop-bit settings; inspect TX/RX waveforms; check FIFO interrupt thresholds and handler latency. DMA or a larger receive buffer can reduce service overruns, but does not fix electrical errors.

**Interview takeaway:** Framing and parity indicate receive-format problems; overrun means the receive path failed to keep up. Clear errors using the documented hardware sequence.

### What is hardware flow control? {E}
Hardware flow control prevents a serial transmitter from sending more data than the receiver can accept. UART implementations often use RTS and CTS signals.

#### 1. Concept

Each endpoint communicates receive readiness to the other endpoint. A transmitter checks its CTS input before sending more characters. On many UART peripherals, the receiver's RTS output signals readiness, but naming and polarity depend on the interface.

```text
Device A TX  ---> Device B RX
Device A RX  <--- Device B TX
Device A RTS ---> Device B CTS
Device A CTS <--- Device B RTS
```

#### 2. Why needed

A receiver may have limited FIFO or software-buffer capacity. Deasserting readiness before the buffer fills gives the transmitter time to stop. Bytes already in flight or in a transmission FIFO may still arrive.

#### 3. Alternatives

Software flow control uses in-band control characters such as XON/XOFF, which may require escaping for binary payloads. Application-level acknowledgments or credit-based protocols can provide additional flow control.

**Interview takeaway:** Flow control prevents overflow by coordinating sender and receiver, not by increasing UART speed. Configure signal polarity and account for in-flight bytes.

### How does RS-232 differ from RS-485 and TTL UART? {M}
UART describes asynchronous serial framing. TTL/CMOS UART, RS-232 and RS-485 describe different electrical signaling arrangements that can carry UART-framed data.

| Interface | Electrical signaling | Typical topology |
|---|---|---|
| MCU UART | Single-ended logic-level signals | Short board-level link |
| RS-232 | Bipolar single-ended signaling | Point-to-point |
| RS-485 | Differential signaling | Multipoint bus possible |

#### 1. Hardware example

```text
MCU UART TX/RX --> RS-485 transceiver --> twisted pair
                       |
                  DE / RE control
```

A half-duplex RS-485 transceiver may require driver-enable timing: enable before transmitting and release only after the final bit has completed.

#### 2. Electrical caution

Do not connect an RS-232 signal directly to a 3.3 V MCU pin. Use a suitable transceiver. For RS-485, termination and biasing must match the bus topology and transceiver requirements.

#### 3. Protocol distinction

RS-485 does not define application addressing or error checking. Modbus RTU is a common higher-level protocol carried over it.

**Interview takeaway:** UART is the framing mechanism; RS-232 and RS-485 are electrical standards. Choose the transceiver and topology separately from the serial protocol.

### What are the SPI modes (CPOL and CPHA)? {M}
SPI has four clock modes determined by clock polarity (CPOL) and clock phase (CPHA).

#### 1. Mode table

| Mode | CPOL | CPHA | Idle SCLK | Sample edge |
|---|---:|---:|---|---|
| 0 | 0 | 0 | Low | Rising |
| 1 | 0 | 1 | Low | Falling |
| 2 | 1 | 0 | High | Falling |
| 3 | 1 | 1 | High | Rising |

CPHA = 0 samples on the first active edge; CPHA = 1 samples on the second edge. Data is normally shifted on the opposite edge.

#### 2. Mode 0 timing

```text
CS   ----\__________________/----
SCLK _____/‾\_/‾\_/‾\_/‾\_____
          ^   ^   ^   ^
          sample rising edges
```

The first data bit must be valid before the first sampling edge. Setup and hold times must satisfy the target datasheet.

#### 3. Debugging wrong mode

A wrong CPHA may cause bit shifts or unstable samples. Wrong CPOL changes idle level and edge interpretation. Capture CS, SCLK and data with a logic analyzer and compare to the target timing diagram.

**Interview takeaway:** Configure both endpoints for the same SPI mode. CPOL defines idle level; CPHA defines which edge samples data.

### How do you choose and configure the SPI clock? {M}
The SPI controller generates SCLK. Its frequency must remain within both controller and target timing limits, including board-level signal integrity.

#### 1. Clock divider example

If a controller has a 48 MHz input clock and supported divisors 2, 4, 8, 16, and the target permits at most 10 MHz, divisor 8 gives 6 MHz. Divisor 4 gives 12 MHz and exceeds the target limit.

The formula and allowed divisors are controller-specific.

#### 2. Configuration procedure

Select CPOL/CPHA, bit order, word width, maximum frequency and chip-select timing from the target datasheet. Configure clocks and pins, then verify the actual signal on hardware.

#### 3. Linux SPI example

```c
spi->max_speed_hz = 6000000;
spi->mode = SPI_MODE_0;
spi->bits_per_word = 8;

ret = spi_setup(spi);
```

This illustrates a Linux SPI client configuration fragment. Respect board/firmware constraints and check the return value. The controller may choose a lower attainable clock.

#### 4. Troubleshooting

Start at a conservative frequency, verify commands and responses, then increase speed within limits. Check setup/hold time, CS gaps, ringing and cable/trace loading.

**Interview takeaway:** Maximum SPI clock is a hardware timing limit, not a guarantee of reliable communication. Configure and measure the real clock.

### How do you connect multiple SPI devices? {E}
**Short answer:** Usually with **independent chip selects**: all devices share SCLK, MOSI and MISO, and each has its own CS line; only the selected device drives MISO, the others keep it high-impedance. Alternatively, **daisy-chain** devices that support it: each device's data output feeds the next device's input and they share one CS, so data shifts through the chain like one long shift register.

```
Independent chip selects               Daisy chain
MCU SCLK ─┬─────┬─────┬                MCU MOSI → [Dev1] → [Dev2] → [Dev3] → MCU MISO
MCU MOSI ─┼──┬──┼──┬──┼──┬             shared SCLK and one CS
MCU MISO ─┼──┼──┼──┼──┼──┼
CS0 ──────┘  │  │  │  │  │   Dev0
CS1 ─────────┼──┘  │  │  │   Dev1
CS2 ─────────┼─────┘  ...
```

**Independent CS details**

- MISO must be tri-stated by every deselected device; some devices do not do this properly (check the datasheet or add a buffer).
- Different devices may need different SPI modes and speeds: reconfigure the peripheral before each transaction, and on a shared bus with an RTOS, protect it with a mutex.
- Put pull-ups on CS lines so devices stay deselected while the MCU is in reset.
- Running out of CS pins: use a GPIO expander, a 3-to-8 decoder (74HC138), or a demultiplexer.

**Daisy chain details**

- Common with shift registers (74HC595), LED drivers and some ADCs/DACs.
- To update N devices you clock out N frames, last device first, then raise CS to latch all of them together.

**On Linux:** each device on the bus has its own `reg` (chip select number) under the SPI controller in the device tree; the SPI core handles CS and mode per device.

### What are Dual, Quad and Octal SPI? {M}
**Short answer:** They are SPI extensions that transfer 2, 4 or 8 bits per clock using bidirectional data lines (IO0–IO7) instead of a single MOSI/MISO pair, multiplying throughput. Quad SPI (QSPI) NOR flash is the standard way to add external code and data storage to MCUs, and many controllers support **execute-in-place (XIP)**, mapping the flash into the address space so the CPU can run code directly from it. Octal SPI and HyperBus reach hundreds of MB/s for external RAM and frame buffers.

| Variant | Data lines | Example throughput |
|---|---|---|
| Single SPI | 1 out + 1 in | 50 MHz → ~6 MB/s |
| Dual | 2 (half duplex) | ~12 MB/s |
| Quad (QSPI) | 4 | 133 MHz → ~66 MB/s |
| Octal (OSPI, DDR) | 8, both edges | 200 MHz DDR → ~400 MB/s |

**How a quad read works:** the command byte may be sent on one line (1-1-4 mode) or all four (4-4-4), followed by the address, dummy cycles (for the flash to fetch data), then data on four lines. The `x-y-z` notation means lines used for command-address-data.

**Memory-mapped mode / XIP:** the controller automatically issues read commands when the CPU accesses the mapped address range. Combined with a cache (Cortex-M7) this gives reasonable performance for code and graphics assets.

**Design considerations**

- Use the controller's memory-mapped mode for reads; writes and erases still go through command mode, and you cannot execute from the flash while it is being erased/programmed (run that code from RAM).
- Some flash chips need the **QE (quad enable)** bit set in a status register before quad modes work.
- Signal integrity at 100+ MHz needs short, matched traces.
- Bootloaders must configure the QSPI controller before jumping to code in external flash.
- Encrypted XIP (on-the-fly decryption, e.g. NXP BEE/OTFAD, ST OTFDEC) protects firmware stored externally.

### What does an I2C transaction look like? {E}
**Short answer:** **START** (SDA falls while SCL is high), then an **address byte** (7-bit address plus a R/W bit: 0 = write, 1 = read), then an **ACK** from the addressed target (it pulls SDA low on the 9th clock), then **data bytes**, each followed by ACK or NACK, then **STOP** (SDA rises while SCL is high). To read a register, write the register address, then send a **repeated START** with the read bit and read the data, with the controller NACKing the last byte.

```
Write register 0x10 = 0xAB on device 0x48:
S | 0x48<<1|W | A | 0x10 | A | 0xAB | A | P

Read 2 bytes from register 0x00:
S | 0x48<<1|W | A | 0x00 | A | Sr | 0x48<<1|R | A | data0 | A | data1 | N | P
(S = START, Sr = repeated START, A = ACK, N = NACK, P = STOP)
```

**Rules**

- SDA may only change while SCL is low; a change while SCL is high is a START or STOP.
- Data is sent MSB first.
- The receiver ACKs each byte: the target during writes, the controller during reads (and NACKs the last byte to tell the target to stop driving SDA).
- A NACK after the address means no device answered (wrong address, device missing or busy, e.g. an EEPROM during its internal write cycle).

**Common bugs**

- Using 8-bit "address" values from a datasheet that already include the R/W bit (e.g. 0x90/0x91 for device 0x48). The 7-bit address is the 8-bit one shifted right by one.
- Sending STOP between the register address and the read: many devices then forget the register pointer or start a new transaction differently.
- Not handling NACK and continuing as if the write succeeded.

**Tools:** `i2cdetect -y 1` (scan the bus on Linux), `i2cget`/`i2cset`/`i2ctransfer`, and a logic analyser with an I2C decoder.

### Why does I2C need pull-up resistors, and how do you size them? {M}
**Short answer:** Both I2C lines are **open-drain**: devices can only pull them low, so resistors pull them high when nobody drives them. A smaller resistor gives faster rising edges but more current when the line is low; a larger resistor saves current but makes edges too slow for the speed mode. Size it between `Rmin = (VDD − VOL(max)) / IOL` and `Rmax ≈ t_r / (0.8473 × Cbus)`.

**Formulas (from the I2C specification)**

- `Rp(min) = (VDD − 0.4 V) / 3 mA` for standard/fast mode (devices must sink 3 mA at 0.4 V).
- `Rp(max) = t_r / (0.8473 × C_b)`, where `t_r` is the maximum rise time (1000 ns at 100 kHz, 300 ns at 400 kHz, 120 ns at 1 MHz Fast-mode Plus) and `C_b` the total bus capacitance (≤ 400 pF).

**Worked example (3.3 V, 400 kHz, 100 pF bus)**

- Rp(min) = (3.3 − 0.4) / 0.003 ≈ 967 Ω
- Rp(max) = 300 ns / (0.8473 × 100 pF) ≈ 3.5 kΩ
- Choose **2.2 kΩ** (common for 400 kHz). At 100 kHz with the same bus, Rp(max) ≈ 11.8 kΩ, so 4.7 kΩ or 10 kΩ work.

**Practical notes**

- Each device's input adds capacitance (≈ 5–10 pF), plus traces and connectors; long cables need lower resistor values, bus buffers (PCA9515) or differential extenders.
- Only **one set** of pull-ups per bus segment; many breakout boards each add their own, and too many in parallel make the value too small.
- Internal MCU pull-ups (20–50 kΩ) are too weak for anything but very slow, short buses.
- Mixed voltages (3.3 V and 5 V devices) need a level shifter (e.g. a MOSFET-based bidirectional shifter).
- The `0.8473` factor comes from the time to rise from 30% to 70% of VDD in an RC circuit: `t = RC × ln(0.7/0.3)`.

### What is clock stretching? {M}
**Short answer:** Clock stretching is when a target device holds SCL low after the controller releases it, to tell the controller to wait until it is ready (for example while it finishes a measurement or prepares data). Because SCL is open-drain, the controller sees that SCL has not gone high and must wait before continuing. Every I2C controller must support it, but some implementations handle it badly.

**When targets stretch**

- After receiving a byte, while processing it (slow MCUs acting as I2C targets).
- Before sending read data that is not ready yet (some sensors during conversion, e.g. certain humidity sensors in "hold master" mode).
- On a bit level, for slow devices (rare).

**Problems seen in practice**

- Some controllers (notably older Raspberry Pi BCM2835 I2C hardware) do not handle stretching correctly in some phases, which corrupts transfers with stretching devices; workarounds are a software (bit-banged) I2C driver or devices configured not to stretch.
- A target that stretches forever (crashed firmware) hangs the bus; controllers should have a **timeout** (SMBus defines 25–35 ms) and use bus recovery.
- When designing an MCU as an I2C target, prefer hardware that stretches automatically while firmware handles each byte, but keep the stretch short.

**Related:** **clock synchronisation** between multiple controllers uses the same wired-AND property: the SCL low period is determined by the device holding it low the longest.

### How does I2C arbitration work with multiple controllers? {H}
**Short answer:** Every controller monitors SDA while it transmits. Because the bus is wired-AND (any device pulling low wins), a 0 overrides a 1. If a controller sends a 1 (releases SDA) but reads back a 0, another controller is sending a 0; it has **lost arbitration** and must stop transmitting immediately, switching to receive mode if needed. Arbitration continues bit by bit through the address and data, so the winner's message is not corrupted.

**Example: two controllers start at the same time**

```
Controller A sends address 0x50: 1 0 1 0 0 0 0
Controller B sends address 0x48: 1 0 0 ...
                                     ↑ A sends 1 (releases), B sends 0 (pulls low)
                                       A reads 0 ≠ 1 → A loses, stops; B continues
```

The lower address wins at the first differing bit; if both address the same device, arbitration continues into the data bytes.

**Clock synchronisation:** both controllers drive SCL; because it is wired-AND, SCL is low while either holds it low, so the combined clock has the longest low period and the shortest high period of the two. Both then stay in step bit by bit.

**What the losing controller does:** sets an "arbitration lost" flag (raises an interrupt) and retries after the bus becomes free (after STOP). Firmware must handle this, not treat it as a fatal error.

**Practical note:** true multi-controller I2C is relatively rare and tricky (some controllers have bugs in arbitration handling). Many systems with two processors use one controller and make the other a target, or use a separate bus.

**Compare with CAN:** CAN uses the same principle (dominant bit wins, lowest ID wins), but CAN is designed for multi-controller from the start.

### How do you recover a stuck I2C bus? {M}
**Short answer:** If a target was reset or interrupted in the middle of a read, it may still be holding SDA low, waiting to send the rest of a byte; the controller then cannot generate a START. To recover: switch SCL to GPIO open-drain mode, toggle SCL up to 9 times until the target releases SDA (it finishes its byte and sees a NACK because SDA is high on the 9th clock), generate a STOP condition manually, then return the pins to I2C mode and reset the I2C peripheral.

```c
#include <stdbool.h>

void scl_set(int level); void sda_set(int level); int sda_get(void); void delay_us(unsigned us);

bool i2c_bus_recover(void)                /* pins temporarily configured as open-drain GPIO */
{
    sda_set(1);
    for (int i = 0; i < 9 && !sda_get(); i++) {
        scl_set(0); delay_us(5);
        scl_set(1); delay_us(5);
    }
    if (!sda_get()) return false;         /* still stuck: power-cycle the device if possible */
    sda_set(0); delay_us(5);              /* generate STOP: SDA low → high while SCL high */
    scl_set(1); delay_us(5);
    sda_set(1); delay_us(5);
    return true;                          /* now re-init the I2C peripheral */
}
```

**Other causes of a stuck bus**

- **SCL held low** by a crashed target (clock stretching forever): clocking does not help; reset or power-cycle the device (a GPIO-controlled reset line or power switch on the board is good design practice).
- **Controller peripheral in a bad state** after a glitch: reset the peripheral (many MCUs have errata requiring this).
- **Missing or wrong pull-ups**, shorted lines, or a device powered off that clamps the lines through its protection diodes.

**Prevention:** use timeouts on every I2C wait, call bus recovery on timeout, and design hardware so devices can be reset. The Linux kernel provides `i2c_recover_bus()` with GPIO-based recovery described in the device tree (`scl-gpios`, `sda-gpios`).

### What is the difference between 7-bit and 10-bit I2C addressing? {E}
**Short answer:** 7-bit addressing gives 128 addresses, of which 16 are reserved, so 112 are usable; it is used by almost all devices. 10-bit addressing sends a first byte `11110xx` + R/W (where `xx` are the two high address bits) followed by a second byte with the low 8 bits, giving 1024 addresses; 10-bit devices are rare.

**Reserved 7-bit addresses**

| Address | Use |
|---|---|
| 0x00 | general call / START byte |
| 0x01 | CBUS |
| 0x02 | other bus formats |
| 0x03 | future use |
| 0x04–0x07 | Hs-mode controller code |
| 0x78–0x7B | 10-bit addressing prefix |
| 0x7C–0x7F | device ID / future use |

**Address conflicts between identical devices**

- Address-select pins (A0, A1…) let you choose among a few addresses (e.g. 4 options for many sensors).
- An **I2C multiplexer/switch** (TCA9548A) puts devices on separate downstream channels.
- A second I2C peripheral on the MCU.
- Some devices allow the address to be reprogrammed.

**7-bit vs 8-bit confusion:** datasheets sometimes give an "8-bit address" that includes the R/W bit, e.g. 0x90 (write) / 0x91 (read) for device 0x48. Most software APIs (Linux, Zephyr, most HALs except STM32 HAL, which expects the shifted value) take the 7-bit address.

### What is SMBus, and what is I3C? {M}
**Short answer:** **SMBus** (System Management Bus) is a stricter variant of I2C used for system management (batteries, power supplies, temperature monitors on PC and server boards): it defines voltage levels, a 25–35 ms clock-low timeout, a minimum 10 kHz clock, optional Packet Error Checking (a CRC-8 byte), standard command formats and an alert line. **I3C** (MIPI Improved Inter-Integrated Circuit) is the modern successor to I2C: push-pull signalling at up to 12.5 MHz (more in HDR modes), dynamic address assignment, in-band interrupts, and backward compatibility with many I2C targets on the same bus.

**SMBus details**

- Timeout means a stuck device cannot hold the bus forever (unlike plain I2C).
- Defined transactions: Quick Command, Send/Receive Byte, Read/Write Byte/Word, Block Read/Write, Process Call.
- **PEC:** CRC-8 (polynomial x⁸ + x² + x + 1) over the whole transaction including addresses.
- **SMBALERT#:** a shared interrupt line plus the Alert Response Address (0x0C) to find which device raised it.
- **PMBus** builds on SMBus for power supply control.
- Linux: `i2c_smbus_read_byte_data()` etc.

**I3C advantages over I2C**

| | I2C | I3C |
|---|---|---|
| Speed | up to 1 MHz (3.4 MHz HS) | 12.5 MHz SDR, ~25–33 Mbps with HDR modes |
| Signalling | open-drain (slow rising edges, power in pull-ups) | push-pull for data (open-drain only during arbitration) |
| Addressing | static, set by pins | dynamic address assignment, plus 48-bit provisioned IDs |
| Interrupts | separate GPIO per device | in-band interrupts on the bus |
| Power | pull-up current | lower |

I3C is used for new sensors in phones and wearables, and for DDR5 memory module management (SPD hubs).

### What is I2S, and how is it different from I2C? {E}
**Short answer:** I2S (Inter-IC Sound) is a synchronous serial bus for **digital audio** between processors, codecs, DACs, ADCs and digital microphones. Despite the similar name, it has nothing to do with I2C: it has a bit clock (**BCLK/SCK**), a word-select or frame clock (**LRCLK/WS**, which selects left or right channel and runs at the sample rate), and one or more data lines (**SD**), plus often a master clock (**MCLK**) for the codec. It streams audio continuously at a fixed sample rate.

**Clock relationships**

```
LRCLK (WS) = sample rate, e.g. 48 kHz
BCLK = sample rate × channels × bits per slot, e.g. 48 kHz × 2 × 32 = 3.072 MHz
MCLK often = 256 × sample rate = 12.288 MHz
```

**Formats:** standard I2S (data delayed by one BCLK after the LRCLK edge, MSB first), left-justified, right-justified, and **TDM** (more than two channels in one frame: multi-mic arrays, multi-channel codecs). PDM is a different 1-bit format used by many MEMS microphones.

**Embedded implementation**

- Use DMA with double (ping-pong) buffers: the I2S peripheral streams samples continuously, and the CPU processes one buffer while DMA fills or empties the other.
- Underrun/overrun causes audible clicks: size buffers for worst-case processing latency.
- Clock accuracy matters: 44.1 kHz and 48 kHz families need different PLL settings; small mismatches between devices cause drift over time (asynchronous sample-rate conversion or clock recovery for USB audio).

**Linux:** ALSA SoC (ASoC) with CPU DAI, codec and machine drivers described in the device tree.

### How does a CAN frame look? {M}
**Short answer:** A classic CAN (2.0A) data frame is: **SOF** (one dominant bit), the **arbitration field** (11-bit identifier + RTR bit; 29-bit identifier in 2.0B extended frames), the **control field** (IDE, reserved bit, 4-bit DLC giving 0–8 data bytes), the **data field** (0–8 bytes), a **15-bit CRC** + delimiter, the **ACK slot** + delimiter, and **EOF** (7 recessive bits), followed by a 3-bit intermission.

```
| SOF | ID (11) | RTR | IDE | r0 | DLC (4) | DATA (0-64 bits) | CRC (15) | CRC del | ACK | ACK del | EOF (7) |
```

**Key points**

- **Dominant (0) vs recessive (1):** a dominant bit from any node overrides recessive bits.
- **ACK slot:** the transmitter sends recessive; **any** node that received the frame correctly drives it dominant. An ACK means "someone received it", not "the intended receiver processed it".
- **Bit stuffing:** after five identical consecutive bits, the transmitter inserts one bit of opposite value (from SOF through CRC), giving enough edges for receivers to stay synchronised; receivers remove stuff bits. Six identical bits in a row is an error (used deliberately by error frames).
- **Frame types:** data frame, remote frame (RTR = 1, requests data; rarely used and removed in CAN FD), error frame, overload frame.
- **Extended frames (2.0B):** 11-bit base ID + SRR + IDE = 1 + 18-bit extension = 29-bit ID.

**Efficiency:** a frame with 8 data bytes is about 111 bits plus stuff bits (up to ~135), so at 500 kbps a full frame takes ~0.25 ms and the payload efficiency is under 50%.

**On Linux:** SocketCAN (`candump can0`, `cansend can0 123#DEADBEEF`) and `struct can_frame`.

### How does CAN arbitration work? {M}
**Short answer:** CAN is a multi-controller bus with **non-destructive bitwise arbitration**. All nodes that want to send start at the same time and transmit their identifier bit by bit while reading the bus. A dominant bit (0) overwrites a recessive bit (1). A node that sends recessive but reads dominant knows a higher-priority frame is on the bus, stops transmitting immediately and becomes a receiver. The frame with the **lowest identifier wins** and continues without delay or corruption; losers retry automatically when the bus is free.

**Example**

```
Node A ID 0x123 = 001 0010 0011
Node B ID 0x0F5 = 000 1111 0101
Bit 2 (from MSB): A sends 1 (recessive), B sends 0 (dominant) → bus = 0
A reads 0 ≠ 1 → A loses; B's frame continues uninterrupted
```

**Consequences for system design**

- **IDs are priorities:** assign low IDs to urgent messages (brake, airbag, engine torque).
- The highest-priority message has bounded latency (one frame time for the frame in progress plus its own), which allows **schedulability analysis** of CAN networks (like RTA for tasks).
- Two nodes must never send data frames with the same ID at the same time (arbitration would not resolve it and errors follow), so each ID has one owner.
- Standard frames win over extended frames with the same 11-bit base ID (the IDE bit is dominant for standard frames).

**Physical requirement:** arbitration needs every node to see every bit within the bit time, which limits bus length vs bit rate (about 40 m at 1 Mbps, 500 m at 125 kbps).

### How does CAN handle errors? {H}
**Short answer:** CAN has five error-detection mechanisms: **bit monitoring** (a transmitter checks that the bus level equals what it sent, outside arbitration and the ACK slot), **bit stuffing check**, **form check** (fixed-format fields such as delimiters and EOF), **CRC check**, and **ACK check**. A node that detects an error transmits an **error frame**, which makes all nodes discard the frame, and the sender retransmits automatically. Error counters confine faulty nodes so one bad node cannot block the bus forever.

**Error confinement states**

| State | Condition | Behaviour |
|---|---|---|
| Error active | TEC < 128 and REC < 128 | sends active error flags (6 dominant bits) |
| Error passive | TEC ≥ 128 or REC ≥ 128 | sends passive error flags (6 recessive bits), waits 8 extra bit times before retransmitting |
| Bus off | TEC ≥ 256 | stops transmitting; recovers only after 128 × 11 recessive bits (and usually a software request) |

TEC (transmit error counter) increases by 8 on a transmit error and decreases by 1 on success; REC increases by 1 (sometimes 8) on receive errors.

**What firmware should do**

- Monitor error counters and state changes (interrupts on error-passive and bus-off) and report them as diagnostics (DTCs in automotive).
- Decide a **bus-off recovery** strategy: automatic recovery with a delay, limited retries, or staying off and entering a safe mode.
- Remember that automatic retransmission means a message can be delayed but also that a misconfigured node (wrong bit rate) can cause continuous error frames until it goes bus-off.

**Common causes of CAN errors:** missing or wrong termination, wrong bit timing or sample point between nodes, oscillator inaccuracy, ground offsets, long stubs, and transceiver problems. Tools: CAN analysers (PCAN, Vector, Kvaser), and oscilloscopes with CAN decoding to look at the analogue signal.

### What is the difference between CAN and CAN FD? {M}
**Short answer:** CAN FD (Flexible Data-rate) keeps classic CAN's arbitration (at the nominal bit rate, so priorities and robustness stay the same) but allows up to **64 data bytes** per frame instead of 8, switches to a **faster bit rate for the data phase** (commonly 2–5 Mbps, versus ≤ 1 Mbps for arbitration), uses stronger CRCs (17 or 21 bits plus a stuff-bit counter), and drops remote frames.

| | Classic CAN | CAN FD | CAN XL |
|---|---|---|---|
| Max payload | 8 bytes | 64 bytes | 2048 bytes |
| Data-phase bit rate | ≤ 1 Mbps | typically 2–5 Mbps (up to 8) | up to ~20 Mbps |
| CRC | 15-bit | 17-bit (≤ 16 bytes) / 21-bit | 13-bit header CRC + 32-bit frame CRC |
| DLC | 0–8 | 0–8, 12, 16, 20, 24, 32, 48, 64 | 1–2048 |
| Remote frames | yes | no | no |

**New control bits:** **FDF** (marks an FD frame), **BRS** (bit-rate switch on/off), **ESI** (error state indicator of the transmitter).

**Practical points**

- A classic CAN controller that sees an FD frame flags errors, so mixed networks need FD-tolerant controllers or gateways ("partial networking" transceivers can ignore FD traffic).
- Data-phase timing is more demanding: transceiver delay compensation (TDC) and accurate sample points are needed at higher rates.
- Linux SocketCAN supports FD (`struct canfd_frame`, `ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on`).
- Larger payloads mean fewer frames for the same data: essential for security (room for MACs, AUTOSAR SecOC) and for flashing ECUs faster.

### Why does a CAN bus need 120 Ω termination? {E}
**Short answer:** A CAN bus is a differential transmission line (twisted pair) with a characteristic impedance of about 120 Ω. A 120 Ω resistor at **each end** matches that impedance so signals are absorbed instead of reflecting back and corrupting bits. The two resistors in parallel (60 Ω) also provide the load that pulls the bus back to the recessive state quickly when no node drives it dominant.

**Quick check:** with all nodes powered off, measure the resistance between CAN_H and CAN_L: about **60 Ω** means both terminators are present; **120 Ω** means one is missing; much lower means too many terminators (or a short).

**Design details**

- Terminate only the two physical **ends** of the bus, not every node; nodes in the middle connect with short stubs (a few tens of cm at high bit rates).
- **Split termination:** two 60 Ω resistors in series with a capacitor (e.g. 4.7 nF) from the midpoint to ground improves EMC by filtering common-mode noise.
- Missing termination may still "work" at low speed on a short bench setup, then fail in the vehicle or at higher bit rates: a classic bring-up trap.
- CAN levels: recessive ≈ 2.5 V on both lines (differential ~0 V); dominant ≈ CAN_H 3.5 V, CAN_L 1.5 V (differential ~2 V).

### What is a CAN bit time and how are its segments configured? {H}
**Short answer:** Each CAN bit is divided into **time quanta (tq)** derived from the CAN controller clock through a prescaler. The bit consists of the **Sync segment** (always 1 tq, where edges are expected), the **Propagation segment** (compensates for signal round-trip delays), **Phase segment 1** and **Phase segment 2**. The **sample point** is between phase 1 and phase 2, typically at 75–87.5% of the bit. The **SJW** (synchronisation jump width) limits how much the controller may lengthen phase 1 or shorten phase 2 to resynchronise on edges.

```
|Sync|  Prop  | Phase 1 | Phase 2 |
 1 tq          sample point ↑
```

**Worked example: 500 kbps from a 40 MHz CAN clock**

- Choose prescaler 5 → tq = 125 ns (8 MHz).
- Bit time at 500 kbps = 2 µs = 16 tq.
- Sync 1 + Prop + Phase1 = 13 tq, Phase2 = 2 tq → sample point = (1 + 13) / 16 = **87.5%**.
- SJW = 2 tq (≤ Phase2).

(Many controllers combine Prop and Phase 1 into one "TSEG1" register field: TSEG1 = 13, TSEG2 = 2.)

**Guidelines**

- Use the **same sample point** on all nodes, as recommended by your network specification (CiA recommends ~87.5% for classic CAN at most rates; automotive OEMs specify exact values).
- More tq per bit (e.g. 16–25) gives finer adjustment and better tolerance.
- Oscillator tolerance: classic CAN typically needs ≤ ±0.5% (depends on bit timing; ±1.58% maximum theoretical with ideal settings); use crystals, not RC oscillators.
- CAN FD needs separate nominal and data-phase timings plus transceiver delay compensation.

**Tools:** bit-timing calculators (e.g. bittiming.can-wiki.info), and on Linux, `ip -details link show can0` shows the computed segments.

### What is LIN, and how is it used alongside CAN? {M}
**Short answer:** LIN (Local Interconnect Network) is a low-cost, single-wire, UART-based automotive bus (up to 20 kbps) with one commander (master) and up to 15 responders (slaves). The commander sends a **header** (break, sync byte 0x55, protected identifier) and the addressed node responds with 1–8 data bytes plus a checksum. It is used for simple, non-critical body electronics (window motors, seat controls, mirrors, rain sensors, switches) where CAN would be too expensive; a CAN ECU usually acts as the LIN commander and gateway.

**Frame**

```
| Break (≥13 dominant bits) | Sync 0x55 | PID (6-bit ID + 2 parity) | Data 1-8 bytes | Checksum |
          ^----------- header (commander) -----------^   ^-------- response (responder) ---------^
```

**Key characteristics**

| | LIN | CAN |
|---|---|---|
| Wires | 1 (+ 12 V and ground) | 2 (twisted pair) |
| Speed | ≤ 20 kbps | 125 kbps–1 Mbps (FD faster) |
| Access | commander polls via a schedule table | multi-controller arbitration |
| Determinism | fully scheduled by the commander | priority-based |
| Cost | very low (UART + simple transceiver, often an RC oscillator) | higher |

**Details**

- The **sync byte 0x55** lets responders with inaccurate RC oscillators measure the bit rate and adjust (auto-baud), which is why cheap nodes work.
- The commander's **schedule table** defines which frames are sent when, giving deterministic timing.
- Checksum: classic (data only) or enhanced (data + PID, LIN 2.x).
- Diagnostics and node configuration are standardised (LIN 2.x, ISO 17987), and LIN supports sleep/wake-up over the bus.
- Many MCUs have LIN mode in their UARTs (break generation/detection).

### What are the USB transfer types? {M}
**Short answer:** USB has four transfer types. **Control** transfers configure and query devices on endpoint 0 (enumeration, standard and class requests) with guaranteed delivery. **Bulk** transfers move large amounts of data with error checking and retries but no timing guarantee (mass storage, printers, CDC serial data). **Interrupt** transfers carry small, periodic data with a guaranteed maximum polling interval (keyboards, mice, HID, status). **Isochronous** transfers reserve bandwidth with fixed timing but no retransmission (audio, video).

| Type | Guaranteed delivery | Guaranteed timing | Max packet (FS / HS) | Typical use |
|---|---|---|---|---|
| Control | yes | best effort (reserved share) | 64 / 64 | enumeration, configuration |
| Bulk | yes (retries) | no | 64 / 512 | storage, serial data, network |
| Interrupt | yes (retries) | bounded polling interval | 64 / 1024 | HID, sensors, notifications |
| Isochronous | no | yes | 1023 / 1024 | audio, video streaming |

**Key facts**

- **The host initiates every transfer**; a device can only answer when polled. "Interrupt" transfers are therefore polled, not true interrupts.
- **Endpoints:** a device has endpoint 0 (control, bidirectional) plus up to 15 IN and 15 OUT endpoints. IN = device to host.
- **Classes** standardise drivers: HID, CDC-ACM (virtual serial port), MSC (mass storage), UAC (audio), UVC (video), DFU (firmware update). Using a standard class means no custom host driver.
- **Speeds:** low (1.5 Mbps), full (12 Mbps), high (480 Mbps), SuperSpeed (5 Gbps+); most MCUs have full-speed device controllers, some high-speed with an external or internal ULPI PHY.

**Embedded stacks:** TinyUSB, vendor stacks (STM32 USB device library), Zephyr USB, and on Linux the gadget framework (configfs).

### What happens during USB enumeration? {H}
**Short answer:** When a device is plugged in, the host detects it, resets it, reads its device descriptor at address 0 to learn the control endpoint's maximum packet size, assigns it a unique address, reads all its descriptors (device, configuration, interfaces, endpoints, strings), chooses a driver based on class or vendor/product ID, and selects a configuration. Only then can the device's other endpoints be used.

**Step by step**

1. **Attach:** the device connects a pull-up on D+ (full/high speed) or D− (low speed); the host sees the line change.
2. **Reset:** the host drives SE0 for at least 10 ms; a high-speed-capable device performs the **chirp** handshake to switch to 480 Mbps.
3. **GET_DESCRIPTOR (device)** to address 0, often only the first 8 bytes, to learn `bMaxPacketSize0`.
4. **SET_ADDRESS:** the device must switch to the new address **after** the status stage of this request (a common firmware bug).
5. **GET_DESCRIPTOR (device)** again (full 18 bytes): VID, PID, class, number of configurations.
6. **GET_DESCRIPTOR (configuration)**: first 9 bytes for `wTotalLength`, then the full configuration with all interface and endpoint descriptors.
7. **String descriptors** (manufacturer, product, serial number), optionally.
8. **Driver binding:** the host OS matches class/subclass/protocol or VID/PID to a driver.
9. **SET_CONFIGURATION:** the device becomes "configured" and its endpoints active. Class-specific requests follow (e.g. HID report descriptor, CDC line coding).

**Common failure causes**

- Descriptor errors (wrong lengths, `wTotalLength` mismatch, wrong endpoint addresses).
- Slow responses to control requests (the host has timeouts, e.g. 500 ms for some stages).
- Wrong USB clock accuracy (full speed needs ±0.25%; internal RC oscillators need clock recovery via SOF packets).
- Missing pull-up or VBUS sensing configuration.

**Debugging:** `dmesg` and `lsusb -v` on Linux, USBView on Windows, Wireshark with usbmon, or a hardware USB protocol analyser.

### What is Modbus? {E}
**Short answer:** Modbus is a simple request/response protocol widely used in industrial automation. A **client** (master) sends a function code and a register address to a **server** (slave), which replies with data or an exception. **Modbus RTU** runs over RS-485 (or RS-232) with compact binary frames, a 1-byte server address and a CRC-16, with frames separated by 3.5 character times of silence. **Modbus TCP** carries the same function codes over TCP port 502 with an MBAP header instead of the address and CRC.

**Data model**

| Table | Access | Size | Function codes |
|---|---|---|---|
| Coils | read/write | 1 bit | 01 read, 05 write single, 15 write multiple |
| Discrete inputs | read only | 1 bit | 02 |
| Input registers | read only | 16 bit | 04 |
| Holding registers | read/write | 16 bit | 03 read, 06 write single, 16 write multiple |

**RTU frame example: read 2 holding registers starting at 0x0010 from server 0x11**

```
Request:  11 03 00 10 00 02 [CRC lo] [CRC hi]
Response: 11 03 04 01 F4 00 64 [CRC lo] [CRC hi]   -> registers = 0x01F4 (500), 0x0064 (100)
```

**Register mapping in a device (design question):** document a map, e.g. 40001 = temperature × 10 (signed), 40002 = setpoint, 40003–40004 = 32-bit counter (decide word order!), 40010 = command register. Values above 16 bits span two registers, and different vendors use different word orders (big-endian bytes, but high or low word first), a classic integration bug.

**Implementation details**

- RTU timing: detect frame end with a 3.5-character silence (≈ 4 ms at 9600 baud); for baud rates above 19200 a fixed 1.75 ms is used. The UART idle-line interrupt or a hardware receiver timeout helps.
- CRC-16 with polynomial 0xA001 (reflected 0x8005), initial value 0xFFFF, sent low byte first.
- Exceptions: function code | 0x80 plus an exception code (01 illegal function, 02 illegal data address, 03 illegal value).
- Broadcast address 0: writes to all servers, no reply.
- Security: none built in; use network segmentation or Modbus/TCP Security (TLS).

### What layers does an embedded Ethernet interface involve? {M}
**Short answer:** The **MAC** (media access controller), usually inside the MCU or SoC, builds and checks frames (preamble, addresses, CRC) and moves them to and from memory with DMA descriptors. The **PHY**, often an external chip, handles the physical signalling on the cable (10/100/1000BASE-T, auto-negotiation, link detection). They connect through a data interface (**MII**, **RMII**, **RGMII**, **SGMII**) and a management bus (**MDIO/MDC**) that reads and writes PHY registers. A TCP/IP stack (lwIP, Zephyr's stack, FreeRTOS+TCP, or Linux) runs above the MAC driver.

| Interface | Data width / clock | Speed | Notes |
|---|---|---|---|
| MII | 4 bits, 25 MHz TX and RX clocks | 100 Mbps | 16 pins |
| RMII | 2 bits, 50 MHz reference clock | 100 Mbps | fewer pins; the 50 MHz clock must come from the PHY or MCU, not both |
| RGMII | 4 bits, DDR at 125 MHz | 1 Gbps | needs ~2 ns clock delays (in PHY, MAC or PCB) |
| SGMII | serial differential | 1 Gbps | SerDes |

**Bring-up checklist and common issues**

1. PHY reset and strap pins: the PHY address and mode (MII/RMII) are often set by pins at reset; wrong straps → no MDIO response.
2. Read PHY ID registers (2 and 3) over MDIO to confirm communication.
3. Reference clock: for RMII, exactly one 50 MHz source, with the right direction configured on both sides.
4. RGMII delays: no delay or double delay → CRC errors or no traffic (`phy-mode = "rgmii-id"` etc. on Linux).
5. Check link status and auto-negotiation result (speed/duplex) and configure the MAC to match.
6. DMA descriptors, buffer alignment and cache maintenance in the MAC driver.
7. Magnetics, cable and LEDs; check with `ethtool` on Linux.

**Above the MAC:** ARP, IP, ICMP, UDP, TCP, DHCP, DNS; MCU stacks need tuning of buffer counts and sizes for RAM. Automotive Ethernet (100BASE-T1, 1000BASE-T1) uses a single twisted pair and a different PHY, with protocols such as SOME/IP and AVB/TSN on top.

### What is the difference between TCP and UDP for embedded devices? {E}
**Short answer:** **TCP** provides a reliable, ordered, connection-oriented byte stream with retransmission, flow control and congestion control, at the cost of RAM for buffers and state, and higher latency when packets are lost. **UDP** sends independent datagrams with no delivery or ordering guarantee and no connection, so it is lighter and has lower, more predictable latency, but the application must handle loss if it matters.

| | TCP | UDP |
|---|---|---|
| Connection | 3-way handshake, teardown | none |
| Reliability and ordering | yes | no |
| Message boundaries | no (byte stream) | yes (datagrams) |
| Flow/congestion control | yes | no |
| Overhead | 20+ byte header, ACKs, state per connection, buffers | 8-byte header |
| Latency under loss | retransmission delays (head-of-line blocking) | none, data is just lost |
| Multicast/broadcast | no | yes |
| Embedded protocols | MQTT, HTTP(S), Modbus TCP, FTP | CoAP, DNS, DHCP, SNTP, mDNS, syslog, RTP, QUIC |

**Choosing**

- Use **TCP** for commands and data that must arrive intact and in order (configuration, firmware updates, MQTT telemetry).
- Use **UDP** for real-time streams where late data is useless (audio, control loops, sensor streams), discovery (mDNS), and very constrained devices (CoAP with its own lightweight reliability), or when you need broadcast/multicast.

**Embedded resource notes:** each TCP connection needs a TCB plus send/receive buffers (several KB in lwIP); MCUs often limit simultaneous connections. TLS on top of TCP adds tens of KB of RAM (mbedTLS); DTLS is TLS for UDP.

**Interview follow-up:** "How would you make UDP reliable?" Sequence numbers, ACKs, retransmission timers and duplicate detection (CoAP confirmable messages, or QUIC, which builds a reliable, encrypted transport on UDP).

### What is MQTT, and how do you make an MQTT client secure? {M}
**Short answer:** MQTT is a lightweight **publish/subscribe** messaging protocol over TCP, widely used in IoT. Devices connect to a **broker**, **publish** messages to hierarchical **topics** (e.g. `factory/line1/temp`) and **subscribe** to topics they are interested in; the broker forwards messages, so senders and receivers never talk directly. It offers three **QoS** levels, retained messages, a "last will" message for unexpected disconnects, and keep-alive. Security comes from **TLS** (encryption and server authentication), **client authentication** (X.509 client certificates or username/password/tokens), and **authorisation** (each client can only publish/subscribe to its own topics).

**QoS levels**

| QoS | Guarantee | Mechanism | Use |
|---|---|---|---|
| 0 | at most once | fire and forget | frequent telemetry where loss is fine |
| 1 | at least once | PUBACK; duplicates possible | most commands and events (make handlers idempotent) |
| 2 | exactly once | 4-step handshake | rarely needed; expensive |

**Useful features**

- **Retained message:** the broker keeps the last message on a topic and sends it to new subscribers (current state).
- **Last Will and Testament:** the broker publishes it if the client disappears without disconnecting (device offline detection).
- **Keep-alive** pings detect dead connections; **persistent sessions** queue QoS 1/2 messages while a client is offline.
- **MQTT 5** adds reason codes, message expiry, user properties, shared subscriptions and request/response.

**Securing an embedded MQTT client**

1. **TLS 1.2/1.3** on port 8883, with the broker's CA certificate pinned in the device; verify the server certificate and hostname.
2. **Mutual TLS:** a unique client certificate and private key per device, ideally generated and stored in a secure element or TrustZone/secure storage (never the same key in every device).
3. **Least-privilege topics:** broker ACLs so device 123 can only publish to `devices/123/#` and subscribe to its own command topic.
4. **Validate payloads** from command topics (sizes, ranges); treat the broker as untrusted input.
5. **Time:** certificate validation needs a correct clock (SNTP or RTC), and plan for certificate rotation before expiry.
6. **Resilience:** reconnect with exponential back-off and jitter, buffer messages while offline, and secure OTA for updates.

**Embedded clients:** Eclipse Paho Embedded C, coreMQTT (FreeRTOS), Zephyr's MQTT library, lwIP's MQTT app; with mbedTLS or wolfSSL for TLS.

### What is Bluetooth Low Energy, and how do GAP and GATT work? {M}
**Short answer:** Bluetooth Low Energy (BLE) is a 2.4 GHz wireless protocol designed for very low power, short-range communication (sensors, wearables, phone accessories). **GAP** (Generic Access Profile) defines how devices discover and connect: **advertisers/peripherals** broadcast advertising packets, **scanners/centrals** listen and initiate connections. **GATT** (Generic Attribute Profile) defines how data is exchanged once connected: a **server** exposes **services**, each containing **characteristics** (values with properties: read, write, notify, indicate), identified by UUIDs, and a **client** reads, writes or subscribes to them.

**Typical sensor example**

```
GATT server (sensor)
└── Service: Environmental Sensing (0x181A)
    ├── Characteristic: Temperature (0x2A6E)   properties: read, notify
    │    └── CCCD descriptor (client enables notifications here)
    └── Characteristic: Humidity (0x2A6F)      properties: read, notify
```

The phone (central/GATT client) connects, discovers services, writes to the CCCD to enable notifications, and receives a notification each time the temperature changes.

**Key concepts**

- **Advertising:** packets every 20 ms–10 s on 3 advertising channels; can carry data without connecting (beacons, broadcast sensors).
- **Connection interval** (7.5 ms–4 s), **peripheral latency** and **supervision timeout** trade latency for power.
- **MTU and data length extension** decide how many bytes fit per packet (default 20 bytes of payload; up to ~244 with DLE and a larger MTU).
- **Security:** pairing (Just Works, Passkey, Numeric Comparison, Out of Band), bonding (storing keys), LE Secure Connections (ECDH). Just Works has no man-in-the-middle protection.
- **PHYs:** 1M, 2M (faster) and Coded (long range, 125/500 kbps).
- Newer features: LE Audio (LC3 codec, Auracast broadcast), direction finding, periodic advertising.

**Power:** a BLE sensor sleeping between connection events can average a few µA and run for years on a coin cell.

**Embedded stacks:** Zephyr Bluetooth (used by nRF Connect SDK), NimBLE (Apache Mynewt, ESP-IDF), vendor stacks (TI, ST, Silicon Labs), BlueZ on Linux.

### How do you choose a wireless technology for an IoT device? {M}
**Short answer:** Match range, data rate, power budget, network topology, infrastructure and cost. **BLE** for short range, very low power and phone connectivity; **Wi-Fi** for high data rates and direct internet access with mains or large batteries; **Thread/Zigbee** (802.15.4) for low-power mesh networks in buildings (Thread with Matter for smart homes); **LoRaWAN** for kilometres of range with tiny data and multi-year battery life; **NB-IoT/LTE-M** (cellular) for wide-area coverage without your own gateways.

| | BLE | Wi-Fi | Thread / Zigbee | LoRaWAN | NB-IoT / LTE-M |
|---|---|---|---|---|---|
| Range | 10–100 m | 30–100 m | 10–100 m per hop, mesh | 2–15 km | km (cellular) |
| Data rate | 1–2 Mbps PHY, ~100s kbps app | 10–1000+ Mbps | 250 kbps | 0.3–50 kbps | ~60 kbps / ~1 Mbps |
| Power | very low | high | low (routers mains-powered) | very low | low–medium (PSM, eDRX) |
| Topology | star (mesh possible) | star (AP) | mesh | star of stars (gateways) | star (base stations) |
| Infrastructure | phone or gateway | access point | border router | gateways + network server | operator network, SIM |
| IP-native | no (yes over IPv6 in some profiles) | yes | Thread: IPv6; Zigbee: no | no | yes |
| Typical use | wearables, sensors, provisioning | cameras, appliances | lighting, smart home (Matter) | agriculture, metering, asset tracking | trackers, meters, remote equipment |

**Questions to ask in a design discussion**

1. How much data, how often, and with what latency?
2. Battery or mains power, and what lifetime is required?
3. Indoor/outdoor range, and is there existing infrastructure (Wi-Fi, phones, cellular coverage)?
4. Cost per unit (module, certification, subscription fees for cellular).
5. Security and provisioning (how a device joins the network securely).
6. Regulatory regions (sub-GHz frequencies differ by region).

**Common combinations:** BLE for setup (phone app provisions Wi-Fi credentials) plus Wi-Fi for data; Thread devices exposed through Matter; LoRaWAN or cellular sensors with BLE for local maintenance.

### How would you design a protocol gateway, for example Modbus RTU to MQTT? {H}
**Short answer:** Split it into layers connected by queues: a **southbound** driver (RS-485 Modbus RTU client polling devices on a schedule), a **data model** that maps device registers to named, scaled values with timestamps and quality flags, and a **northbound** client (MQTT over TLS publishing values and receiving commands), plus configuration, buffering for offline periods, diagnostics and secure updates. Each side runs independently so a slow cloud connection never stalls field-bus polling.

**Architecture**

```
[Modbus devices] --RS-485--> [Modbus RTU poller] --queue--> [Data model / mapping] --queue--> [MQTT client] --TLS--> [Broker]
                                   ^                                  |                              |
                           [Config: register map, poll rates]   [Store-and-forward buffer]   [Command handler → write queue]
```

**Design points to discuss**

1. **Configuration-driven mapping:** a table per device: address, function code, register, data type (int16/uint32/float, word order), scale, units, poll period, MQTT topic. No code changes for a new device type.
2. **Scheduling:** poll fast-changing values often and others rarely; respect inter-frame delays and timeouts; one outstanding request at a time per RS-485 bus.
3. **Error handling:** retries with limits, mark values as stale/bad quality after timeouts, per-device health statistics, bus recovery.
4. **Buffering:** store-and-forward in RAM/flash when the uplink is down, with a bounded size and a drop policy (oldest first) and timestamps from an RTC/NTP.
5. **Commands (writes):** validate topic, range and permissions before writing to devices; send acknowledgements back over MQTT.
6. **Publishing efficiency:** publish on change or with deadband, batch values into one JSON/CBOR/Protobuf message, use QoS 1 for important data.
7. **Security:** TLS with per-device certificates, minimum broker permissions, signed firmware updates, no default passwords on a local web UI.
8. **Observability:** logs, counters (polls, timeouts, CRC errors, publish failures), a status topic and a last-will message.
9. **Platform:** an MCU with an RTOS for simple gateways, or embedded Linux (more protocols, containers, easier TLS and storage) for larger ones.

**Interviewers are looking for:** decoupling with queues, explicit handling of failure and backlog, configuration over hard-coding, and security from the start.
