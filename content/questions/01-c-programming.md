---
slug: c-programming
title: C Programming
icon: 🧩
level: Beginner
order: 1
desc: Keywords, storage classes, scope, the preprocessor, integer rules, undefined behaviour and the questions every C interview starts with.
---
Almost every embedded interview opens with C. These questions cover the language itself: types, storage classes, the preprocessor, integer conversion rules, and the corners where C stops protecting you. Each answer gives the one-line answer first, then the explanation, an example, and the traps interviewers look for.

### What are the storage classes in C? {E}
Storage classes in C determine the **lifetime, storage duration and linkage** of variables.

#### **1. Types of storage classes**

| Storage class | Scope | Lifetime | Default value |
|---|---|---|---|
| `auto` | Local | Until block exits | Indeterminate |
| `register` | Local | Until block exits | Indeterminate |
| `static` | Local or file | Entire program | Zero |
| `extern` | Depends on declaration | Entire program for ordinary objects | Zero at definition, if not explicitly initialized |
| `_Thread_local` | Depends on declaration | Thread lifetime | Zero |

#### **2. Example**

```c
int global = 100;

void fun(void)
{
    auto int a = 10;
    register int b = 20;
    static int c = 0;
    extern int global;

    printf("%d ", ++c);
}
```

Calling `fun()` three times prints `1 2 3`, because `static` retains its value between function calls.

#### **3. Typical memory location**

| Variable | Memory location |
|---|---|
| `auto` | Stack |
| `register` | CPU register or stack |
| Initialized static/global | `.data` |
| Zero-initialized static/global | `.bss` |

Actual placement depends on the compiler and linker.

**Interview takeaway:** `auto` is used for ordinary local variables, `register` suggests fast access, `static` preserves lifetime or restricts linkage, and `extern` typically provides access to variables defined elsewhere.

C11 introduced `_Thread_local`. The `typedef` keyword is also grammatically a storage-class specifier, but it creates a type alias rather than allocating storage.

### What does the static keyword do in different contexts? {E}
The `static` keyword in C controls the **lifetime and linkage** of variables and functions. Its behaviour depends on where it is used.

#### 1. Static local variable

A static local variable retains its value between function calls and is initialized only once.

```c
void fun(void)
{
    static int count = 0;
    count++;
    printf("%d ", count);
}

int main(void)
{
    fun();
    fun();
    fun();
    return 0;
}
```

**Output:** `1 2 3`

Without `static`, the output would be `1 1 1`.

#### 2. Static global variable

A static global variable has internal linkage, meaning it cannot be accessed by name from another source file.

```c
// file1.c
static int count = 10;

// file2.c
extern int count;  // Cannot link to file1's count
```

It is useful for hiding module-specific data.

#### 3. Static function

A static function has internal linkage and can only be called by name within the same translation unit.

```c
static void driver_init(void)
{
    printf("Driver initialized");
}
```

It is commonly used in embedded software and Linux device drivers to hide internal helper functions.

#### 4. Memory location

| Declaration | Typical memory location |
|---|---|
| `static int a = 10;` | `.data` |
| `static int a = 0;` | `.bss` |
| `static int a;` | `.bss` |
| Static function | `.text` |

Static variables exist throughout the program's lifetime.

#### 5. Summary

| Context | Purpose |
|---|---|
| Static local variable | Retains value between function calls |
| Static global variable | Restricts linkage to the current translation unit |
| Static function | Restricts linkage to the current translation unit |

**Interview takeaway:** A static local variable changes its storage duration, whereas a static global variable or function restricts its linkage. Static variables are not automatically thread-safe.

### What is the difference between declaration and definition? {E}
A **declaration** introduces the name and type of a variable or function to the compiler, whereas a **definition** provides the actual variable or function body.

#### 1. Variable declaration and definition

```c
extern int count;  // Declaration
int count = 10;    // Definition
```

- **Declaration:** Tells the compiler that `count` exists and is of type `int`.
- **Definition:** Allocates storage for `count` and initializes it to `10`.

#### 2. Function declaration and definition

```c
int add(int, int);  // Declaration

int add(int a, int b)  // Definition
{
    return a + b;
}
```

The declaration tells the compiler about the function's name, return type and parameter types. The definition provides its implementation.

#### 3. Example using multiple source files

**file1.c**

```c
int count = 100;
```

**file2.c**

```c
extern int count;

void fun(void)
{
    printf("%d", count);
}
```

<div style="max-width:680px;margin:16px 0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 145" width="100%" role="img" aria-label="The linker resolves the count reference in file2.c to the definition in file1.c">
  <rect x="5" y="8" width="155" height="56" rx="6" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/>
  <text x="82.5" y="28" font-size="12" font-weight="600" fill="currentColor" text-anchor="middle">file1.c</text>
  <text x="82.5" y="47" font-size="11" font-family="monospace" fill="currentColor" text-anchor="middle">int count = 100;</text>
  <rect x="180" y="8" width="155" height="56" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
  <text x="257.5" y="28" font-size="12" font-weight="600" fill="currentColor" text-anchor="middle">file2.c</text>
  <text x="257.5" y="47" font-size="11" font-family="monospace" fill="currentColor" text-anchor="middle">extern int count;</text>
  <path d="M82.5 64 V82 H170 M257.5 64 V82 H170 V99" stroke="currentColor" stroke-width="1.3" fill="none"/>
  <path d="M166 94 L170 99 L174 94" stroke="currentColor" fill="none"/>
  <rect x="80" y="100" width="180" height="37" rx="6" fill="#94a3b8" fill-opacity=".12" stroke="currentColor" stroke-opacity=".5"/>
  <text x="170" y="115" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">Linker</text>
  <text x="170" y="129" font-size="10" text-anchor="middle" fill="currentColor">Resolves count reference</text>
</svg>
</div>

The linker resolves the reference in `file2.c` to the definition in `file1.c`.

#### 4. Summary

| Declaration | Definition |
|---|---|
| Introduces name and type | Provides the actual object or function body |
| Can appear multiple times | Normally defined once for an externally linked symbol |
| Does not necessarily allocate memory | Defines storage for an object |
| `extern int a;` | `int a = 10;` |
| `int add(int, int);` | `int add(int a, int b) { return a+b; }` |

**Interview takeaway:** Every definition is a declaration, but every declaration is not necessarily a definition.

### What is the use of the extern keyword? {E}
The `extern` keyword in C is used to **declare a variable or function that is defined elsewhere**, typically in another source file.

It allows multiple source files to access the same global variable without creating separate copies.

#### 1. Using extern with variables

**file1.c**

```c
int count = 100;
```

**file2.c**

```c
extern int count;

void fun(void)
{
    printf("%d", count);
}
```

**Output:** `100`

The compiler knows the type of `count` through its declaration, and the linker resolves its reference to the definition in `file1.c`.

<div style="max-width:680px;margin:16px 0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 172" width="100%" role="img" aria-label="Both source files reference the same count variable in shared memory">
  <rect x="8" y="5" width="148" height="65" rx="6" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/>
  <text x="82" y="22" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">file1.c</text>
  <text x="82" y="40" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">int count = 100;</text>
  <text x="82" y="57" font-size="10" text-anchor="middle" fill="currentColor">Definition</text>
  <rect x="184" y="5" width="148" height="65" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
  <text x="258" y="22" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">file2.c</text>
  <text x="258" y="40" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">extern int count;</text>
  <text x="258" y="57" font-size="10" text-anchor="middle" fill="currentColor">Declaration</text>
  <path d="M82 70 V91 H170 M258 70 V91 H170 V116" stroke="currentColor" fill="none" stroke-width="1.3"/>
  <path d="M165 111 L170 116 L175 111" stroke="currentColor" fill="none"/>
  <rect x="85" y="116" width="170" height="43" rx="6" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/>
  <text x="170" y="133" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">Shared memory (.data)</text>
  <text x="170" y="150" font-size="12" font-family="monospace" text-anchor="middle" fill="currentColor">count = 100</text>
</svg>
</div>

Both source files access the same memory location.

#### 2. Using extern with functions

**file1.c**

```c
void driver_init(void)
{
    printf("Driver initialized");
}
```

**file2.c**

```c
extern void driver_init(void);

void fun(void)
{
    driver_init();
}
```

For ordinary function declarations, `extern` is implicit, so explicitly writing it is generally unnecessary.

#### 3. Does extern allocate memory?

```c
extern int a;       // Declaration
int a = 10;         // Definition
extern int b = 20;  // Definition at file scope
```

An `extern` variable declaration without an initializer normally does not allocate memory. However, an `extern` declaration with an initializer at file scope is a definition.

#### 4. Difference between static and extern

| `static` (file scope) | `extern` (normally) |
|---|---|
| Internal linkage | External linkage |
| Symbol restricted to current translation unit | Symbol accessible across translation units |
| Used for hiding module-specific data | Used for sharing variables and functions |

**Interview takeaway:** `extern` allows multiple source files to share the same global variable or function. The compiler checks its declaration, and the linker resolves its reference to the corresponding definition.

### What is the difference between const and #define? {E}
Both `const` and `#define` are used to represent constant values in C, but they work differently.

`const` creates a **type-qualified object**, whereas `#define` performs **textual substitution during preprocessing**.

#### 1. Using const

```c
const int max = 100;

int main(void)
{
    printf("%d", max);
    return 0;
}
```

- Has a specific data type.
- Cannot be modified through its const-qualified name.
- Can have a memory address.
- Follows C scope rules.

#### 2. Using #define

```c
#define MAX 100

int main(void)
{
    printf("%d", MAX);
    return 0;
}
```

Before compilation, the preprocessor replaces `MAX` with `100`.

```c
printf("%d", 100);
```

The macro itself does not create a variable or allocate memory.

