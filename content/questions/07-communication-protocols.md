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
A single SPI controller can communicate with multiple targets by sharing clock and data lines and providing a separate chip-select signal for each target.

#### 1. Typical wiring

```text
Controller SCLK, MOSI ----+---- Target A
                          +---- Target B
Controller MISO <---------+---- shared return
Controller CS_A -------------- A select
Controller CS_B -------------- B select
```

Only the selected target should drive the shared MISO line. Nonselected targets must release it if the bus is shared.

#### 2. Transaction sequence

Select the correct target, configure its mode/speed if needed, assert its CS, transfer command/data, and deassert CS according to its timing requirements. Do not switch device configuration while a transfer is active.

#### 3. Other topologies

Some targets support daisy chaining or address selection through an external decoder. These are device-specific alternatives and not universally supported by SPI.

#### 4. Firmware synchronization

If multiple tasks share one SPI controller, serialize entire transactions, including configuration and chip select. An RTOS mutex or single bus-owner task can prevent interleaving.

**Interview takeaway:** SPI has no standard in-band device addressing. Chip selection and bus ownership determine which target communicates.

### What are Dual, Quad and Octal SPI? {M}
Dual, Quad and Octal SPI extend the number of data lines used during selected phases of a serial-memory transaction. Standard SPI commonly uses one data line per direction, whereas multi-I/O modes can carry multiple bits per clock.

| Mode | Data lines in multi-I/O phase | Bits per clock (SDR) |
|---|---:|---:|
| Single | 1 | 1 per direction |
| Dual | 2 | 2 |
| Quad | 4 | 4 |
| Octal | 8 | 8 |

#### 1. Example

A quad-data transfer at 40 MHz in single-data-rate mode has a theoretical data-phase throughput of 160 Mbit/s, or 20 MB/s. Command, address, dummy cycles and chip-select gaps reduce effective throughput.

#### 2. Transaction phases

A flash device might receive a command on one line, an address on one or four lines, and return data on four lines. The exact protocol depends on the command and device. Some interfaces support double-data-rate operation.

#### 3. Embedded use

QSPI/OSPI controllers can access serial flash through indirect commands or memory-mapped modes, including execute-in-place when supported. Configure dummy cycles, line direction, read opcode and clock timing according to both device and controller.

**Interview takeaway:** Quad SPI is not automatically four times faster for an entire transaction. The gain depends on which phases use multiple lines and the supported timing.

### What does an I2C transaction look like? {E}
I2C is a synchronous addressed bus using open-drain SDA and SCL signals. A controller initiates a transaction and the addressed target acknowledges its address and appropriate data bytes.

#### 1. Register write example

For a target with 7-bit address 0x50, write value 0xAB to register 0x10:

```text
START | address 0x50 + W | ACK
      | register 0x10    | ACK
      | data 0xAB        | ACK | STOP
```

The transmitted address byte is 0xA0. The receiver drives ACK low on the ninth clock; NACK leaves SDA high.

#### 2. Register read with repeated START

```text
START | address + W | ACK | register | ACK
REPEATED START | address + R | ACK
      | read data | controller NACK | STOP
```

The device's datasheet determines whether a repeated START and register-address bytes are required. For multiple read bytes, the controller commonly ACKs intermediate bytes and NACKs the last.

#### 3. Linux example

```c
int val = i2c_smbus_read_byte_data(client, 0x10);
if (val < 0)
    return val;
```

Use this helper only if the device and adapter support the compatible SMBus-style transaction. Otherwise use an appropriate i2c_transfer message sequence.

**Interview takeaway:** START/STOP delimit the transaction, address and direction select the target, and ACK/NACK coordinates byte reception. Do not confuse a 7-bit address with the transmitted address byte.

### Why does I2C need pull-up resistors, and how do you size them? {M}
I2C requires pull-up resistors because conventional SDA and SCL outputs are open-drain. Devices drive low but release the line for high. The pull-up charges bus capacitance when every device releases it.

#### 1. Rise-time limit

