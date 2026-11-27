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
Smart pointers model ownership and automate resource release. Whether they are appropriate on an MCU depends on the allocation and lifetime policy.

| Type | Ownership |
|---|---|
| unique_ptr | Exclusive ownership |
| shared_ptr | Shared ownership via reference count |
| weak_ptr | Non-owning observation of shared ownership |

#### 1. Custom resource deleter

```cpp
struct ReturnBuffer {
    void operator()(Buffer* p) const {
        if (p) pool_release(p);
    }
};

using BufferHandle = std::unique_ptr<Buffer, ReturnBuffer>;
```

A BufferHandle can own a buffer obtained from a fixed pool and return it automatically without using delete. The pool must outlive its handles.

#### 2. MCU considerations

unique_ptr can be lightweight and does not inherently require heap allocation with a custom deleter. shared_ptr typically requires a control block and reference-count operations; cycles and unpredictable destruction paths require attention.

**Interview takeaway:** Prefer exclusive ownership where possible. Smart pointers solve ownership, not arbitrary concurrency, ISR safety or deterministic allocation.

### What is the difference between new/delete and malloc/free? {E}
`new/delete` are C++ object allocation/lifetime operations; `malloc/free` allocate and release raw storage through C library APIs.

#### 1. Example

```cpp
Widget* p = new Widget(10);
delete p;
```

A new-expression allocates storage and constructs Widget. Delete destroys it and deallocates the storage.

```cpp
void* mem = std::malloc(sizeof(Widget));
std::free(mem);
```

Malloc does not ordinarily perform Widget's constructor, and free does not invoke its destructor.

#### 2. Failure and matching

Ordinary new normally throws std::bad_alloc on failure; nothrow new can return nullptr for allocation failure. Malloc returns null on failure for nonzero requests. Pair new with delete, new[] with delete[], and malloc with free. Never mix allocation families without a documented compatible mechanism.

**Interview takeaway:** C++ object lifetime is separate from raw storage. Embedded projects can use custom allocation policies, but constructors/destructors must still be respected.

### What is placement new and when is it used in embedded code? {M}
Placement new constructs an object at an already supplied memory address without allocating new storage.

#### 1. Example

```cpp
#include <new>
#include <cstddef>

struct Widget {
    int x;
    explicit Widget(int n) : x(n) {}
};

alignas(Widget) unsigned char storage[sizeof(Widget)];

Widget* p = ::new (static_cast<void*>(storage)) Widget(42);
// Use p->x.
p->~Widget();
```

The storage must have sufficient size and alignment, and no conflicting live object. Explicit destruction ends the object's lifetime; the original storage remains.

#### 2. Embedded use

Construct objects in fixed pools, statically reserved memory or custom arenas. Handle constructor failure according to the configured C++ runtime. Reusing storage may require careful lifetime/pointer rules; use the returned pointer and documented mechanisms.

**Interview takeaway:** Placement new is construction, not allocation. Do not call ordinary delete on an object constructed in a raw static buffer.

### What does volatile mean in C++ and what changed in C++20? {H}
C++ volatile, like C volatile, marks accesses whose observable behavior must be preserved according to the implementation. It is useful for platform-defined MMIO, not general thread synchronization.

#### 1. Example

```cpp
auto* reg = reinterpret_cast<volatile uint32_t*>(0x40000000u);
uint32_t value = *reg;
```

This assumes a valid bare-metal register mapping and access width.

#### 2. C++20 changes

C++20 deprecated several volatile-related constructs, including certain compound assignments and increment/decrement operations on volatile-qualified scalar objects, and certain volatile-qualified function parameter/return types. Exact rules and subsequent revisions matter; the volatile qualifier itself remains available.

A clearer MMIO RMW expression is a separate read and write when the hardware permits it. Separating the operations does not make them atomic.

#### 3. Synchronization

Use std::atomic, mutexes or platform primitives for concurrent shared memory. Confirm atomics are suitable for the execution context; device memory is not ordinary C++ atomic storage.

**Interview takeaway:** Volatile preserves required accesses; it is not a memory fence or lock. Follow the target MMIO semantics and language version.

### How do you model a hardware register in type-safe C++? {H}
A type-safe C++ register abstraction can encode register address, width and permitted operations in types, reducing accidental misuse while retaining direct MMIO access.

