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
Bit-fields allow structure members to occupy a specified number of bits rather than an entire integer member.

#### 1. Example

```c
struct Status {
    unsigned int ready : 1;
    unsigned int mode  : 3;
    unsigned int error : 1;
};

struct Status s = {1, 5, 0};
```

The ready and error fields store one bit each; mode stores three bits (0–7).

#### 2. Conceptual representation

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 88" width="100%" role="img" aria-label="One illustrative five-bit field layout, not guaranteed by C">
<rect x="10" y="23" width="110" height="34" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="65" y="44" text-anchor="middle" font-size="11" fill="currentColor">Unused / other</text>
<rect x="120" y="23" width="42" height="34" fill="#a855f7" fill-opacity=".2" stroke="#a855f7"/><text x="141" y="44" text-anchor="middle" font-size="10" fill="currentColor">error</text>
<rect x="162" y="23" width="126" height="34" fill="#3b82f6" fill-opacity=".2" stroke="#3b82f6"/><text x="225" y="44" text-anchor="middle" font-size="12" fill="currentColor">mode (3 bits)</text>
<rect x="288" y="23" width="42" height="34" fill="#16a34a" fill-opacity=".2" stroke="#16a34a"/><text x="309" y="44" text-anchor="middle" font-size="10" fill="currentColor">ready</text>
<text x="170" y="74" text-anchor="middle" font-size="10" fill="currentColor">Illustrative arrangement only; actual layout is implementation-defined.</text>
</svg></div>

#### 3. Drawbacks

- Allocation order, padding and storage-unit layout depend on the implementation.
- The address of an individual bit-field cannot be taken.
- Updating one field may require a read-modify-write of a larger storage unit.
- Volatile bit-fields do not automatically guarantee the access width or atomicity needed by hardware.

#### 4. Safer alternative for hardware registers

```c
#define READY_MASK (1u << 0)
#define MODE_MASK  (7u << 1)

uint32_t value = (5u << 1) | READY_MASK;
```

Use masks and shifts that match the hardware specification. Read-modify-write must still respect register semantics.

**Interview takeaway:** Bit-fields are useful for compact compiler-managed flags, but masks and shifts usually provide more explicit and portable control of hardware register and protocol layouts.

### What is an enum and how big is it? {E}
An enumeration (`enum`) defines a set of named integer constants and an enumerated type. It improves readability by replacing numeric values with meaningful names.

#### 1. Default values

```c
enum State {
    IDLE,
    RUNNING,
    ERROR
};

enum State state = IDLE;
```

By default IDLE is 0, RUNNING is 1 and ERROR is 2.

#### 2. Explicit values

```c
enum Error {
    OK = 0,
    TIMEOUT = 10,
    BUS_ERROR
};
```

BUS_ERROR automatically becomes 11.

#### 3. Size of enum

```c
printf("%zu", sizeof(enum State));
```

The size depends on the implementation, supported values, ABI and compiler options such as GCC's `-fshort-enums`. Four bytes is common, but not guaranteed. C23 also supports enums with explicitly specified underlying types.

#### 4. Use in embedded state machines

```c
enum State state = IDLE;

switch (state) {
case IDLE:
    start_device();
    state = RUNNING;
    break;
case RUNNING:
    process_data();
    break;
case ERROR:
default:
    recover_device();
    break;
}
```

Use named states to make control flow easier to understand. C does not automatically guarantee an enum object contains only the listed enumerator values.

**Interview takeaway:** An enum is useful for states, errors and configuration choices. Do not assume its memory size is four bytes or directly serialize its representation into a fixed-width protocol.

### What is the difference between malloc, calloc, realloc and free? {E}
These four functions from `<stdlib.h>` manage dynamically allocated memory.

#### 1. malloc()

Allocates the requested number of bytes. The initial contents are indeterminate.

```c
int *p = malloc(5 * sizeof *p);
if (p == NULL)
    return;
p[0] = 10;
```

#### 2. calloc()

Allocates space for an array and initializes all allocated bytes to zero.

```c
int *p = calloc(5, sizeof *p);
```