For a simple resistor-capacitor bus, the 30%-to-70% rise time is approximately:

```text
tr ≈ 0.8473 × Rp × Cbus
Rp_max ≈ tr_max / (0.8473 × Cbus)
```

The maximum pull-up resistance is set by the applicable I2C mode's rise-time requirement.

#### 2. Sink-current limit

```text
Rp_min ≈ (VDD - VOL_max) / IOL
```

A smaller resistor increases the low-state sink current. Respect the weakest device's specified drive capability.

#### 3. Example calculation

Assume 3.3 V, 100 pF bus capacitance, a 300 ns rise-time limit, VOL_max = 0.4 V and allowable sink current 3 mA.

Rp_max ≈ 3.54 kΩ; Rp_min ≈ 0.97 kΩ. A 2.2 kΩ resistor is within this illustrative range. Confirm actual capacitance, device limits and measured waveform.

#### 4. Debugging

Weak pull-ups give slow rising edges; overly strong pull-ups can violate low-level voltage or sink-current limits. Multiple pull-ups in parallel reduce effective resistance.

**Interview takeaway:** Pull-up sizing is an electrical timing/current trade-off, not a universal 4.7 kΩ rule.

### What is clock stretching? {M}
Clock stretching allows an I2C target to delay communication by holding SCL low after the controller releases it. The bus cannot rise until all participants release the open-drain line.

#### 1. Sequence

```text
Controller drives SCL low
Controller releases SCL
Target keeps SCL low while preparing data
Target releases SCL
SCL rises; transfer continues
```

This permits a slower device to request additional processing time.

#### 2. Practical constraints

The controller must support observing the actual SCL line and waiting for it to become high. Some controllers or modes have limitations. SMBus and device-specific protocols may impose timeout requirements.

#### 3. Debugging

If SCL remains low, determine whether a legitimate stretch, stalled target, controller state or electrical fault is responsible. Use a logic analyzer and a bounded driver timeout; do not assume every low period is ordinary clock stretching.

**Interview takeaway:** Clock stretching extends a clock-low interval, not the configured nominal clock frequency. Both hardware support and timeout handling matter.

### How does I2C arbitration work with multiple controllers? {H}
I2C supports arbitration when more than one controller begins transmitting. Because SDA is open-drain, a transmitted low level dominates a released high level.

#### 1. Arbitration example

```text
Controller A sends bit 1 (releases SDA)
Controller B sends bit 0 (drives SDA low)
Observed SDA = 0
Controller A loses arbitration
Controller B continues
```

During the relevant arbitration phase, a controller that sends high but observes low while SCL is high recognizes that another controller is transmitting a dominant bit.

#### 2. Why the winning message is preserved

The winner's intended low bit remains on the bus. The losing controller stops interfering and follows the specified arbitration-loss behavior, allowing the winning transfer to continue.

#### 3. Clock synchronization

Open-drain SCL also enables controllers to synchronize clock-low/high timing according to I2C multi-controller rules. Arbitration and clock synchronization are related but distinct mechanisms.

#### 4. Driver handling

A controller may report arbitration loss as a retryable error. Retry only when appropriate, after the bus is available, with bounded backoff and awareness of transaction side effects.

**Interview takeaway:** I2C arbitration is nondestructive for the winning bit stream. A released-high controller loses when it observes a low level during arbitration.

### How do you recover a stuck I2C bus? {M}
An I2C bus may become stuck when SDA or SCL remains low, for example after a controller reset in the middle of a transaction, an unpowered device or a hardware fault.

#### 1. Diagnose first

Read both line levels and inspect recent bus activity. Check power rails, pull-ups, target reset state and controller error flags.

#### 2. Bus recovery

If the controller is the only active bus owner and the hardware permits recovery, an SDA-low target waiting for clock edges may release the line after clock pulses. A conventional recovery sequence can attempt up to nine SCL pulses, observing actual line levels, then generate STOP when possible.

