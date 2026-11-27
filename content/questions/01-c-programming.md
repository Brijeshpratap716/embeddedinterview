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
A **macro** performs textual substitution during preprocessing, whereas an **inline function** is a normal function that the compiler may expand directly at the calling location to reduce function call overhead.

#### 1. Macro

A macro is defined using `#define`.

```c
#define SQUARE(x) ((x) * (x))

int main(void)
{
    int a = SQUARE(5);
    return 0;
}
```

During preprocessing:

```c
int a = ((5) * (5));
```

The preprocessor replaces the macro with its corresponding expression.

#### 2. Inline function

An inline function is defined using the `inline` keyword.

```c
static inline int square(int x)
{
    return x * x;
}

int main(void)
{
    int a = square(5);
    return 0;
}
```

The compiler may replace the function call with its implementation, avoiding function call overhead.

However, **the inline keyword does not guarantee inlining.**

#### 3. How they work internally

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 254" width="100%" role="img" aria-label="Macro expansion by preprocessor compared with compiler function inlining"><text x="82.5" y="16" font-size="13" font-weight="600" fill="currentColor" text-anchor="middle">Macro</text><rect x="5" y="28" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="82.5" y="48" font-size="11" text-anchor="middle" fill="currentColor">SQUARE(5)</text><path d="M82.5 59 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="5" y="74" width="155" height="31" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/><text x="82.5" y="94" font-size="11" text-anchor="middle" fill="currentColor">Preprocessor</text><path d="M82.5 105 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="5" y="120" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="82.5" y="140" font-size="11" text-anchor="middle" fill="currentColor">((5) * (5))</text><path d="M82.5 151 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="5" y="166" width="155" height="31" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/><text x="82.5" y="186" font-size="11" text-anchor="middle" fill="currentColor">Compiler</text><path d="M82.5 197 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="5" y="212" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="82.5" y="232" font-size="11" text-anchor="middle" fill="currentColor">Machine code</text><text x="257.5" y="16" font-size="13" font-weight="600" fill="currentColor" text-anchor="middle">Inline function</text><rect x="180" y="28" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="257.5" y="48" font-size="11" text-anchor="middle" fill="currentColor">square(5)</text><path d="M257.5 59 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="180" y="74" width="155" height="31" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/><text x="257.5" y="94" font-size="11" text-anchor="middle" fill="currentColor">Preprocessor</text><path d="M257.5 105 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="180" y="120" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="257.5" y="140" font-size="11" text-anchor="middle" fill="currentColor">square(5)</text><path d="M257.5 151 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="180" y="166" width="155" height="31" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/><text x="257.5" y="186" font-size="11" text-anchor="middle" fill="currentColor">Compiler</text><path d="M257.5 197 v15 m-4 -5 4 5 4 -5" stroke="currentColor" fill="none"/><rect x="180" y="212" width="155" height="31" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="257.5" y="232" font-size="11" text-anchor="middle" fill="currentColor">Machine code</text></svg></div>

A macro is expanded by the preprocessor, while function inlining is performed by the compiler.

#### 4. Problems with macros

Consider the following example:

```c
#define SQUARE(x) ((x) * (x))

int i = 5;
int result = SQUARE(i++);
```

After macro expansion:

```c
int result = ((i++) * (i++));
```

This causes **undefined behaviour** because `i` is modified twice without sequencing.

With an inline function:

```c
static inline int square(int x)
{
    return x * x;
}

int i = 5;
int result = square(i++);
```

Result:

```text
result = 25
i = 6
```

The argument is evaluated only once.

#### 5. Comparison table

| Feature | Macro | Inline function |
|---|---|---|
| Keyword | `#define` | `inline` |
| Processed by | Preprocessor | Compiler |
| Type checking | After expansion | Function type checking |
| Argument evaluation | May occur multiple times | Once per argument |
| Function call overhead | None | None if inlined |
| Debugging | More difficult | Easier |
| Code size | May increase | May increase if inlined |
| Function address | Not available for macro itself | Can be obtained |
| Scope | Preprocessor rules | C scope rules |