Check for failure before access. For integers, the resulting values are zero; all-bits-zero need not represent a null pointer or floating-point zero on every implementation.

#### 3. realloc()

Changes the size of an existing allocation. It may move the allocation to a different address.

```c
int *tmp = realloc(p, 10 * sizeof *p);

if (tmp != NULL)
    p = tmp;
```

For a nonzero requested size, failure leaves the old allocation valid. Existing contents are preserved up to the smaller of the two sizes. Additional bytes are not initialized.

#### 4. free()

Releases previously allocated memory.

```c
free(p);
p = NULL;
```

Do not dereference a freed pointer or free the same allocation twice.

| Function | Purpose | Initialization |
|---|---|---|
| malloc | Allocate bytes | Indeterminate |
| calloc | Allocate array | Zeroed bytes |
| realloc | Resize allocation | Preserves old portion |
| free | Release allocation | Not applicable |

#### 5. Embedded considerations

Dynamic allocation can fail, fragment the heap and introduce unpredictable latency. Fixed-size memory pools or static allocation may be preferable for hard real-time firmware.

**Interview takeaway:** Check allocation failures, guard size calculations against overflow, use a temporary pointer for realloc, and avoid zero-size realloc for portable behaviour.

### What is the difference between strcpy, strncpy and memcpy? {M}
All three copy data, but they differ in how they determine the length and whether they treat the input as a string.

#### 1. strcpy()

Copies a null-terminated string, including its terminating zero.

```c
char dst[8];
strcpy(dst, "hello");
```

Six bytes are copied. The destination must have enough space.

#### 2. strncpy()

Copies up to n characters and pads the destination with zero bytes if the source string is shorter than n.

```c
char dst[4];
strncpy(dst, "hello", sizeof dst);
```

The buffer contains h, e, l, l and has no null terminator. Do not use it as a C string until it is terminated safely.

```c
char dst[8];
strncpy(dst, src, sizeof dst - 1);
dst[sizeof dst - 1] = '\0';
```

This deliberately truncates long input.

#### 3. memcpy()

Copies exactly n bytes, including any zero bytes inside binary data.

```c
uint8_t src[] = {1, 0, 3};
uint8_t dst[3];

memcpy(dst, src, sizeof src);
```

All three bytes are copied.

| Function | Copy length | Termination |
|---|---|---|
| strcpy | Through first NUL | Copies NUL |
| strncpy | Exactly n destination bytes | Not guaranteed |
| memcpy | Exactly n bytes | No string semantics |

#### 4. What about overlapping memory?

Use memmove instead of memcpy when source and destination overlap.

```c
char s[] = "ABCDE";
memmove(s + 1, s, 4);  // "AABCD"
```

**Interview takeaway:** Use string APIs for properly bounded strings, memcpy for non-overlapping binary data, and memmove for overlapping byte ranges. None of these functions knows the destination capacity automatically.

### What is the difference between an array and a pointer? {M}
An **array** is an object containing consecutive elements of the same type. A **pointer** is a separate object containing a pointer value that can refer to an element.

#### 1. Declaration

```c
int a[5] = {10,20,30,40,50};
int *p = a;
```

Here the array expression a is converted to a pointer to its first element.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 117" width="100%" role="img" aria-label="Pointer p refers to first element of an array of five integers">
<rect x="8" y="38" width="78" height="34" rx="5" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/>
<text x="47" y="59" font-size="11" text-anchor="middle" fill="currentColor">p = &amp;a[0]</text>
<path d="M86 55 H132 M126 50 L132 55 L126 60" fill="none" stroke="currentColor"/>
<rect x="136" y="38" width="39" height="34" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="155.5" y="59" text-anchor="middle" font-size="12" fill="currentColor">10</text><text x="155.5" y="85" text-anchor="middle" font-size="9" fill="currentColor">a[0]</text><rect x="175" y="38" width="39" height="34" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="194.5" y="59" text-anchor="middle" font-size="12" fill="currentColor">20</text><text x="194.5" y="85" text-anchor="middle" font-size="9" fill="currentColor">a[1]</text><rect x="214" y="38" width="39" height="34" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="233.5" y="59" text-anchor="middle" font-size="12" fill="currentColor">30</text><text x="233.5" y="85" text-anchor="middle" font-size="9" fill="currentColor">a[2]</text><rect x="253" y="38" width="39" height="34" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="272.5" y="59" text-anchor="middle" font-size="12" fill="currentColor">40</text><text x="272.5" y="85" text-anchor="middle" font-size="9" fill="currentColor">a[3]</text><rect x="292" y="38" width="39" height="34" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="311.5" y="59" text-anchor="middle" font-size="12" fill="currentColor">50</text><text x="311.5" y="85" text-anchor="middle" font-size="9" fill="currentColor">a[4]</text>
<text x="47" y="100" text-anchor="middle" font-size="10" fill="currentColor">8 bytes</text><text x="233" y="100" text-anchor="middle" font-size="10" fill="currentColor">20 bytes total</text></svg></div>

