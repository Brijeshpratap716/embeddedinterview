---
slug: cpp-embedded
title: C++ for Embedded
icon: ➕
level: Intermediate
order: 14
desc: Classes, virtual functions and vtables, CRTP, RAII, move semantics, templates, constexpr, smart pointers, placement new, extern "C", std::array/span, and which C++ features are safe on a microcontroller.
---
More firmware teams now use a subset of modern C++ (C++17/20) on Cortex-M. Interviewers want to know which features are free, which cost RAM, flash or determinism, and how you would keep a codebase safe. Each answer gives the short version, then code and follow-ups.

### What is the difference between C and C++ for embedded systems? {E}
C and C++ can both produce efficient embedded software. C++ adds language features for abstraction, type safety and resource management, while retaining low-level hardware access.

| C | C++ |
|---|---|
| Functions, structs and explicit interfaces | Classes, templates, RAII and overloads |
| Manual resource cleanup | Destructors can manage resource lifetime |
| Function pointers for dynamic dispatch | Function pointers or virtual functions |
| Straightforward small runtime common | Runtime requirements depend on features used |

#### 1. Example

A C driver can expose init/read/deinit functions. A C++ driver can wrap the same operations in an object whose destructor releases an owned resource.

#### 2. Embedded considerations

Templates and inline functions can provide abstraction without runtime dispatch. Exceptions, dynamic allocation, RTTI and some library components can increase memory or timing complexity. They are not mandatory features for every C++ firmware project.

#### 3. Interoperability

Use extern "C" interfaces to call C libraries or expose selected functions to C code.

**Interview takeaway:** C++ is not inherently slower than C. Evaluate the generated code, runtime configuration, allocation policy and worst-case behavior of the features actually used.

### How do virtual functions work? What is a vtable? {M}
A virtual function supports runtime polymorphism: calling through a base reference or pointer selects the override belonging to the object's dynamic type.

#### 1. Example

```cpp
struct Device {
    virtual void start() = 0;
    virtual ~Device() = default;
};

struct Uart : Device {
    void start() override { /* Enable UART */ }
};

void enable(Device& d)
{
    d.start();
}
```

Calling enable with a Uart object invokes Uart::start.

#### 2. Typical implementation

```text
Object: [vptr | data members]
          |
          v
Virtual table: [start address | destructor entries | ...]
          |
          v
Indirect call to selected override
```

Most common C++ ABIs use a hidden virtual-table pointer and tables of function entries, but the language does not mandate a particular layout. The compiler can sometimes devirtualize a call.

#### 3. Embedded impact

Virtual dispatch can add object storage and an indirect branch, and complicate worst-case timing. A virtual destructor is needed if objects are deleted polymorphically through the base pointer.

**Interview takeaway:** Virtual functions enable runtime substitution. A vtable is a common implementation technique, not a required C++ object layout.

### What is CRTP and how does static polymorphism compare with virtual functions? {H}
**Short answer:** The Curiously Recurring Template Pattern (CRTP) is a class that derives from a template instantiated with itself: `class Uart1 : public UartBase<Uart1>`. The base can call derived-class functions through `static_cast<Derived*>(this)`, which the compiler resolves at **compile time**, so there is no vtable, no vptr and calls can be inlined. It gives a common interface and shared code with zero run-time cost, but you lose the ability to store different types behind one base pointer at run time.

```cpp
#include <cstdint>
#include <cstdio>

template <typename Derived>
class UartBase {
public:
    void write(const char *s) {                    // shared code, written once
        while (*s) static_cast<Derived *>(this)->put(static_cast<uint8_t>(*s++));
    }
};

class Uart1 : public UartBase<Uart1> {
public:
    void put(uint8_t c) { std::putchar(c); }       // would write the UART1 data register
};

class LogBuffer : public UartBase<LogBuffer> {
public:
    void put(uint8_t c) { if (n < sizeof buf) buf[n++] = c; }
    uint8_t buf[64]; unsigned n = 0;
};

template <typename Port>
void banner(UartBase<Port> &p) { p.write("boot ok\n"); }    // generic, no virtual calls

int main()
{
    Uart1 u; LogBuffer lb;
    banner(u); banner(lb);
    std::printf("log has %u bytes\n", lb.n);                  // log has 8 bytes
}
```