#### 6. Use in embedded systems

**Macro for register masks:**

```c
#define BIT(n) (1U << (n))

#define UART_ENABLE BIT(3)
```

**Inline function for register operations:**

```c
static inline void set_bit(volatile uint32_t *reg,
                           uint32_t mask)
{
    *reg |= mask;
}
```

Inline functions are commonly used in firmware, HAL libraries and Linux kernel drivers for small, frequently executed operations.

**Note:** This register operation is a read-modify-write and is not necessarily atomic or safe for every hardware register.

**Interview takeaway:** Prefer inline functions for type safety and single argument evaluation. Use macros for compile-time constants, register masks, conditional compilation and operations requiring preprocessor substitution.

### Why should macro arguments and bodies be wrapped in parentheses? {E}
Macro arguments and bodies should be wrapped in parentheses to **avoid unexpected results caused by operator precedence during macro expansion.**

The preprocessor performs textual substitution without understanding the intended mathematical operation.

#### 1. Macro without parentheses

```c
#define SQUARE(x) x*x

int result = SQUARE(2+3);
```

After macro expansion:

```c
int result = 2+3*2+3;
```

Since multiplication has higher precedence than addition:

```text
result = 2 + 6 + 3
result = 11
```

Expected result: `25`

#### 2. Macro with argument parentheses

```c
#define SQUARE(x) (x)*(x)

int result = SQUARE(2+3);
```

After macro expansion:

```c
int result = (2+3)*(2+3);
```

**Output:** `25`

However, another problem remains when the macro is used inside a larger expression.

```c
int result = 100 / SQUARE(5);
```

After expansion:

```c
int result = 100 / (5)*(5);
```

**Output:** `100`, instead of `4`.

This happens because multiplication and division have the same precedence and are evaluated from left to right.

#### 3. Correct macro implementation

Wrap both individual arguments and the entire macro body in parentheses.

```c
#define SQUARE(x) ((x)*(x))

int result = 100 / SQUARE(5);
```

After expansion:

```c
int result = 100 / ((5)*(5));
```

**Output:** `4`

#### 4. Macro expansion comparison

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 220" width="100%" role="img" aria-label="Macro expansion comparison: incorrect result 11 versus correct result 25"><rect x="5" y="5" width="330" height="100" rx="7" fill="#dc2626" fill-opacity=".06" stroke="#dc2626"/>
<text x="170" y="22" font-size="12" font-weight="600" fill="#dc2626" text-anchor="middle">Incorrect macro</text>
<text x="170" y="40" font-size="11" font-family="monospace" fill="currentColor" text-anchor="middle">#define SQUARE(x) x*x</text>
<text x="170" y="56" font-size="10" fill="currentColor" text-anchor="middle">SQUARE(2+3) expands to</text>
<text x="170" y="75" font-size="13" font-family="monospace" fill="currentColor" text-anchor="middle">2 + 3 * 2 + 3</text>
<text x="170" y="94" font-size="12" font-weight="600" fill="#dc2626" text-anchor="middle">11 (Incorrect)</text>
<rect x="5" y="115" width="330" height="100" rx="7" fill="#16a34a" fill-opacity=".06" stroke="#16a34a"/>
<text x="170" y="132" font-size="12" font-weight="600" fill="#16a34a" text-anchor="middle">Correct macro</text>
<text x="170" y="150" font-size="11" font-family="monospace" fill="currentColor" text-anchor="middle">#define SQUARE(x) ((x)*(x))</text>
<text x="170" y="166" font-size="10" fill="currentColor" text-anchor="middle">SQUARE(2+3) expands to</text>
<text x="170" y="185" font-size="13" font-family="monospace" fill="currentColor" text-anchor="middle">((2 + 3) * (2 + 3))</text>
<text x="170" y="204" font-size="12" font-weight="600" fill="#16a34a" text-anchor="middle">25 (Correct)</text>
</svg></div>

#### 5. Use in embedded systems