Example assumes a typical 64-bit system and four-byte int.

#### 2. sizeof difference

```c
sizeof(a);  // 20 bytes on this system
sizeof(p);  // 8 bytes on this system
```

The array size includes all elements. The pointer size is independent of the array length.

#### 3. Reassignment

```c
p = &a[2];   // Allowed
// a = p;    // Invalid
```

A pointer variable can change its target. An array cannot be assigned as a whole using ordinary assignment.

#### 4. Passing an array to a function

```c
void print(int a[], size_t n)
{
    for (size_t i = 0; i < n; i++)
        printf("%d ", a[i]);
}
```

The array parameter is adjusted to int *. Pass the length separately; sizeof(a) inside this function gives the pointer size.

**Interview takeaway:** An array is not a pointer, although an array expression usually decays to a pointer to its first element. sizeof and unary address-of are important exceptions.

### What is a function pointer and where is it used? {M}
A **function pointer** stores a reference to a function with a compatible signature. It allows a function to be selected and called indirectly at runtime.

#### 1. Declaration and call

```c
int add(int a, int b)
{
    return a + b;
}

int (*operation)(int, int) = add;
int result = operation(10, 20);
```

**Result:** 30

The parentheses around *operation are essential. Without them, the declaration would describe a function returning a pointer instead.

#### 2. Callback example

```c
typedef void (*callback_t)(int);

void notify(callback_t cb, int value)
{
    if (cb != NULL)
        cb(value);
}

void on_receive(int data)
{
    printf("%d", data);
}

// notify(on_receive, 42);
```

The caller supplies the function to execute when an event occurs.

#### 3. Use in Linux device drivers

```c
static const struct file_operations my_fops = {
    .owner = THIS_MODULE,
    .read  = my_read,
    .write = my_write,
};
```

The VFS invokes the registered driver callbacks for file operations. Here my_read and my_write must have the signatures required by the kernel interface.

<div style="max-width:580px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 180" width="100%" role="img" aria-label="Linux VFS dispatches a read through a driver function pointer" font-family="system-ui,sans-serif"><rect x="25" y="5" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Userspace</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">read(fd, buffer, length)</text><path d="M170 48 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="65" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Linux VFS</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Select registered file operations</text><path d="M170 108 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="125" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Driver callback</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">my_read(...) handles the request</text></svg></div>

#### 4. Other uses

Function pointers are common in HAL callbacks, state-machine dispatch tables and interrupt vector implementations.

**Interview takeaway:** Function pointers implement callbacks and runtime dispatch without hardcoding the callee. Calling through an incompatible function pointer type is undefined behaviour.

### What is the difference between call by value and call by reference? {E}
C supports **pass by value only**. A function can modify a caller's object by receiving a copy of its pointer, which is commonly described as call by reference.

#### 1. Passing a value

```c
void change(int x)
{
    x = 100;
}

int a = 10;
change(a);
```

After the call, a remains 10 because x is a separate copy.

#### 2. Passing an address

```c
void change(int *p)
{
    *p = 100;
}

int a = 10;
change(&a);
```