```text
Release SDA --> pulse SCL with open-drain semantics
             --> check whether SDA is released
             --> generate STOP if bus state permits
             --> restore controller/pin configuration
```

If SCL itself is held low, pulses cannot be generated normally. Reset or power-cycle the faulty device only when the system design permits it.

#### 3. Linux

Use the adapter driver's supported bus-recovery mechanism where available. Do not directly toggle GPIOs behind an active I2C controller or another bus owner.

**Interview takeaway:** Recovery is conditional on the actual fault and bus ownership. Use bounded timeouts and the hardware/controller's recovery procedure; do not assume nine pulses always fix a stuck bus.

### What is the difference between 7-bit and 10-bit I2C addressing? {E}
I2C supports 7-bit and 10-bit target addresses. The address width changes the address-phase encoding, not the width of a data byte.

#### 1. 7-bit addressing

A seven-bit address is followed by a read/write bit in the first transmitted byte.

```text
7-bit address: 0x50
Write address byte: (0x50 << 1) | 0 = 0xA0
Read address byte:  (0x50 << 1) | 1 = 0xA1
```

Some address values are reserved by the specification.

#### 2. 10-bit addressing

The initial address byte contains the reserved prefix 11110, the two high address bits and the direction bit. A second byte carries the remaining eight address bits. A 10-bit read uses the specified repeated-START/address sequence.

#### 3. Linux configuration

In a device tree, an ordinary 7-bit I2C target commonly uses its unshifted address:

```dts
sensor@50 {
    compatible = "vendor,sensor";
    reg = <0x50>;
};
```

Ten-bit devices require the appropriate binding/address flag and adapter support.

**Interview takeaway:** Most driver APIs use the unshifted 7-bit address. Check the API before shifting; 10-bit addressing uses a different protocol sequence.

### What is SMBus, and what is I3C? {M}
SMBus and I3C are related to I2C but define additional or different protocol and electrical behavior.

#### 1. SMBus

System Management Bus is an I2C-derived interface used for management functions such as battery, temperature and power monitoring. It defines standardized transactions, timing constraints and optional packet error checking (PEC), depending on the device/protocol.

A device may be compatible with both I2C and SMBus transactions, but not every arbitrary I2C transaction maps to an SMBus helper.

#### 2. I3C

MIPI I3C is a newer two-wire interface designed for higher throughput and additional features, including dynamic address assignment, in-band interrupts and push-pull signaling during supported phases. It can support certain legacy I2C targets subject to bus restrictions.

| Feature | SMBus | I3C |
|---|---|---|
| Main purpose | System management | Efficient modern sensor/device bus |
| Address handling | Typically static | Dynamic assignment supported |
| Signaling | Open-drain style | Open-drain and push-pull phases |
| Interrupts | Separate mechanisms possible | In-band interrupts supported |

**Interview takeaway:** Do not treat SMBus, I2C and I3C as identical. Match the controller, target, electrical requirements and transaction type.

### What is I2S, and how is it different from I2C? {E}
I2S (Inter-IC Sound) is a serial interface for digital audio samples. I2C is an addressed control/data bus; the similar names do not imply compatible protocols.

#### 1. Common I2S signals

- BCLK: serial bit clock.
- WS/LRCLK: word-select or left/right channel clock.
- SD: serial audio data.
- MCLK: optional master clock depending on codec/system.

In standard I2S format, the most significant data bit follows the word-select transition by one bit-clock period. Other audio serial formats use different alignment.

#### 2. Clock example

For 48 kHz stereo audio with 32-bit slots:

```text
BCLK = 48000 × 2 channels × 32 bits
     = 3.072 MHz
LRCLK = 48 kHz
```

A sample may have fewer valid bits than its slot width.

#### 3. Embedded use

An SoC may configure an audio codec through I2C, then transfer audio through I2S using DMA. Clock master/slave roles, sample format, bit width and channel ordering must agree.

**Interview takeaway:** I2S streams time-synchronized audio; I2C configures addressed devices. They often coexist in the same audio design.

