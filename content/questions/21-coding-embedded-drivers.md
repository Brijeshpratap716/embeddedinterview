---
slug: coding-embedded-drivers
title: "Coding: Embedded Drivers, Buffers & Schedulers"
icon: 🛠️
level: Intermediate
order: 21
desc: UART TX/RX, SPI and I2C transfer functions, busy-wait delays, lock-free SPSC ring buffers, overwrite and blocking queues, software timers, a cooperative scheduler, watchdog service, traffic-light and driver state machines, DMA descriptor rings.
---
These are the "write the driver code" questions from embedded interviews. Register names follow STM32-style conventions (`SR`, `DR`, flag bits) but the patterns apply to any MCU: wait with a timeout, never block forever, keep ISRs short, and make shared data safe between interrupt and task context. Each answer is brief: working C plus what the interviewer checks.

### Implement a delay without using a library function. {E}
**Short answer:** Use a free-running hardware counter and busy-wait until the required number of ticks has passed: on implementations with an available DWT cycle counter (`CYCCNT`), it gives cycle-count resolution for microsecond delays, and a 1 ms SysTick counter works for millisecond delays. Compare with unsigned subtraction `(now - start) < ticks`, which stays correct when the counter wraps around.

```c
#include <stdint.h>

/* Cortex-M3/M4/M7: cycle-accurate busy wait using the DWT cycle counter */
#define DEMCR      (*(volatile uint32_t *)0xE000EDFCu)
#define DWT_CTRL   (*(volatile uint32_t *)0xE0001000u)
#define DWT_CYCCNT (*(volatile uint32_t *)0xE0001004u)

extern uint32_t SystemCoreClock;                 /* Hz, set by the clock setup code */

void dwt_init(void)
{
    DEMCR |= (1u << 24);                         /* TRCENA: enable DWT */
    DWT_CYCCNT = 0;
    DWT_CTRL |= 1u;                              /* CYCCNTENA */
}

void delay_us(uint32_t us)
{
    uint32_t start = DWT_CYCCNT;
    uint64_t ticks64 = ((uint64_t)us * SystemCoreClock + 999999u) / 1000000u;
    /* Example API: reject unsupported delay lengths. */
    if (ticks64 > UINT32_MAX / 2u) return;
    uint32_t ticks = (uint32_t)ticks64;
    while ((uint32_t)(DWT_CYCCNT - start) < ticks) { }   /* wrap-safe */
}

/* millisecond delay from a 1 ms SysTick counter */
extern volatile uint32_t g_ms;
void delay_ms(uint32_t ms) { uint32_t s = g_ms; while ((uint32_t)(g_ms - s) < ms) { } }
```

**Points:** a plain `for (i = 0; i < N; i++);` loop is a bad delay: the optimiser can delete it, and its duration changes with clock speed, flash wait states and compiler flags (add `volatile` and calibrate if you must). Hardware counters give accurate timing; unsigned subtraction handles wrap-around. Busy delays waste CPU and power: use timers or an RTOS delay for anything long. (Cortex-M0/M0+ has no CYCCNT: use SysTick or a timer. On other cores check that CYCCNT exists, is enabled and runs in the intended power state.)

**Why unsigned subtraction is wrap-safe:** with a 32-bit counter, if `start = 0xFFFFFFF0` and `now = 0x00000010` after wrapping, `now - start` = 0x20 (32 ticks) in unsigned arithmetic — exactly the elapsed time. Comparing `now < start + ticks` instead breaks at the wrap.

**Numbers to know:** at 168 MHz, 1 µs = 168 cycles; `CYCCNT` wraps every 2³² / 168 MHz ≈ 25.6 s, so a single delay must be shorter than that.

**Choosing a delay method**

| Method | Resolution | CPU usage | Use |
|---|---|---|---|
| Calibrated `volatile` loop | rough | 100% | early boot before clocks/timers are set up |
| DWT `CYCCNT` busy-wait | 1 cycle | 100% | short µs delays (sensor timing, bit-banging) |
| SysTick ms counter busy-wait | 1 ms | 100% | simple bare-metal code |
| Hardware timer + interrupt / one-pulse mode | sub-µs | ~0% | precise delays without blocking |
| RTOS `vTaskDelay` | 1 tick | 0% (task blocked) | anything ≥ 1 tick in an RTOS |

**Pitfalls:** interrupts lengthen busy-wait delays (the delay is a **minimum**, not exact); `SystemCoreClock` must match the real clock after any frequency change; the DWT counter does not run on Cortex-M0/M0+ and may need the debug unit enabled; and busy loops prevent sleep modes, wasting power.

**Interview follow-up:** "How would you make a 10 µs delay accurate even with interrupts?" Briefly disable interrupts around it (if the system tolerates the latency) or use a hardware timer in one-pulse mode to generate the timing in hardware.

#### Worked example: counter wrap

At 80 MHz, a 10 µs delay corresponds to 800 cycles. If the initial 32-bit counter is 0xFFFFFFF0, after 800 cycles it is 0x00000310. Unsigned subtraction still gives 800 modulo 2^32. The counter must actually be running, the interval must be representable and the loop must observe it before a full wrap is missed. Clock changes, debug halt, sleep and interrupt preemption affect wall-clock accuracy. On unsupported DWT implementations, use a peripheral timer with a documented clock rate.

### Write a UART transmit routine (polled and interrupt-driven). {M}
**Short answer:** In the **polled** version, for each byte wait until the transmit data register is empty (`TXE`), then write the byte; at the end wait for transmission complete (`TC`) if the caller needs the line idle. In the **interrupt-driven** version, the caller copies data into a ring buffer and enables the TXE interrupt; the ISR moves one byte from the buffer to the data register each time TXE fires and disables the interrupt when the buffer is empty, so the CPU is free while bytes go out.

```c
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct { volatile uint32_t SR, DR, BRR, CR1; } uart_t;     /* simplified register map */
#define UART_SR_TXE   (1u << 7)                  /* transmit data register empty */
#define UART_SR_TC    (1u << 6)                  /* transmission complete */
#define UART_CR1_TXEIE (1u << 7)                 /* TXE interrupt enable */

/* polled, with a timeout so a broken UART cannot hang the system */
int uart_write_polled(uart_t *u, const uint8_t *buf, size_t len, uint32_t timeout)
{
    for (size_t i = 0; i < len; i++) {
        uint32_t t = timeout;
        while (!(u->SR & UART_SR_TXE)) {
            if (t == 0) return -1;
            --t;
        }
        u->DR = buf[i];
    }
    return 0;
}

/* interrupt-driven: application fills a ring buffer, the ISR drains it */
#define TXQ 256u
static volatile uint8_t  txq[TXQ];
static volatile uint16_t tx_head, tx_tail;      /* head written by app, tail by ISR */
static uart_t *g_uart;

bool uart_putc(uint8_t c)
{
    uint16_t next = (uint16_t)((tx_head + 1u) % TXQ);
    if (next == tx_tail) return false;           /* full: caller decides to wait or drop */
    txq[tx_head] = c;
    tx_head = next;
    g_uart->CR1 |= UART_CR1_TXEIE;               /* (re)enable TXE interrupt; in real code use an
                                                    atomic set or a critical section for this RMW */
    return true;
}

void UART_IRQHandler(void)
{
    if ((g_uart->SR & UART_SR_TXE) && (g_uart->CR1 & UART_CR1_TXEIE)) {
        if (tx_tail != tx_head) {
            g_uart->DR = txq[tx_tail];
            tx_tail = (uint16_t)((tx_tail + 1u) % TXQ);
        } else {
            g_uart->CR1 &= ~UART_CR1_TXEIE;      /* nothing left: stop TXE interrupts */
        }
    }
}
```

**Points:** wait for `TXE` before writing `DR`; wait for `TC` before disabling the UART or turning an RS-485 driver around (the last byte is still shifting out when TXE is set); always use timeouts in polled code; in the interrupt version, disable the TXE interrupt when the buffer empties, otherwise it fires continuously. For large transfers, use DMA.

**TXE vs TC (frequently asked)**

| Flag | Meaning | Use |
|---|---|---|
| TXE (TX empty) | the data register can accept the next byte (previous byte moved to the shift register) | feed the next byte |
| TC (transmission complete) | the shift register has finished sending the last bit, including the stop bit | before turning off an RS-485 driver, changing baud rate or entering low-power mode |