After the call, a becomes 100 because p points to a.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 170" width="100%" role="img" aria-label="Passing a copy versus modifying the original object through a copied pointer">
<text x="10" y="16" font-size="12" font-weight="600" fill="currentColor">Pass by value</text><rect x="10" y="26" width="108" height="32" rx="4" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="64" y="46" text-anchor="middle" font-size="12" fill="currentColor">a = 10</text><path d="M118 42 H222 m-5-4 5 4-5 4" stroke="currentColor" fill="none"/><text x="170" y="35" text-anchor="middle" font-size="10" fill="currentColor">copy</text><rect x="222" y="26" width="108" height="32" rx="4" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="276" y="46" text-anchor="middle" font-size="12" fill="currentColor">x = 100</text>
<text x="10" y="91" font-size="12" font-weight="600" fill="currentColor">Pass a pointer value</text><rect x="10" y="101" width="108" height="32" rx="4" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="64" y="121" text-anchor="middle" font-size="12" fill="currentColor">a = 100</text><rect x="222" y="101" width="108" height="32" rx="4" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="276" y="121" text-anchor="middle" font-size="12" fill="currentColor">p = &amp;a</text><path d="M222 117 H118 m5-4 -5 4 5 4" fill="none" stroke="currentColor"/><text x="170" y="110" text-anchor="middle" font-size="10" fill="currentColor">writes via *p</text>
<text x="170" y="153" text-anchor="middle" font-size="10" fill="currentColor">The pointer is copied, but the pointed-to object is shared.</text></svg></div>

#### 3. Modifying the caller's pointer

```c
void assign(int **p, int *target)
{
    *p = target;
}

int a = 10;
int *ptr = NULL;
assign(&ptr, &a);
```

Now ptr points to a. A double pointer is needed here because the object to modify is itself a pointer.

**Interview takeaway:** All C arguments are passed by value. Passing a pointer permits indirect modification of the caller's object; use const-qualified pointees when modification is not intended.

### What is recursion and why is it avoided in embedded code? {E}
Recursion occurs when a function calls itself directly or indirectly. A recursive algorithm must have a terminating base case and make progress toward it.

#### 1. Example

```c
unsigned int fact(unsigned int n)
{
    if (n <= 1)
        return 1;
    return n * fact(n - 1);
}
```

For fact(4), the result is 24.

```text
fact(4)
  4 * fact(3)
      3 * fact(2)
          2 * fact(1)
              returns 1
          returns 2
      returns 6
  returns 24
```

#### 2. Stack usage

Each active function call may require its own stack frame containing saved registers, local variables and return information. Deep recursion can exhaust a small microcontroller or RTOS task stack.

#### 3. Iterative alternative

```c
unsigned int fact(unsigned int n)
{
    unsigned int result = 1;

    while (n > 1)
        result *= n--;

    return result;
}
```

The iterative version avoids growing the call depth. Both versions need an input bound to avoid unwanted arithmetic overflow.

#### 4. Why embedded projects often restrict recursion

Limited stack memory, worst-case execution-time analysis, and safety requirements make unbounded recursion particularly undesirable. Some compilers optimize certain tail-recursive functions, but the C language does not guarantee this optimization.

**Interview takeaway:** Recursion is not inherently incorrect in firmware, but its maximum depth and timing must be bounded. Prefer iteration when it simplifies resource analysis.

### What are the stages of compilation in C? {E}
A typical C toolchain converts source files into an executable or firmware image in four stages: **preprocessing, compilation, assembly and linking**.

<div style="max-width:580px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 300" width="100%" role="img" aria-label="C compilation stages from source to ELF executable" font-family="system-ui,sans-serif"><rect x="25" y="5" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="22" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Source code (.c)</text><text x="170" y="37" text-anchor="middle" font-size="10" fill="currentColor">C statements and preprocessor directives</text><path d="M170 48 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="65" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="82" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Preprocessor (.i)</text><text x="170" y="97" text-anchor="middle" font-size="10" fill="currentColor">Expands macros and includes headers</text><path d="M170 108 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="125" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="142" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Compiler (.s)</text><text x="170" y="157" text-anchor="middle" font-size="10" fill="currentColor">Checks C and generates assembly</text><path d="M170 168 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="185" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="202" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Assembler (.o)</text><text x="170" y="217" text-anchor="middle" font-size="10" fill="currentColor">Produces machine code and relocation information</text><path d="M170 228 v17 m-4-5 4 5 4-5" fill="none" stroke="currentColor"/><rect x="25" y="245" width="290" height="43" rx="6" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="262" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">Linker (.elf)</text><text x="170" y="277" text-anchor="middle" font-size="10" fill="currentColor">Resolves symbols and places sections</text></svg></div>