| | Virtual functions | CRTP / templates |
|---|---|---|
| Dispatch | run time (indirect call) | compile time (direct, inlinable) |
| RAM per object | vptr | none |
| Flash | one vtable per class; one copy of generic code | one copy of generic code **per type** (possible bloat) |
| Heterogeneous containers (`Sensor*` list of mixed types) | yes | no (unless combined with a small virtual wrapper) |
| Error messages | simple | template errors can be verbose (C++20 concepts help) |

**When to use which:** CRTP/templates when the configuration is fixed at compile time (which UART, which pins, which buffer size); virtual interfaces when types are chosen at run time (plugin-style sensor drivers, mocks in tests, different boards from one binary). C++20 **concepts** document and check the required interface (`requires { p.put(uint8_t{}); }`).

### What is RAII? {E}
**Short answer:** Resource Acquisition Is Initialisation: a resource (lock, interrupt mask, peripheral clock, chip-select line, buffer) is acquired in an object's constructor and released in its destructor. Because destructors run automatically when the object goes out of scope — on every return path — the resource can never be leaked or left locked by an early return. It costs nothing at run time compared with doing it by hand.

```cpp
#include <cstdint>
#include <cstdio>

// stand-ins for __get_PRIMASK / __disable_irq / __set_PRIMASK on Cortex-M
static uint32_t primask;
static uint32_t get_primask() { return primask; }
static void disable_irq() { primask = 1; }
static void set_primask(uint32_t v) { primask = v; }

class CriticalSection {
public:
    CriticalSection() : saved_(get_primask()) { disable_irq(); }
    ~CriticalSection() { set_primask(saved_); }          // restores the previous state (nesting-safe)
    CriticalSection(const CriticalSection &) = delete;   // non-copyable
    CriticalSection &operator=(const CriticalSection &) = delete;
private:
    uint32_t saved_;
};

static int shared_counter;

bool update(int v)
{
    CriticalSection cs;                 // interrupts off from here...
    if (v < 0) return false;            // ...restored on this path
    shared_counter += v;
    return true;                        // ...and on this one
}

int main()
{
    update(5); update(-1);
    std::printf("counter=%d primask=%u\n", shared_counter, (unsigned)primask);   // counter=5 primask=0
}
```

**Other RAII uses in firmware**

- `std::lock_guard` / `std::scoped_lock` around RTOS mutexes (wrap the RTOS API in a class with `lock()`/`unlock()`).
- `ChipSelect cs(spi_dev);` asserts CS for the duration of a transaction.
- Peripheral power or clock enable for a scope; DMA buffer ownership; file handles.
- `std::unique_ptr` with a custom deleter (e.g. returning a buffer to a pool).

**Rules:** make RAII classes non-copyable (or movable only, transferring ownership), never throw from destructors, and keep the destructor's work short in interrupt-sensitive code.

### What are move semantics and why do they matter even without a heap? {M}
**Short answer:** Move semantics (C++11) let an object transfer ownership of its resources to another object instead of copying them. A **move constructor** / **move assignment** takes an rvalue reference (`T&&`), steals the source's resource, and leaves the source in a valid but empty state. `std::move` is just a cast that says "this object may be moved from". On embedded systems, moves matter mostly for **unique ownership** types: a buffer handle from a pool, a DMA channel or a file descriptor that must have exactly one owner, can be returned from functions and stored in containers without copying or double release.