#### 3. How the compiler handles them

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 225" width="100%" role="img" aria-label="Comparison of const and define preprocessing and compilation"><text x="82.5" y="16" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">const</text>
<rect x="5" y="28" width="155" height="34" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
<text x="82.5" y="49" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">const int x = 100;</text>
<path d="M82.5 62 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="5" y="78" width="155" height="30" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/>
<text x="82.5" y="97" font-size="11" text-anchor="middle" fill="currentColor">Preprocessor</text>
<path d="M82.5 108 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="5" y="124" width="155" height="33" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
<text x="82.5" y="145" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">const int x = 100;</text>
<path d="M82.5 157 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="5" y="173" width="155" height="44" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/>
<text x="82.5" y="190" font-size="11" text-anchor="middle" fill="currentColor">Compiler</text>
<text x="82.5" y="205" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">Typed object</text>
<text x="257.5" y="16" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">#define</text>
<rect x="180" y="28" width="155" height="34" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
<text x="257.5" y="49" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">#define X 100</text>
<path d="M257.5 62 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="180" y="78" width="155" height="30" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/>
<text x="257.5" y="97" font-size="11" text-anchor="middle" fill="currentColor">Preprocessor</text>
<path d="M257.5 108 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="180" y="124" width="155" height="33" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/>
<text x="257.5" y="145" font-size="11" font-family="monospace" text-anchor="middle" fill="currentColor">X replaced by 100</text>
<path d="M257.5 157 v16 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/>
<rect x="180" y="173" width="155" height="44" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/>
<text x="257.5" y="190" font-size="11" text-anchor="middle" fill="currentColor">Compiler</text>
<text x="257.5" y="205" font-size="11" font-weight="600" text-anchor="middle" fill="currentColor">Literal value</text>
</svg></div>

#### 4. Memory location

```c
const int a = 10;
#define B 20
```

- `a` may be stored in `.rodata`, stack or another memory region, depending on its scope and compiler optimization.
- `B` has no dedicated memory location. Its value is substituted wherever the macro is used.

#### 5. Difference between const and #define

| Feature | `const` | `#define` |
|---|---|---|
| Processed by | Compiler | Preprocessor |
| Data type | Yes | No inherent type |
| Type checking | Yes | After macro expansion |
| Memory allocation | May require storage | No dedicated storage |
| Address | Can be obtained | Macro itself has no address |
| Scope | C scope rules | Until `#undef` or end of translation unit |
| Debugging | Generally easier | Generally harder |
| Use in `#if` | No | Yes |

#### 6. Use in embedded systems

```c
#define UART_BASE 0x40011000U
#define BUFFER_SIZE 256

const int timeout_ms = 100;
```

`#define` is commonly used for hardware addresses, register masks and compile-time configuration, while `const` is useful for typed, read-only configuration objects.

**Interview takeaway:** Prefer `const` for type safety and read-only objects. Use `#define` for preprocessing, conditional compilation and compile-time constants. In C, a `const int` is not generally an integer constant expression.

### What does const int *p, int *const p and const int *const p mean? {M}
The position of the `const` keyword determines whether the **data, pointer, or both** can be modified.

#### 1. `const int *p` — Pointer to constant data

The pointer can point to another variable, but the data cannot be modified through the pointer.

```c
int a = 10, b = 20;
const int *p = &a;

*p = 30;  // Error
p = &b;   // Allowed
```

<div style="max-width:680px;margin:16px 0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 112" width="100%" role="img" aria-label="Modifiable pointer to read-only data">
  <rect x="10" y="20" width="90" height="44" rx="5" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/>
  <text x="55" y="38" font-size="13" text-anchor="middle" fill="currentColor" font-weight="600">Pointer p</text>
  <text x="55" y="53" font-size="10" text-anchor="middle" fill="currentColor">Modifiable</text>
  <rect x="235" y="8" width="95" height="38" rx="5" fill="#ef4444" fill-opacity=".12" stroke="#ef4444"/>
  <text x="282" y="31" font-size="13" text-anchor="middle" fill="currentColor">a = 10</text>
  <rect x="235" y="65" width="95" height="38" rx="5" fill="#ef4444" fill-opacity=".12" stroke="#ef4444"/>
  <text x="282" y="88" font-size="13" text-anchor="middle" fill="currentColor">b = 20</text>
  <path d="M100 38 L235 27 m-6 -4 6 4-6 4" stroke="#16a34a" fill="none" stroke-width="1.5"/>
  <path d="M100 48 L235 84 m-5 -6 5 6-7 2" stroke="#16a34a" stroke-dasharray="4 3" fill="none" stroke-width="1.5"/>
  <text x="166" y="106" font-size="10" text-anchor="middle" fill="#16a34a">Can change address</text>
</svg>
</div>

**Note:** The original variable `a` can still be modified directly.

#### 2. `int *const p` — Constant pointer

The pointer cannot point to another variable, but the data can be modified through it.

```c
int a = 10, b = 20;
int *const p = &a;

*p = 30;  // Allowed
p = &b;   // Error
```

<div style="max-width:680px;margin:16px 0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 100" width="100%" role="img" aria-label="Constant pointer to modifiable data">
  <rect x="10" y="15" width="105" height="48" rx="5" fill="#ef4444" fill-opacity=".12" stroke="#ef4444"/>
  <text x="62" y="34" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">Pointer p</text>
  <text x="62" y="50" font-size="11" text-anchor="middle" fill="currentColor">Fixed address</text>
  <path d="M115 39 H225 m-6 -5 6 5-6 5" stroke="currentColor" fill="none" stroke-width="1.5"/>
  <rect x="225" y="15" width="105" height="48" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/>
  <text x="277" y="34" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">a = 30</text>
  <text x="277" y="50" font-size="11" text-anchor="middle" fill="currentColor">Modifiable data</text>
  <text x="170" y="85" font-size="11" text-anchor="middle" fill="currentColor">Address fixed, data can change</text>
</svg>
</div>

#### 3. `const int *const p` — Constant pointer to constant data

Neither the pointer nor the data can be modified through the pointer.

```c
int a = 10, b = 20;
const int *const p = &a;

*p = 30;  // Error
p = &b;   // Error
```

<div style="max-width:680px;margin:16px 0">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 100" width="100%" role="img" aria-label="Constant pointer to read-only data">
  <rect x="10" y="15" width="105" height="48" rx="5" fill="#ef4444" fill-opacity=".12" stroke="#ef4444"/>
  <text x="62" y="34" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">Pointer p</text>
  <text x="62" y="50" font-size="11" text-anchor="middle" fill="currentColor">Fixed address</text>
  <path d="M115 39 H225 m-6 -5 6 5-6 5" stroke="currentColor" fill="none" stroke-width="1.5"/>
  <rect x="225" y="15" width="105" height="48" rx="5" fill="#ef4444" fill-opacity=".12" stroke="#ef4444"/>
  <text x="277" y="34" font-size="13" font-weight="600" text-anchor="middle" fill="currentColor">a = 10</text>
  <text x="277" y="50" font-size="11" text-anchor="middle" fill="currentColor">Read-only via p</text>
  <text x="170" y="85" font-size="11" text-anchor="middle" fill="currentColor">Neither operation is allowed through p</text>
</svg>
</div>

#### 4. Comparison table

| Declaration | Change data (`*p`)? | Change address (`p`)? |
|---|---|---|
| `int *p` | Yes | Yes |
| `const int *p` | No | Yes |
| `int *const p` | Yes | No |
| `const int *const p` | No | No |

#### 5. Use in embedded systems

A pointer to a read-only hardware status register at a fixed address:

```c
const volatile uint32_t *const status =
    (const volatile uint32_t *)0x40000000U;
```

- First `const`: Software cannot modify the register through this pointer.
- `volatile`: Hardware may change the register value.
- Second `const`: The pointer cannot change its address.

**Interview takeaway:** If `const` appears before `*`, the pointed-to data is read-only through the pointer. If `const` appears after `*`, the pointer itself is constant. If it appears on both sides, both restrictions apply.

### What is the difference between a macro and an inline function? {M}
**Short answer:** A macro is text substitution by the preprocessor: no type checking, arguments may be evaluated several times, and it is hard to debug. A `static inline` function is a real function that the compiler may expand in place: arguments are type-checked and evaluated exactly once, and it can be stepped through in a debugger. Prefer `static inline`; use macros only for what functions cannot do.

| | Macro | `static inline` function |
|---|---|---|
| Processed by | preprocessor | compiler |
| Type checking | none | full |
| Argument evaluation | as many times as it appears | exactly once |
| Scope | ignores scope | normal C scope |
| Debugging | hard (expanded text) | normal (can set breakpoints when not inlined) |
| Generic over types | yes | no (except via `_Generic`) |
| Can use `#`, `##`, `__FILE__`, `__LINE__` of the caller | yes | no |
| Can return a value from a statement block | only with GCC statement expressions | yes |

**The classic macro bugs**

```c
#define SQUARE(x) ((x) * (x))
int y = SQUARE(i++);          /* i incremented twice: undefined behaviour */
int z = SQUARE(read_adc());   /* the ADC is read twice, maybe giving different values */

#define MAX(a, b) ((a) > (b) ? (a) : (b))
MAX(x++, y)                   /* x may be incremented twice */
```

```c
static inline int square(int x) { return x * x; }   /* no surprises */
```

**`inline` is only a hint.** The compiler decides whether to inline based on size and optimisation level; `__attribute__((always_inline))` forces it. A plain `inline` (without `static`) in C has awkward linkage rules (you need one external definition somewhere), which is why `static inline` in headers is the common idiom.

**When macros are the right tool:** compile-time constants used in `#if`, stringification (`#define STR(x) #x`) and token pasting, logging with the caller's `__FILE__`/`__LINE__`, `offsetof`/`container_of`-style tricks, and type-generic helpers (with `_Generic`, or C23 `typeof`).

**Code size:** inlining a large function at many call sites increases flash use; on small MCUs, check the map file and use `-Os`.

### Why should macro arguments and bodies be wrapped in parentheses? {E}
**Short answer:** Macros substitute text, so operator precedence around and inside the macro can change the meaning. Put parentheses around **every use of each argument** and around the **whole body** so the macro behaves like a single value.