#### 1. Preprocessing

```sh
gcc -E main.c -o main.i
```

Processes #include, #define and conditional directives.

#### 2. Compilation

```sh
gcc -S main.i -o main.s
```

Parses and checks C code, optimizes it and generates target assembly.

#### 3. Assembly

```sh
gcc -c main.s -o main.o
```

Converts assembly to an object file containing machine instructions, sections, symbols and relocation records.

#### 4. Linking

```sh
gcc main.o -o main
```

Combines object files and libraries, resolves external references and produces an executable.

#### 5. Embedded firmware example

For an appropriate ARM bare-metal target, a typical build uses arm-none-eabi-gcc, a linker script, startup objects and target-specific flags. An ELF image can subsequently be converted into a raw binary:

```sh
arm-none-eabi-objcopy -O binary firmware.elf firmware.bin
```

The linker script determines addresses for sections such as .text, .data and .bss. Startup code prepares RAM before calling main.

**Interview takeaway:** The preprocessor expands source, compiler generates assembly, assembler generates objects and linker resolves symbols. Actual toolchains may combine stages or use link-time optimization.

### What is the difference between a .bss and a .data section? {E}
Both sections typically store writable objects with static storage duration. The **.data** section contains initialized values, while **.bss** represents objects that must start at zero.

#### 1. Example

```c
int global_count = 10; // Usually .data
int global_flag;       // Usually .bss
static int state = 0;  // Usually .bss
```

These objects exist throughout program execution. Automatic local variables normally use registers or stack instead.

#### 2. How startup works on a microcontroller

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 154" width="100%" role="img" aria-label="Startup copies initial data from flash to RAM and zeroes BSS">
<text x="68" y="18" font-size="12" font-weight="600" fill="currentColor" text-anchor="middle">Flash</text><text x="268" y="18" font-size="12" font-weight="600" fill="currentColor" text-anchor="middle">RAM</text>
<rect x="10" y="30" width="116" height="42" rx="5" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="68" y="55" font-size="11" fill="currentColor" text-anchor="middle">Initial count = 10</text>
<rect x="206" y="30" width="124" height="42" rx="5" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="268" y="55" font-size="11" fill="currentColor" text-anchor="middle">.data: count = 10</text>
<path d="M126 51 H206 m-6 -5 l6 5 -6 5" stroke="currentColor" fill="none"/><text x="166" y="43" font-size="10" fill="currentColor" text-anchor="middle">Copy</text>
<rect x="10" y="92" width="116" height="42" rx="5" stroke="currentColor" stroke-opacity=".4" fill="none"/><text x="68" y="117" font-size="11" fill="currentColor" text-anchor="middle">Startup code</text>
<rect x="206" y="92" width="124" height="42" rx="5" fill="#eab308" fill-opacity=".15" stroke="#ca8a04"/><text x="268" y="117" font-size="11" fill="currentColor" text-anchor="middle">.bss: flag = 0</text>
<path d="M126 113 H206 m-6 -5 l6 5 -6 5" stroke="currentColor" fill="none"/><text x="166" y="105" font-size="10" fill="currentColor" text-anchor="middle">Clear</text>
</svg></div>

1. Startup code copies the initial .data image from flash into RAM.
2. It clears the .bss region in RAM.
3. It calls the C runtime and main according to the platform startup sequence.

On Linux, the executable loader establishes mappings and zero-initialized storage instead.

#### 3. Difference

| Feature | .data | .bss |
|---|---|---|
| Initial values | Typically nonzero | Zero |
| Runtime storage | RAM | RAM |
| Initial image | Stores initial bytes | Normally needs only size information |
| MCU startup | Copy from load address | Clear to zero |

#### 4. Inspect the executable

```sh
size firmware.elf
readelf -S firmware.elf
```