```cpp
#include <cstdio>
#include <utility>

class PoolBuffer {
public:
    explicit PoolBuffer(int idx) : idx_(idx) { std::printf("take %d\n", idx_); }
    ~PoolBuffer() { if (idx_ >= 0) std::printf("give %d\n", idx_); }   // return to the pool

    PoolBuffer(const PoolBuffer &) = delete;                // one owner only
    PoolBuffer &operator=(const PoolBuffer &) = delete;

    PoolBuffer(PoolBuffer &&o) noexcept : idx_(o.idx_) { o.idx_ = -1; }   // steal
    PoolBuffer &operator=(PoolBuffer &&o) noexcept {
        if (this != &o) { if (idx_ >= 0) std::printf("give %d\n", idx_); idx_ = o.idx_; o.idx_ = -1; }
        return *this;
    }
    int index() const { return idx_; }
private:
    int idx_;
};

PoolBuffer acquire() { return PoolBuffer(3); }     // returned without copying (guaranteed elision)

int main()
{
    PoolBuffer a = acquire();
    PoolBuffer b = std::move(a);                  // ownership moves; a is now empty
    std::printf("a=%d b=%d\n", a.index(), b.index());
}                                                 // prints "give 3" exactly once
```

**Key rules**

- **Rule of zero:** prefer members that already manage themselves (`std::array`, `std::unique_ptr`), so you write no special members at all.
- **Rule of five:** if you write a destructor, copy constructor/assignment or move constructor/assignment, think about all five.
- Mark moves `noexcept` (containers rely on it).
- Copy elision: returning a local or a temporary usually constructs it directly in the caller (guaranteed for prvalues since C++17).
- Using an object after `std::move` is legal only for operations that don't assume a value (assign, destroy).

### What are constexpr and consteval? {M}
**Short answer:** `constexpr` marks variables and functions that **can** be evaluated at compile time; when used where a constant is required (array sizes, template arguments, `static_assert`, `constexpr` variables), the compiler must evaluate them, so lookup tables, register values and configuration checks cost no run-time code or RAM. `consteval` (C++20) marks functions that **must** be evaluated at compile time — calling one with run-time values is an error. `constinit` (C++20) guarantees a variable is initialised statically (no run-time constructor, no initialisation-order problems).

```cpp
#include <array>
#include <cstdint>
#include <cstdio>

constexpr uint32_t SYSCLK = 84'000'000;

void baud_rate_out_of_range();                       // not constexpr: calling it at compile time is an error

consteval uint32_t baud_div(uint32_t baud)           // must be compile time
{
    uint32_t div = (SYSCLK + baud / 2) / baud;
    if (div < 16 || div > 0xFFFF) baud_rate_out_of_range();   // error checks become compile errors
    return div;                                      // (works with -fno-exceptions, unlike throw)
}

constexpr std::array<uint8_t, 256> make_crc8_table()
{
    std::array<uint8_t, 256> t{};
    for (int i = 0; i < 256; i++) {
        uint8_t c = static_cast<uint8_t>(i);
        for (int b = 0; b < 8; b++) c = (c & 0x80) ? static_cast<uint8_t>((c << 1) ^ 0x07) : static_cast<uint8_t>(c << 1);
        t[i] = c;
    }
    return t;
}

constexpr auto CRC8_TABLE = make_crc8_table();       // computed by the compiler, placed in flash
static_assert(CRC8_TABLE[1] == 0x07, "table check");

constinit uint32_t uart_brr = baud_div(115200);      // static init, no constructor at startup

int main()
{
    std::printf("BRR=%u crc[0x31]=0x%02X\n", (unsigned)uart_brr, CRC8_TABLE[0x31]);
}
```

**Why it is useful in firmware**

- Tables (CRC, sine, gamma, calibration curves) generated at compile time end up in flash, not RAM, with no start-up cost.
- Configuration errors (impossible baud rates, PLL settings out of range, buffer sizes not powers of two) become compile errors via `static_assert` or `consteval`.
- Replaces many macros with type-safe functions.

**Note:** a `constexpr` function called with run-time arguments simply runs at run time; to force compile-time evaluation, assign the result to a `constexpr` variable or use `consteval`.