Macros are frequently used for register masks and bit manipulation.

```c
#define BIT(n) (1U << (n))
#define SET_BIT(reg, n) ((reg) |= BIT(n))
#define CLEAR_BIT(reg, n) ((reg) &= ~BIT(n))
```

Parentheses ensure correct expansion when expressions are passed as arguments. The bit position must be within the valid width of the unsigned operand.

#### 6. Comparison table

| Macro definition | Expression | Result |
|---|---|---|
| `#define SQ(x) x*x` | `SQ(2+3)` | 11 |
| `#define SQ(x) (x)*(x)` | `SQ(2+3)` | 25 |
| `#define SQ(x) (x)*(x)` | `100/SQ(5)` | 100 |
| `#define SQ(x) ((x)*(x))` | `100/SQ(5)` | 4 |

**Note:** Parentheses do not prevent multiple argument evaluation. For example, `SQUARE(i++)` still causes undefined behaviour.

**Interview takeaway:** Always wrap individual macro arguments and the entire expression macro body in parentheses to prevent operator precedence problems. Prefer inline functions when arguments may have side effects.

### Why are multi-line macros wrapped in do { } while(0)? {M}
A multi-statement macro is wrapped in `do { ... } while (0)` to make it behave like **one C statement**, even when used inside an unbraced `if-else`.

#### 1. Problem without a wrapper

```c
#define RESET(a,b) (a)=0; (b)=0

if (error)
    RESET(x,y);
```

After expansion, only `x=0` is conditional; `y=0` executes regardless of the condition.

#### 2. Why braces alone are insufficient

```c
#define RESET(a,b) { (a)=0; (b)=0; }

if (error)
    RESET(x,y);
else
    recover();
```

The semicolon after the closing brace becomes a separate empty statement, so the `else` cannot attach to the `if`.

#### 3. Correct implementation

```c
#define RESET(a,b) do { \
    (a) = 0;           \
    (b) = 0;           \
} while (0)

if (error)
    RESET(x,y);
else
    recover();
```

The body executes once and the caller's semicolon completes the do-while statement. There is no useful loop to execute again; optimizing compilers remove unnecessary loop overhead.

#### 4. Use in firmware

```c
#define LOG_ERROR(msg) do { \
    log_message(msg);       \
    error_count++;          \
} while (0)
```

This is useful for logging, assertions and grouped register operations. It does not make the operations atomic or protect against interrupts.

**Interview takeaway:** Use `do { ... } while (0)` for multi-statement macros. Prefer a typed inline function when preprocessing is unnecessary. The wrapper does not fix repeated argument evaluation, and `break` or `continue` inside it affects the wrapper loop.

### What are # and ## in macros? {M}
The C preprocessor provides two operators for manipulating macro arguments: **`#` (stringification)** and **`##` (token pasting)**.

#### 1. Stringification operator (#)

It converts a macro argument's spelling into a string literal.

```c
#define STR(x) #x

printf("%s", STR(hello));
```

Expansion: `printf("%s", "hello");`

**Output:** `hello`

It does not evaluate the argument. For example, `STR(2+3)` produces the string `"2+3"`, not `"5"`.

#### 2. Token pasting operator (##)

It combines two preprocessing tokens into a single token.

```c
#define JOIN(a,b) a##b

int JOIN(reg,1) = 100;
printf("%d", reg1);
```

Expansion: `int reg1 = 100;`

**Output:** `100`

The combined token must be valid.

#### 3. Expanding a macro before stringification

```c
#define VERSION 3
#define STR_RAW(x) #x
#define STR_EXPAND(x) STR_RAW(x)

STR_RAW(VERSION)     // "VERSION"
STR_EXPAND(VERSION)  // "3"
```

Arguments immediately used with `#` or `##` are not macro-expanded first. An extra macro layer allows expansion before stringification or pasting.

#### 4. Embedded debugging example

```c
#define CHECK(x) do {                 \
    if (!(x)) log_error(#x);          \
} while (0)

CHECK(buffer != NULL);
```