**Interrupt flow**

1. `uart_write()` puts bytes into the TX ring buffer (inside a short critical section if shared with the ISR) and sets `TXEIE`.
2. The ISR fires as soon as TXE is set: writes the next byte; if the buffer is now empty, clears `TXEIE`.
3. Optionally enable the `TC` interrupt to signal "all sent" (e.g. to release an RS-485 transmitter).

**Timing math:** at 115200 baud (8N1), each byte takes 86.8 µs. Polled transmission of a 100-byte message blocks the CPU for 8.7 ms; interrupt-driven transmission costs only a short ISR per byte; DMA costs nothing per byte.

**Design questions to discuss:** what happens when the TX buffer is full (block with timeout, drop, or return a partial count); thread safety when several tasks print (a mutex around `uart_write`, or a dedicated logging task); and the DMA approach for long or frequent transfers (configure source address and length, start, get a transfer-complete interrupt).

#### TXE versus TC

TXE means the transmit data register can accept another byte. TC means the final frame has completed transmission. For RS-485, keep the transceiver driver enabled until TC, not merely TXE; otherwise the last byte can be truncated. At 115200 baud with 8N1, a byte takes about 86.8 µs on the wire.

The interrupt-driven example assumes one producer, a single-core target and correctly synchronized queue publication and interrupt-enable updates. Protect the producer/ISR handoff using a short appropriate critical section or a verified atomic protocol. TXE interrupt must be disabled when there is no work, then re-enabled reliably after enqueue. A loop-count timeout is not a calibrated wall-clock timeout.

### Write a UART receive interrupt handler with a ring buffer. {E}
**Short answer:** In the RX interrupt, read the status register, read the received byte from the data register (which clears the RXNE flag), and store it in a ring buffer at the head index, dropping and counting it if the buffer is full. The application reads bytes from the tail index in the main loop or a task. With one producer (the ISR) and one consumer (the task), each index has a single writer, so no lock is needed on a single core.

```c
#include <stdint.h>
#include <stdbool.h>

#define UART_SR_RXNE (1u << 5)
#define UART_SR_ORE  (1u << 3)                   /* overrun error */
#define RXQ 128u                                 /* power of two */

static volatile uint8_t  rxq[RXQ];
static volatile uint16_t rx_head;                /* written only by the ISR */
static volatile uint16_t rx_tail;                /* written only by the reader */
static volatile uint32_t rx_dropped, rx_overruns;

void UART_RX_IRQHandler(uart_t *u)               /* called from the vector with the instance */
{
    uint32_t sr = u->SR;
    if (sr & (UART_SR_RXNE | UART_SR_ORE)) {
        uint8_t b = (uint8_t)u->DR;              /* reading DR clears RXNE (and ORE after SR read) */
        if (sr & UART_SR_ORE) rx_overruns++;
        uint16_t next = (uint16_t)((rx_head + 1u) & (RXQ - 1u));
        if (next != rx_tail) { rxq[rx_head] = b; rx_head = next; }
        else rx_dropped++;                       /* buffer full */
    }
}

bool uart_getc(uint8_t *c)                       /* called from the main loop or a task */
{
    if (rx_tail == rx_head) return false;
    *c = rxq[rx_tail];
    rx_tail = (uint16_t)((rx_tail + 1u) & (RXQ - 1u));
    return true;
}
```

**Points:** read `DR` in every path that clears the interrupt; check and count errors (overrun, framing, noise) instead of ignoring them; single producer (ISR) and single consumer means each index has one writer, so no lock is needed on a single core; count dropped bytes so you can size the buffer. On a Cortex-M7 or multi-core system, add barriers (see the lock-free SPSC question).

**ISR steps**

1. Read the status register once.
2. If an error flag is set (overrun ORE, framing FE, noise NE, parity PE): count it and clear it as the reference manual describes (often by reading SR then DR) — an uncleared overrun flag can block further reception on some MCUs.
3. If RXNE: read DR, compute `next = (head + 1) % N`; if `next != tail`, store the byte and publish `head = next`; otherwise increment a `dropped` counter.

**Buffer sizing:** bytes arriving during the longest time the consumer can be delayed, plus margin. At 115200 baud ≈ 11,520 bytes/s; if the task may be blocked for 20 ms, you need at least ~230 bytes → choose 256 or 512.

**Detecting message boundaries:** for line-based protocols, the consumer looks for `'\n'`; for binary protocols, use a length field or framing (SLIP, COBS) plus a CRC; for "end of burst", use the UART **IDLE line** interrupt.

**Faster alternative — DMA circular reception:** the DMA writes into a circular buffer by itself; firmware learns the head position from the DMA counter on the half-transfer, transfer-complete and IDLE interrupts. This removes the per-byte interrupt entirely, which matters above about 1 Mbaud.

**Common bugs:** forgetting `volatile`/atomic on the indices, processing data inside the ISR (keep it minimal), and signed/unsigned mix-ups in the index arithmetic.

#### RX overflow and error handling

With a ring of 128 slots and one reserved slot, usable capacity is 127 bytes. If the ISR receives another byte when full, it must still service/acknowledge the hardware as specified, increment a drop counter and apply the chosen overflow policy. Hardware overrun and software queue overflow are different failures.

The example models an older STM32-style SR/DR interface; newer UARTs may use ISR, RDR and ICR registers instead. On a status containing ORE without RXNE, do not enqueue a value unless the device documents valid data. The raw vector handler normally has a void(void) signature and calls an instance-specific helper. Use the atomic SPSC implementation or the platform's ISR synchronization rules rather than assuming volatile is universally sufficient.

### Write an SPI transfer function. {E}
**Short answer:** SPI is full duplex: every byte you send clocks one byte back in. A transfer routine asserts chip select, then for each byte waits for TXE, writes the byte to the data register, waits for RXNE and reads the received byte; after the last byte it waits until the BSY flag clears before releasing chip select. To read from a device you send dummy bytes (often 0xFF or 0x00) and keep what comes back.

```c
#include <stdint.h>
#include <stddef.h>

typedef struct { volatile uint32_t CR1, CR2, SR, DR; } spi_t;
#define SPI_SR_RXNE (1u << 0)
#define SPI_SR_TXE  (1u << 1)
#define SPI_SR_BSY  (1u << 7)

void cs_low(void);
void cs_high(void);

/* full duplex: every byte sent clocks one byte in */
int spi_transfer(spi_t *s, const uint8_t *tx, uint8_t *rx, size_t len, uint32_t timeout)
{
    int rc = 0;
    cs_low();
    for (size_t i = 0; i < len; i++) {
        uint32_t t = timeout;
        while (!(s->SR & SPI_SR_TXE))  if (t == 0 || --t == 0) { rc = -1; goto out; }
        *(volatile uint8_t *)&s->DR = tx ? tx[i] : 0xFF;          /* dummy byte for read-only */
        t = timeout;
        while (!(s->SR & SPI_SR_RXNE)) if (t == 0 || --t == 0) { rc = -1; goto out; }
        uint8_t b = *(volatile uint8_t *)&s->DR;                  /* always read to clear RXNE */
        if (rx) rx[i] = b;
    }
    { uint32_t t = timeout; while (s->SR & SPI_SR_BSY) { if (t == 0 || --t == 0) { rc = -1; goto out; } } }   /* last bit fully out */
out:
    cs_high();
    return rc;
}

/* typical register read from an SPI sensor: send address with the read bit, then clock out data */
int sensor_read_reg(spi_t *s, uint8_t reg, uint8_t *val)
{
    uint8_t tx[2] = { (uint8_t)(reg | 0x80u), 0xFF }, rx[2];
    int rc = spi_transfer(s, tx, rx, 2, 10000);
    *val = rx[1];                                                 /* rx[0] is clocked in during the address */
    return rc;
}
```

**Points:** SPI is full duplex, so you must read a byte for every byte written (or RXNE/overrun errors build up); send dummy bytes to read; wait for `BSY` to clear before releasing chip select; set the right mode (CPOL/CPHA), bit order and clock speed for the device; use byte access to `DR` on parts with a FIFO so the peripheral does not send 16 bits; use DMA for long transfers.