These commands help inspect section sizes and placement.

**Interview takeaway:** .bss saves initial image space because it does not normally store every zero byte. Both sections consume RAM at runtime; exact placement depends on the linker script and toolchain.

### What is a dangling pointer, a wild pointer and a NULL pointer? {E}
These terms describe three different pointer states. Dereferencing any of them is invalid unless the pointer has been set to refer to a valid object.

#### 1. Wild pointer

An uninitialized automatic pointer is commonly called a wild pointer.

```c
int *p;
// *p = 10;   // Undefined behaviour
```

Initialize it before use:

```c
int a = 10;
int *p = &a;
```

#### 2. Dangling pointer

A dangling pointer refers to storage whose object's lifetime has ended.

```c
int *p = malloc(sizeof *p);
if (p != NULL) {
    *p = 10;
    free(p);
    // *p = 20;  // Use-after-free
    p = NULL;
}
```

Returning the address of an automatic local variable also creates a lifetime problem.

#### 3. NULL pointer

A null pointer intentionally refers to no object or function.

```c
int *p = NULL;

if (p != NULL)
    printf("%d", *p);
```

Checking for NULL is useful, but it does not establish that a non-null pointer is valid.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 185" width="100%" role="img" aria-label="Wild pointer is uninitialized; dangling pointer refers to expired storage; null pointer refers to no object">
<text x="10" y="18" font-size="11" font-weight="600" fill="currentColor">Wild pointer</text><rect x="10" y="25" width="100" height="30" rx="4" fill="#dc2626" fill-opacity=".1" stroke="#dc2626"/><text x="60" y="44" text-anchor="middle" font-size="12" fill="currentColor">p = ?</text><path d="M110 40 H218 m-5-4 5 4-5 4" stroke="#dc2626" stroke-dasharray="4 3" fill="none"/><rect x="218" y="25" width="112" height="30" rx="4" fill="#dc2626" fill-opacity=".1" stroke="#dc2626"/><text x="274" y="44" text-anchor="middle" font-size="11" fill="currentColor">Unknown target</text><text x="10" y="76" font-size="11" font-weight="600" fill="currentColor">Dangling pointer</text><rect x="10" y="83" width="100" height="30" rx="4" fill="#dc2626" fill-opacity=".1" stroke="#dc2626"/><text x="60" y="102" text-anchor="middle" font-size="12" fill="currentColor">p</text><path d="M110 98 H218 m-5-4 5 4-5 4" stroke="#dc2626" stroke-dasharray="4 3" fill="none"/><rect x="218" y="83" width="112" height="30" rx="4" fill="#dc2626" fill-opacity=".1" stroke="#dc2626"/><text x="274" y="102" text-anchor="middle" font-size="11" fill="currentColor">Expired object</text><text x="10" y="134" font-size="11" font-weight="600" fill="currentColor">NULL pointer</text><rect x="10" y="141" width="100" height="30" rx="4" fill="#64748b" fill-opacity=".1" stroke="#64748b"/><text x="60" y="160" text-anchor="middle" font-size="12" fill="currentColor">p = NULL</text><path d="M110 156 H218 m-5-4 5 4-5 4" stroke="#64748b" stroke-dasharray="4 3" fill="none"/><rect x="218" y="141" width="112" height="30" rx="4" fill="#64748b" fill-opacity=".1" stroke="#64748b"/><text x="274" y="160" text-anchor="middle" font-size="11" fill="currentColor">No object</text>
</svg></div>

| Pointer | Meaning |
|---|---|
| Wild | Uninitialized pointer |
| Dangling | Object lifetime has ended |
| NULL | Intentionally points to no object |

**Interview takeaway:** Initialize pointers, respect object lifetime and manage allocation ownership. Setting one pointer to NULL after free does not repair other aliases to the freed object.

### What is the volatile keyword? {E}
The `volatile` qualifier tells the compiler that accesses through a volatile-qualified lvalue have observable significance. It must perform the required accesses according to the implementation's volatile semantics rather than assuming that the value cannot change externally.

#### 1. Memory-mapped register example