On failure the logger receives the expression's spelling.

| Operator | Operation | Example |
|---|---|---|
| `#` | Stringify | `STR(ready)` becomes `"ready"` |
| `##` | Paste tokens | `JOIN(uart,2)` becomes `uart2` |

**Interview takeaway:** These operators operate on preprocessing tokens, not runtime strings or values.

### What is the difference between #include <file> and #include "file"? {E}
Both forms of `#include` insert header contents during preprocessing. They differ primarily in **header search rules**.

#### 1. Angle brackets

```c
#include <stdio.h>
#include <stdint.h>
```

The compiler normally searches configured include directories, including standard library and toolchain headers.

#### 2. Double quotes

```c
#include "driver.h"
#include "board.h"
```

Compilers such as GCC normally look in the directory containing the including file first, followed by configured quote/include search paths.

#### 3. Example project

```text
project/
    main.c
    board.h
    drivers/
        uart.h
```

```c
// main.c
#include "board.h"
#include "uart.h"
#include <stdint.h>
```

Build with GCC:

```sh
gcc -I drivers -c main.c -o main.o
```

The `-I` option adds a directory to the header search path.

#### 4. Comparison

| Feature | Angle brackets | Double quotes |
|---|---|---|
| Common use | Library and SDK headers | Project headers |
| Typical first search | Configured include paths | Including file's directory |
| Example | `<stdint.h>` | `"board.h"` |

Exact search order is implementation-defined and can be changed by build flags. Both forms can find project headers if the paths are configured.

**Interview takeaway:** Use quotes for nearby project headers and angle brackets for standard or configured SDK headers. `#include` is a preprocessing operation, not a linker operation.

### What are include guards and #pragma once? {E}
Include guards and `#pragma once` prevent a header from being processed multiple times within the **same translation unit**.

#### 1. Why are they needed?

Suppose both `uart.h` and `spi.h` include `common.h`, and `main.c` includes both driver headers.

```text
          main.c
         /      \
      uart.h   spi.h
         \      /
         common.h
```

Without protection, definitions such as a structure type in `common.h` could be processed twice and cause a compilation error.

#### 2. Include guards

```c
#ifndef COMMON_H_INCLUDED
#define COMMON_H_INCLUDED

struct config {
    int speed;
};

#endif
```

On the first inclusion the macro is undefined, so the contents are processed and the guard becomes defined. Later inclusions skip the guarded content.

#### 3. Using #pragma once

```c
#pragma once

struct config {
    int speed;
};
```

This instructs supporting compilers to process the header only once.

#### 4. Comparison

| Include guard | #pragma once |
|---|---|
| Standard C preprocessor directives | Widely supported compiler extension |
| Requires a unique macro name | No guard macro needed |
| Works with conforming C preprocessors | Depends on compiler and file identity handling |

Include guards do not prevent duplicate external object definitions across different source files. Put declarations in headers and ordinary external definitions in one source file.

**Interview takeaway:** Both prevent repeated header processing; include guards are the portable choice.

### What is the difference between typedef and #define for creating type names? {E}
The `typedef` keyword creates a **type alias** understood by the C compiler. A `#define` macro merely replaces preprocessing tokens.

#### 1. Using typedef

```c
typedef unsigned int uint;

uint count = 10;
```

The compiler treats `uint` as an alias for `unsigned int`. It follows C type and scope rules.

#### 2. Using #define

```c
#define UINT unsigned int

UINT count = 10;
```

The preprocessor substitutes `unsigned int` for `UINT` before the compiler analyzes the declaration.

#### 3. Important pointer example

```c
typedef int *IntPtr;

IntPtr a, b;  // Both are int pointers

#define PTR int *

PTR x, y;     // x is int pointer, y is int
```

The last declaration expands to:

```c
int *x, y;
```

The asterisk belongs to the declarator for `x`, not the common base type.

#### 4. Embedded use

```c
typedef struct {
    unsigned int baud;
    unsigned int port;
} uart_config_t;

uart_config_t cfg = {115200, 1};
```