**Typical register read from an SPI sensor**

```
CS low
send  [reg | 0x80]  (read bit)  → receive garbage
send  0x00 (dummy)              → receive register value
CS high
```

**Why read for every write:** if you skip reading DR, the RX side overflows (OVR flag), and on some MCUs later reads return stale data or the peripheral stops.

**Why wait for BSY before raising CS:** TXE only means the data register is free; the last byte may still be shifting out. Raising CS too early truncates the last byte.

**Device settings to match:** SPI mode (CPOL/CPHA), bit order (usually MSB first), word size (8/16 bit), maximum clock rate, and CS setup/hold times from the device datasheet.

**Shared bus with several devices:** each device has its own CS; reconfigure mode and speed per device; protect the bus with a mutex in an RTOS so two tasks do not interleave transactions.

**Performance:** byte-by-byte polling has gaps between bytes (software overhead). For long transfers (displays, flash, SD cards), use DMA for both TX and RX channels and wait for the RX DMA complete (RX finishes last). On Linux, the equivalent is `spi_sync()` with `spi_transfer` structures or the `spidev` interface from user space.

#### Full-duplex register read example

For a sensor using bit 7 as a read-command flag, reading register 0x12 may transmit 0x92 followed by 0xFF. The first received byte may be undefined; the second may be the requested data. Check the sensor's exact opcode and dummy-cycle rules. Hold CS across both bytes, configure the correct CPOL/CPHA and wait for the documented end-of-transfer condition before deasserting CS. On timeout, stop or recover the controller according to its hardware rules; deasserting CS alone may not abort a running peripheral. Use a monotonic timer for production deadlines.

### Write I2C register read and write functions. {M}
**Short answer:** A **register write** is: START, device address + W, register address, data byte(s), STOP. A **register read** is: START, address + W, register address, then a **repeated START**, address + R, read the data bytes (ACK each except the last, which gets a NACK), STOP. Every step needs a timeout and a check for NACK, and the driver must be able to recover a stuck bus.

```c
#include <stdint.h>
#include <stddef.h>

/* Portable version on top of a bus primitive: write `wlen` bytes then (repeated START) read `rlen`.
   On Linux, the same primitive is the I2C_RDWR ioctl; on MCUs it wraps the I2C peripheral. */
int i2c_xfer(uint8_t addr7, const uint8_t *w, size_t wlen, uint8_t *r, size_t rlen);

int i2c_write_reg(uint8_t addr, uint8_t reg, const uint8_t *data, size_t len)
{
    uint8_t buf[1 + 16];
    if (len > 16) return -1;
    buf[0] = reg;                                     /* register address first */
    for (size_t i = 0; i < len; i++) buf[1 + i] = data[i];
    return i2c_xfer(addr, buf, 1 + len, NULL, 0);     /* START, addr+W, reg, data..., STOP */
}

int i2c_read_reg(uint8_t addr, uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_xfer(addr, &reg, 1, data, len);        /* START, addr+W, reg, RESTART, addr+R, data..., NACK, STOP */
}

/* Linux user-space implementation of the primitive */
#ifdef __linux__
#include <linux/i2c.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
extern int g_i2c_fd;                                  /* open("/dev/i2c-1", O_RDWR) */

int i2c_xfer(uint8_t addr7, const uint8_t *w, size_t wlen, uint8_t *r, size_t rlen)
{
    struct i2c_msg msgs[2];
    int n = 0;
    if (wlen) msgs[n++] = (struct i2c_msg){ .addr = addr7, .flags = 0, .len = (uint16_t)wlen, .buf = (uint8_t *)w };
    if (rlen) msgs[n++] = (struct i2c_msg){ .addr = addr7, .flags = I2C_M_RD, .len = (uint16_t)rlen, .buf = r };
    struct i2c_rdwr_ioctl_data d = { .msgs = msgs, .nmsgs = (uint32_t)n };
    return ioctl(g_i2c_fd, I2C_RDWR, &d) == n ? 0 : -1;
}
#endif
```

**Points:** a register read is a write of the register address followed by a **repeated START** and a read (no STOP in between, or some devices lose the address); the controller NACKs the last byte to tell the target to stop sending; check for NACK on the address (device missing) and on data; add timeouts and bus recovery (clock out 9 pulses if SDA is stuck low); respect the device's maximum burst length and page boundaries (EEPROMs); 16-bit register addresses send two address bytes, usually MSB first.

**Bus sequence for reading 2 bytes from register 0x0F of device 0x68**

```
S | 0xD0 (0x68<<1 | W) | A | 0x0F | A | Sr | 0xD1 (0x68<<1 | R) | A | data0 | A | data1 | N | P
```

**Error handling to include**

| Condition | Meaning | Action |
|---|---|---|
| NACK after the address | device missing, wrong address, or busy (EEPROM writing) | return `-ENODEV`/retry later |
| NACK after a data byte | device rejected the data/register | return an error |
| Timeout waiting for a flag | bus stuck (SDA or SCL held low), clock stretching too long | reset the peripheral, run bus recovery |
| Arbitration lost | another controller on the bus | retry after the bus is free |

**Bus recovery:** if a device holds SDA low (it was reset in the middle of a read), switch SCL to GPIO, clock up to 9 pulses until SDA is released, generate a STOP, then re-initialise the I2C peripheral.

**Device-specific details:** EEPROMs need page-aligned writes and a write-cycle delay (poll with address NACK until ready); multi-byte registers may need an auto-increment bit in the register address; some devices require no STOP between write and read (repeated START).

**On Linux:** `i2c_smbus_read_byte_data()` / `i2c_transfer()` in drivers, or `ioctl(I2C_RDWR)` from user space with `/dev/i2c-N`.

#### Read sequence for a two-byte register value

```text
S | 0xA0 | ACK | 0x10 | ACK
Sr| 0xA1 | ACK | MSB  | ACK | LSB | NACK | P
```

The target's unshifted address is 0x50. The register pointer is written first, followed by a repeated START for reading. Decode the two data bytes according to the target's byte order, e.g. ((uint16_t)data[0] << 8) | data[1] for big-endian data. Validate length, address, buffers and transfer result; an I2C_RDWR call succeeds fully only when its return equals the number of requested messages. Check that lengths fit the message structure's fields and controller limits. Use a synchronous primitive for the local stack buffers, not an asynchronous submission that outlives them.

### Implement a lock-free single-producer single-consumer (SPSC) ring buffer. {H}
**Short answer:** Use a power-of-two buffer with two free-running indices: only the producer writes `head`, only the consumer writes `tail`. The producer writes the data, then publishes the new head with a **release** store; the consumer reads head with an **acquire** load before reading the data, then publishes the new tail with a release store. Full is `head - tail == N`, empty is `head == tail`. No locks, no disabled interrupts, O(1) per operation.

```c
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>

#define RING_SIZE 1024u                               /* power of two */

typedef struct {
    uint8_t buf[RING_SIZE];
    _Atomic uint32_t head;                            /* written only by the producer */
    _Atomic uint32_t tail;                            /* written only by the consumer */
} ring_t;

bool ring_push(ring_t *r, uint8_t v)                  /* producer: ISR, or thread A */
{
    uint32_t h = atomic_load_explicit(&r->head, memory_order_relaxed);
    uint32_t t = atomic_load_explicit(&r->tail, memory_order_acquire);
    if (h - t == RING_SIZE) return false;             /* full (indexes run freely and wrap) */
    r->buf[h & (RING_SIZE - 1u)] = v;
    atomic_store_explicit(&r->head, h + 1u, memory_order_release);   /* publish after the data */
    return true;
}

bool ring_pop(ring_t *r, uint8_t *v)                  /* consumer: task, or thread B */
{
    uint32_t t = atomic_load_explicit(&r->tail, memory_order_relaxed);
    uint32_t h = atomic_load_explicit(&r->head, memory_order_acquire);
    if (h == t) return false;                         /* empty */
    *v = r->buf[t & (RING_SIZE - 1u)];
    atomic_store_explicit(&r->tail, t + 1u, memory_order_release);   /* free the slot after reading */
    return true;
}
```

**Answers to the usual follow-ups**