### How does a CAN frame look? {M}
A CAN (Controller Area Network) frame carries an identifier, control information, payload and integrity/acknowledgment fields. Classical CAN data frames carry up to eight payload bytes.

#### 1. Simplified standard-format data frame

```text
SOF | 11-bit identifier + RTR | control / DLC
    | data (0–8 bytes) | CRC | ACK | EOF
```

Extended-format frames use a 29-bit identifier and additional arbitration/control bits. Bit stuffing, delimiters and intermission rules are part of the actual wire format.

#### 2. Important fields

| Field | Purpose |
|---|---|
| Identifier | Message identity and arbitration priority |
| DLC | Encodes payload length |
| Data | Application payload |
| CRC | Detects transmission errors |
| ACK | Receivers acknowledge a valid received frame |
| EOF | Marks frame end |

A CAN acknowledgment does not establish that a specific application processed the data, only that an eligible receiver acknowledged at the protocol level.

#### 3. Embedded example

A controller can send a sensor reading using an agreed identifier and payload encoding. Acceptance filters select which frames are delivered to software; application protocols define signal packing and interpretation.

**Interview takeaway:** CAN is message-oriented, not a direct node-addressing protocol. The identifier participates in arbitration and describes the message according to the network design.

### How does CAN arbitration work? {M}
CAN uses nondestructive bitwise arbitration to allow multiple nodes to start transmission while preserving the highest-priority valid frame. A dominant bit (typically logical 0) overrides a recessive bit (logical 1).

#### 1. Example: standard data frames

Consider two nodes transmitting different 11-bit identifiers at the same time.

```text
Node A: ID 0x100 = 00100000000
Node B: ID 0x180 = 00110000000
Bus:              0010...
                       ^
               Node B sends recessive, sees dominant
```

Node B stops transmitting and becomes a receiver. Node A continues without losing its message. For comparable standard-format data frames, the smaller numerical identifier has higher arbitration priority.

#### 2. Why no collision retransmission?

Nodes monitor the bus while transmitting arbitration bits. A losing node withdraws rather than corrupting the winner's frame. The complete arbitration field, including frame-format and RTR-related bits, determines priority when identifiers overlap.

#### 3. Design concern

Assign identifiers based on network timing requirements. High-priority traffic can delay lower-priority messages; analyze worst-case bus load, frame lengths and response time.

**Interview takeaway:** CAN arbitration is based on dominant/recessive signaling, not a central scheduler. Losing arbitration is normal, not a transmission error.

### How does CAN handle errors? {H}
CAN detects transmission errors using multiple protocol checks and manages faulty nodes through error confinement.

#### 1. Detection mechanisms

| Check | Detects |
|---|---|
| CRC | Corruption in protected frame fields |
| Bit monitoring | Unexpected bus value outside permitted exceptions |
| Bit stuffing | Invalid run length in stuffed fields |
| Form check | Incorrect fixed-format bits |
| ACK check | Missing receiver acknowledgment |

A detected error can trigger an error frame and retransmission according to controller settings and protocol rules.

#### 2. Error confinement

Controllers maintain transmit and receive error counters. The protocol uses these to transition among error-active, error-passive and bus-off states. Bus-off is triggered when the transmit error counter exceeds its permitted threshold (255 in Classical CAN).

#### 3. Debugging example

Repeated transmit errors may indicate missing termination, wrong bit timing, wiring faults or no other node acknowledging frames. Inspect controller status, error counters, waveform and bus configuration.

#### 4. Recovery

Bus-off recovery follows the controller, protocol and application policy. Automatic recovery is not always suitable in safety-related systems. Diagnose and report persistent faults rather than blindly retrying forever.

**Interview takeaway:** CAN combines error detection, retransmission and error confinement. A valid CAN ACK is not an application-level acknowledgment.

### What is the difference between CAN and CAN FD? {M}
CAN FD (Flexible Data-rate) extends Classical CAN by supporting longer payloads and optionally switching to a faster bit rate during part of a frame.