Aliases are useful for structures, callback types and complex declarations.

| Feature | typedef | #define |
|---|---|---|
| Handled by | Compiler | Preprocessor |
| Meaning | Type alias | Token substitution |
| Scope | C scope | Macro visibility |
| Pointer declarations | Preserves aliased pointer type | Depends on expanded syntax |

**Interview takeaway:** Prefer `typedef` for type names. It creates an alias, not a distinct new type in C. Use `#define` for preprocessing and configuration.

### What is undefined behaviour? Give examples. {M}
Undefined behaviour (UB) occurs when a program performs an operation for which the **C standard imposes no requirements**. The program may crash, produce unexpected results or appear to work.

#### 1. Examples

```c
int a[5];
a[5] = 10;    // Out-of-bounds write

int *p = NULL;
*p = 20;      // NULL dereference
```

```c
int n = INT_MAX;
n++;          // Signed integer overflow

int divisor = 0;
int x = 10 / divisor; // Division by zero
```

Other common examples include reading uninitialized automatic integers, accessing freed memory, invalid shift counts and data races on ordinary shared objects.

#### 2. Why optimization matters

```c
int greater(int x)
{
    return x + 1 > x;
}
```

A compiler may optimize this function to return 1 because signed overflow is undefined; it need not support a wrapping result for `INT_MAX`.

#### 3. Safe alternatives

- Validate indices and pointers before accessing memory.
- Check arithmetic bounds and use unsigned types when modular arithmetic is intended.
- Use atomics or locks for concurrent access.
- Use warnings, sanitizers and static analysis on supported platforms.

#### 4. Related terms

| Behaviour | Meaning |
|---|---|
| Undefined | No requirements imposed by the standard |
| Unspecified | One of several permitted behaviours; documentation not required |
| Implementation-defined | Implementation selects and documents a permitted behaviour |

For example, function argument evaluation order is generally unspecified, and plain `char` signedness is implementation-defined.

**Interview takeaway:** Correct behaviour on one board or at `-O0` is not proof of valid C. Fix the underlying UB instead of disabling optimization.

### What is a sequence point? {H}
A sequence point establishes a boundary at which preceding evaluations and side effects have completed before subsequent ones begin. Modern C describes this more generally using **sequenced-before** relationships.

#### 1. Defined sequence

```c
int i = 5;
i++;
i++;

printf("%d", i);
```

**Output:** `7`

Each expression statement completes before the next one.

#### 2. Undefined behaviour

```c
int i = 5;
int x = i++ + i++;
```

The operands of `+` are not sequenced relative to one another. Both modify `i`, causing undefined behaviour in C.

Similarly, `i = i++ + 1;` is undefined.

#### 3. Operators that provide sequencing

```c
if (p != NULL && *p == 10) {
    // Safe dereference if p is valid and non-NULL
}
```

The left operand of `&&` is evaluated first. The right operand is evaluated only if needed. The same short-circuit principle applies to `||`. The comma operator and the first operand of `?:` also establish sequencing.

#### 4. Function arguments

```c
printf("%d %d", i++, i++);
```

This has undefined behaviour in C. A comma separating function arguments is not the comma operator, and argument evaluation order is generally unspecified.

Use separate statements instead:

```c
int a = i++;
int b = i++;
printf("%d %d", a, b);
```

**Interview takeaway:** Avoid unsequenced modifications to the same scalar, or an unsequenced modification and read of its value. Operator precedence determines expression grouping, not evaluation order.

### What is the size of an int, and what are fixed-width types? {E}
The size of `int` is **implementation-defined**. C guarantees a minimum range of -32767 to 32767, but does not require `int` to be 32 bits.

#### 1. Check the actual size

```c
#include <stdio.h>
#include <limits.h>

int main(void)
{
    printf("%zu bytes\n", sizeof(int));
    printf("%zu bits\n", sizeof(int) * CHAR_BIT);
}
```

Typical ARM Linux output is 4 bytes and 32 bits. Some microcontrollers use a 16-bit `int`.