### Why are exceptions and RTTI often disabled in embedded C++? {M}
**Short answer:** **Exceptions** add unwind tables and support code (often tens of KB of flash), make worst-case timing hard to bound (unwinding cost depends on the call stack), may allocate memory for the exception object, and add hidden control-flow paths that safety standards dislike. **RTTI** (`typeid`, `dynamic_cast`) adds type-information tables for every polymorphic class. Many teams compile with `-fno-exceptions -fno-rtti` and use error codes, `std::optional`, or `std::expected` (C++23, or a small equivalent) instead.

**Error handling without exceptions**

```cpp
#include <cstdio>
#include <optional>

enum class Err { Timeout, Nack, Range };

template <typename T>
struct Result {                       // tiny expected-like type
    bool ok; T value; Err err;
    static Result success(T v) { return { true, v, {} }; }
    static Result failure(Err e) { return { false, T{}, e }; }
};

Result<int> read_temp(bool sensor_present)
{
    if (!sensor_present) return Result<int>::failure(Err::Nack);
    return Result<int>::success(23);
}

std::optional<int> parse_digit(char c)
{
    if (c < '0' || c > '9') return std::nullopt;
    return c - '0';
}

int main()
{
    auto r = read_temp(false);
    if (!r.ok) std::printf("error %d\n", static_cast<int>(r.err));   // error 1
    std::printf("%d\n", parse_digit('7').value_or(-1));             // 7
}
```

Mark result types `[[nodiscard]]` so ignoring an error produces a compiler warning.

**Consequences of `-fno-exceptions`**

- `new` that fails must not throw: use `new (std::nothrow)` and check for null, or avoid `new`.
- Standard library functions that would throw call `std::abort()` (or a terminate handler) instead — e.g. `std::vector::at` out of range; provide your own `abort` handler that logs and resets.
- Third-party libraries that rely on exceptions cannot be used as is.

**When exceptions are acceptable:** larger embedded Linux applications, or MCUs with plenty of flash where the team decides the timing impact is acceptable for rare error paths. Modern compilers have "zero-cost" (table-based) exceptions with no cost on the non-throwing path, but the size and worst-case cost remain.

### What are templates and what is code bloat? {M}
**Short answer:** Templates let you write type- or value-generic code (functions, classes) that the compiler instantiates for each set of template arguments used, producing code as efficient as hand-written specialised code. **Code bloat** is the downside: every distinct instantiation (e.g. `RingBuffer<uint8_t, 64>`, `RingBuffer<uint8_t, 128>`, `RingBuffer<uint16_t, 64>`) generates a separate copy of the functions, which can grow flash usage significantly.

```cpp
#include <array>
#include <cstddef>
#include <cstdio>

template <typename T, std::size_t N>
class RingBuffer {
    static_assert((N & (N - 1)) == 0, "N must be a power of two");
public:
    bool push(const T &v) { if (head_ - tail_ == N) return false; buf_[head_++ & (N - 1)] = v; return true; }
    bool pop(T &v)        { if (head_ == tail_) return false; v = buf_[tail_++ & (N - 1)]; return true; }
    std::size_t size() const { return head_ - tail_; }
private:
    std::array<T, N> buf_{};
    std::size_t head_ = 0, tail_ = 0;
};

int main()
{
    RingBuffer<int, 4> rb;
    for (int i = 0; i < 6; i++) rb.push(i);
    int v;
    while (rb.pop(v)) std::printf("%d ", v);     // 0 1 2 3
    std::printf("\n");
}
```

**Controlling bloat**

- **Hoist type-independent code** into a non-template base class that works on `void*` and sizes, with a thin template wrapper on top (the "thin template" idiom).
- Limit the number of distinct instantiations (e.g. standardise buffer sizes).
- Use `extern template` / explicit instantiation in one file to avoid duplicates across translation units (the linker removes identical duplicates anyway, but compile time shrinks).
- Build with `-Os`, `-ffunction-sections -fdata-sections -Wl,--gc-sections` and LTO; the linker's identical code folding (`--icf` in lld/gold) merges identical instantiations.
- Measure: check the map file or `nm --size-sort -C` for large template symbols.

**Good embedded uses:** fixed-capacity containers, register access with compile-time addresses, unit-safe types (milliseconds vs microseconds), and compile-time pin configuration.