- **Is it thread-safe?** Yes for exactly **one** producer and **one** consumer, because each index has a single writer. Multiple producers or consumers need a lock or a CAS-based design.
- **ISR writes, thread reads?** That is the classic use; on a single-core MCU the ISR and the task never run truly in parallel, but the compiler must still not reorder the data write after the index update, which the atomics (or `volatile` + a compiler barrier) guarantee.
- **Where are barriers needed?** The producer must make the data visible **before** the new head (release); the consumer must read the head **before** the data (acquire). On Cortex-M7, Cortex-A and multi-core parts these compile to `DMB`s or `LDAR`/`STLR`.
- **Head/tail overflow?** The indexes are free-running 32-bit counters; `h - t` is still correct after they wrap because of unsigned arithmetic, and using all `RING_SIZE` slots needs no "one slot empty" rule.
- **Why a power-of-two size?** `& (SIZE - 1)` replaces a slow modulo, and wrap-around of the free-running counters stays consistent only if SIZE divides 2³².
- **No atomics (Cortex-M0, old compiler)?** Make the indexes `volatile`, aligned 32-bit (atomic loads/stores on Arm), and put a compiler barrier between the data write and the index update.

**Why it is safe without a lock**

- **Single writer per variable:** no read-modify-write races on the indices.
- **Ordering:** release/acquire guarantees that when the consumer sees the new `head`, the data written before it is also visible (important on Cortex-M7, Cortex-A and multi-core systems with out-of-order memory systems).
- **Atomic index size:** 32-bit loads and stores are single instructions on 32-bit MCUs.

**Free-running indices:** the indices only ever increase and wrap naturally at 2³²; `head - tail` (unsigned) is always the number of items, and `index & (N - 1)` picks the slot. This uses every slot (no "one empty slot" rule) and handles wrap-around for free, as long as N is a power of two.

**Dry run (N = 4):** producer writes items at head 0, 1, 2, 3 → `head - tail = 4` → full. Consumer reads one → tail = 1 → producer may write again into slot `4 & 3 = 0`.

**Where it is used:** UART RX ISR → task, audio DMA → processing task, inter-core mailboxes (with cache maintenance or uncached memory), Linux `kfifo`, and the virtio/virtqueue rings between guest and host.

**Limits:** exactly one producer and one consumer. With several producers, use a lock, a CAS-based multi-producer queue, or one SPSC queue per producer.

#### Why two release/acquire pairs are required

Producer writes payload, then release-stores head. Consumer acquire-loads head before reading payload. Consumer release-stores tail only after reading; producer acquire-loads tail before reusing that slot. This protects both initial publication and subsequent slot reuse. With unsigned monotonic indices, occupancy is head−tail modulo 2^32 and the valid range is zero through capacity. Masking applies only to physical indexing, so every slot is usable.

Initialize both atomic indices before starting either context. Confirm the atomic operations are lock-free on the target before ISR use, and never reset the indices concurrently. This is not an MPMC queue or a DMA cache-management scheme.

### Implement a ring buffer that overwrites the oldest data when full. {M}
**Short answer:** When the buffer is full, a new item is still written at the head position and the oldest item is discarded by advancing the tail (or by keeping only a head index and a count). The buffer therefore always holds the most recent N items, which is exactly what logging and 'last N samples' buffers need.

```c
#include <stdint.h>
#include <stdbool.h>

#define LOG_SIZE 64u                                   /* power of two */
typedef struct { int16_t buf[LOG_SIZE]; uint32_t head, count; } log_ring_t;

void log_push(log_ring_t *r, int16_t v)
{
    r->buf[r->head] = v;
    r->head = (r->head + 1u) & (LOG_SIZE - 1u);
    if (r->count < LOG_SIZE) r->count++;              /* once full, the oldest entry is overwritten */
}

/* i = 0 is the oldest entry still stored */
bool log_get(const log_ring_t *r, uint32_t i, int16_t *v)
{
    if (i >= r->count) return false;
    uint32_t oldest = (r->head - r->count) & (LOG_SIZE - 1u);
    *v = r->buf[(oldest + i) & (LOG_SIZE - 1u)];
    return true;
}
```

**Points:** used for "last N samples" (oscilloscope pre-trigger buffers, moving averages) and crash logs ("last N events before the fault", often kept in a `.noinit` RAM section). The oldest index is derived from `head` and `count`. If a separate reader consumes concurrently, overwriting means the writer also moves the reader's tail, which needs a lock or a sequence counter.

**Dry run (N = 3):** write 1, 2, 3 → [1 2 3] full; write 4 → overwrite the oldest → contents in order 2, 3, 4; write 5 → 3, 4, 5.

**Reading out in chronological order:** the oldest element is at `(head - count) mod N`; iterate `count` elements from there.

**Overwrite vs reject**

| Policy | Use |
|---|---|
| Overwrite oldest | event logs, crash history, pre-trigger capture, telemetry where the latest data matters most |
| Reject newest (return "full") | commands, protocol messages, anything that must not silently lose data |

**Concurrency caveat:** in overwrite mode the producer also moves the tail, so the producer and consumer both write the tail — the lock-free SPSC guarantee no longer holds. Options: a short critical section around reads, a sequence number per entry so the reader can detect that it was overwritten, or have the reader copy the whole buffer snapshot while the writer is paused.

**Crash-log trick:** place the buffer in a `.noinit` RAM section (not zeroed at reset) with a magic number, so after a watchdog reset the firmware can dump the last events that happened before the crash.

### Implement a blocking producer-consumer ring buffer (mutex + condition variable). {M}
**Short answer:** Protect the buffer with a mutex and use two condition variables: producers wait on `not_full` while the buffer is full, consumers wait on `not_empty` while it is empty. After a put, signal `not_empty`; after a get, signal `not_full`. Always wait inside a `while` loop that re-checks the condition after waking.

```c
#include <pthread.h>
#include <stdint.h>

#define BQ_SIZE 16u
typedef struct {
    uint8_t buf[BQ_SIZE];
    unsigned head, tail, count;
    pthread_mutex_t m;
    pthread_cond_t not_empty, not_full;
} bqueue_t;

#define BQUEUE_INIT { .m = PTHREAD_MUTEX_INITIALIZER, \
                      .not_empty = PTHREAD_COND_INITIALIZER, .not_full = PTHREAD_COND_INITIALIZER }

void bq_put(bqueue_t *q, uint8_t v)
{
    pthread_mutex_lock(&q->m);
    while (q->count == BQ_SIZE) pthread_cond_wait(&q->not_full, &q->m);
    q->buf[q->head] = v; q->head = (q->head + 1u) % BQ_SIZE; q->count++;
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->m);
}

uint8_t bq_get(bqueue_t *q)
{
    pthread_mutex_lock(&q->m);
    while (q->count == 0) pthread_cond_wait(&q->not_empty, &q->m);
    uint8_t v = q->buf[q->tail]; q->tail = (q->tail + 1u) % BQ_SIZE; q->count--;
    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->m);
    return v;
}
```

**Points:** wait in a `while` loop (spurious wake-ups, several consumers); the mutex protects all queue state; signal the other condition after changing the count. Works with many producers and consumers. Never call this from an ISR (it blocks): in an RTOS the equivalent is a message queue (`xQueueSend` / `xQueueReceive`), with `FromISR` variants for interrupts.

**Why a `while`, not an `if`**

- **Spurious wake-ups:** `pthread_cond_wait` may return without a signal.
- **Stolen wake-ups:** with several consumers, another consumer may take the item between the signal and this thread re-acquiring the mutex.

**Why `pthread_cond_wait` takes the mutex:** it atomically releases the mutex and sleeps, then re-acquires the mutex before returning, so no signal can be lost between checking the condition and going to sleep.

**Sequence of a put**

1. `pthread_mutex_lock(&m)`
2. `while (count == N) pthread_cond_wait(&not_full, &m);`
3. Store the item, advance head, `count++`.
4. `pthread_cond_signal(&not_empty);`
5. `pthread_mutex_unlock(&m)`

**Extensions interviewers ask:** timeouts (`pthread_cond_timedwait` with an absolute `CLOCK_MONOTONIC` deadline), shutdown (a `closing` flag plus `pthread_cond_broadcast` so blocked threads wake up and exit), and signal vs broadcast (signal wakes one waiter — enough when any waiter can make progress).

