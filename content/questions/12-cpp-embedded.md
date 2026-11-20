---
slug: cpp-embedded
title: C++ for Embedded
icon: ➕
level: Intermediate
order: 14
desc: Classes, virtual functions, RAII, templates, constexpr, smart pointers and which C++ features are safe on a microcontroller.
---
More firmware teams now use C++. Interviewers want to know you understand what each feature costs in flash, RAM and time.

### What is the difference between C and C++ for embedded systems? {E}
C++ adds classes, templates, RAII, references, namespaces, `constexpr`, stronger typing and a richer standard library. Most of these are **zero-cost**: they produce the same code as hand-written C. The features with real cost are exceptions, RTTI, dynamic allocation, and careless use of virtual functions or templates (code bloat). Many embedded projects compile with `-fno-exceptions -fno-rtti` and avoid the heap after start-up.

### How do virtual functions work? What is a vtable? {M}
For each class with virtual functions, the compiler generates a **vtable**: a table of function pointers in `.rodata`. Every object of such a class contains a hidden **vptr** pointing to its class's vtable. A virtual call loads the vptr, loads the function pointer from a fixed offset and calls it indirectly. Cost: one pointer per object, one table per class, and an indirect call that cannot be inlined. A base class with virtual functions should have a **virtual destructor**, so deleting through a base pointer runs the derived destructor.

### What is RAII? {E}
Resource Acquisition Is Initialisation: a resource is acquired in an object's constructor and released in its destructor, so it is released automatically when the object goes out of scope, on every return path.

```cpp
class IrqLock {
public:
    IrqLock() : primask_(__get_PRIMASK()) { __disable_irq(); }
    ~IrqLock() { __set_PRIMASK(primask_); }
    IrqLock(const IrqLock&) = delete;
    IrqLock& operator=(const IrqLock&) = delete;
private:
    uint32_t primask_;
};

void update() { IrqLock lock; shared++; }   // re-enabled on any exit
```

The same pattern covers mutexes (`std::lock_guard`), chip selects, and file handles.

### What are constexpr and consteval? {M}
`constexpr` marks variables and functions that **can** be evaluated at compile time; if their arguments are constants, the result is computed by the compiler and placed in flash. `consteval` (C++20) functions **must** be evaluated at compile time. Embedded uses: computing baud-rate divisors, CRC tables and register values at compile time, and `static_assert` checks on configuration.

```cpp
constexpr uint32_t brr(uint32_t clk, uint32_t baud) { return (clk + baud / 2) / baud; }
static_assert(brr(84'000'000, 115200) == 729);
```

### Why are exceptions and RTTI often disabled in embedded C++? {M}
Exceptions need unwind tables and runtime support that add significant flash, and the time to throw and catch is hard to bound, which conflicts with real-time requirements. RTTI (`typeid`, `dynamic_cast`) adds type information for every polymorphic class. Disabling them with `-fno-exceptions -fno-rtti` makes binaries smaller and behaviour predictable; errors are then returned through status codes or types like `std::expected` (C++23) or a custom `Result<T, E>`.

### What are templates and what is code bloat? {M}
Templates generate code for each set of type (or value) parameters at compile time, giving type-safe generic code with no runtime overhead. Each distinct instantiation produces its own copy of the code, so `Buffer<uint8_t, 64>` and `Buffer<uint8_t, 128>` are two separate functions. Reduce bloat by moving size-independent logic into a non-template base class and keeping templates thin; check with the map file or `nm --size-sort`.

### What are smart pointers and should you use them on an MCU? {M}
`std::unique_ptr` owns an object exclusively and deletes it when it goes out of scope; it has no overhead beyond a raw pointer. `std::shared_ptr` uses a reference count (with atomic operations) and a separate control block, which costs RAM and time. On MCUs that forbid the heap, smart pointers are less relevant, but `unique_ptr` with a custom deleter is still useful for RAII around pool allocations or handles.

### What is the difference between new/delete and malloc/free? {E}
`new` allocates memory **and** calls the constructor; `delete` calls the destructor and then frees. `malloc`/`free` only deal with raw bytes. `new` throws `std::bad_alloc` on failure (or returns `nullptr` with `new (std::nothrow)`). **Placement new** constructs an object in memory you already own, such as a static buffer or a pool, which is common in embedded C++. Never mix them: do not `free` memory obtained with `new`.

### What does volatile mean in C++ and what changed in C++20? {H}
`volatile` has the same meaning as in C: accesses must happen as written. C++20 **deprecated** compound operations and increments on volatile variables (`vreg |= 1;`, `v++`) and volatile function parameters and return types, because these suggest an atomicity they do not have. Write the read and write explicitly (`vreg = vreg | 1;`). C++23 un-deprecated bitwise compound assignment after feedback from the embedded community, since `REG |= MASK` is so common. Use `std::atomic` for inter-thread data, not `volatile`.

### How do you model a hardware register in type-safe C++? {H}
Wrap the address in a small template so the compiler checks access rights and can inline everything:

```cpp
template <uintptr_t Addr>
struct Reg {
    static uint32_t read() { return *reinterpret_cast<volatile uint32_t*>(Addr); }
    static void write(uint32_t v) { *reinterpret_cast<volatile uint32_t*>(Addr) = v; }
    static void set(uint32_t m) { write(read() | m); }
};
using GPIOA_ODR = Reg<0x40020014>;
GPIOA_ODR::set(1u << 5);
```

Extend the same idea with separate read-only and write-only types and with enum classes for field values, so illegal register writes fail to compile.

### What is the static initialisation order fiasco? {M}
The order in which global objects in **different translation units** are constructed is unspecified. If one global's constructor uses another global from a different file, it may run before that object is constructed. In firmware this also means constructors run in start-up code before `main`, possibly before clocks are configured. Fixes: construct-on-first-use (a function returning a reference to a static local), explicit `init()` functions called from `main`, or `constinit` (C++20) to guarantee compile-time initialisation.