```c
#define DOUBLE(x) x + x
int r = 3 * DOUBLE(2);        /* expands to 3 * 2 + 2 = 8, not 12 */

#define SQUARE(x) (x * x)
int s = SQUARE(1 + 2);        /* expands to (1 + 2 * 1 + 2) = 5, not 9 */
```

Correct versions:

```c
#define DOUBLE(x) ((x) + (x))
#define SQUARE(x) ((x) * (x))
```

**Both kinds of parentheses are needed**

- **Around arguments** `(x)`: protects against operators inside the argument (`1 + 2`).
- **Around the body** `( ... )`: protects against operators next to the macro where it is used (`3 * DOUBLE(2)`).

**Other macro hygiene rules**

- Multi-statement macros: wrap in `do { ... } while (0)` (next question).
- Arguments with side effects are still evaluated multiple times; parentheses do not fix that. Document it or use an inline function.
- Avoid names that clash: local variables inside macros should have unusual names (`t_`), because they can shadow the caller's variables.
- Do not end a macro definition with a semicolon (`#define X 5;`), or `if (a == X) ...` becomes a syntax error.

**Hardware register macros** need the same care: `#define REG_CTRL (*(volatile uint32_t *)(BASE + 0x04u))` has parentheses around the address arithmetic and the whole dereference, so `REG_CTRL |= 1u;` works as expected.

### Why are multi-line macros wrapped in do { } while(0)? {M}
**Short answer:** It turns several statements into one statement that needs a trailing semicolon, so the macro behaves correctly everywhere a single statement can appear, especially in an `if`/`else` without braces. The compiler removes the "loop" completely, so it costs nothing.

```c
#define SWAP(a, b) do { int t_ = (a); (a) = (b); (b) = t_; } while (0)

if (x > y)
    SWAP(x, y);      /* one statement: works */
else
    other();
```

**What goes wrong without it**

With only braces:

```c
#define SWAP(a, b) { int t_ = (a); (a) = (b); (b) = t_; }

if (x > y)
    SWAP(x, y);      /* expands to { ... };  <- the ';' ends the if statement */
else                 /* error: 'else' without a previous 'if' */
    other();
```

With no braces at all, only the first statement would be controlled by the `if`, and the rest would always run.

**Alternatives**

- A `static inline` function, which avoids the problem entirely and is type-checked; prefer it when possible.
- GCC/Clang **statement expressions** `({ ... })` can also return a value, but they are a compiler extension, not standard C.
- The comma operator `(a(), b())` works for simple expression-only macros.

**Typical embedded uses:** logging macros that capture `__FILE__` and `__LINE__`, `ASSERT()` macros that call a fault handler, and critical-section helpers:

```c
#define CRITICAL(code) do { uint32_t pm_ = __get_PRIMASK(); __disable_irq(); \
                            code; __set_PRIMASK(pm_); } while (0)
```

### What are # and ## in macros? {M}
**Short answer:** `#` (the stringizing operator) turns a macro argument into a string literal. `##` (the token-pasting operator) joins two tokens into one. They let macros generate names and strings automatically.

```c
#define STR(x)     #x
#define XSTR(x)    STR(x)          /* two-level trick: expand x first */
#define REG(port)  GPIO##port##_ODR

STR(UART1)                         /* "UART1" */
REG(A)                             /* GPIOA_ODR */

#define VERSION 3
STR(VERSION)                       /* "VERSION"  - argument not expanded */
XSTR(VERSION)                      /* "3"        - expanded first, then stringized */
```

**Why the two-level trick is needed:** an argument used with `#` or `##` is **not** macro-expanded first. Passing it through another macro (`XSTR`) expands it before it reaches `#`.

**Practical uses**

- **Assert and log messages** that show the failed expression: `#define ASSERT(e) do { if (!(e)) fail(#e, __FILE__, __LINE__); } while (0)`.
- **X-macros** that keep an enum and its string names in sync:

```c
#define STATES(X) X(IDLE) X(RUN) X(ERROR)
#define AS_ENUM(n)   ST_##n,
#define AS_STRING(n) #n,

enum state { STATES(AS_ENUM) ST_COUNT };
static const char *const state_name[] = { STATES(AS_STRING) };
/* ST_IDLE, ST_RUN, ST_ERROR and "IDLE", "RUN", "ERROR" from one list */
```

- **Generating register or handler names:** `#define IRQ_HANDLER(n) void n##_IRQHandler(void)`.
- Embedding the firmware version string: `const char fw_version[] = XSTR(MAJOR) "." XSTR(MINOR);`

**Rules:** the result of `##` must be a valid single token (pasting `+` and `/` is undefined), and `#` escapes quotes and backslashes in the argument.

### What is the difference between #include <file> and #include "file"? {E}
**Short answer:** `#include <file>` searches only the system include directories and those given with `-I`. `#include "file"` first looks in the directory of the file that contains the `#include`, then falls back to the same paths as `<file>`. Use quotes for your project's own headers and angle brackets for the standard library and third-party SDK headers.

**Search order with GCC**