**RTOS equivalent:** a FreeRTOS queue (`xQueueSend`/`xQueueReceive` with a block time) implements exactly this, including the waiting lists, and adds `FromISR` variants so interrupts can produce without blocking.

### Implement an ISR-safe queue (interrupt producer, task consumer) using a critical section. {M}
**Short answer:** Let the ISR enqueue and the task dequeue, and protect any state that both sides modify. If the design keeps a shared `count`, the task must disable the relevant interrupt (a short critical section) while it updates the queue, because the ISR could fire in the middle of its read-modify-write. The ISR itself needs no lock on a single core, since the task cannot run while the ISR runs (unless a higher-priority ISR also uses the queue).

```c
#include <stdint.h>
#include <stdbool.h>

typedef struct { uint16_t id; uint8_t len; uint8_t data[8]; } msg_t;   /* e.g. a CAN frame */
#define MQ 16u

static msg_t mq[MQ];
static volatile unsigned mq_head, mq_tail, mq_count;

uint32_t irq_save(void);            /* save PRIMASK and disable interrupts */
void     irq_restore(uint32_t s);

bool mq_put_from_isr(const msg_t *m)               /* called only from the ISR */
{
    if (mq_count == MQ) return false;
    mq[mq_head] = *m;
    mq_head = (mq_head + 1u) % MQ;
    mq_count++;
    return true;
}

bool mq_get(msg_t *out)                            /* called from task context */
{
    bool ok = false;
    uint32_t s = irq_save();                       /* short critical section: copy one message */
    if (mq_count) {
        *out = mq[mq_tail];
        mq_tail = (mq_tail + 1u) % MQ;
        mq_count--;
        ok = true;
    }
    irq_restore(s);
    return ok;
}
```

**Points:** the shared `count` is modified by both sides, so the task side needs a critical section (the ISR cannot be interrupted by the task on a single core, so it needs none, unless a higher-priority ISR also uses the queue). Keep the critical section to a single copy. Alternatives: the lock-free SPSC ring (no shared counter), or an RTOS queue with `xQueueSendFromISR` and a context-switch request.

**The race being prevented**

```
task: load count (5)      ← ISR fires here: count = 6
task: store count - 1 (4) ← the ISR's increment is lost; count is now wrong
```

**Critical section options on Cortex-M**

| Method | Effect |
|---|---|
| `__disable_irq()` / restore PRIMASK | blocks all maskable interrupts (simplest) |
| Raise `BASEPRI` | blocks only interrupts at or below a priority; urgent ISRs still run |
| `NVIC_DisableIRQ(irq)` | blocks only the producing interrupt |
| RTOS `taskENTER_CRITICAL()` | the RTOS's own version (BASEPRI on Cortex-M3+) |

**Keep it short:** copy one item (or just update the index) inside the critical section, not the processing. Interrupt latency grows by the length of the critical section.

**Signalling the task:** after enqueueing, the ISR can give a semaphore or send a task notification (`vTaskNotifyGiveFromISR` + `portYIELD_FROM_ISR`) so the task blocks instead of polling, which saves CPU and power.

**Alternative without any critical section:** the SPSC ring with separate head/tail indices (no shared count), as in the lock-free question.

### Implement a software timer module. {M}
**Short answer:** Keep a table of timers, each with an expiry time, a period (0 for one-shot), an active flag and a callback. A 1 ms tick interrupt only increments a time counter; the main loop (or a timer task) calls `timer_process()`, which compares each active timer's expiry with the current time using a wrap-safe signed difference, runs the callback for expired timers, and re-arms periodic ones by adding the period to the previous expiry.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef void (*timer_cb_t)(void *arg);
typedef struct { uint32_t expiry, period; timer_cb_t cb; void *arg; bool active; } swtimer_t;

#define MAX_TIMERS 8
static swtimer_t timers[MAX_TIMERS];
extern volatile uint32_t g_ms;                        /* 1 ms tick */

int timer_start(uint32_t delay_ms, uint32_t period_ms, timer_cb_t cb, void *arg)
{
    for (int i = 0; i < MAX_TIMERS; i++) {
        if (!timers[i].active) {
            timers[i] = (swtimer_t){ g_ms + delay_ms, period_ms, cb, arg, true };
            return i;                                  /* handle */
        }
    }
    return -1;
}

void timer_stop(int h) { if (h >= 0 && h < MAX_TIMERS) timers[h].active = false; }

void timer_poll(void)                                 /* call from the main loop / a timer task */
{
    uint32_t now = g_ms;
    for (int i = 0; i < MAX_TIMERS; i++) {
        swtimer_t *t = &timers[i];
        if (t->active && (int32_t)(now - t->expiry) >= 0) {   /* wrap-safe "now >= expiry" */
            if (t->period) t->expiry += t->period;            /* periodic: no drift */
            else t->active = false;                           /* one-shot */
            t->cb(t->arg);
        }
    }
}
```

**Points:** wrap-safe comparison with signed difference; periodic timers add the period to the old expiry (not to "now") so they do not drift; callbacks run in the main loop, not in the tick ISR, so they can take time (but must not block). Scaling up: keep timers in a list sorted by expiry (or a timer wheel) so each tick checks only the first one, and program a hardware timer for the next expiry (tickless) to save power. RTOS equivalents: FreeRTOS software timers (run in the timer service task), Zephyr `k_timer`.

**Wrap-safe comparison:** `(int32_t)(now - expiry) >= 0` is true when `now` has reached `expiry`, even when the 32-bit counter wraps (valid as long as timeouts are shorter than 2³¹ ticks ≈ 24.8 days at 1 kHz).

**Drift-free periodic timers:** `expiry += period` keeps the long-term rate exact even if a callback runs late; `expiry = now + period` would accumulate the lateness every period.

**Dry run:** timer A one-shot at 100 ms, timer B periodic 50 ms. At t = 50 → B fires, B.expiry = 100. At t = 100 → A fires (deactivated) and B fires, B.expiry = 150.

**API to present**

| Function | Purpose |
|---|---|
| `timer_start(id, delay, period, cb, arg)` | arm a timer |
| `timer_stop(id)` | cancel |
| `timer_process()` | run expired callbacks (main loop / timer task) |
| `timer_next_expiry()` | how long the CPU may sleep (tickless low power) |

**Scaling up:** a sorted list or min-heap of timers makes `timer_process` check only the earliest one; hierarchical timer wheels (Linux) give O(1) insert and expiry; programming a hardware compare register for the next expiry allows tickless sleep.

**Pitfalls:** running callbacks inside the tick ISR (they then delay all other interrupts), modifying the timer table from an ISR without protection, and starting/stopping a timer from inside its own callback (design the loop to handle it).

### Implement a simple cooperative task scheduler. {M}
**Short answer:** Store tasks in a table with a function pointer, a period and the next run time. The main loop repeatedly checks each task: if its time has come, it calls the function and adds the period to its next run time. Each task must do a little work and return quickly (no blocking), so the scheduler needs no stacks, no context switching and no locks between tasks.

```c
#include <stdint.h>

typedef struct {
    void (*run)(void);
    uint32_t period_ms;
    uint32_t next_ms;
} task_t;

static void task_led(void);
static void task_sensor(void);
static void task_comms(void);

static task_t tasks[] = {
    { task_led,     500, 0 },
    { task_sensor,   10, 0 },
    { task_comms,     1, 0 },
};

extern volatile uint32_t g_ms;

