---
slug: c-programming
title: C Programming
icon: 🧩
level: Beginner
order: 1
desc: Keywords, storage classes, scope, the preprocessor, undefined behaviour and the questions every C interview starts with.
---
Almost every embedded interview opens with C. These questions cover the language itself: types, storage classes, the preprocessor, and the corners where C stops protecting you.

### What are the storage classes in C? {E}
C has four storage-class specifiers that decide **lifetime**, **scope** and **linkage**:

| Specifier | Lifetime | Default value | Where it lives |
|---|---|---|---|
| `auto` | block | garbage | stack (or register) |
| `register` | block | garbage | CPU register (a hint only) |
| `static` | whole program | zero | `.data` / `.bss` |
| `extern` | whole program | zero | defined elsewhere |

C11 adds `_Thread_local`. Local variables are `auto` by default, so you almost never write the keyword. You cannot take the address of a `register` variable.

### What does the static keyword do in different contexts? {E}
`static` means two different things depending on where it appears:

1. **Inside a function**, a static local keeps its value between calls. It is initialised once, before `main` runs, and lives in `.data` or `.bss`, not on the stack.
2. **At file scope**, on a global variable or a function, it gives **internal linkage**: the name is visible only inside that translation unit. This is how you make a "private" function in C.

```c
static int counter;          /* only visible in this .c file */

int next_id(void)
{
    static int id = 100;     /* survives across calls */
    return id++;
}
```

In embedded code, file-scope `static` is the main tool for encapsulating driver state.

### What is the difference between declaration and definition? {E}
A **declaration** tells the compiler a name exists and what its type is. A **definition** also allocates storage (for a variable) or provides the body (for a function).

```c
extern int baud;        /* declaration only */
int baud = 115200;      /* definition */
int add(int, int);      /* declaration (prototype) */
int add(int a, int b) { return a + b; }  /* definition */
```

You can declare something many times but define it exactly once in the program (the One Definition Rule). Put declarations in headers and definitions in `.c` files.

### What is the use of the extern keyword? {E}
`extern` declares a variable or function that is defined in another translation unit, so the linker can resolve it. Functions are `extern` by default. For variables you write `extern int g_ticks;` in a header and `int g_ticks;` in exactly one `.c` file. If you forget the definition you get an "undefined reference" link error; if you define it in two files you get "multiple definition".

### What is the difference between const and #define? {E}
- `#define` is a textual substitution done by the preprocessor. It has no type, no scope, and does not exist in the debugger.
- `const` creates a typed, scoped object that the compiler checks. It can be placed in flash (`.rodata`) and seen in a debugger.

Use `const` (or `enum` for integer constants) for type safety. One C-specific catch: a `const int` is **not** a constant expression in C, so it cannot size a file-scope array or be a `case` label. That is why `#define` and `enum` are still common in C headers.

### What does const int *p, int *const p and const int *const p mean? {M}
Read right-to-left from the variable name:

- `const int *p` (same as `int const *p`): pointer to a const int. You can move `p` but cannot write `*p`.
- `int *const p`: const pointer to int. You can write `*p` but cannot move `p`. Must be initialised.
- `const int *const p`: neither can change.

A typical embedded use is `volatile uint32_t *const UART_DR = (uint32_t *)0x40011004;`: the address is fixed, the contents change.

### What is the difference between a macro and an inline function? {M}
| | Macro | `static inline` function |
|---|---|---|
| Processed by | Preprocessor | Compiler |
| Type checking | None | Full |
| Arguments evaluated | Possibly many times | Exactly once |
| Debuggable | No | Yes |
| Can be generic | Yes | No (until `_Generic`) |

The classic macro bug:

```c
#define SQUARE(x) ((x) * (x))
int y = SQUARE(i++);   /* i incremented twice: undefined behaviour */
```

Prefer `static inline` for small helpers. Use macros when you need stringification (`#`), token pasting (`##`), `__FILE__`/`__LINE__`, or compile-time constants.

### Why should macro arguments and bodies be wrapped in parentheses? {E}
Because macros are text substitution, operator precedence can silently change the meaning:

```c
#define DOUBLE(x) x + x
int r = 3 * DOUBLE(2);   /* becomes 3 * 2 + 2 = 8, not 12 */
```