#### 2. Fixed-width integers

The `<stdint.h>` header defines exact-width types where the implementation supports them.

| Signed type | Unsigned type | Width |
|---|---|---|
| `int8_t` | `uint8_t` | 8 bits |
| `int16_t` | `uint16_t` | 16 bits |
| `int32_t` | `uint32_t` | 32 bits |
| `int64_t` | `uint64_t` | 64 bits |

#### 3. Why embedded software uses them

```c
#include <stdint.h>

uint8_t command = 0xA5;
uint16_t sensor_value = 1024;
uint32_t reg_mask = 0x80000000u;
```

These types express the intended register, protocol or data width independently of the size of `int`. Use explicit byte-order conversion for serialized data.

#### 4. Other useful types

`size_t` represents object sizes, `uintptr_t` (if provided) can hold converted object pointer values, and `uint_fast32_t` provides an unsigned type of at least 32 bits selected for speed.

**Interview takeaway:** Never assume `sizeof(int)` is 4 or that a C byte is always 8 bits. Use fixed-width types for hardware and protocol fields when available, and `<inttypes.h>` format macros when printing them.

### Is char signed or unsigned, and why does it matter? {M}
C has three distinct character types: `char`, `signed char` and `unsigned char`. Whether plain `char` behaves as signed or unsigned is **implementation-defined**.

#### 1. Range on typical 8-bit-byte systems

| Type | Range |
|---|---|
| `signed char` | -128 to 127 |
| `unsigned char` | 0 to 255 |
| `char` | Depends on compiler and target |

#### 2. Example

```c
#include <stdio.h>

unsigned char a = 0xFF;
char b = (char)a;

printf("%u\n", (unsigned int)a);
printf("%d\n", (int)b);
```

The first line prints 255. The second commonly prints -1 when plain char is signed, or 255 when it is unsigned. The conversion to a signed type when the value is not representable is implementation-dependent in traditional C.

#### 3. Why it matters in embedded systems

A binary protocol may contain the byte 0xFF. Using signed char can turn this byte into a negative value after integer promotion, affecting comparisons, indexing and bit shifts.

```c
unsigned char rx = 0xFF;

if (rx == 0xFF)
    handle_command();
```

Use unsigned char for object representations or `uint8_t` for exactly eight bits where available.

#### 4. Check the target

```c
#include <limits.h>

#if CHAR_MIN < 0
    // Plain char is signed.
#else
    // Plain char is unsigned.
#endif
```

**Interview takeaway:** Use plain char for text and explicitly signed or unsigned types when numeric interpretation matters. Cast to unsigned char before passing a potentially negative char to character classification functions such as `isalpha()`.

### What is integer promotion? {M}
Integer promotion converts integer types with sufficiently low rank, such as `char` and `short`, to `int` if it can represent all their values, otherwise to `unsigned int`. This happens before many arithmetic and bitwise operations.

#### 1. Arithmetic example

```c
uint8_t a = 200;
uint8_t b = 100;

int result = a + b;       // 300
uint8_t small = a + b;    // 44
```

On a typical 32-bit-int target:

1. Both operands are promoted to int.
2. Addition produces 300.
3. Assignment to uint8_t converts 300 modulo 256, giving 44.

The addition itself does not occur in an eight-bit type.

#### 2. Bitwise complement example

```c
uint8_t mask = 0x0F;

int x = ~mask;
uint8_t y = (uint8_t)~mask;
```

On a typical 32-bit two's-complement target, `x` has the bit pattern 0xFFFFFFF0, while `y` is 0xF0.

The complement acts on the promoted type, not just the original eight bits.

#### 3. Embedded example: constructing a register value

```c
uint8_t byte = 0xAB;
uint32_t reg = (uint32_t)byte << 24;
```

Casting before shifting ensures unsigned 32-bit arithmetic. On a common 32-bit-int system, shifting the promoted signed value directly by 24 would overflow the representable signed range.

**Interview takeaway:** Small integer operands may be promoted before arithmetic. Watch the type of intermediate expressions, especially when manipulating registers, shifts and masks.