void scheduler_run(void)
{
    for (;;) {
        uint32_t now = g_ms;
        for (unsigned i = 0; i < sizeof tasks / sizeof tasks[0]; i++) {
            if ((int32_t)(now - tasks[i].next_ms) >= 0) {
                tasks[i].next_ms += tasks[i].period_ms;    /* fixed rate */
                tasks[i].run();                            /* must return quickly: no blocking */
            }
        }
        /* __WFI();  sleep until the next tick interrupt */
    }
}
```

**Points:** each task is a function that does a small amount of work and returns (long jobs become state machines); tasks run in table order, so order sets priority on ties; the worst-case response time is the sum of the longest task runs, so measure task execution times; no task stacks or context switches, so it is tiny and easy to debug. Add an overrun check (`next_ms` falling behind `now`) to detect overload. When you need pre-emption or blocking APIs, move to an RTOS.

**Dry run (1 ms tick):** tasks: `read_sensors` every 10 ms, `update_display` every 100 ms, `blink_led` every 500 ms. At t = 0 all run; at t = 10, 20 … only `read_sensors`; at t = 100 both `read_sensors` and `update_display` run; at t = 500 all three run.

**Turning long jobs into state machines:** a task that would wait (e.g. for an ADC conversion) instead starts the conversion, records its state and returns; on the next call it checks whether the result is ready.

**Worst-case response time:** a task can be delayed by every other task that runs before it in the same loop pass, so latency ≈ sum of the longest execution times. Measure execution times (DWT cycle counter or GPIO toggles) and keep each task short.

**Cooperative vs pre-emptive (RTOS)**

| | Cooperative loop | Pre-emptive RTOS |
|---|---|---|
| Code size / RAM | tiny, one stack | kernel + one stack per task |
| Shared data | safe between tasks (no pre-emption); only ISRs need care | needs mutexes/queues |
| Latency for urgent work | bounded by the longest task | bounded by kernel latency |
| Blocking calls | not allowed | allowed |

**Improvements:** priority order in the table, overrun detection (log when `now` is already past the next run time by more than one period), idle sleep (`__WFI()`) when no task is due, and a watchdog kick after a full pass.

### Write a watchdog service routine. {E}
**Short answer:** Configure an independent watchdog timer early in start-up and refresh ('kick') it only when the whole system is healthy. A robust design has every critical task set its bit in a 'checked-in' word; a supervisor kicks the watchdog only when all bits are set, then clears them for the next period. If any task hangs, the watchdog is not refreshed and the MCU resets.

```c
#include <stdint.h>
#include <stdbool.h>

#define IWDG_KR (*(volatile uint32_t *)0x40003000u)      /* STM32 independent watchdog key register */
#define TASK_SENSOR (1u << 0)
#define TASK_COMMS  (1u << 1)
#define TASK_CTRL   (1u << 2)
#define ALL_ALIVE   (TASK_SENSOR | TASK_COMMS | TASK_CTRL)

static volatile uint32_t alive_flags;

void wdg_checkin(uint32_t task_bit)                      /* each task calls this when it completes a cycle */
{
    __atomic_fetch_or(&alive_flags, task_bit, __ATOMIC_RELAXED);
}

void wdg_service(void)                                   /* called periodically, e.g. every 100 ms */
{
    if ((alive_flags & ALL_ALIVE) == ALL_ALIVE) {
        IWDG_KR = 0xAAAAu;                               /* reload (kick) the watchdog */
        __atomic_store_n(&alive_flags, 0u, __ATOMIC_RELAXED);
    }
    /* else: do not kick; the watchdog resets the MCU */
}
```

**Points:** kick only when **every** critical task has proven it is running, not from a timer interrupt alone; use a window watchdog to also catch code that runs too fast; record the reset cause at boot; freeze the watchdog in debug halt. On Cortex-M0 (no atomic OR instructions) wrap the read-modify-write in a short critical section.

**Why not kick from a timer interrupt:** the interrupt keeps running even if the main loop or a task is stuck, so the watchdog would never fire — the most common watchdog design mistake.

**Independent vs window watchdog**

| Type | Detects | Notes |
|---|---|---|
| Independent (IWDG) | code stopped or too slow | own low-speed clock, keeps running if the main clock fails |
| Window (WWDG) | too slow **or too fast** | refreshing too early also resets: catches runaway loops that kick repeatedly |
| External watchdog chip | MCU completely dead, clock failure | safety designs |

**Choosing the timeout:** longer than the worst-case normal loop or task period (including flash erase operations — kick or pause the watchdog around long erases), short enough that recovery time is acceptable (typically 100 ms – a few seconds).

**At boot:** read and log the reset cause (watchdog, brown-out, pin, software) and any crash record; count consecutive watchdog resets and enter a safe/recovery mode if they repeat (to avoid a reset loop).

**During debugging:** freeze the watchdog when the core is halted (`DBGMCU` freeze bits on STM32), otherwise breakpoints cause resets.

**Note:** once enabled, an independent watchdog usually cannot be disabled by software (by design) until the next reset.

### Implement a state machine for a traffic light. {E}
**Short answer:** Model the light as a set of states (for example RED, RED_AMBER, GREEN, AMBER), each with an output pattern and a duration, stored in a constant table along with the next state. The main loop checks whether the current state's time has elapsed (using a timestamp, not a blocking delay); if so, it moves to the next state and sets the lamp outputs for that state.

```c
#include <stdint.h>

typedef enum { RED, RED_AMBER, GREEN, AMBER } light_t;

typedef struct { light_t next; uint32_t duration_ms; uint8_t lamps; } state_info_t;
#define L_RED 4u
#define L_AMB 2u
#define L_GRN 1u

static const state_info_t fsm[] = {
    [RED]       = { RED_AMBER, 20000, L_RED },
    [RED_AMBER] = { GREEN,      2000, L_RED | L_AMB },
    [GREEN]     = { AMBER,     20000, L_GRN },
    [AMBER]     = { RED,        3000, L_AMB },
};

void set_lamps(uint8_t mask);
extern volatile uint32_t g_ms;

void traffic_light_task(void)                     /* call often from the main loop */
{
    static light_t state = RED;
    static uint32_t entered;
    static int started;
    if (!started) { started = 1; entered = g_ms; set_lamps(fsm[state].lamps); }
    if ((uint32_t)(g_ms - entered) >= fsm[state].duration_ms) {
        state = fsm[state].next;
        entered = g_ms;
        set_lamps(fsm[state].lamps);              /* entry action */
    }
}
```

**Points:** a `const` table describes states, durations and outputs (easy to check against the specification); timing uses timestamps, not blocking delays; outputs are set on state entry. Extensions interviewers ask for: a pedestrian button (an event that shortens GREEN), a fault state (flashing amber) entered on lamp failure, and a safe start-up state (all red).

**State table (UK-style sequence)**

| State | Red | Amber | Green | Duration | Next |
|---|---|---|---|---|---|
| RED | on | off | off | 30 s | RED_AMBER |
| RED_AMBER | on | on | off | 2 s | GREEN |
| GREEN | off | off | on | 25 s | AMBER |
| AMBER | off | on | off | 3 s | RED |

**Why table-driven:** the behaviour can be checked line by line against the specification, changing timings does not touch the logic, and adding a state is a new row.

**Why timestamps instead of `delay()`:** a blocking delay of 30 s means the controller cannot react to a pedestrian button, a fault input or communication during that time. With `if ((now - entered_at) >= duration)` the loop keeps running.

**Extensions interviewers ask for**

- Pedestrian request: an event that shortens GREEN (but respects a minimum green time) and inserts a WALK phase.
- Fault handling: lamp failure or conflict detection → FLASHING_AMBER state, entered from any state.
- Safe start-up: begin in ALL_RED for a few seconds.
- Two directions: states describe both roads, and the table guarantees they are never green together (a safety property you can check with an assertion in every state).

**Event-driven form:** `next = transition[state][event]` handles both timeouts and inputs uniformly (see the next question).

### Implement a finite state machine for a device driver. {M}
**Short answer:** Represent the driver as a per-device context with a current state, and convert everything that happens — API calls, interrupts, timeouts — into events. A transition function (a `switch` on the state, or a state × event table) decides, for each event, the action to perform and the next state. Events that are illegal in the current state are rejected, and errors move to a recovery state with limited retries.

```c
#include <stdint.h>

typedef enum { DRV_OFF, DRV_INIT, DRV_IDLE, DRV_BUSY, DRV_ERROR } drv_state_t;
typedef enum { EV_POWER_ON, EV_INIT_OK, EV_INIT_FAIL, EV_START, EV_DONE, EV_FAULT, EV_RESET } drv_event_t;

typedef struct { drv_state_t state; uint8_t retries; } drv_t;

void hw_power_on(void); void hw_start_transfer(void); void hw_reset(void); void report(int err);