| Feature | Classical CAN | CAN FD |
|---|---|---|
| Maximum payload | 8 bytes | 64 bytes |
| Bit rate | One nominal rate | Nominal arbitration rate; optional faster data rate |
| CRC | Classical frame CRC | Updated CRC/error-detection scheme |
| DLC | Direct lengths through 8 | Encoded lengths above 8 |

#### 1. Example

A 32-byte sensor message requires at least four Classical CAN frames if every frame carries eight data bytes. CAN FD can carry the 32 bytes in one frame, subject to its DLC encoding and application protocol.

#### 2. Bit-rate switching

Arbitration remains at the nominal bit rate so participating controllers can resolve priority. If BRS is enabled, the appropriate data-phase fields use the configured data bit rate before the frame returns to nominal timing.

#### 3. Compatibility

Classical-only CAN nodes generally cannot participate transparently in a bus carrying FD frames unless the network provides suitable compatibility mechanisms. Controller, transceiver, wiring and timing must support the chosen FD configuration.

**Interview takeaway:** CAN FD improves payload efficiency and potential throughput. It is not simply Classical CAN with a larger buffer; frame format, CRC and timing differ.

### Why does a CAN bus need 120 Ω termination? {E}
High-speed CAN commonly uses 120-ohm termination resistors at the two physical ends of the main bus. Termination matches the approximate characteristic impedance of the twisted pair and reduces signal reflections.

#### 1. Bus topology

```text
120 Ω across CAN_H/L                      120 Ω across CAN_H/L
        |                                          |
        +========= main twisted-pair bus ==========+
                   |                     |
                Node A                Node B
                 short stubs
```

The resistors are across the differential pair, not in series with the signal.

#### 2. Resistance check

With the network safely powered down and no other paths affecting the measurement, two 120-ohm terminations in parallel give about 60 ohms between CAN_H and CAN_L.

One termination typically gives about 120 ohms; extra terminations can lower the measured resistance and overload drivers.

#### 3. Signal integrity

Use a suitable cable, short stubs and the network's required grounding and common-mode design. Some systems use split termination to improve common-mode behavior.

**Interview takeaway:** Terminate the two ends of a high-speed CAN trunk, not every node. Termination rules depend on the physical-layer standard and topology.

### What is a CAN bit time and how are its segments configured? {H}
CAN bit timing divides each nominal bit into time quanta (TQ). The controller derives the time quantum from its clock and baud-rate prescaler, then configures segments around the sample point.

#### 1. Bit segments

```text
| Sync_Seg | Prop_Seg | Phase_Seg1 | Phase_Seg2 |
                                    ^
                               sample point
```

Sync_Seg is normally one TQ. Controllers often combine Prop_Seg and Phase_Seg1 into TSEG1. SJW limits the permitted resynchronization adjustment.

#### 2. Example calculation

Assume a 40 MHz CAN clock, actual prescaler divisor 4, and 20 TQ per bit.

```text
TQ clock = 40 MHz / 4 = 10 MHz
Bit rate = 10 MHz / 20 = 500 kbit/s
```

For TSEG1 = 15 and TSEG2 = 4, the sample point is (1+15)/20 = 80%. Hardware register encodings may store segment values minus one.

#### 3. Configuration constraints

Account for cable propagation, transceiver delays, oscillator tolerance, controller limits and desired sample point. For CAN FD, nominal and data-phase timing are configured separately, and transmitter-delay compensation may be needed.

**Interview takeaway:** CAN bit rate is not determined by the prescaler alone. The number and arrangement of time quanta, SJW and physical network timing all matter.

### What is LIN, and how is it used alongside CAN? {M}
LIN (Local Interconnect Network) is a low-cost serial automotive network commonly used for slower body-control devices. It uses a scheduled communication model with one controlling node.

#### 1. Frame concept

```text
Header from commander: Break | Sync | Protected ID
Response:              Data bytes | Checksum
```

The configured publisher supplies the response; subscribed nodes consume it according to the schedule. LIN uses a single-wire physical layer with an appropriate transceiver and typically operates at up to about 20 kbit/s.