### What happens when you compare signed and unsigned integers? {M}
C applies the **usual arithmetic conversions** to operands of comparisons. Depending on type rank and representable range, a signed value can be converted to an unsigned value.

#### 1. Unexpected result

```c
int a = -1;
unsigned int b = 1;

if (a < b)
    printf("True");
else
    printf("False");
```

**Output:** `False`

Because both have the same rank, a is converted to unsigned int. Conversion of -1 gives UINT_MAX.

On a typical 32-bit target:

| Operand | Before conversion | After conversion |
|---|---:|---:|
| a | -1 | 4294967295 |
| b | 1 | 1 |

The converted comparison is false.

#### 2. Why this matters in embedded code

```c
int index = -1;
size_t len = 16;

if (index < len) {
    // Do not rely on mixed-type comparison alone.
}
```

The correct check must first reject a negative index.

```c
if (index >= 0 && (size_t)index < len) {
    // Access buffer[index] if buffer is valid.
}
```

#### 3. Does unsigned always win?

No. If a higher-ranked signed type can represent all values of the unsigned operand, the unsigned operand is converted to the signed type. Otherwise, the rules may select an unsigned common type.

**Interview takeaway:** Do not mix signed error values and unsigned lengths without checking their ranges. Enable compiler warnings such as `-Wsign-compare`.

### What is the difference between ++i and i++? {E}
Both operators increment a variable by one. The difference is the **value produced by the expression**.

#### 1. Pre-increment (++i)

```c
int i = 5;
int a = ++i;
```

The expression produces the incremented value.

**Result:** `i = 6, a = 6`

#### 2. Post-increment (i++)

```c
int i = 5;
int a = i++;
```

The expression produces the original value, while i is also incremented.

**Result:** `i = 6, a = 5`

| Expression | Value assigned to a | Final i (initially 5) |
|---|---:|---:|
| `a = ++i;` | 6 | 6 |
| `a = i++;` | 5 | 6 |

#### 3. Embedded example

```c
uint8_t buffer[4] = {10,20,30,40};
unsigned int index = 0;

uint8_t value = buffer[index++];
```

The code reads buffer[0], which contains 10, and then index becomes 1 by the end of the statement.

#### 4. Is one faster?

When the expression result is unused, `++i;` and `i++;` perform the same update for an ordinary C integer. Optimizing compilers normally generate equivalent code.

**Interview takeaway:** Prefix produces the new value, postfix produces the old value. Avoid expressions such as `i++ + ++i`, which contain unsequenced modifications and cause undefined behaviour.

### What is the difference between a structure and a union? {E}
A **structure** stores each member in a separate region of memory, while a **union** overlays its members in the same storage.

#### 1. Structure

```c
struct Data {
    int a;
    char b;
};

struct Data d = {100, 'X'};
```

Both members hold their own values simultaneously. On a typical ABI with four-byte int alignment, sizeof(struct Data) is 8 bytes.

#### 2. Union

```c
union Data {
    int a;
    char b;
};

union Data u;
u.a = 100;
u.b = 'X';
```

Writing b changes part of the storage also occupied by a. Do not expect a to retain its original independent value. Typical size is 4 bytes.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 340 183" role="img" aria-label="Typical structure uses separate member storage, union members overlap" font-family="system-ui,sans-serif"><text x="8" y="18" font-size="11" fill="currentColor">Structure: 8 bytes (P = padding)</text><rect x="8" y="24" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="21.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="35" y="24" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="48.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="62" y="24" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="75.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="89" y="24" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="102.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="116" y="24" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="129.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="143" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="156.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="170" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="183.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="197" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="210.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><text x="8" y="75" font-size="11" fill="currentColor">Union viewed as int member</text><rect x="8" y="81" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="21.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="35" y="81" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="48.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="62" y="81" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="75.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="89" y="81" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="102.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">a</text><text x="8" y="132" font-size="11" fill="currentColor">Same union storage viewed as char member</text><rect x="8" y="138" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="21.5" y="155" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="35" y="138" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="48.5" y="155" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="62" y="138" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="75.5" y="155" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="89" y="138" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="102.5" y="155" font-size="12" text-anchor="middle" fill="currentColor">P</text></svg></div>