### What are smart pointers and should you use them on an MCU? {M}
**Short answer:** Smart pointers own the object they point to and release it automatically. `std::unique_ptr` has a single owner, is the same size as a raw pointer (with a stateless deleter) and has no run-time overhead, so it is fine on an MCU, especially with a **custom deleter** that returns memory to a pool. `std::shared_ptr` uses reference counting with a separately allocated control block and atomic increments, adding RAM, code and allocation, so it is usually avoided in firmware. Since most MCU code avoids the heap anyway, the main value is clear ownership.

```cpp
#include <cstdio>
#include <memory>

struct Msg { int id; char data[32]; };

static Msg pool[4];
static bool used[4];

Msg *pool_alloc() { for (int i = 0; i < 4; i++) if (!used[i]) { used[i] = true; return &pool[i]; } return nullptr; }

struct PoolDeleter {
    void operator()(Msg *m) const { used[m - pool] = false; std::printf("returned %d\n", m->id); }
};
using MsgPtr = std::unique_ptr<Msg, PoolDeleter>;     // same size as Msg*

MsgPtr make_msg(int id)
{
    Msg *m = pool_alloc();
    if (m) m->id = id;
    return MsgPtr(m);                                 // may be empty if the pool is exhausted
}

int main()
{
    auto a = make_msg(1);
    {
        auto b = make_msg(2);
    }                                                 // "returned 2"
    std::printf("sizeof(MsgPtr)=%zu\n", sizeof(MsgPtr));
}                                                     // "returned 1"
```

**Guidance**

- Prefer stack objects, static objects and references; use `unique_ptr` when ownership must be passed around.
- Avoid `shared_ptr` in hard real-time paths (atomic operations, allocation, unpredictable destruction time when the last reference drops).
- `std::make_unique` allocates from the heap: only use it at initialisation if heap use is allowed.
- Raw pointers are still fine for **non-owning** references; `std::span` and references make intent clearer.
- Beware of destroying objects in ISRs through smart pointers (destructors may not be ISR-safe).

### What is the difference between new/delete and malloc/free? {E}
**Short answer:** `new` allocates memory **and** runs the constructor, returning a correctly typed pointer; `delete` runs the destructor and then frees the memory. `malloc`/`free` only allocate and free raw bytes and know nothing about constructors or types. By default `new` throws `std::bad_alloc` on failure (with exceptions disabled it typically aborts, so use `new (std::nothrow)` and check for null), while `malloc` returns NULL. Memory from `new` must be released with `delete` (and `new[]` with `delete[]`), never with `free`.

| | `new` / `delete` | `malloc` / `free` |
|---|---|---|
| Constructors / destructors | yes | no |
| Returns | typed pointer | `void *` |
| Failure | throws `bad_alloc` (or `nullptr` with `nothrow`) | NULL |
| Size | computed from the type | given in bytes |
| Customisable | per class (`operator new`) or globally | wrap or replace the allocator |
| Arrays | `new[]` / `delete[]` (stores the count) | manual |

**Embedded considerations**

- Both usually use the same heap (the default `operator new` calls `malloc`), so fragmentation and non-deterministic timing apply equally.
- You can **override global `operator new`/`delete`** to route allocations to an RTOS heap (`pvPortMalloc`), to a pool, or to trap any use after initialisation (call an error handler), enforcing a "no heap at run time" policy.
- **Placement new** constructs an object in memory you already have, without allocating (next question).
- Class-specific `operator new` can allocate from a per-class pool: fast and fragmentation-free.

### What is placement new and when is it used in embedded code? {M}
**Short answer:** Placement new (`new (address) T(args)`) constructs an object in memory you already own — a static buffer, a memory pool slot or a memory-mapped region — without allocating anything. You are then responsible for calling the destructor explicitly (`obj->~T()`) and for the memory's alignment and lifetime. It is how fixed-capacity containers, `std::optional`, object pools and "construct later" singletons work without a heap.