Wrap each argument and the whole body: `#define DOUBLE(x) ((x) + (x))`. For multi-statement macros, wrap them in `do { ... } while (0)` so they behave like a single statement after an `if` without braces.

### Why are multi-line macros wrapped in do { } while(0)? {M}
It makes the macro a single statement that requires a trailing semicolon, so it is safe in every context:

```c
#define SWAP(a, b) do { int t_ = (a); (a) = (b); (b) = t_; } while (0)

if (x > y)
    SWAP(x, y);   /* works */
else
    other();
```

With plain braces `{ ... }` the `;` after the macro ends the `if`, and the `else` becomes a syntax error. The compiler removes the loop entirely, so it costs nothing.

### What are # and ## in macros? {M}
- `#` (stringizing) turns a macro argument into a string literal: `#define STR(x) #x` makes `STR(UART1)` into `"UART1"`.
- `##` (token pasting) glues two tokens: `#define REG(n) GPIO##n##_ODR` makes `REG(A)` into `GPIOA_ODR`.

To stringify the *value* of another macro you need two levels: `#define XSTR(x) STR(x)`.

### What is the difference between #include <file> and #include "file"? {E}
`<file>` searches only the system and `-I` include paths. `"file"` first searches the directory of the current source file, then falls back to the same paths as `<>`. Use quotes for your project headers and angle brackets for the standard library and third-party SDKs.

### What are include guards and #pragma once? {E}
Include guards stop a header being processed twice in one translation unit, which would cause redefinition errors:

```c
#ifndef UART_H
#define UART_H
/* declarations */
#endif
```

`#pragma once` does the same in one line. It is supported by GCC, Clang, IAR and Keil, but it is not part of the C standard, so some coding standards (such as MISRA) still require classic guards.

### What is undefined behaviour? Give examples. {M}
Undefined behaviour (UB) means the standard places no requirement on what happens. The compiler is allowed to assume UB never occurs and optimise on that basis, so the result can be anything, including code that appears to work in debug builds and breaks at `-O2`.

Common examples:
- Signed integer overflow (`INT_MAX + 1`)
- Dereferencing NULL or a dangling pointer
- Reading an uninitialised local variable
- Out-of-bounds array access
- Shifting by a negative amount or by ≥ the type's width
- Modifying a variable twice without a sequence point: `i = i++;`
- Violating strict aliasing

Related terms: *unspecified* behaviour (one of several valid outcomes, such as argument evaluation order) and *implementation-defined* behaviour (the compiler must document it, such as the size of `int` or right-shift of a negative number).

### What is a sequence point? {H}
A sequence point is a point at which all side effects of previous evaluations are complete. Examples are the end of a full expression (`;`), the `&&`, `||`, `?:` and comma operators, and the point just before a function is called. C11 replaced the term with "sequenced before", but the rule is the same: modifying an object twice, or reading and modifying it, without sequencing between them is undefined.

```c
i = i++ + 1;      /* UB */
a[i] = i++;       /* UB */
f(i++, i++);      /* UB: argument evaluation is unsequenced */
```

### What is the size of an int, and what are fixed-width types? {E}
The standard only guarantees minimum ranges: `int` is at least 16 bits, `long` at least 32, `long long` at least 64. On an 8-bit AVR `int` is 16 bits; on ARM Cortex-M and x86-64 Linux it is 32 bits.

For hardware registers and protocols, always use `<stdint.h>` types such as `uint8_t`, `int16_t`, `uint32_t`, so the width is the same on every target. `size_t` is for sizes and indexes, and `uintptr_t` is for holding a pointer as an integer.

### What is integer promotion? {M}
In arithmetic, any type smaller than `int` (`char`, `short`, bit-fields) is converted to `int` (or `unsigned int` if `int` cannot hold all its values) before the operation. This catches people out:

```c
uint8_t a = 0xFF;
if (~a == 0x00) { /* never true: ~a is int 0xFFFFFF00 */ }

uint8_t x = 200, y = 100;
uint8_t z = x + y;   /* computed as int 300, truncated to 44 */
```

Cast back explicitly, for example `(uint8_t)~a`, when you want 8-bit results.

### What happens when you compare signed and unsigned integers? {M}
The usual arithmetic conversions turn the signed operand into unsigned when both have the same rank. A negative number becomes a huge positive one:

```c
int i = -1;
unsigned int u = 1;
if (i < u) puts("less");   /* not printed: -1 becomes 0xFFFFFFFF */
```