#### 2. LIN versus CAN

| LIN | CAN |
|---|---|
| Scheduled communication | Message arbitration |
| Single-wire physical layer | Differential physical layer common |
| Low cost, lower speed | Higher throughput and robust error handling |

#### 3. Vehicle example

A body controller can communicate with window or seat modules over LIN and publish aggregated status to a CAN network. The gateway manages scheduling, signal mapping and diagnostics.

**Interview takeaway:** LIN trades bandwidth and distributed arbitration for predictable low-cost scheduled communication. It complements rather than universally replaces CAN.

### What are the USB transfer types? {M}
USB defines four transfer types with different reliability and timing characteristics.

| Transfer | Purpose | Typical example |
|---|---|---|
| Control | Configuration and requests | Endpoint 0 enumeration |
| Bulk | Reliable large data, no guaranteed latency | Mass storage |
| Interrupt | Periodic host-polled data with scheduled opportunities | HID input reports |
| Isochronous | Time-sensitive data, no retransmission guarantee | Audio/video streams |

#### 1. Host-driven scheduling

On conventional USB host/device links, the host schedules transactions. An interrupt endpoint does not independently interrupt the host like a GPIO IRQ; the host polls it according to its scheduling rules.

#### 2. Bulk versus isochronous

Bulk transfers use available bandwidth and can retry failed transactions. Isochronous transfers reserve appropriate service opportunities and prioritize timing over recovery of every lost packet.

#### 3. Driver selection

Select endpoints according to device class, bandwidth, latency and data-integrity needs. Maximum packet sizes and scheduling constraints depend on USB speed and endpoint descriptors.

**Interview takeaway:** Choose transfer type based on timing versus reliability. USB transfer type is distinct from endpoint direction and device class.

### What happens during USB enumeration? {H}
USB enumeration is the host process that discovers, identifies, addresses and configures a connected USB device. The exact sequence depends on USB version, host stack and device speed.

#### 1. Typical USB 2.0 enumeration

```text
Device attach detected
        |
Port reset / speed detection
        |
Default address 0, endpoint 0
        |
Read descriptors; assign unique address
        |
Read configuration/interface/endpoint descriptors
        |
Select configuration; bind suitable driver
```

The host may issue requests in a different order or repeat some descriptor reads.

#### 2. Standard control requests

GET_DESCRIPTOR obtains information such as device, configuration and string descriptors. SET_ADDRESS assigns the device address; SET_CONFIGURATION selects a configuration. Endpoint 0 supports control transfers.

#### 3. Debugging enumeration failure

Check power, cable, connector, PHY clock/reset, speed detection and endpoint-zero responses. Inspect host logs and capture transactions using a USB analyzer or host-side tracing (for example usbmon on Linux).

Incorrect descriptor lengths, invalid endpoint configuration or timing failures can prevent driver binding.

**Interview takeaway:** Enumeration is a host-driven control-transfer process. A device must implement its default control endpoint correctly before ordinary data endpoints are useful.

### What is Modbus? {E}
Modbus is an industrial application protocol for reading and writing data such as coils and registers. Common transports are Modbus RTU over a serial link and Modbus TCP over TCP/IP.

#### 1. Data model

| Object | Common meaning |
|---|---|
| Coils | Read/write bits |
| Discrete inputs | Read-only bits |
| Input registers | Read-only 16-bit values |
| Holding registers | Read/write 16-bit values |

The actual device register map defines the meanings, supported functions and scaling.

#### 2. RTU example

```text
Server address | Function code | Data fields | CRC-16
```

Function code 03 commonly reads holding registers. Serial timing and silent intervals identify RTU frame boundaries. RS-485 is a common electrical transport.

#### 3. TCP variant

Modbus TCP uses an MBAP header for transaction identification, length and unit information. It does not append the serial RTU CRC to the TCP message.

#### 4. Implementation cautions