void drv_handle(drv_t *d, drv_event_t ev)
{
    switch (d->state) {
    case DRV_OFF:
        if (ev == EV_POWER_ON) { hw_power_on(); d->retries = 0; d->state = DRV_INIT; }
        break;
    case DRV_INIT:
        if (ev == EV_INIT_OK) d->state = DRV_IDLE;
        else if (ev == EV_INIT_FAIL) {
            if (++d->retries < 3) hw_power_on();           /* retry */
            else { report(1); d->state = DRV_ERROR; }
        }
        break;
    case DRV_IDLE:
        if (ev == EV_START) { hw_start_transfer(); d->state = DRV_BUSY; }
        break;
    case DRV_BUSY:
        if (ev == EV_DONE) d->state = DRV_IDLE;
        else if (ev == EV_FAULT) { report(2); d->state = DRV_ERROR; }
        break;
    case DRV_ERROR:
        if (ev == EV_RESET) { hw_reset(); d->retries = 0; d->state = DRV_INIT; }
        break;
    }
    /* events not handled in a state are ignored here; log them in real code */
}
```

**Points:** the driver's API calls and interrupts become events; the state decides what is legal (e.g. `EV_START` is ignored or rejected unless IDLE); errors move to a recovery state with limited retries; the state is per device instance (a struct), so several devices can share the code. Feed events from ISRs through a queue so the FSM runs in one context.

**Example states for a sensor/ADC driver**

```
UNINIT --init--> IDLE --start--> BUSY --irq_done--> DATA_READY --read--> IDLE
                  ^                |  \--timeout/err--> ERROR --reset(ok)--> IDLE
                  |                                       \--retries exceeded--> FAULT
                  +---------------------------------------- stop (from BUSY) ----+
```

**Why FSMs suit drivers**

- Interrupt-driven hardware is naturally event based.
- Each state documents what is allowed: `start` in BUSY returns `-EBUSY` instead of corrupting a transfer in progress.
- Error recovery becomes explicit and testable (feed events in unit tests and check the transitions).

**Running the FSM in one context:** ISRs should only post events to a queue; the FSM runs in a task or the main loop, so state changes are never interleaved and no locking is needed inside the FSM.

**Implementation choices**

| Style | Pros | Cons |
|---|---|---|
| `switch (state)` with nested `switch (event)` | readable, flexible actions | grows long |
| Table of `{next_state, action_fn}` per state/event | compact, data-driven, easy to review | actions separate from the table |
| State functions (`state = state(event)`) | each state self-contained | harder to see the whole picture |
| Hierarchical (QP framework, UML statecharts) | shared behaviour in parent states | more machinery |

**Testing:** a transition coverage test that feeds every event in every state; log every transition (state, event, next) to a trace buffer for field debugging.

### Implement atomic bit set and clear on a shared flags word. {M}
**Short answer:** `flags |= bit` is a load, OR and store, so an interrupt or another core can change the word in between and one update is lost. Use an atomic read-modify-write: C11 `atomic_fetch_or` / `atomic_fetch_and` (LDREX/STREX loops on Cortex-M3 and above), or on cores without exclusive instructions, a tiny critical section that disables interrupts around the read-modify-write.

```c
#include <stdatomic.h>
#include <stdint.h>
#include <stdbool.h>

static _Atomic uint32_t flags;

static inline void flag_set(unsigned n)    { atomic_fetch_or_explicit(&flags,  1u << n,  memory_order_relaxed); }
static inline void flag_clear(unsigned n)  { atomic_fetch_and_explicit(&flags, ~(1u << n), memory_order_relaxed); }
static inline bool flag_test(unsigned n)   { return (atomic_load_explicit(&flags, memory_order_relaxed) >> n) & 1u; }
static inline bool flag_test_and_clear(unsigned n)
{
    return (atomic_fetch_and_explicit(&flags, ~(1u << n), memory_order_acq_rel) >> n) & 1u;
}
```

**Points:** `flags |= bit` is a non-atomic read-modify-write; C11 atomics compile to an `LDREX`/`STREX` retry loop on Cortex-M3+ (or single `LDSET`/`LDCLR` instructions on Armv8.1-A). On Cortex-M0/M0+, which lack exclusives, the compiler calls a library helper that disables interrupts; doing that yourself in a tiny critical section is equivalent. For hardware registers, use the peripheral's set/clear registers or bit-banding instead (atomic instructions often do not work on device memory). `test_and_clear` is the typical "consume an event flag" operation.

**The lost update**

```
task: r = flags            (0b0001)
      ISR: flags |= 0b0100 (now 0b0101)
task: flags = r | 0b0010   (0b0011)  ← the ISR's bit is lost
```

**How LDREX/STREX works:** `LDREX` loads the value and marks the address as exclusively monitored; `STREX` stores only if nothing touched that address (or an exception occurred) since the `LDREX`, and returns failure otherwise, so the code retries. This gives an atomic update without disabling interrupts.

**Alternatives worth mentioning**

| Technique | Where |
|---|---|
| Bit-banding (alias address per bit, single write sets/clears one bit atomically) | Cortex-M3/M4 SRAM and peripheral regions only |
| Peripheral set/clear registers (GPIO `BSRR`, `ODR` set/clear, NVIC ISER/ICER) | hardware registers designed for atomic bit access |
| One variable (byte/word) per flag | each flag has one writer; reads and writes of aligned words are atomic |
| RTOS event groups / task notifications | flags plus waiting |
| Linux `set_bit()`, `clear_bit()`, `test_and_set_bit()` | kernel atomic bitops |

**Test-and-set:** `atomic_fetch_or` returns the old value, so `if (!(atomic_fetch_or(&flags, BIT) & BIT))` tells you whether this caller was the one that set it — useful for "only one context may start this operation".

### Parse a hardware status register into named fields. {E}
**Short answer:** Read the register **once** into a local variable, then extract each field with mask-then-shift: `(val & FIELD_Msk) >> FIELD_Pos`. Define every field's position and mask once in macros (or use `FIELD_GET`/`GENMASK` style helpers), and fill a struct of named values that the rest of the code uses.

```c
#include <stdint.h>
#include <stdbool.h>

/* example: bit 0 READY, bit 1 ERROR, bits 4..6 MODE, bits 8..15 FIFO level */
#define ST_READY       (1u << 0)
#define ST_ERROR       (1u << 1)
#define ST_MODE_Pos    4u
#define ST_MODE_Msk    (7u << ST_MODE_Pos)
#define ST_FIFO_Pos    8u
#define ST_FIFO_Msk    (0xFFu << ST_FIFO_Pos)
#define FIELD_GET(reg, f) (((reg) & f##_Msk) >> f##_Pos)

typedef struct { bool ready, error; uint8_t mode, fifo_level; } status_t;

status_t parse_status(uint32_t reg)          /* read the register ONCE, then decode the copy */
{
    status_t s;
    s.ready      = (reg & ST_READY) != 0;
    s.error      = (reg & ST_ERROR) != 0;
    s.mode       = (uint8_t)FIELD_GET(reg, ST_MODE);
    s.fifo_level = (uint8_t)FIELD_GET(reg, ST_FIFO);
    return s;
}
/* parse_status(0x00002353) -> ready 1, error 1, mode 5, fifo 0x23 */
```

**Points:** read the register once into a local (re-reading may give inconsistent fields, and some status bits clear on read); decode with mask-then-shift; define each field once with `_Pos`/`_Msk` macros; check reserved bits are ignored. To clear write-1-to-clear flags afterwards, write only the bits you handled.

**Example: an 8-bit status register**

```
bit:   7     6..4      3      2..0
      BUSY   ERRCODE   RDY    FIFO_LEVEL