```c
#include <stdint.h>

#define STATUS (*(volatile uint32_t *)0x40000000U)
#define READY  (1U << 0)

while ((STATUS & READY) == 0) {
    // Wait for hardware.
}
```

Assuming this is a valid status-register address and access width for the target, every evaluation of STATUS requires a volatile read. Hardware can change the value independently of the running code.

Without volatile, the compiler may reuse an earlier read or transform the polling loop in a way that does not observe external changes.

#### 2. Interrupt-shared flag

```c
static volatile unsigned int done;

void Timer_IRQHandler(void)
{
    // Acknowledge the timer according to its specification.
    done = 1;
}

void wait_for_timer(void)
{
    while (done == 0) {
    }
}
```

This is a simple bare-metal example for a target supporting indivisible accesses to this flag and the required interrupt semantics. More complex sharing needs synchronization. Real polling code should usually have a timeout.

#### 3. What volatile does not guarantee

| Property | Guaranteed by volatile? |
|---|---|
| Required volatile accesses | Yes, under implementation rules |
| Atomic read-modify-write | No |
| Thread synchronization | No |
| CPU memory barriers | No |
| DMA cache coherency | No |

For example, `volatile int count; count++;` is not guaranteed atomic.

#### 4. Linux drivers

Use kernel MMIO accessors such as readl and writel for mapped registers, and use kernel synchronization APIs for shared memory instead of relying on volatile.

**Interview takeaway:** Volatile is primarily about compiler-visible accesses, not concurrency. Use the correct platform MMIO, atomic, barrier or DMA API for the actual requirement.

### Can a variable be both const and volatile? What is the difference between them? {M}
Yes. The `const` and `volatile` qualifiers serve different purposes and can be combined.

- **const:** Prevents modification through the qualified lvalue.
- **volatile:** Preserves required accesses when an object can be affected by external events.

#### 1. Read-only hardware register

```c
#include <stdint.h>

const volatile uint32_t *status =
    (const volatile uint32_t *)0x40000000U;

uint32_t value = *status;  // Allowed
// *status = 10;           // Invalid
```

Assuming the address is valid on the target, hardware can update the register, but the application cannot write through status. Every evaluation of *status requires the appropriate volatile access.

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 150" width="100%" role="img" aria-label="Hardware updates a status register, software can read but not write through a const volatile pointer">
<rect x="5" y="8" width="105" height="33" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="57.5" y="29" font-size="11" text-anchor="middle" fill="currentColor">Hardware</text>
<rect x="220" y="8" width="115" height="33" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="277.5" y="29" font-size="11" text-anchor="middle" fill="currentColor">Status register</text>
<path d="M110 24 H220 m-5-4 5 4-5 4" stroke="#16a34a" fill="none"/><text x="165" y="17" font-size="10" text-anchor="middle" fill="currentColor">Updates</text>
<rect x="5" y="104" width="105" height="33" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="57.5" y="125" font-size="11" text-anchor="middle" fill="currentColor">Software / CPU</text>
<path d="M277 41 V68 H57 V104 m-4-5 4 5 4-5" stroke="#16a34a" fill="none"/><text x="167" y="62" font-size="10" text-anchor="middle" fill="currentColor">Read allowed</text>
<path d="M110 120 H277 V85" stroke="#dc2626" stroke-dasharray="4 3" fill="none"/><path d="M270 78 l14 14 m0-14 l-14 14" stroke="#dc2626" stroke-width="2"/><text x="188" y="114" font-size="10" text-anchor="middle" fill="#dc2626">Write forbidden via pointer</text>
</svg></div>

#### 2. Fixed register address

```c
const volatile uint32_t *const status =
    (const volatile uint32_t *)0x40000000U;
```

The additional const after the asterisk prevents changing the pointer itself.

#### 3. Comparison

| Declaration | Software write through lvalue | Required volatile reads |
|---|---|---|
| int x | Allowed | No |
| const int x | Not allowed | No |
| volatile int x | Allowed | Yes |
| const volatile int x | Not allowed | Yes |

**Interview takeaway:** Const means read-only through a particular qualified access, not necessarily that the underlying value can never change. Const volatile is commonly used for read-only MMIO status registers.

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