Distinguish human-facing register numbers from zero-based protocol offsets. Check multi-register byte/word ordering, timeouts and exception responses. Do not expose unauthenticated Modbus control traffic directly to untrusted networks.

**Interview takeaway:** Modbus defines message semantics; RTU and TCP define different framing/transport conventions. The device-specific register map is essential.

### What layers does an embedded Ethernet interface involve? {M}
An embedded Ethernet interface consists of physical signaling hardware, a MAC, driver-managed buffers and higher-layer network software.

#### 1. Layer flow

```text
Application (MQTT / HTTP / custom)
            |
TCP or UDP
            |
IP / network stack
            |
Ethernet MAC driver / DMA descriptors
            |
MAC -- MII/RMII/RGMII/etc. -- PHY
            |
Magnetics / connector / network medium
```

The physical interface varies; the diagram represents a common copper Ethernet design.

#### 2. MAC versus PHY

The MAC handles Ethernet frame transmission/reception and related control. The PHY converts data to physical-medium signaling, handles link negotiation where applicable, and exposes link status. MDIO is commonly used to manage PHY registers.

#### 3. Driver responsibilities

Configure DMA rings and buffer ownership, handle interrupts or polling, maintain cache coherency, report link state and pass packets to the network stack. Linux often uses NAPI for efficient receive processing.

#### 4. Debugging

Check PHY power/clock/reset, link state, interface timing, MAC address, descriptor ownership and packet counters. A working link does not guarantee valid IP configuration.

**Interview takeaway:** Ethernet link, MAC frame delivery and IP/application connectivity are separate layers. Debug each layer with appropriate evidence.

### What is the difference between TCP and UDP for embedded devices? {E}
TCP and UDP are transport protocols over IP. TCP provides a reliable ordered byte stream; UDP provides individual datagrams without inherent delivery, ordering or duplicate-suppression guarantees.

| TCP | UDP |
|---|---|
| Connection-oriented | Connectionless transport |
| Retransmission and flow/congestion control | Application handles needed reliability |
| Byte stream, no message boundaries | Preserves datagram boundaries |
| Often suitable for reliable configuration/data | Often suitable for latency-sensitive telemetry |

#### 1. TCP example

A firmware configuration server receives a stream of bytes. One send does not necessarily correspond to one recv. Define message framing, handle partial sends/reads and detect connection failures.

#### 2. UDP example

A sensor broadcasts or sends periodic datagrams. Include sequence numbers and timestamps if missing or stale data must be detected. Avoid oversized datagrams and design for packet loss.

#### 3. Security

TCP and UDP do not provide encryption by themselves. Use suitable TLS, DTLS or another authenticated transport/protocol when required.

**Interview takeaway:** Choose based on whether every byte must arrive in order or whether timely individual messages are more important. Neither protocol guarantees a real-time deadline.

### What is MQTT, and how do you make an MQTT client secure? {M}
MQTT is a lightweight publish/subscribe application protocol commonly used for IoT messaging through a broker.

#### 1. Message flow

```text
Sensor client --> publish topic "sensor/temp" --> broker
                                                  |
                                         subscribed client
```

Publishers and subscribers do not need direct connections to each other. Topic names and subscription filters determine message delivery.

#### 2. Quality of Service

| QoS | Delivery semantics |
|---|---|
| 0 | At most once |
| 1 | At least once; duplicates possible |
| 2 | Exactly once at the MQTT protocol delivery level |

Application side effects still need idempotency or appropriate state handling, especially across retries and reconnects.

#### 3. Secure embedded client

Use authenticated TLS with server certificate validation, secure credential storage, per-client identity and restricted topic permissions. Keep trust roots and time validation appropriate to the platform. Do not disable certificate checks to fix connection errors.

#### 4. Reliability

Use bounded reconnect backoff, keepalive, explicit session/retained-message policy and a limited offline queue. Consider stale telemetry and local operation during network loss.

**Interview takeaway:** MQTT QoS controls messaging delivery, not device safety or confidentiality. Secure the connection, broker permissions and application-level handling separately.

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