```

`val = 0xA5` = 1010 0101 → BUSY = 1, ERRCODE = 010 (2), RDY = 0, FIFO_LEVEL = 101 (5).

**Why read once:** the register can change between reads (hardware updates it continuously), so reading it separately per field may combine values from different moments; some bits are **clear-on-read**, so a second read loses information.

**Mask-then-shift vs shift-then-mask:** both work; mask-then-shift lets you reuse the same `_Msk` macro for setting and clearing the field in the register, which is the CMSIS convention (`USART_SR_RXNE_Msk`, `USART_CR1_M_Pos`).

**Writing fields back (read-modify-write):**
`reg = (reg & ~FIELD_Msk) | ((value << FIELD_Pos) & FIELD_Msk);` — the final mask stops an oversized value from corrupting neighbouring fields.

**Why not C bit-fields for registers:** bit order and access width are implementation-defined, and the compiler may use byte accesses on a register that requires 32-bit accesses. Bit-fields are acceptable for the **decoded** struct, not for mapping the register itself.

**Write-1-to-clear flags:** clear them by writing a 1 only to the bits you handled (`reg = HANDLED_BITS;`), never with a read-modify-write, which would clear other pending flags.

### Implement a DMA descriptor ring (as used by Ethernet drivers). {H}
**Short answer:** A descriptor ring is an array of descriptors shared between the CPU and a DMA engine (as in Ethernet MACs). Each descriptor holds a buffer address, a length, status bits and an **OWN** bit saying who may touch it. For receive, software gives empty buffers to the hardware (OWN = hardware); the hardware fills one, writes the length/status and clears OWN; software processes it, refills it and hands it back. Both sides walk the ring in order and wrap at the end.

```c
#include <stdint.h>
#include <stddef.h>

#define RX_DESC   8u
#define BUF_SIZE  1536u
#define OWN_DMA   (1u << 31)                      /* descriptor owned by the DMA engine */
#define LEN_MASK  0x3FFFu

typedef struct { volatile uint32_t status; uint32_t buf_addr; uint32_t ctrl; uint32_t next; } dma_desc_t;

static dma_desc_t rx_ring[RX_DESC] __attribute__((aligned(32)));
static uint8_t    rx_buf[RX_DESC][BUF_SIZE] __attribute__((aligned(32)));
static unsigned   rx_idx;                         /* next descriptor software will look at */

void rx_ring_init(void)
{
    for (unsigned i = 0; i < RX_DESC; i++) {
        rx_ring[i].buf_addr = (uint32_t)(uintptr_t)rx_buf[i];
        rx_ring[i].ctrl     = BUF_SIZE;
        rx_ring[i].next     = (uint32_t)(uintptr_t)&rx_ring[(i + 1) % RX_DESC];   /* chained ring */
        rx_ring[i].status   = OWN_DMA;            /* give every buffer to the hardware */
    }
    rx_idx = 0;
    /* write &rx_ring[0] to the DMA's descriptor base register, start RX */
}

/* called from the RX interrupt or a polling loop */
void rx_poll(void (*deliver)(const uint8_t *frame, size_t len))
{
    while (!(rx_ring[rx_idx].status & OWN_DMA)) {        /* software owns it: a frame arrived */
        uint32_t st = rx_ring[rx_idx].status;
        /* on cached cores: invalidate rx_buf[rx_idx] before reading it */
        deliver(rx_buf[rx_idx], st & LEN_MASK);
        rx_ring[rx_idx].status = OWN_DMA;                 /* hand the buffer back to the hardware */
        rx_idx = (rx_idx + 1) % RX_DESC;
        /* then write the DMA "poll demand" register in case it stopped on a full ring */
    }
}
```

**Points:** each descriptor has an **ownership bit**: hardware fills a buffer and clears OWN; software processes it and sets OWN again. Software must never touch a descriptor the hardware owns. Descriptors and buffers need the alignment the DMA requires, cache maintenance on cached cores (or a non-cacheable region), and memory barriers between writing buffer/length fields and setting OWN. This is the same producer/consumer idea as a ring buffer, with the hardware as one side; Linux NIC drivers, virtio virtqueues and USB controllers all use variants of it.

**RX loop step by step**

1. Init: allocate N aligned buffers, fill N descriptors with their addresses, set OWN = DMA, write the ring base address to the MAC, start reception.
2. Interrupt (or poll): starting at `rx_index`, while the descriptor's OWN bit is clear: read the status and length, check errors, pass the frame up (or copy it), refill/reuse the buffer, set OWN = DMA, advance `rx_index` with wrap-around.
3. If the DMA stopped because it ran out of descriptors ("buffer unavailable"), write the poll-demand register to restart it.

**Memory ordering and caches (key interview points)**

- Write buffer address and length **before** setting OWN, with a barrier (`__DMB()` or `dma_wmb()`) in between, so the device never sees OWN with stale fields.
- On cores with data caches (Cortex-M7, Cortex-A): clean the cache before giving a TX buffer to the DMA, invalidate it before reading an RX buffer, or place descriptors/buffers in a non-cacheable MPU region. Buffers should be cache-line aligned so maintenance doesn't affect neighbours.

**TX side:** fill a buffer, set length and flags (first/last segment), set OWN; the DMA sends it and clears OWN; the TX-complete handler reclaims descriptors whose OWN is clear and frees their buffers.

**Why rings:** no allocation in the data path, the hardware can work ahead on several frames without CPU involvement, and flow control is natural (no free descriptor = back-pressure). The same design is used by virtio virtqueues, NVMe submission/completion queues and USB controllers.

### Implement a packet queue for a network driver (TX path). {M}
**Short answer:** Keep a fixed pool of packet buffers and a FIFO of packets waiting for transmission. `net_send()` (called by the protocol stack) copies or attaches the packet to a free buffer, appends it to the queue and, if the hardware is idle, starts the first transmission. The TX-complete interrupt frees the finished buffer and starts the next queued packet, so the link stays busy. When the pool or queue is full, `net_send()` returns an error so the stack slows down.

```c
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#define PKT_MAX  1518u
#define TXQ_LEN  8u

typedef struct { uint16_t len; uint8_t data[PKT_MAX]; } pkt_t;

static pkt_t    pool[TXQ_LEN];                  /* static packet pool, no malloc */
static unsigned q_head, q_tail, q_count;        /* protect with a lock or critical section */
static bool     hw_busy;

bool nic_hw_start_tx(const pkt_t *p);           /* starts DMA/transmit, completes via tx_done_isr */

static void kick(void)
{
    if (!hw_busy && q_count) {
        hw_busy = true;
        nic_hw_start_tx(&pool[q_tail]);
    }
}

int net_send(const uint8_t *frame, uint16_t len)
{
    if (len > PKT_MAX) return -1;
    if (q_count == TXQ_LEN) return -2;          /* queue full: back-pressure the stack */
    pkt_t *p = &pool[q_head];
    memcpy(p->data, frame, len);
    p->len = len;
    q_head = (q_head + 1) % TXQ_LEN;
    q_count++;
    kick();
    return 0;
}

void tx_done_isr(void)                          /* hardware finished sending pool[q_tail] */
{
    q_tail = (q_tail + 1) % TXQ_LEN;
    q_count--;
    hw_busy = false;
    kick();                                     /* start the next queued packet */
}
```

**Points:** a fixed pool avoids fragmentation; when the queue is full, return an error so the protocol stack applies back-pressure (Linux drivers call `netif_stop_queue()` and wake it in the TX-complete interrupt); the completion interrupt starts the next packet so the link stays busy; shared counters need a critical section because `net_send` (task) and `tx_done_isr` (interrupt) both modify them. Zero-copy designs pass buffer ownership (pointers) instead of copying frames.

**Flow**

```
stack → net_send() → [free pool] → [TX queue] → hardware/DMA → TX-done IRQ → buffer back to pool
                         ↑ full? return -EBUSY / stop queue                 ↓ start next packet
```

**Shared state and locking:** the queue head/tail and counters are touched by both `net_send` (task context) and the TX-done ISR, so updates need a short critical section — or split ownership so the task only writes the tail and the ISR only writes the head (SPSC).

**Back-pressure:** in Linux, the driver calls `netif_stop_queue()` when the ring is full and `netif_wake_queue()` from the completion interrupt when space returns; this tells the network stack to hold packets in its own queues (qdiscs) instead of dropping them in the driver.

**Statistics to keep:** packets sent, bytes, drops because the queue was full, errors, and the queue high-water mark (to size the pool).

**Priorities:** for real-time traffic (e.g. control messages over Ethernet), use several queues with a strict priority or weighted scheduling, which is what TSN-capable MACs and Linux `mqprio` provide.

**Zero-copy option:** instead of copying into driver buffers, keep a pointer to the stack's buffer (lwIP `pbuf`, Linux `sk_buff`) and release it in the completion handler — fewer copies, but the buffer must stay valid until the DMA finishes.
