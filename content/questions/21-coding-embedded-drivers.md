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
    uint32_t ticks = us * (SystemCoreClock / 1000000u);
    while ((uint32_t)(DWT_CYCCNT - start) < ticks) { }   /* wrap-safe */
}

/* millisecond delay from a 1 ms SysTick counter */
extern volatile uint32_t g_ms;
void delay_ms(uint32_t ms) { uint32_t s = g_ms; while ((uint32_t)(g_ms - s) < ms) { } }
```

**Points:** a plain `for (i = 0; i < N; i++);` loop is a bad delay: the optimiser can delete it, and its duration changes with clock speed, flash wait states and compiler flags (add `volatile` and calibrate if you must). Hardware counters give accurate timing; unsigned subtraction handles wrap-around. Busy delays waste CPU and power: use timers or an RTOS delay for anything long. (Cortex-M0/M0+ has no DWT counter: use SysTick or a timer.)

### Write a UART transmit routine (polled and interrupt-driven). {M}
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
        while (!(u->SR & UART_SR_TXE)) if (--t == 0) return -1;
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

### Write a UART receive interrupt handler with a ring buffer. {E}
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

### Write an SPI transfer function. {E}
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
        while (!(s->SR & SPI_SR_TXE))  if (--t == 0) { rc = -1; goto out; }
        *(volatile uint8_t *)&s->DR = tx ? tx[i] : 0xFF;          /* dummy byte for read-only */
        t = timeout;
        while (!(s->SR & SPI_SR_RXNE)) if (--t == 0) { rc = -1; goto out; }
        uint8_t b = *(volatile uint8_t *)&s->DR;                  /* always read to clear RXNE */
        if (rx) rx[i] = b;
    }
    { uint32_t t = timeout; while ((s->SR & SPI_SR_BSY) && --t) { } }   /* last bit fully out */
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

### Write I2C register read and write functions. {M}
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

### Implement a lock-free single-producer single-consumer (SPSC) ring buffer. {H}
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

### Implement a ring buffer that overwrites the oldest data when full. {M}
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

### Implement a blocking producer-consumer ring buffer (mutex + condition variable). {M}
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

### Implement an ISR-safe queue (interrupt producer, task consumer) using a critical section. {M}
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

### Implement a software timer module. {M}
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

### Implement a simple cooperative task scheduler. {M}
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

### Write a watchdog service routine. {E}
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

### Implement a state machine for a traffic light. {E}
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

### Implement a finite state machine for a device driver. {M}
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

### Implement atomic bit set and clear on a shared flags word. {M}
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

### Parse a hardware status register into named fields. {E}
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

### Implement a DMA descriptor ring (as used by Ethernet drivers). {H}
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

### Implement a packet queue for a network driver (TX path). {M}
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