For the union's char view, P denotes bytes outside the char member, not necessarily ordinary structure padding.

#### 3. Embedded use case: tagged data

```c
enum Kind { TEMPERATURE, RAW };
struct Message {
    enum Kind kind;
    union {
        float temp;
        uint32_t raw;
    } value;
};
```

The tag identifies which union member contains the meaningful value. This is useful when messages carry one of several payload types.

| Feature | Structure | Union |
|---|---|---|
| Member storage | Separate | Shared |
| Size | All members plus padding | Largest member plus required padding |
| Independent values | All members | Not simultaneous independent storage |

**Interview takeaway:** Use structures for related fields and unions when alternative representations share storage. Union type-punning has representation-dependent results; use explicit conversions for portable protocol handling.

### What is structure padding and how do you avoid it? {M}
Structure padding is unused storage inserted by the compiler to satisfy **member alignment and overall structure alignment**.

#### 1. Example

```c
struct A {
    char a;
    int b;
    char c;
};
```

Assuming four-byte int size and alignment:

| Member | Offset |
|---|---:|
| a | 0 |
| b | 4 |
| c | 8 |

The structure typically occupies 12 bytes, not 6.

#### 2. Reduce padding by rearranging members

```c
struct B {
    int b;
    char a;
    char c;
};
```

Now the int starts at offset zero, the chars occupy offsets four and five, and two tail padding bytes remain.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 340 126" role="img" aria-label="Reordering structure members reduces padding from six bytes to two bytes on the assumed ABI" font-family="system-ui,sans-serif"><text x="8" y="18" font-size="11" fill="currentColor">Before: 12 bytes</text><rect x="8" y="24" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="21.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="35" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="48.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="62" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="75.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="89" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="102.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="116" y="24" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="129.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="143" y="24" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="156.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="170" y="24" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="183.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="197" y="24" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="210.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="224" y="24" width="27" height="25" fill="#a855f7" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="237.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">c</text><rect x="251" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="264.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="278" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="291.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="305" y="24" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="318.5" y="41" font-size="12" text-anchor="middle" fill="currentColor">P</text><text x="8" y="75" font-size="11" fill="currentColor">After: 8 bytes</text><rect x="8" y="81" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="21.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="35" y="81" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="48.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="62" y="81" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="75.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="89" y="81" width="27" height="25" fill="#3b82f6" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="102.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">b</text><rect x="116" y="81" width="27" height="25" fill="#16a34a" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="129.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">a</text><rect x="143" y="81" width="27" height="25" fill="#a855f7" fill-opacity=".6" stroke="currentColor" stroke-width=".5"/><text x="156.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">c</text><rect x="170" y="81" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="183.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">P</text><rect x="197" y="81" width="27" height="25" fill="#94a3b8" fill-opacity=".2" stroke="currentColor" stroke-width=".5"/><text x="210.5" y="98" font-size="12" text-anchor="middle" fill="currentColor">P</text></svg></div>

#### 3. Packed structures

GCC and Clang support a packing attribute:

```c
struct __attribute__((packed)) Packet {
    uint8_t type;
    uint32_t length;
};
```

On an eight-bit-byte target this commonly occupies five bytes. However, the 32-bit member may be unaligned, causing slower accesses or hardware faults depending on the platform and access instruction.

#### 4. Verify layout

```c
#include <stddef.h>

printf("%zu", sizeof(struct A));
printf("%zu", offsetof(struct A, b));
```

`offsetof()` returns the byte offset of a non-bit-field member. Use `_Static_assert` for required ABI layouts.

**Interview takeaway:** Rearrange members to reduce padding where ABI compatibility permits. Avoid packing by default; use explicit serialization for protocols and never assume that the C structure layout matches a hardware or wire format.

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
