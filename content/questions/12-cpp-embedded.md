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
CRTP (Curiously Recurring Template Pattern) uses a derived type as a template argument to its base class, enabling compile-time polymorphism.

#### 1. Example

```cpp
template<class Derived>
struct Driver {
    void start() {
        static_cast<Derived&>(*this).start_impl();
    }
};

struct Uart : Driver<Uart> {
    void start_impl() { /* Enable UART */ }
};

Uart uart;
uart.start();
```

The compiler knows Derived is Uart and can resolve the call statically.

| CRTP | Virtual functions |
|---|---|
| Compile-time dispatch | Runtime dispatch |
| Often easy to inline | Indirect call may be needed |
| Separate template instantiations | Common base interface |
| Does not inherently support heterogeneous base-pointer collections | Supports runtime substitution |

#### 2. Embedded use

CRTP can implement common driver algorithms while allowing target-specific register operations. Template instantiations may increase code size; misuse of the derived-type contract can be unsafe.

**Interview takeaway:** Static polymorphism trades runtime flexibility for compile-time knowledge. Use virtual dispatch when runtime selection is genuinely needed.

### What is RAII? {E}
RAII (Resource Acquisition Is Initialization) associates resource ownership with an object's lifetime. A constructor or factory establishes ownership; the destructor releases it.

#### 1. Example: mutex guard

```cpp
class LockGuard {
    Mutex& m;
public:
    explicit LockGuard(Mutex& mutex) : m(mutex) {
        m.lock();
    }
    ~LockGuard() { m.unlock(); }

    LockGuard(const LockGuard&) = delete;
    LockGuard& operator=(const LockGuard&) = delete;
};

void update(Mutex& m)
{
    LockGuard guard(m);
    update_shared_state();
}
```

The lock is released when guard leaves scope, including an early return. Mutex is an illustrative platform type.

#### 2. Embedded uses

GPIO resource ownership, interrupt-mask restoration, peripheral clocks, mutexes, file descriptors and buffer handles. Destruction must be valid in the execution context; a blocking destructor is not suitable in an ISR.

**Interview takeaway:** RAII makes cleanup follow scope and ownership. It does not require heap allocation or exception support, and should be designed around acquisition failure.

### What are move semantics and why do they matter even without a heap? {M}
Move semantics transfer ownership or state from one object to another instead of copying expensive or exclusive resources. They are useful even when the resource is a fixed hardware channel rather than heap memory.

#### 1. Example

```cpp
#include <utility>

class Channel {
    int id = -1;
public:
    explicit Channel(int n) : id(n) {}
    ~Channel() { if (id >= 0) release_channel(id); }

    Channel(const Channel&) = delete;
    Channel& operator=(const Channel&) = delete;

    Channel(Channel&& other) noexcept
        : id(std::exchange(other.id, -1)) {}
    Channel& operator=(Channel&&) = delete;
};
```

The move constructor transfers the channel ID and invalidates the old owner. Only the new owner releases it. The channel must have been validly acquired.

#### 2. std::move

std::move casts an expression to an rvalue category that permits move-aware overload selection; it does not itself transfer anything. The chosen constructor or assignment performs the move.

**Interview takeaway:** Move semantics encode transfer of ownership, not just heap optimization. Moved-from objects must remain valid according to their documented state; avoid duplicate resource release.

### What are constexpr and consteval? {M}
`constexpr` allows expressions/functions to participate in compile-time evaluation when requirements are satisfied. `consteval` declares an immediate function whose potentially evaluated calls must produce constant expressions under the language rules.

#### 1. Example

```cpp
constexpr unsigned mask(unsigned bit)
{
    return 1u << bit;
}

constexpr unsigned ENABLE = mask(3);
```

mask can also be called with a runtime value, provided the shift count is valid.

```cpp
consteval unsigned register_offset(unsigned n)
{
    return 4u * n;
}

constexpr unsigned OFFSET = register_offset(5);
```

This uses C++20 immediate functions; a call requiring runtime evaluation is not allowed.

#### 2. Embedded applications

Compile-time register masks, lookup tables, configuration validation and fixed-size buffer calculations. Use static_assert for invalid constant configuration.

**Interview takeaway:** constexpr permits constant evaluation; consteval requires it for immediate calls. Neither implies that arbitrary runtime operations or MMIO reads can be evaluated at compile time.

### Why are exceptions and RTTI often disabled in embedded C++? {M}
Exceptions provide stack unwinding and error propagation; RTTI (Run-Time Type Information) supports runtime type queries such as certain dynamic_cast operations and typeid.

#### 1. Why disable them?

Embedded toolchains may disable exceptions or RTTI to reduce runtime support, binary size, metadata and timing-analysis complexity. The actual costs depend on ABI and toolchain; exceptions can have low overhead on the normal path while throwing/unwinding may be expensive.

#### 2. Alternatives

```cpp
enum class Error { ok, timeout, invalid };

Error read_sensor(int& value);
```

Use explicit status values, expected-like result types, tagged variants or static polymorphism when appropriate. RAII still works without exceptions during normal scope exit.

#### 3. Build considerations

Flags such as -fno-exceptions and -fno-rtti are compiler-specific. Ensure libraries and all translation units follow compatible assumptions; disabling a feature does not automatically make error paths safe.

**Interview takeaway:** Exceptions and RTTI are optional design choices in many embedded projects. Decide based on measured footprint, supported toolchain and timing/error-handling requirements.

### What are templates and what is code bloat? {M}
Templates define code parameterized by types or compile-time values. The compiler instantiates versions needed by the program.

#### 1. Example

```cpp
template<class T, unsigned N>
struct Buffer {
    T data[N]{};
    constexpr unsigned size() const { return N; }
};

Buffer<unsigned char, 64> rx;
Buffer<unsigned short, 32> samples;
```

The two buffer types have different element types and capacities known at compile time.

#### 2. Code bloat

Multiple template instantiations can generate separate machine-code copies for similar operations. Link-time optimization and linker folding may reduce duplicates, but are not guaranteed to eliminate them.

#### 3. Reduce size

Move type-independent work into shared non-template functions, avoid unnecessary combinations of parameters, use explicit instantiation where appropriate, and inspect the linker map and generated code.

**Interview takeaway:** Templates can give strong typing and static dispatch without dynamic allocation. Code size depends on instantiation and optimization, so measure rather than assuming templates are free or always expensive.

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