#### 1. Example

```cpp
#include <cstdint>

template<std::uintptr_t Address>
struct ReadOnlyReg32 {
    static std::uint32_t read() {
        return *reinterpret_cast<volatile const std::uint32_t*>(
            Address);
    }
};

template<std::uintptr_t Address>
struct WriteOnlyReg32 {
    static void write(std::uint32_t value) {
        *reinterpret_cast<volatile std::uint32_t*>(Address) = value;
    }
};
```

A read-only type has no write method; a write-only type has no read method. Addresses must be valid, mapped and aligned for the device.

#### 2. Usage

```cpp
using Status = ReadOnlyReg32<0x40000010u>;
using Clear = WriteOnlyReg32<0x40000014u>;

auto status = Status::read();
Clear::write(1u << 3);
```

The clear register is assumed to accept a direct mask write. Build separate abstractions for W1C and ordinary read/write registers rather than exposing unsafe universal bit setters.

**Interview takeaway:** Types can prevent invalid register operations at compile time. They cannot replace the hardware manual, barriers, endian handling or concurrency design.

### What is the static initialisation order fiasco? {M}
The static initialization order fiasco occurs when a global object in one C++ translation unit depends on another global object whose dynamic initialization has not yet occurred.

#### 1. Example

```cpp
// file1.cpp
extern Device device;
Logger logger(device);

// file2.cpp
Device device(/* hardware configuration */);
```

The initialization order across translation units is not generally a dependency order chosen by the programmer. Logger may observe a device that has not been dynamically initialized.

#### 2. Solutions

Prefer constant initialization where possible (constexpr/constinit as applicable), explicitly initialize dependent resources in a board-init sequence, or use function-local static objects with documented initialization/lifetime behavior.

#### 3. Embedded caveat

Global constructors may run before application hardware initialization. Function-local static guards can require runtime synchronization; verify behavior if they are used from multiple threads or interrupt contexts.

**Interview takeaway:** Avoid hidden hardware dependencies in global constructors. Explicit startup ordering makes firmware initialization and failure handling easier to reason about.

### How do you call C code from C++ and C++ from C (extern "C")? {E}
extern "C" gives a C++ declaration C language linkage, commonly avoiding C++ name mangling and enabling interoperability with C functions.

#### 1. Shared header

```c
#ifndef DRIVER_H
#define DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif

int driver_start(void);

#ifdef __cplusplus
}
#endif
#endif
```

The header can be included by both C and C++ source files.

#### 2. C++ implementation exposed to C

```cpp
#include "driver.h"

int driver_start(void)
{
    return start_cpp_driver();
}
```

The earlier declaration establishes C linkage. The wrapper exposes a C-compatible signature while hiding C++ implementation details.

#### 3. Limits

Do not expose C++ references, exceptions or arbitrary class layouts as a portable C ABI. Use opaque handles and explicit create/destroy functions when sharing object ownership across the boundary.

**Interview takeaway:** extern "C" controls linkage, not automatic type conversion or exception compatibility. Design a C-compatible API and keep C++ details behind it.

### Which standard library features are safe on a microcontroller? {M}
Many C++ standard library features are useful in embedded systems, provided their memory, timing and runtime requirements fit the target.

| Feature | Consideration |
|---|---|
| std::array | Fixed-size storage |
| std::span (C++20) | Non-owning view; no allocation itself |
| std::optional / variant | In-place value representation; inspect size |
| std::unique_ptr | Ownership; custom deleter can avoid heap |
| std::vector / string | May allocate dynamically |
| std::function | May allocate depending on stored callable |
| iostream | Potentially significant runtime/footprint |

#### 1. Example

```cpp
std::array<unsigned char, 128> buffer{};
std::span<unsigned char> view(buffer);
```

The array owns fixed storage and span describes it without owning it. The view must not outlive the array.

#### 2. Selection process

Check availability in the toolchain, hidden allocation, exception/RTTI requirements, synchronization, destructor behavior and worst-case execution. Freestanding implementations may provide only a subset of library facilities.

**Interview takeaway:** Evaluate each library facility's actual behavior and target support. Fixed-capacity containers and non-owning views are often valuable in MCU firmware; neither library use nor avoidance alone guarantees deterministic behavior.