Compile with `-Wall -Wextra -Wsign-compare` to catch this. The same trap appears with `sizeof`, which returns unsigned `size_t`.

### What is the difference between ++i and i++? {E}
`++i` increments and yields the new value; `i++` yields the old value and then increments. As a standalone statement (`i++;` in a `for` loop) they produce identical machine code for integers. The difference matters only when the result is used in an expression.

### What is the difference between a structure and a union? {E}
In a `struct` every member has its own storage, so the size is at least the sum of the members (plus padding). In a `union` all members share the same storage, so the size is that of the largest member (plus padding) and only one member holds a meaningful value at a time.

Unions are used for variant types, for saving RAM, and for viewing the same bytes in different ways:

```c
typedef union {
    uint32_t word;
    uint8_t  byte[4];
} reg32_t;
```

Type punning through a union is allowed in C (not in C++), but byte order is implementation-defined.

### What is structure padding and how do you avoid it? {M}
Compilers insert padding bytes so each member sits at an address that is a multiple of its alignment. This makes access fast and, on some CPUs, possible at all.

```c
struct a { char c; int i; char d; };   /* 12 bytes on 32-bit ARM */
struct b { int i; char c; char d; };   /* 8 bytes */
```

To reduce padding, order members from largest to smallest alignment. To remove it entirely use `__attribute__((packed))` or `#pragma pack(1)`, but unaligned access is slower and can fault on some cores (Cortex-M0, older ARM). Never rely on struct layout for data sent over a wire: serialise field by field.

### What are bit-fields and what are their drawbacks? {M}
Bit-fields let you name individual bits in a struct:

```c
struct status {
    unsigned ready : 1;
    unsigned error : 1;
    unsigned mode  : 3;
};
```

They save memory and read well, but the standard leaves bit order, padding and whether they can straddle storage units implementation-defined. Writing one bit-field is a read-modify-write of the whole storage unit, which is not atomic. For memory-mapped registers most teams use explicit masks and shifts instead, so the layout is guaranteed.

### What is an enum and how big is it? {E}
An `enum` defines named integer constants. The constants have type `int`. The size of the enum type itself is implementation-defined: it must be able to hold all its values, and most compilers use `int`, but options such as `-fshort-enums` (common in ARM toolchains) make it as small as possible. Do not use an enum type directly inside a struct that crosses an ABI or a wire; use a fixed-width integer.

### What is the difference between malloc, calloc, realloc and free? {E}
- `malloc(n)` allocates `n` bytes, uninitialised.
- `calloc(count, size)` allocates `count * size` bytes, zeroed, and checks the multiplication for overflow.
- `realloc(p, n)` resizes a block, possibly moving it. If it fails it returns `NULL` and leaves the original block alive, so never write `p = realloc(p, n);`.
- `free(p)` releases the block. `free(NULL)` is safe.

Many embedded projects ban heap use after start-up (MISRA, safety standards) because of fragmentation and non-deterministic timing. See the Pointers & Memory topic.

### What is the difference between strcpy, strncpy and memcpy? {M}
- `strcpy(d, s)` copies until and including `'\0'`. No bounds check, a classic overflow source.
- `strncpy(d, s, n)` copies at most `n` bytes and pads with zeros, but **does not terminate** `d` if `s` is `n` bytes or longer.
- `memcpy(d, s, n)` copies exactly `n` bytes, ignores `'\0'`, and is undefined if the regions overlap. Use `memmove` for overlapping regions.

Safer patterns: `snprintf(d, sizeof d, "%s", s)` or a project-specific `strlcpy`.

### What is the difference between an array and a pointer? {M}
An array is a block of contiguous objects; a pointer is a variable that holds an address. An array name **decays** to a pointer to its first element in most expressions, which is why they feel interchangeable. They differ in three places:

- `sizeof arr` gives the whole array size; `sizeof ptr` gives the pointer size.
- `&arr` has type pointer-to-array (`int (*)[10]`), not pointer-to-pointer.
- You cannot assign to an array name.

Passing an array to a function always passes a pointer, so the function cannot know the length. Pass it separately.

### What is a function pointer and where is it used? {M}
A function pointer stores the address of a function so it can be called indirectly:

```c
typedef void (*handler_t)(uint8_t event);

static void on_press(uint8_t e) { /* ... */ }
handler_t cb = on_press;
cb(3);
```

Embedded uses: interrupt vector tables, callbacks from drivers to application code, state machines (table of handlers per state), and driver "ops" structures, like the Linux `struct file_operations`. Always check a callback pointer for `NULL` before calling it.

### What is the difference between call by value and call by reference? {E}
C only has call by value: the function receives a copy of each argument. To let a function modify the caller's variable, pass its address (a pointer), which is often called "call by reference" in C. Passing a large struct by value copies it onto the stack, so embedded code usually passes `const struct foo *` instead.

### What is recursion and why is it avoided in embedded code? {E}
Recursion is a function calling itself. It is often avoided in embedded systems because stack depth depends on the input, so the worst-case stack usage cannot be bounded statically, and an overflow silently corrupts memory on MCUs without an MPU. MISRA C forbids it. Rewrite with a loop and an explicit, bounded stack when needed.

### What are the stages of compilation in C? {E}
1. **Preprocessing** (`gcc -E`): expands `#include`, macros and conditionals into a `.i` file.
2. **Compilation** (`gcc -S`): turns C into assembly (`.s`).
3. **Assembly** (`gcc -c`): turns assembly into a relocatable object file (`.o`) with symbol and relocation tables.
4. **Linking**: combines objects and libraries, resolves symbols and places sections at addresses defined by the linker script, producing an ELF. For a microcontroller you then convert it with `objcopy -O binary` or `-O ihex` for flashing.

### What is the difference between a .bss and a .data section? {E}
- `.data` holds initialised globals and statics with non-zero values. The initial values are stored in flash and copied to RAM by the start-up code.
- `.bss` holds globals and statics that are zero or uninitialised. Only their size is stored; start-up code zeroes the RAM region.
- `.rodata` holds constants and string literals, usually left in flash.
- `.text` holds code.

Moving a large table from `int table[] = {...}` to `const int table[] = {...}` moves it from `.data` (flash + RAM) to `.rodata` (flash only).

### What is a dangling pointer, a wild pointer and a NULL pointer? {E}
- **NULL pointer**: deliberately points to nothing; dereferencing it is UB (on Cortex-M address 0 is often the vector table, so it may not even fault).
- **Wild pointer**: an uninitialised pointer with a garbage value.
- **Dangling pointer**: points to memory that has been freed or to a local variable whose function has returned.

Initialise pointers, set them to `NULL` after `free`, and never return the address of a local.

### What is the volatile keyword? {E}
`volatile` tells the compiler that an object can change outside the normal flow of the program, so every read and write in the source must actually happen, in order, and cannot be cached in a register or removed. It is covered in depth in the Embedded C topic and in the article on `volatile`.

### Can a variable be both const and volatile? {M}
Yes. `const` means *this code* may not write it; `volatile` means *something else* may change it. A read-only hardware status register is the textbook example:

```c
#define USART_SR (*(const volatile uint32_t *)0x40011000u)
```

The compiler will reject writes and will re-read the register every time.

### What does the restrict keyword mean? {H}
`restrict` (C99) is a promise from the programmer that, for the lifetime of the pointer, the object it points to is accessed only through that pointer. It lets the compiler skip reloading values after stores through other pointers and vectorise loops. `memcpy` is declared with `restrict` parameters, which is exactly why overlapping buffers are undefined for it. Breaking the promise is UB.

### What is the difference between exit() and return from main? {E}
Returning from `main` is equivalent to calling `exit()` with that value: `atexit` handlers run and streams are flushed. `_Exit()` or `_exit()` terminate without cleanup. On a bare-metal MCU, `main` should never return. If it does, the start-up code usually falls into an infinite loop, so firmware ends with `for (;;) { }`.

### How do variadic functions work? {M}
A variadic function like `printf` takes a fixed parameter followed by `...`. It reads the extra arguments with `<stdarg.h>`:

```c
#include <stdarg.h>
int sum(int count, ...)
{
    va_list ap;
    int s = 0;
    va_start(ap, count);
    while (count--) s += va_arg(ap, int);
    va_end(ap);
    return s;
}
```

The callee has no way to know the number or types of arguments, so a format string or count must tell it. Arguments undergo default promotions (`char`/`short` become `int`, `float` becomes `double`), so `va_arg(ap, char)` is wrong.