```cpp
#include <cstddef>
#include <cstdio>
#include <new>

class Driver {
public:
    explicit Driver(int port) : port_(port) { std::printf("init port %d\n", port_); }
    ~Driver() { std::printf("deinit port %d\n", port_); }
private:
    int port_;
};

alignas(Driver) static std::byte storage[sizeof(Driver)];   // static memory, correct alignment
static Driver *drv;

void driver_start(int port) { drv = new (storage) Driver(port); }   // construct in place
void driver_stop() { drv->~Driver(); drv = nullptr; }              // explicit destructor call

int main()
{
    driver_start(2);      // construct after the clocks/board are set up, not before main()
    driver_stop();
    driver_start(3);      // reuse the same storage
    driver_stop();
}
```

**Typical uses**

- Delaying construction of global objects until hardware is ready (avoids static initialisation order problems).
- Object pools: fixed array of raw storage slots, construct with placement new, destroy explicitly, mark the slot free.
- Fixed-capacity containers (ETL's `etl::vector<T, N>`, `std::inplace_vector` in C++26).

**Rules**

- Storage must be correctly aligned (`alignas(T)`) and large enough.
- Don't call `delete` on a placement-new object; call the destructor.
- In modern C++, `std::launder` may be needed when reusing storage for a new object accessed through an old pointer; `std::construct_at` / `std::destroy_at` (C++20) are cleaner spellings.
- Prefer `std::optional<T>` for the simple "maybe constructed" case: it handles storage, alignment and destruction for you.

### What does volatile mean in C++ and what changed in C++20? {H}
**Short answer:** As in C, `volatile` tells the compiler that every read and write of the object is an observable side effect (e.g. a hardware register), so it must not optimise accesses away, merge them, or reorder them relative to other volatile accesses. It does **not** make operations atomic and does not provide memory ordering for multi-threaded code — use `std::atomic` for that. C++20 **deprecated** compound operations on volatile objects (`++`, `--`, `+=`, `|=` ...), volatile function parameters and return types, because they suggest an atomic read-modify-write that does not exist; write explicit loads and stores instead.

```cpp
#include <cstdint>

struct GpioRegs { volatile uint32_t ODR; volatile uint32_t BSRR; };

void toggle(GpioRegs *gpio, uint32_t pin_mask)
{
    // gpio->ODR ^= pin_mask;            // deprecated in C++20: hides a read-modify-write
    uint32_t v = gpio->ODR;              // explicit read
    gpio->ODR = v ^ pin_mask;            // explicit write (still not atomic w.r.t. interrupts)
}

void set_atomic(GpioRegs *gpio, uint32_t pin_mask)
{
    gpio->BSRR = pin_mask;               // hardware set/reset register: a single write, no RMW race
}
```

**C++23 note:** after feedback from the embedded community, C++23 un-deprecated the bitwise compound assignments (`|=`, `&=`, `^=`) on volatile, because they are so common in register code; `++`, `--`, `+=` and the other cases remain deprecated.

**volatile vs atomic**

| | `volatile` | `std::atomic<T>` |
|---|---|---|
| Prevents optimising accesses away | yes | yes (for the atomic object) |
| Atomic read-modify-write | no | yes (`fetch_add`, `compare_exchange`) |
| Memory ordering with other variables | no | yes (`memory_order_*`) |
| Use for | MMIO registers, variables changed by hardware | data shared between threads/ISRs |

**Embedded rule:** registers → volatile; flags shared between an ISR and the main loop on a single-core MCU → `std::atomic` (lock-free for word sizes on Cortex-M3+; on Cortex-M0 check `is_lock_free()`) or volatile plus a critical section for multi-step updates.

### How do you model a hardware register in type-safe C++? {H}
**Short answer:** Wrap register addresses and fields in types so misuse becomes a compile error: put the address and access type (read-only, write-only, read-write) in a template, model fields with compile-time offset and width, and use `enum class` for field values. Everything resolves to the same single load or store as hand-written C (`*(volatile uint32_t*)addr`), but writing to a read-only register or putting a value in the wrong field no longer compiles.

```cpp
#include <cstdint>
#include <cstdio>

enum class Access { RO, WO, RW };

template <uintptr_t Addr, Access A = Access::RW>
struct Reg {
    static volatile uint32_t &ref() { return *reinterpret_cast<volatile uint32_t *>(Addr); }
    static uint32_t read() { static_assert(A != Access::WO, "write-only register"); return ref(); }
    static void write(uint32_t v) { static_assert(A != Access::RO, "read-only register"); ref() = v; }
};

template <typename R, unsigned Offset, unsigned Width>
struct Field {
    static constexpr uint32_t mask = ((1u << Width) - 1u) << Offset;
    static void set(uint32_t v) {
        uint32_t r = R::read();
        R::write((r & ~mask) | ((v << Offset) & mask));
    }
    static uint32_t get() { return (R::read() & mask) >> Offset; }
};

enum class Mode : uint32_t { Input = 0, Output = 1, Alt = 2, Analog = 3 };

// demo: point the "register" at RAM so this runs on a PC
static uint32_t fake_moder;
using GPIOA_MODER = Reg<0>;                       // placeholder; real code uses 0x4002'0000
struct Moder {                                    // adapter so the demo can use fake memory
    static uint32_t read() { return fake_moder; }
    static void write(uint32_t v) { fake_moder = v; }
};
template <unsigned Pin> using PinMode = Field<Moder, Pin * 2, 2>;

int main()
{
    PinMode<5>::set(static_cast<uint32_t>(Mode::Output));
    PinMode<6>::set(static_cast<uint32_t>(Mode::Alt));
    std::printf("MODER=0x%08X pin5=%u\n", (unsigned)fake_moder, (unsigned)PinMode<5>::get());   // 0x00002400 1
    (void)sizeof(GPIOA_MODER);
}
```

**Real-world options**

- Vendor CMSIS headers (C structs with `volatile` members) are the baseline; C++ wrappers sit on top.
- Libraries: **Kvasir**, **modm** (generated from vendor data), **cpp-register** styles, Rust's svd2rust as the inspiration; **SVD files** describe registers and fields so code can be generated.
- `reinterpret_cast` makes these functions non-`constexpr`; keep addresses as `uintptr_t` template parameters and cast only inside the access function.

**Benefits to mention:** read-only/write-only enforcement, field width checks, impossible to mix up registers of different peripherals, self-documenting code, and zero overhead (check the disassembly).

### What is the static initialisation order fiasco? {M}
**Short answer:** Global and static objects with dynamic initialisation (constructors that run before `main`) in **different translation units** are initialised in an unspecified order. If one global's constructor uses another global defined in a different `.cpp` file, it may run before that object is constructed and use garbage. On embedded systems, there is a second problem: global constructors run from start-up code, possibly before clocks, memory (external SDRAM) or peripherals are initialised.

```cpp
// uart.cpp
Uart debug_uart(USART2, 115200);            // constructor configures hardware

// logger.cpp
Logger logger(debug_uart);                  // constructor writes a banner through debug_uart
// if logger is constructed first, it uses an unconstructed Uart → undefined behaviour
```

**Fixes**

| Technique | How |
|---|---|
| Construct on first use | `Uart &debug_uart() { static Uart u(USART2, 115200); return u; }` — initialised the first time the function runs (thread-safe "magic statics" in C++11; with `-fno-threadsafe-statics` you must ensure first use from one context) |
| `constexpr` / `constinit` constructors | objects initialised statically at compile time have no order problem |
| Explicit initialisation | globals with trivial constructors plus an `init()` called from `main` in a defined order, after the clock and board setup |
| Placement new into static storage | construct objects explicitly in `main` (see the placement new question) |
| Keep globals in one translation unit | order within one file is the definition order |

**Embedded advice:** keep global constructors trivial (no hardware access), initialise hardware explicitly from `main` in a documented order, and check that the start-up code actually runs `__libc_init_array` (otherwise global constructors never run at all, a common bug with custom start-up files). Destruction order at exit is the reverse, which rarely matters in firmware that never exits.

### How do you call C code from C++ and C++ from C (extern "C")? {E}
**Short answer:** C++ compilers **mangle** function names to encode namespaces and parameter types (for overloading), while C uses plain names. Declaring functions `extern "C"` tells the C++ compiler to use C linkage (unmangled names and the C calling convention), so C and C++ object files can link together. C headers used from C++ wrap their declarations in `extern "C"` guarded by `#ifdef __cplusplus`; C++ functions that C code must call (including interrupt handlers referenced by a C vector table) are defined `extern "C"`.

```cpp
/* hal_uart.h — usable from both C and C++ */
#ifndef HAL_UART_H
#define HAL_UART_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

void hal_uart_init(uint32_t baud);
void hal_uart_putc(char c);

#ifdef __cplusplus
}
#endif
#endif

/* irq.cpp — C++ handler with the exact name the startup file expects */
extern "C" void USART2_IRQHandler(void)
{
    uart_driver.on_interrupt();     // forward into a C++ object
}
```

**What can cross the boundary:** plain functions with C-compatible parameter types (integers, pointers, POD structs, function pointers). Not classes with virtual functions, references, overloaded functions, templates or exceptions (an exception must never propagate into C code).

**Common bugs**

- An ISR written in C++ without `extern "C"` gets a mangled name (`_Z17USART2_IRQHandlerv`), so the weak default handler in the vector table is used instead and the interrupt "never fires" or hangs in `Default_Handler`.
- Passing a C++ member function as a C callback: use a static member or a free function with a `void *context` parameter that you cast back to the object.
- Mismatched struct layouts if C++ adds a vptr or non-standard-layout members; check with `static_assert(std::is_standard_layout_v<T>)`.

### Which standard library features are safe on a microcontroller? {M}
**Short answer:** Most of the **algorithm and type** parts of the standard library are header-only and do not allocate: `std::array`, `std::span`, `std::optional`, `std::variant`, `std::string_view`, `std::bitset`, `<algorithm>` (`std::sort`, `std::find`, `std::min/max`), `<type_traits>`, `<limits>`, `<chrono>` durations, `std::atomic` and `<cstdint>`. The parts that allocate or are large — `std::vector`, `std::string`, `std::map`, `std::function` (may allocate), `<iostream>`, `std::thread` — are avoided or used only at initialisation. Fixed-capacity alternatives come from the **ETL** (Embedded Template Library) or similar.

| Usually fine | Use with care | Usually avoided |
|---|---|---|
| `std::array`, `std::span`, `std::string_view` | `std::function` (small buffer may avoid heap; size varies) | `std::vector`/`std::string` after init |
| `std::optional`, `std::variant`, `std::expected` | `std::sort` (recursion, check stack) | `std::map`, `std::unordered_map`, `std::list` |
| `<algorithm>`, `<numeric>`, `<type_traits>` | `std::chrono` clocks (need a time source) | `<iostream>`, `<regex>`, `<locale>` |
| `std::atomic`, `std::bitset`, `std::byte` | `<cstdio>` `printf` with floats (code size) | `std::thread`, `std::shared_ptr` |

**`std::span` example (safe buffer passing)**

```cpp
#include <array>
#include <cstdint>
#include <cstdio>
#include <span>

uint32_t checksum(std::span<const uint8_t> data)    // pointer + length in one object, no copy
{
    uint32_t s = 0;
    for (uint8_t b : data) s += b;
    return s;
}

int main()
{
    std::array<uint8_t, 4> pkt{ 1, 2, 3, 4 };
    uint8_t raw[3] = { 10, 20, 30 };
    std::printf("%u %u\n", (unsigned)checksum(pkt), (unsigned)checksum(raw));   // 10 60
    std::printf("%u\n", (unsigned)checksum(std::span(pkt).subspan(1, 2)));      // 5
}
```

**Practical setup:** compile with `-fno-exceptions -fno-rtti`, consider `-fno-threadsafe-statics` on bare metal, link with `--specs=nano.specs` (newlib-nano), and check the map file after adding any new standard library feature to see what it pulled in.