| Form | Searched |
|---|---|
| `"file.h"` | directory of the current file → `-iquote` dirs → `-I` dirs → system dirs |
| `<file.h>` | `-I` dirs → `-isystem` dirs → system dirs (e.g. the toolchain's `include/`) |

See the exact list with `arm-none-eabi-gcc -xc -E -v /dev/null`.

**Why it matters**

- If your project has a header with the same name as a system one (e.g. `config.h`, `time.h`), quotes find yours first; angle brackets find the system one. Avoid such clashes.
- Headers included with `-isystem` get fewer warnings, which is useful for noisy vendor code but can hide real problems.

**Good include practice**

- Each header should be self-contained (include what it needs) and have include guards.
- Each `.c` file includes its own header first, which proves the header is self-contained.
- Do not put definitions (variables, non-inline functions) in headers.
- Prefer forward declarations (`struct uart;`) over including big headers when only a pointer is needed; it speeds up builds and reduces coupling.

**Embedded note:** vendor SDKs (CMSIS, STM32 HAL, nRF SDK) are usually added with `-I`, and you include them with angle brackets or quotes depending on the project's convention. Consistency matters more than the choice.

### What are include guards and #pragma once? {E}
**Short answer:** Include guards stop a header from being processed twice in the same translation unit (which would cause redefinition errors for types and inline functions). The classic form uses `#ifndef`/`#define`/`#endif`; `#pragma once` does the same in one line and is supported by all major compilers, but it is not part of the C standard.

```c
#ifndef DRIVERS_UART_H
#define DRIVERS_UART_H

#include <stdint.h>

typedef struct { uint32_t baud; uint8_t parity; } uart_cfg_t;
void uart_init(const uart_cfg_t *cfg);

#endif /* DRIVERS_UART_H */
```

```c
#pragma once
/* same effect */
```

**Why a header gets included twice:** `main.c` includes `uart.h` and `board.h`, and `board.h` also includes `uart.h`. Without guards, `uart_cfg_t` is defined twice and the compiler reports a redefinition.

**Comparison**

| | `#ifndef` guards | `#pragma once` |
|---|---|---|
| Standard C | yes | no (but GCC, Clang, IAR, Keil, MSVC all support it) |
| Risk | two headers accidentally using the same guard name, so one is silently skipped | the same file reached through two different paths (symlinks, copies on a network drive) may be included twice |
| Typing | three lines and a unique name | one line |

**Naming guards:** use the path, e.g. `PROJECT_DRIVERS_UART_H`. Do not start them with an underscore followed by a capital letter (`_UART_H`): such names are reserved for the compiler and library.

**MISRA C and some safety coding standards** require the standard `#ifndef` form. Otherwise either is fine; pick one and use it consistently.

**Guards do not help across translation units:** if a header *defines* a global variable (`int counter = 0;`), every `.c` file that includes it gets its own definition and the linker reports "multiple definition". Headers should only declare (`extern int counter;`).

### What is the difference between typedef and #define for creating type names? {E}
**Short answer:** `typedef` creates a real alias for a type that the compiler understands, with normal scope rules. `#define` only replaces text, which breaks with pointer types and can surprise you in declarations. Use `typedef` for types.

```c
typedef char *str_t;
#define STR_T char *

str_t a, b;     /* a and b are both char *            */
STR_T c, d;     /* becomes "char * c, d;": c is char *, d is just char! */
```

**Other differences**

| | `typedef` | `#define` |
|---|---|---|
| Processed by | compiler | preprocessor |
| Scope | block/file scope like any declaration | until `#undef` or end of file |
| Works with complex types (function pointers, arrays) | yes | fragile |
| Can be combined with `unsigned`, etc. | no (`unsigned my_int` is an error) | yes (text) |
| Debugger shows the name | usually | no |

**Readable function-pointer types (a very common use):**

```c
typedef void (*isr_t)(void);
isr_t vector_table[64];            /* array of 64 function pointers */

typedef int (*cmd_handler_t)(int argc, char **argv);
```

**Struct typedefs:**

```c
typedef struct uart uart_t;        /* opaque type: users cannot see inside */
uart_t *uart_open(int port);
```

Opaque types like this are good encapsulation in C: the struct is only defined in `uart.c`.

**Style notes:** names ending in `_t` are reserved by POSIX for its own types, so some projects avoid that suffix; and hiding a pointer inside a typedef (`typedef struct x *xptr;`) is discouraged by many style guides (including Linux), because it hides that the value is a pointer.

### What is undefined behaviour? Give examples. {M}
**Short answer:** Undefined behaviour (UB) means the C standard places **no requirements** on what happens. The program may crash, give a wrong result, or appear to work. Worse, the optimiser assumes UB never happens and transforms code on that basis, so a bug can be invisible at `-O0` and appear at `-O2`, or remove a safety check entirely.

**Common examples**

| Example | Why it is UB |
|---|---|
| `INT_MAX + 1` | signed integer overflow (unsigned wraps and is defined) |
| `*p` where `p` is NULL, freed, or out of scope | invalid pointer dereference |
| `int x; return x + 1;` | reading an uninitialised automatic variable |
| `a[10]` for `int a[10]` | out-of-bounds access |
| `1 << 32` on a 32-bit int, `x << -1` | shift by ≥ width or negative |
| `i = i++;` | unsequenced modifications |
| accessing a `float` through an `int *` | strict aliasing violation |
| modifying a string literal: `char *s = "hi"; s[0] = 'H';` | literals may be in read-only memory |
| returning without a value from a non-void function and using the result | missing return |
| `INT_MIN / -1`, `x / 0` | division overflow / by zero |

**How the optimiser exploits UB**

```c
int check(int x)
{
    if (x + 1 < x)          /* intended overflow check */
        return -1;          /* compiler: signed overflow can't happen, so this is never true */
    return x + 1;           /* the check is deleted */
}
```

Correct: `if (x == INT_MAX) return -1;`.

**Related categories (often asked together)**

- **Unspecified behaviour:** one of several valid outcomes, not documented: order of evaluation of function arguments (`f(a(), b())`).
- **Implementation-defined behaviour:** the compiler must choose and document: `sizeof(int)`, right shift of negative numbers, whether `char` is signed.

**Finding UB:** `-Wall -Wextra`, `-fsanitize=undefined,address` on a host build of your code, static analysers (cppcheck, clang-tidy, PC-lint, Polyspace), and MISRA C rules, many of which exist precisely to avoid UB.

### What is a sequence point? {H}
**Short answer:** A sequence point is a point in the execution where all side effects of earlier evaluations are complete and none of the later ones have started. If an object is modified twice, or modified and also read for another purpose, without a sequence point (in C11 terms, without being "sequenced before") between them, the behaviour is undefined.

**Where sequence points are (C99 terms)**

- At the end of a full expression (the `;`, the condition of `if`/`while`/`for`, a `return` expression).
- After the first operand of `&&`, `||`, `?:` and the comma operator.
- After evaluating a function's arguments, just before the call.

**Undefined examples**

```c
i = i++ + 1;        /* i modified twice */
a[i] = i++;         /* i read (for the index) and modified, unsequenced */
f(i++, i++);        /* the two arguments are unsequenced relative to each other */
x = y++ * y++;      /* y modified twice */
```

**Well-defined examples**

```c
i++, j = i;               /* comma operator: i++ completes first */
if (p != NULL && p->ok)   /* && sequences and short-circuits */
x = (i++ > 0) ? i : 0;    /* ?: sequences after the condition */
```

**C11 terminology:** "sequenced before", "unsequenced" and "indeterminately sequenced" replaced "sequence point". The practical rule is unchanged: **do not modify a variable more than once in one expression, and do not read it elsewhere in an expression that modifies it.**

**Note on function arguments:** the order in which `f(a(), b())` calls `a` and `b` is **unspecified** (either order is allowed, but it is not UB as long as they do not touch the same object without sequencing). Code that depends on that order is still a bug.

**Embedded twist:** reading a `volatile` hardware register twice in one expression (`STATUS + STATUS`) gives unspecified order of the two reads; with registers that clear on read, that matters. Read into a local first.

### What is the size of an int, and what are fixed-width types? {E}
**Short answer:** The C standard only fixes minimum ranges: `char` at least 8 bits, `short` and `int` at least 16, `long` at least 32, `long long` at least 64. The actual sizes depend on the compiler and target: `int` is 16 bits on 8-bit AVR and MSP430, and 32 bits on ARM Cortex-M, ARM64 and x86. For hardware registers and data formats use the fixed-width types from `<stdint.h>`.

**Typical data models**

| Type | AVR (8-bit) | Cortex-M (ILP32) | ARM64 / x86-64 Linux (LP64) | 64-bit Windows (LLP64) |
|---|---|---|---|---|
| `char` | 8 | 8 | 8 | 8 |
| `short` | 16 | 16 | 16 | 16 |
| `int` | 16 | 32 | 32 | 32 |
| `long` | 32 | 32 | 64 | 32 |
| pointer | 16 | 32 | 64 | 64 |

**`<stdint.h>` types**

- **Exact width:** `int8_t`, `uint16_t`, `uint32_t`, `int64_t` — for registers, protocol fields, file formats.
- **Least:** `uint_least16_t` — at least 16 bits (portable even to unusual DSPs without 8-bit types).
- **Fast:** `uint_fast16_t` — the fastest type with at least 16 bits (often 32 bits on Arm, avoiding extra masking instructions).
- `intptr_t`/`uintptr_t` — an integer that can hold a pointer.
- `size_t` (sizes and indexes, unsigned), `ptrdiff_t` (pointer differences, signed).

**printf formats:** use `<inttypes.h>` macros, e.g. `printf("%" PRIu32 "\n", x);`, because `uint32_t` is `unsigned long` on some toolchains and `unsigned int` on others.

**Common bugs from assuming sizes**

- Storing a pointer in an `int` (breaks on 64-bit).
- `long` timestamps that overflow on ILP32 but not on the PC where tests run.
- A loop `for (uint8_t i = 0; i < 300; i++)` never ends: `i` wraps at 255.

**Check sizes at compile time:** `_Static_assert(sizeof(struct header) == 16, "header must be 16 bytes");`.

### Is char signed or unsigned, and why does it matter? {M}
**Short answer:** It is implementation-defined. Plain `char` is a distinct type from both `signed char` and `unsigned char`, and it behaves like one of them depending on the platform: **signed on x86** (and on Arm for Windows/macOS), **unsigned on most Arm Linux and Arm bare-metal toolchains** (AAPCS), PowerPC and RISC-V. Code that stores byte values above 127 in a plain `char` can behave differently on different targets.

```c
char c = 0xE9;            /* 233 if unsigned, -23 if signed */
if (c > 127) { ... }      /* never true where char is signed */

int table[256];
table[c]++;               /* table[-23] where char is signed: out of bounds! */

while ((c = getchar()) != EOF) { ... }   /* bug: getchar returns int; with unsigned char
                                            the loop never ends, with signed char a 0xFF byte
                                            looks like EOF */
```

**Rules to follow**

- Use `char` only for text.
- Use `uint8_t` (or `unsigned char`) for raw bytes, buffers, and protocol data.
- Cast to `unsigned char` before passing a `char` to `<ctype.h>` functions (`isdigit((unsigned char)c)`) and before using it as an array index.
- Store the result of `getchar()`/`fgetc()` in an `int`.
- GCC options `-funsigned-char` / `-fsigned-char` force one behaviour; `-Wchar-subscripts` warns on indexing with `char`.

**Related trivia:** `sizeof(char)` is 1 by definition (a "byte" in C is a `char`, which is `CHAR_BIT` bits, almost always 8). In C, a character constant like `'a'` has type `int`, so `sizeof('a')` is 4 on a 32-bit target, while in C++ it is `char` and `sizeof('a')` is 1.

### What is integer promotion? {M}
**Short answer:** Before most arithmetic, any integer type smaller than `int` (`char`, `short`, `uint8_t`, `uint16_t`, bit-fields) is converted to `int` (or to `unsigned int` if `int` cannot hold all its values). The operation is done in `int`, and the result is only narrowed again if you store it into a smaller type. This leads to surprising results with `~`, shifts and comparisons.

```c
uint8_t a = 0xFF;
if (~a == 0x00) { }          /* never true: ~a is int ~255 = 0xFFFFFF00 (-256) */
if ((uint8_t)~a == 0x00) { } /* true */

uint8_t x = 200, y = 100;
uint8_t z = x + y;           /* computed as int 300, stored as 300 % 256 = 44 */
int     w = x + y;           /* 300: no overflow, because the math was done in int */

uint16_t u = 0xFFFF;
uint32_t r = u * u;          /* u promoted to *signed* int on 32-bit targets:
                                65535 * 65535 overflows int -> undefined behaviour! */
uint32_t ok = (uint32_t)u * u;
```

**Usual arithmetic conversions** (what happens after promotion when the two operands differ): the operand with the "lower" type is converted to the other's type; if one is unsigned and has the same or greater rank, the signed one becomes unsigned.

**Where it bites in embedded code**

- **Inverting a byte mask:** `reg8 &= ~MASK8;` is fine (the result is truncated back), but comparisons with `~byte` are not.
- **Shifts:** `uint8_t b = 0x80; uint32_t v = b << 24;` promotes `b` to signed `int`, and `0x80 << 24` overflows into the sign bit: undefined behaviour. Write `(uint32_t)b << 24`.
- **Checksums** accumulated in a `uint8_t` behave correctly only because the result is truncated on every assignment.
- On 16-bit MCUs (`int` = 16 bits), `uint16_t` promotes to `unsigned int`, so the same code behaves differently than on a 32-bit Arm.

**MISRA C** has the "essential type" rules exactly to catch these issues; compiler warnings such as `-Wconversion` and `-Wsign-conversion` help too.

### What happens when you compare signed and unsigned integers? {M}
**Short answer:** If the two operands have the same rank (e.g. `int` and `unsigned int`), the usual arithmetic conversions convert the **signed** one to **unsigned**. A negative number becomes a very large positive one, so comparisons give the "wrong" answer.

```c
int i = -1;
unsigned int u = 1;
if (i < u) puts("less");       /* not printed: -1 becomes 0xFFFFFFFF */

if (-1 < sizeof(int)) puts("yes");   /* not printed: sizeof is size_t (unsigned) */

for (unsigned i = 10; i >= 0; i--) { }   /* infinite loop: unsigned is always >= 0 */

size_t len = strlen(s);
if (len - 1 >= 0) { }          /* always true; if len is 0, len - 1 wraps to SIZE_MAX */
```

**When it does not happen:** if the signed type is wider and can represent all values of the unsigned one, the unsigned operand is converted to the signed type instead. `long long x = -1; unsigned int u = 1; x < u` is true, because `u` becomes `long long`. Small types (`uint8_t`, `uint16_t`) are promoted to `int` first, so `int8_t a = -1; uint8_t b = 1; a < b` is true.

**How to avoid it**

- Compile with `-Wall -Wextra` (which includes `-Wsign-compare`) and fix every warning.
- Use one signedness consistently for sizes and indexes (`size_t`), and check for negative values before converting signed to unsigned.
- Compare explicitly: `if (i < 0 || (unsigned)i < u)`.
- For "count down to zero" with unsigned indices, use `for (size_t i = n; i-- > 0; )`.

**C23** adds checked-arithmetic helpers (`ckd_add`, `ckd_sub`, `ckd_mul` in `<stdckdint.h>`), and GCC/Clang have `__builtin_add_overflow` for overflow-safe arithmetic.

### What is the difference between ++i and i++? {E}
**Short answer:** `++i` (pre-increment) increments `i` and gives the **new** value. `i++` (post-increment) gives the **old** value, and `i` is incremented as a side effect. Used alone as a statement, for example in a `for` loop, they generate identical code for integers; the difference only matters when the result is used.

```c
int i = 5;
int a = ++i;    /* i = 6, a = 6 */
int b = i++;    /* b = 6, i = 7 */

while (n--)  { }    /* tests the old value: runs n times */
while (--n)  { }    /* tests the new value: runs n - 1 times */
```

**Common uses of post-increment**

```c
buf[len++] = byte;              /* store at len, then advance */
*dst++ = *src++;                /* copy one element, advance both pointers */
```

`*p++` means `*(p++)`: increment the **pointer**, return the old pointed value. `(*p)++` increments the **value**.

**Performance:** for built-in types any modern compiler produces the same code. In C++, for class types such as iterators, `i++` has to make a copy of the old value, so `++i` is preferred out of habit.

**Undefined behaviour reminder:** do not use the same variable twice in an expression that increments it: `a[i] = i++;` and `i = i++;` are undefined.

**Interview puzzle:** what does this print?

```c
int x = 5;
printf("%d %d\n", x++, x);   /* undefined: x is read and modified unsequenced */
```

The correct answer is "it is undefined"; any specific output is a guess about a particular compiler.

### What is the difference between a structure and a union? {E}
**Short answer:** In a `struct`, every member has its own storage, so all members hold values at the same time and the size is at least the sum of the members (plus padding). In a `union`, all members **share the same storage**; the size is that of the largest member (plus padding), and only the member last written holds a meaningful value.

```c
struct s { uint8_t a; uint32_t b; };   /* 8 bytes on 32-bit Arm: a, 3 padding, b */
union  u { uint8_t a; uint32_t b; };   /* 4 bytes: a and b overlap */
```

**Uses of unions**

1. **Variant types (tagged unions):** one value that can be one of several types, with an enum saying which.

```c
typedef enum { MSG_TEMP, MSG_ACCEL } msg_type_t;
typedef struct {
    msg_type_t type;
    union {
        int16_t temp_c10;                 /* used when type == MSG_TEMP */
        struct { int16_t x, y, z; } acc;  /* used when type == MSG_ACCEL */
    } u;
} msg_t;                                  /* size of the largest variant, not the sum */
```

2. **Saving RAM** when different data is never needed at the same time.

3. **Viewing the same bytes differently** (type punning):

```c
typedef union {
    uint32_t word;
    uint8_t  byte[4];
    float    f;
} reg32_t;
```

**Type punning rules:** in C (C99 TC3 onward) reading a different member than the one written is allowed and reinterprets the bytes. In C++ it is undefined behaviour (use `memcpy` or `std::bit_cast`). The **byte order** you see in `byte[]` depends on endianness, and the result is not portable between little- and big-endian systems.

**Do not use unions or structs to map network or file formats directly** unless you control padding, packing and endianness; serialise field by field instead.

### What is structure padding and how do you avoid it? {M}
**Short answer:** The compiler inserts unused **padding bytes** between members (and at the end) so that each member starts at an address that is a multiple of its alignment, and so that arrays of the struct keep every element aligned. To reduce padding, order members from largest alignment to smallest. To remove it entirely, use `__attribute__((packed))` or `#pragma pack(1)`, but packed members may be accessed unaligned, which is slower and can fault on some cores.

```c
struct a { char c; int i; char d; };   /* 12 bytes on 32-bit Arm */
/* offset: c 0, padding 1-3, i 4-7, d 8, padding 9-11 */

struct b { int i; char c; char d; };   /* 8 bytes */
/* offset: i 0-3, c 4, d 5, padding 6-7 */
```

**Why the trailing padding in `struct b`?** The struct's alignment is 4 (its largest member). In an array `struct b arr[2]`, `arr[1].i` must be 4-byte aligned, so the size is rounded up to a multiple of 4.

**Checking layout**

```c
#include <stddef.h>
_Static_assert(offsetof(struct b, c) == 4, "layout changed");
_Static_assert(sizeof(struct b) == 8, "size changed");
```

`pahole` (from dwarves) prints the layout and holes of every struct in an ELF file with debug info.

**Packed structs and their costs**

```c
struct __attribute__((packed)) hdr { uint8_t type; uint32_t len; };   /* 5 bytes */
```

- Accessing `len` needs an unaligned access. Cortex-M3/M4/M7 handle unaligned 32-bit loads in hardware (slower); **Cortex-M0/M0+** and older Arm cores fault, so the compiler must generate byte-by-byte accesses (correct but slower and larger).
- Taking the address of a packed member (`uint32_t *p = &h.len;`) and using it as a normal pointer can produce unaligned accesses the compiler does not know about (GCC warns with `-Waddress-of-packed-member`).
- Packed structs are fine for matching a wire format when you also handle endianness; many projects still prefer explicit serialisation with shifts and `memcpy`.

**Memory saving on MCUs:** reordering members in large arrays of structs can save a significant amount of RAM with no runtime cost.

### What are bit-fields and what are their drawbacks? {M}
**Short answer:** Bit-fields let you declare struct members that are a given number of bits wide, so several flags or small values share one word and can be accessed by name. Their drawbacks are that bit order, padding, whether a field can cross a storage unit, and the signedness of plain `int` fields are all implementation-defined, and writing one field is a non-atomic read-modify-write of the whole storage unit.

```c
struct status {
    unsigned ready : 1;
    unsigned error : 1;
    unsigned mode  : 3;     /* values 0..7 */
    unsigned       : 3;     /* unnamed padding bits */
};

struct status s = {0};
s.mode = 5;
s.ready = 1;
```

**Advantages:** compact storage (e.g. thousands of flags in a table), readable code, the compiler generates the masks and shifts.

**Drawbacks in detail**

- **Layout is not portable:** one compiler puts the first field at the least significant bit, another (or the same compiler on a big-endian target) at the most significant. This makes bit-fields unsuitable for matching hardware registers or network formats across compilers.
- **Access width:** the compiler may use a byte or halfword access to update a field. Some peripheral registers only accept 32-bit accesses. (GCC's `-fstrict-volatile-bitfields`, the default for Arm EABI, uses the declared type's width for volatile bit-fields, which helps but is still compiler-specific.)
- **Not atomic:** `s.ready = 1` reads the word, modifies one bit and writes it back. If an ISR modifies `s.error` in between, the update is lost.
- **No address:** `&s.mode` is not allowed, and there are no arrays of bit-fields.
- **Signedness:** `int x : 3;` may be signed or unsigned depending on the compiler. Always use `unsigned` (or `_Bool`) explicitly.

**What most embedded teams do:** use explicit masks and shifts (`#define CTRL_MODE_Pos 2`, `#define CTRL_MODE_Msk (7u << CTRL_MODE_Pos)`) for hardware registers and wire formats, and use bit-fields only for internal data whose layout does not matter.

**Note:** some vendor headers (e.g. TI C2000, older Microchip) do define registers as bit-field unions; that works because the vendor controls the compiler. Do not copy the pattern to portable code.

### What is an enum and how big is it? {E}
**Short answer:** An `enum` defines a set of named integer constants. In C the constants have type `int`, but the size of the enum **type** is implementation-defined: it must be able to hold all its values, and most compilers use `int` (4 bytes). Options such as `-fshort-enums` (the default in some Arm bare-metal ABIs and toolchains) make it the smallest type that fits, often 1 byte.

```c
enum state { IDLE, RUN, ERROR = 10, SHUTDOWN };   /* 0, 1, 10, 11 */
enum state s = RUN;
```

**Why use enums instead of `#define`**

- They are typed integer constant expressions (usable as array sizes and `case` labels).
- Debuggers show names instead of numbers.
- Compilers warn about unhandled cases in a `switch` without a `default` (`-Wswitch`).
- Values are assigned automatically and stay consistent when items are added.

**Pitfalls**

- **Size differs between builds:** a struct containing an `enum` can have a different layout if one library was built with `-fshort-enums` and another without; the linker cannot detect this. For structs that cross a module, ABI, file or network boundary, store a fixed-width integer (`uint8_t state;`) and convert.
- **C does not enforce enum ranges:** `enum state s = 42;` compiles. Validate values that come from outside (a received message).
- Enum constants are `int`; values larger than `INT_MAX` were not allowed before C23.

**C23 improvements:** you can fix the underlying type: `enum state : uint8_t { IDLE, RUN };`, which makes the size explicit and portable.

**Useful patterns:** a final `STATE_COUNT` member to size lookup tables (`const char *names[STATE_COUNT]`), and X-macros to generate the enum and its string names from one list.

### What is the difference between malloc, calloc, realloc and free? {E}
**Short answer:** `malloc(n)` allocates `n` bytes with **uninitialised** contents. `calloc(count, size)` allocates `count * size` bytes, **zeroed**, and checks the multiplication for overflow. `realloc(p, n)` resizes a block, possibly moving it to a new address. `free(p)` releases a block; `free(NULL)` does nothing.

```c
int *a = malloc(10 * sizeof *a);          /* garbage values */
int *b = calloc(10, sizeof *b);           /* all zero */
if (a == NULL || b == NULL) { /* handle failure */ }

int *tmp = realloc(a, 20 * sizeof *a);    /* keep the old pointer until success */
if (tmp == NULL) { free(a); /* error */ }
else a = tmp;

free(a);
free(b);
a = b = NULL;                              /* avoid dangling pointers */
```

**Details worth mentioning**

- `realloc` may move the block: any other pointers into the old block are now invalid.
- `p = realloc(p, n);` is a classic leak: if `realloc` fails, it returns `NULL` and the original block is lost.
- `realloc(NULL, n)` behaves like `malloc(n)`. `realloc(p, 0)` is implementation-defined (and deprecated in C23), so do not rely on it to free.
- `malloc(0)` may return NULL or a unique pointer; do not dereference it.
- Write `sizeof *p` rather than `sizeof(int)` so the size stays correct if the type changes.
- Every allocation must be freed exactly once: double free and use-after-free are undefined behaviour and common security bugs.

**Why many embedded projects avoid the heap**

- **Fragmentation:** after many allocations and frees of different sizes, free memory is split into pieces too small to use, and an allocation fails even though plenty of memory is free in total. On a device that must run for years, this is a real failure mode.
- **Non-deterministic timing:** allocation time depends on the heap state, which is a problem for real-time code.
- **Failure handling:** what does an airbag controller do if `malloc` returns NULL?

MISRA C and many safety standards ban dynamic allocation after initialisation. Alternatives: static allocation, fixed-size **memory pools** (allocate and free in O(1), no fragmentation), and allocating everything once at start-up.

### What is the difference between strcpy, strncpy and memcpy? {M}
**Short answer:** `strcpy(d, s)` copies a string including its `'\0'` with **no bounds check**. `strncpy(d, s, n)` copies at most `n` characters and pads the rest with zeros, but does **not** add a terminator if the source is `n` characters or longer. `memcpy(d, s, n)` copies exactly `n` bytes regardless of content, and is undefined if the buffers overlap (use `memmove` then).

```c
char dst[8];

strcpy(dst, "this is too long");     /* buffer overflow: writes past dst */

strncpy(dst, "abcdefgh", sizeof dst); /* copies 8 chars, NO '\0': dst is not a string */
dst[sizeof dst - 1] = '\0';           /* you must terminate it yourself */

memcpy(dst, src, 8);                  /* exactly 8 bytes; overlapping src/dst is UB */
memmove(buf + 1, buf, 7);             /* overlapping: use memmove */
```

| | Stops at `'\0'` | Bounds | Terminates | Pads | Overlap |
|---|---|---|---|---|---|
| `strcpy` | yes | none | yes | no | UB |
| `strncpy` | yes (then pads) | n | only if `strlen(s) < n` | with zeros up to n | UB |
| `memcpy` | no | n | not applicable | no | UB |
| `memmove` | no | n | not applicable | no | safe |

**Why `strncpy` exists:** it was designed for fixed-width, zero-padded fields (old Unix directory entries), not as a "safe strcpy". Padding a 4 KB buffer when copying a short string is also wasted time.

**Safer patterns**

```c
snprintf(dst, sizeof dst, "%s", src);        /* always terminates, truncates safely */

size_t n = strlen(src);                      /* or a bounded strnlen */
if (n >= sizeof dst) n = sizeof dst - 1;
memcpy(dst, src, n);
dst[n] = '\0';
```

`strlcpy` (BSD, glibc 2.38+, and many embedded libraries) copies, always terminates, and returns the source length so you can detect truncation. C11 Annex K `strcpy_s` exists but is rarely implemented.

**Embedded note:** these functions are a frequent source of overflows when parsing input from a UART or network. Always know the size of the destination, and prefer length-carrying buffers (`ptr + len`) over relying on `'\0'` in binary protocols.

### What is the difference between an array and a pointer? {M}
**Short answer:** An array is a block of contiguous objects; a pointer is a variable that holds an address. In most expressions an array name **decays** into a pointer to its first element, which is why they often look interchangeable. They differ in `sizeof`, in `&`, in assignment, and in how they are stored.

```c
int arr[10];
int *ptr = arr;          /* arr decays to &arr[0] */

sizeof arr               /* 40: the whole array */
sizeof ptr               /* 4 on 32-bit, 8 on 64-bit: just the pointer */

&arr                     /* type int (*)[10]: pointer to the whole array */
&ptr                     /* type int **: address of the pointer variable */

arr = ptr;               /* error: an array is not assignable */
ptr = arr + 1;           /* fine */

arr[3] == *(arr + 3) == *(ptr + 3) == ptr[3] == 3[arr]   /* all the same element */
```

**Where an array does not decay:** as the operand of `sizeof`, of `&`, and as a string literal used to initialise a `char` array.

**Function parameters:** `void f(int a[10])` is exactly the same as `void f(int *a)`. The `10` is ignored, and `sizeof a` inside `f` gives the pointer size, a classic bug:

```c
void clear(int a[10]) { memset(a, 0, sizeof a); }   /* clears only 4 or 8 bytes! */
void clear(int *a, size_t n) { memset(a, 0, n * sizeof *a); }   /* correct */
```

**Storage difference:**

```c
char s1[] = "hello";     /* an array of 6 chars, writable copy */
char *s2  = "hello";     /* a pointer to a string literal, which must not be modified */
```

**Multi-dimensional arrays:** `int m[3][4]` decays to `int (*)[4]` (pointer to a row), not to `int **`. Passing it to a function expecting `int **` is wrong; declare `void f(int m[][4])` or `void f(int (*m)[4])`.

**Count elements safely:** `#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))` works only on real arrays, not on pointers; GCC/Clang can be made to reject pointers with a `__builtin_types_compatible_p` check (as the Linux kernel's version does).

### What is a function pointer and where is it used? {M}
**Short answer:** A function pointer holds the address of a function so the function can be called indirectly, chosen at run time. Embedded code uses them for interrupt vector tables, driver callbacks, state machines, command tables and "operations" structures that give C a form of polymorphism.

```c
#include <stdint.h>
#include <stddef.h>

typedef void (*event_cb_t)(uint8_t event, void *ctx);

static event_cb_t user_cb;
static void *user_ctx;

void button_register(event_cb_t cb, void *ctx) { user_cb = cb; user_ctx = ctx; }

void button_isr(void)
{
    if (user_cb != NULL)          /* always check before calling */
        user_cb(1, user_ctx);
}
```

**Common embedded uses**

- **Vector table:** an array of function pointers placed at the start of flash; the CPU reads the handler address from it on each interrupt.

```c
__attribute__((section(".isr_vector")))
void (*const vector_table[])(void) = { (void (*)(void))&_estack, Reset_Handler, NMI_Handler, /* ... */ };
```

- **Callbacks:** a driver calls application code when data arrives, without depending on the application.
- **State machines:** a table indexed by state (and event) that gives the handler to run.
- **Driver operations structures:** `struct sensor_ops { int (*init)(void); int (*read)(int16_t *v); };`, which lets the same code drive different sensors (like Linux's `struct file_operations`).
- **Command parsers:** a table of `{ "name", handler }` pairs.

**Syntax help**

```c
int (*fp)(int, int);          /* pointer to function taking two ints, returning int */
int *fp2(int, int);           /* a function returning int* — not a pointer! */
int (*ops[4])(int, int);      /* array of 4 function pointers */
```

Use a `typedef` to keep declarations readable.

**Safety and performance notes**

- Calling a NULL or corrupted function pointer jumps to a random address; on a Cortex-M this typically ends in a HardFault (or executes the vector table as code if the pointer is 0). Check for NULL and consider placing tables in flash (`const`) so they cannot be corrupted at run time.
- Indirect calls prevent inlining and can be slightly slower.
- The `void *ctx` parameter lets one callback serve several instances (C's version of a "this" pointer).

### What is the difference between call by value and call by reference? {E}
**Short answer:** C always passes arguments **by value**: the function receives a copy, so changing the parameter does not change the caller's variable. To let a function modify the caller's data, you pass a **pointer** to it, which is what people call "call by reference" in C. (C++ has true references; C does not.)

```c
void inc_value(int x)    { x++; }           /* changes only the local copy */
void inc_ref(int *x)     { (*x)++; }         /* changes the caller's variable */

int n = 5;
inc_value(n);   /* n is still 5 */
inc_ref(&n);    /* n is now 6 */
```

**Passing a pointer is still pass-by-value**: the pointer itself is copied. So a function cannot change *which* object the caller's pointer points to, unless you pass a pointer to the pointer:

```c
void alloc_buf(uint8_t **out, size_t n) { *out = malloc(n); }
uint8_t *buf;
alloc_buf(&buf, 64);
```

**Arrays** are passed as a pointer to their first element, so the function can modify the caller's array.

**Structs** are copied when passed by value. A 100-byte config struct passed by value costs 100 bytes of stack and a copy on every call. Embedded code usually passes `const struct cfg *` for read-only access (no copy, and the `const` documents and enforces that the function will not modify it):

```c
void uart_init(const uart_cfg_t *cfg);
```

**Returning values:** returning small structs by value is fine and often efficient (the AAPCS returns structs up to 4 bytes in `r0`, larger ones through memory provided by the caller). For several results, return a status and write results through pointer parameters, or return a small struct.

### What is recursion and why is it avoided in embedded code? {E}
**Short answer:** Recursion is a function calling itself (directly or through other functions). Each call uses a new stack frame. It is avoided in embedded systems because the maximum stack depth depends on the input and cannot easily be bounded at compile time, stacks are small (often 512 bytes to a few KB per task), and a stack overflow on a microcontroller without an MPU silently corrupts other memory. MISRA C forbids recursion.

```c
/* recursive: stack use grows with n */
unsigned fact_rec(unsigned n) { return n <= 1 ? 1 : n * fact_rec(n - 1); }

/* iterative: constant stack use */
unsigned fact_iter(unsigned n)
{
    unsigned r = 1;
    while (n > 1) r *= n--;
    return r;
}
```

**Problems in detail**

- **Unbounded stack:** a recursive tree walk on a degenerate (linked-list shaped) tree goes as deep as the number of nodes.
- **Static analysis:** tools that compute worst-case stack usage (`-fstack-usage` + call-graph analysis, StackAnalyzer) cannot give a bound for recursive call cycles.
- **Silent corruption:** on a Cortex-M without stack limit checking, the stack grows into `.bss` or another task's stack. The failure appears somewhere else, much later.
- **Timing:** deep recursion takes variable time, bad for real-time code.

**How to replace recursion**

- Tail-recursive functions become simple loops.
- Tree and graph traversals use an explicit stack (a fixed-size array) with a checked maximum depth.
- Divide-and-conquer sorting: use heapsort or an iterative merge sort, or quicksort that recurses only on the smaller part (bounding depth to log₂ n) and loops on the larger.

**If you must use recursion:** prove a maximum depth (e.g. a parser limited to 8 nesting levels), check it at run time, and size the stack for it. Cortex-M33 (Armv8-M) has stack limit registers (`MSPLIM`/`PSPLIM`) that fault on overflow instead of corrupting memory.

### What are the stages of compilation in C? {E}
**Short answer:** There are four stages. **Preprocessing** expands `#include`, macros and conditional compilation. **Compilation** translates the preprocessed C into assembly. **Assembly** turns that into a relocatable object file (`.o`). **Linking** combines object files and libraries, resolves symbols, and places code and data at addresses defined by the linker script, producing an executable (ELF).

```bash
arm-none-eabi-gcc -E main.c -o main.i      # 1. preprocess
arm-none-eabi-gcc -S main.i -o main.s      # 2. compile to assembly
arm-none-eabi-gcc -c main.s -o main.o      # 3. assemble to object file
arm-none-eabi-gcc main.o uart.o -T stm32.ld -o firmware.elf   # 4. link
arm-none-eabi-objcopy -O binary firmware.elf firmware.bin     # for flashing
arm-none-eabi-objcopy -O ihex   firmware.elf firmware.hex
```

**What each stage produces and checks**

| Stage | Output | Errors you see |
|---|---|---|
| Preprocessor | `.i` (pure C, no `#` lines except line markers) | missing header, bad macro |
| Compiler | `.s` assembly | syntax and type errors, warnings |
| Assembler | `.o` with sections (`.text`, `.data`, `.bss`, `.rodata`), a symbol table and relocations | rare (invalid inline assembly) |
| Linker | `.elf` (plus a `.map` file with `-Wl,-Map=...`) | undefined reference, multiple definition, region `FLASH` overflowed |

**Useful inspection tools:** `nm` (symbols), `objdump -d` (disassembly), `readelf -S` (sections), `size` (text/data/bss sizes), and the **map file**, which shows where every function and variable ended up and how much flash and RAM is used.

**Embedded specifics**

- The **linker script** (`.ld`) defines the memory regions (FLASH, RAM) and where each section goes.
- The **start-up code** (often `startup_xxx.s`) is linked in and runs before `main`.
- `-ffunction-sections -fdata-sections` plus `-Wl,--gc-sections` let the linker remove unused functions, which saves a lot of flash.
- **LTO** (`-flto`) does optimisation across files at link time.

### What is the difference between a .bss and a .data section? {E}
**Short answer:** `.data` holds global and static variables with **non-zero initial values**; the values are stored in flash and copied into RAM by the start-up code. `.bss` holds global and static variables that are **zero or uninitialised**; only its size is stored, and the start-up code fills that RAM with zeros. `.rodata` holds constants (in flash), and `.text` holds code.

```c
int counter;                  /* .bss  (zero)                         */
int baud = 115200;            /* .data (initial value in flash, copy in RAM) */
static uint8_t buf[512];      /* .bss                                 */
const uint8_t lut[256] = {1}; /* .rodata (flash only)                 */
void f(void) { }              /* .text                                */
int x = 0;                    /* .bss: explicitly zero still goes in .bss with GCC */
```

**Memory cost of each section on an MCU**

| Section | Flash | RAM |
|---|---|---|
| `.text` | yes | no |
| `.rodata` | yes | no |
| `.data` | yes (initial values) | yes (the variables) |
| `.bss` | no | yes |
| stack, heap | no | yes |

**Start-up code (simplified):**

```c
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;   /* from the linker script */

void Reset_Handler(void)
{
    uint32_t *src = &_sidata, *dst = &_sdata;
    while (dst < &_edata) *dst++ = *src++;      /* copy .data from flash to RAM */
    for (dst = &_sbss; dst < &_ebss; ) *dst++ = 0;  /* zero .bss */
    SystemInit();
    main();
    for (;;) { }
}
```

**Practical consequences**

- Making a large table `const` moves it from `.data` (flash **and** RAM) to `.rodata` (flash only). On a 20 KB RAM part this can be the difference between fitting and not fitting.
- A big `.bss` makes boot slightly slower (zeroing) but costs no flash.
- Variables that must survive a reset (e.g. a crash counter or a bootloader flag) go in a separate `.noinit` section that the start-up code does not touch.

**Check sizes:** `arm-none-eabi-size firmware.elf` prints `text data bss`. Flash used = text + data; RAM used = data + bss (plus stack and heap).

### What is a dangling pointer, a wild pointer and a NULL pointer? {E}
**Short answer:** A **NULL pointer** deliberately points to nothing; dereferencing it is undefined behaviour. A **wild pointer** is an uninitialised pointer containing a random address. A **dangling pointer** still holds the address of an object that no longer exists: memory that was freed, or a local variable whose function has returned.

```c
int *wild;                  /* wild: indeterminate value */
*wild = 5;                  /* writes to a random address */

int *dang = malloc(sizeof *dang);
free(dang);
*dang = 5;                  /* dangling: use after free */

int *get_local(void)
{
    int x = 42;
    return &x;              /* dangling: x is gone when the function returns */
}

int *np = NULL;
*np = 1;                    /* NULL dereference: undefined behaviour */
```

**Why they are dangerous in embedded systems**

- On a Cortex-M, address 0 is usually the start of flash (or the vector table). A NULL **read** returns the initial stack pointer value instead of faulting, and a NULL **write** may be silently ignored or cause a bus fault depending on the memory map. Bugs survive testing.
- A dangling pointer to a stack frame may "work" until an interrupt or another call overwrites that stack area.

**Prevention**

- Initialise every pointer, to a valid object or `NULL`.
- Set pointers to `NULL` after `free()` (and avoid keeping several copies of an owning pointer).
- Never return the address of a non-static local.
- Check pointers from callers and from allocation (`if (p == NULL)`).
- Use the **MPU** to make the first few hundred bytes at address 0 inaccessible so NULL dereferences fault immediately.
- Run code on the host with **AddressSanitizer** (`-fsanitize=address`) and use static analysis to catch use-after-free and uninitialised use.

**Interview follow-up:** "Is `free(NULL)` safe?" Yes, it does nothing. "Is double `free` safe?" No, it is undefined behaviour and can corrupt the heap.

### What is the volatile keyword? {E}
**Short answer:** `volatile` tells the compiler that an object can change, or that accessing it has effects, outside the normal flow of the program it can see (hardware, an ISR, another core, a debugger). So every read and write written in the source must actually be performed, in program order relative to other volatile accesses, and cannot be cached in a register, merged or removed.

**Three classic cases where it is required**

1. **Memory-mapped hardware registers:** the value changes on its own (status registers), and writes have effects (sending a byte).
2. **Variables shared with an interrupt handler:** the main loop must re-read a flag that the ISR sets.
3. **Variables modified by another thread or core in bare-metal code without an OS** (although proper synchronisation is still needed; see below).

```c
static volatile bool data_ready;           /* set in the ISR */

void USART1_IRQHandler(void) { data_ready = true; }

int main(void)
{
    while (!data_ready) { }   /* without volatile, the compiler may read once and loop forever */
    /* ... */
}
```

**What volatile does not do**

- It does **not** make operations atomic: `volatile uint32_t count; count++;` is still load–add–store and can lose updates.
- It does **not** order non-volatile accesses around it, and it does not add CPU memory barriers (on multi-core systems or with DMA you need `__DMB()`/`atomic_thread_fence()` as well).
- It is **not** a replacement for mutexes or atomics in multi-threaded code (C11 `_Atomic` is the right tool there).

**Cost:** every access goes to memory, which prevents optimisations. Only mark what needs it.

The Embedded C topic covers `volatile` in more depth, including pointer declarations and the C++20 changes.

### Can a variable be both const and volatile? What is the difference between them? {M}
**Short answer:** Yes. `const` means **this program** must not write the object; `volatile` means **something else** may change it (or that reading it has side effects), so every access must really happen. Together they describe a read-only hardware register: you cannot write it, but you must re-read it every time.

```c
#define USART_SR (*(const volatile uint32_t *)0x40011000u)

while ((USART_SR & TXE) == 0) { }   /* re-read on every iteration; USART_SR = 0 is a compile error */
```

**const vs volatile**

| | `const` | `volatile` |
|---|---|---|
| Promise made by | the programmer: "this code will not modify it" | the programmer: "it can change outside the program's control" |
| Effect on the compiler | rejects writes; may place the object in flash (`.rodata`); may assume the value never changes | must perform every read/write; cannot cache, merge or remove accesses |
| Typical use | lookup tables, configuration, function parameters that must not be modified | hardware registers, ISR-shared flags, memory written by DMA |
| Combined | `const volatile`: read-only register, or a variable this module only reads but an ISR or hardware writes |

**Other examples of `const volatile`**

- A free-running timer counter that software only reads.
- A shared variable that the main loop only reads and an ISR writes: in the main module it could be declared `extern const volatile uint32_t g_ticks;` so the main code cannot write it by accident.
- A configuration word in flash that the bootloader or a debugger might rewrite.

**Order of qualifiers:** `const volatile uint32_t`, `volatile const uint32_t` and `uint32_t const volatile` are all the same.

### What does the restrict keyword mean? {H}
**Short answer:** `restrict` (C99) applies to a pointer and is a promise from the programmer that, for the lifetime of that pointer, the object it points to is accessed **only through that pointer** (or pointers derived from it). This lets the compiler assume no aliasing, keep values in registers and vectorise loops. If the promise is broken, the behaviour is undefined.

```c
void add(int *restrict dst, const int *restrict a, const int *restrict b, size_t n)
{
    for (size_t i = 0; i < n; i++)
        dst[i] = a[i] + b[i];
}
```

**Why it helps**

Without `restrict`, the compiler must assume `dst` might overlap `a` or `b`. After every store to `dst[i]`, it has to reload `a` and `b` from memory, and it cannot safely load several elements at once with SIMD (Neon/Helium) instructions. With `restrict`, it can.

A smaller example of the effect:

```c
int f(int *p, int *q) { *p = 1; *q = 2; return *p; }        /* must reload *p: q may equal p */
int g(int *restrict p, int *restrict q) { *p = 1; *q = 2; return *p; }   /* returns 1 directly */
```

**Standard library uses:** `memcpy(void *restrict dst, const void *restrict src, size_t n)` is declared with `restrict`, which is the formal reason overlapping buffers are undefined for `memcpy` (and why `memmove`, without `restrict`, must exist). `printf`, `strcpy` and `sprintf` use it too.

**When to use it:** performance-critical loops in DSP code (filters, FFT, image processing) on Cortex-M4/M7/M55 and Cortex-A, where you know the buffers never overlap. Check the generated assembly to confirm it helped.

**Notes:** C++ has no `restrict` keyword (compilers offer `__restrict__`/`__restrict`). It only matters for optimisation; removing it never changes the meaning of a correct program.

### What is the difference between exit() and return from main? {E}
**Short answer:** In a hosted program, returning from `main` is equivalent to calling `exit()` with the returned value: functions registered with `atexit()` run, open `FILE` streams are flushed and closed, and temporary files are removed. `_Exit()` / `_exit()` terminate immediately **without** that cleanup. On a bare-metal microcontroller there is nobody to return to, so `main` should never return.

```c
#include <stdio.h>
#include <stdlib.h>

static void cleanup(void) { puts("cleanup"); }

int main(void)
{
    atexit(cleanup);
    printf("work");          /* buffered */
    return 0;                /* or exit(0): flushes "work", prints "cleanup" */
    /* _exit(0) here would lose "work" (unflushed) and skip cleanup */
}
```

**Differences that can matter**

- `exit()` can be called from any function; `return` only leaves `main` when written in `main`.
- After `return` from `main`, `main`'s local variables are gone before `atexit` handlers run, so a handler must not use pointers to them (for example, a `setvbuf` buffer that is a local array in `main`).
- Exit status: `EXIT_SUCCESS` (0) and `EXIT_FAILURE`; only the low 8 bits reach the parent on POSIX.
- In a multi-threaded program, `exit()` (or returning from `main`) ends **all** threads.
- In a child process after a failed `exec()`, use `_exit()` so the child does not flush the parent's copied stdio buffers a second time.

**Bare metal**

- The start-up code calls `main()` and, if it returns, typically falls into an infinite loop (`b .`) or calls `exit()`, which in newlib may loop forever or trigger a semihosting exit.
- Firmware therefore ends with a super loop or starts the RTOS scheduler, which never returns:

```c
int main(void)
{
    board_init();
    vTaskStartScheduler();   /* does not return */
    for (;;) { }             /* reached only if the scheduler could not start */
}
```

### How do variadic functions work? {M}
**Short answer:** A variadic function such as `printf` has at least one fixed parameter followed by `...`. It reads the extra arguments with the `<stdarg.h>` macros `va_start`, `va_arg`, `va_end` (and `va_copy`). The function has no way to know how many arguments were passed or their types, so a fixed parameter (a count or a format string) must tell it.

```c
#include <stdarg.h>
#include <stdio.h>

int sum(int count, ...)
{
    va_list ap;
    int s = 0;
    va_start(ap, count);              /* start after the last fixed parameter */
    while (count--)
        s += va_arg(ap, int);         /* read the next argument as an int */
    va_end(ap);
    return s;
}

/* a logging wrapper that forwards to vprintf */
void log_msg(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
void log_msg(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    printf("[%lu] ", (unsigned long)0 /* tick */);
    vprintf(fmt, ap);
    va_end(ap);
}
```

**Rules and pitfalls**

- **Default argument promotions** apply to the variable arguments: `char` and `short` become `int`, `float` becomes `double`. So `va_arg(ap, char)` or `va_arg(ap, float)` is wrong; use `int` and `double`.
- Reading more arguments than were passed, or with the wrong type, is undefined behaviour. `printf("%d", 3.5)` and `printf("%s", 42)` are classic bugs.
- The `format` attribute lets GCC/Clang check format strings in your own wrappers, catching those bugs at compile time.
- To pass the arguments on, write a `v` version that takes a `va_list` (like `vprintf`), because you cannot forward `...` directly.
- Use `va_copy` if you need to traverse the list twice.

**How it works underneath:** on Arm (AAPCS), the first four integer arguments are in registers `r0`–`r3`, and the rest are on the stack. `va_start` makes the callee save the register arguments to memory so `va_arg` can walk them like an array. Floating-point variadic arguments go in integer registers or on the stack even with a hardware FPU (the variadic calling convention is the soft-float one).

**Embedded notes:** a full `printf` implementation can add 10–30 KB of flash; small projects use `newlib-nano` (`--specs=nano.specs`), a minimal printf, or deferred/binary logging where the device sends a format ID and raw arguments and a PC tool formats them (Trice, defmt, Zephyr dictionary logging). Avoid `printf` in ISRs (slow and usually not reentrant).

### What is conditional compilation, and how is it used in embedded projects? {E}
**Short answer:** Conditional compilation uses preprocessor directives (`#if`, `#ifdef`, `#ifndef`, `#elif`, `#else`, `#endif`, and the `defined()` operator) to include or exclude code before it is compiled. Embedded projects use it to build one code base for several boards and MCUs, to enable debug features, and to select features at build time.

```c
#if defined(BOARD_REV_B)
#  define LED_PIN 5
#elif defined(BOARD_REV_A)
#  define LED_PIN 3
#else
#  error "Unknown board revision"
#endif

#ifndef UART_BAUD
#  define UART_BAUD 115200u          /* default that can be overridden with -DUART_BAUD=9600 */
#endif

#if DEBUG_LEVEL >= 2
#  define LOG_DEBUG(...) log_msg(__VA_ARGS__)
#else
#  define LOG_DEBUG(...) do { } while (0)   /* compiled out completely */
#endif
```

**Where the symbols come from:** `-D` options on the compiler command line (set by Make/CMake per build configuration), a generated `config.h` (Kconfig in Zephyr and Linux, `sdkconfig.h` in ESP-IDF), and compiler-predefined macros (`__ARM_ARCH`, `__GNUC__`, `__BYTE_ORDER__`, `__ARM_FEATURE_DSP`).

**`#ifdef` vs `#if`**

- `#ifdef X` checks only whether `X` is defined, even if it is defined as 0.
- `#if X` evaluates its value; an undefined `X` silently counts as 0. GCC's `-Wundef` warns about that, which catches typos like `#if DEBUG_LEVLE > 1`.
- Kconfig-style systems prefer `#if IS_ENABLED(CONFIG_FOO)` or `if (IS_ENABLED(CONFIG_FOO))` in C code, so both branches are still compiled and type-checked.

**Good practice**

- Use `#error` to stop the build when a required option is missing or inconsistent.
- Keep `#ifdef` blocks small; large conditional regions make code hard to read and test. Prefer separate source files per platform, selected by the build system (`uart_stm32.c`, `uart_nrf.c`).
- Remember that code inside a disabled `#if` is not compiled at all, so it can rot. CI should build all configurations.

### What is _Static_assert and why is it useful? {M}
**Short answer:** `_Static_assert(condition, "message")` (C11; `static_assert` with `<assert.h>`, and a keyword in C23) checks a constant expression **at compile time**. If the condition is false, the build fails with your message. It costs nothing at run time, so it is ideal for checking assumptions about sizes, layouts and configuration that would otherwise cause subtle run-time bugs.

```c
#include <assert.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t  type;
    uint8_t  flags;
    uint16_t length;
    uint32_t crc;
} __attribute__((packed)) frame_hdr_t;

static_assert(sizeof(frame_hdr_t) == 8, "frame header must be 8 bytes on the wire");
static_assert(offsetof(frame_hdr_t, crc) == 4, "crc must be at offset 4");

#define RX_BUF_SIZE 128u
static_assert((RX_BUF_SIZE & (RX_BUF_SIZE - 1u)) == 0, "RX_BUF_SIZE must be a power of two");

static_assert(sizeof(void *) == 4, "this driver assumes a 32-bit target");
```

**Typical uses in firmware**

- Struct sizes and offsets that must match hardware, a protocol, flash layout or a bootloader.
- Ring-buffer sizes that must be powers of two (for `& (size - 1)` wrapping).
- Lookup tables that must have one entry per enum value: `static_assert(ARRAY_SIZE(state_names) == STATE_COUNT, "...");` catches a forgotten table entry when someone adds a state.
- Timer and baud-rate calculations that must fit in a register's range.
- Assumptions about type sizes and endianness when porting.

**Compared with `assert()`:** `assert()` checks at run time, costs code, and disappears with `NDEBUG`. `static_assert` can only check things known at compile time but catches them before the code ever runs.

**Before C11**, projects used tricks such as declaring an array with a negative size when the condition is false: `typedef char check_size[(sizeof(x) == 8) ? 1 : -1];`. You may still see this in older code.
