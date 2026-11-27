---
slug: c-programming
title: C Programming
icon: 🧩
level: Beginner
order: 1
desc: Keywords, storage classes, scope, the preprocessor, integer rules, undefined behaviour and the questions every C interview starts with.
---
Concise C interview notes with language rules, practical examples and original illustrations. Examples are fragments unless a complete function is shown; include appropriate standard headers and validate target assumptions.

### What are the storage classes in C? {E}
**Short answer:** Storage-class specifiers affect storage duration and linkage; scope depends on the declaration's position.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Automatic: block lifetime|Static: program lifetime|Thread: thread lifetime" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Automatic: block lifetime</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Static: program lifetime</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Thread: thread lifetime</text></svg></div>

**How it works**

1. An ordinary local has automatic duration.
2. Static locals retain state.
3. File-scope static gives internal linkage.
4. Extern usually declares an entity defined elsewhere; _Thread_local gives thread duration (C11).

**Example**

```c
static int count; // persists
extern int baud; // declaration
```

**Interview takeaway:** typedef is grammatically a storage-class specifier but creates an alias, not storage.

### What does the static keyword do in different contexts? {E}
**Short answer:** static preserves a local object's lifetime across calls or limits a file-scope name to one translation unit.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Call 1: 1|Call 2: 2|Call 3: 3" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Call 1: 1</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Call 2: 2</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Call 3: 3</text></svg></div>

**How it works**

1. A static local is initialized before program startup in C.
2. Its value persists.
3. A file-scope static function or object has internal linkage.

**Example**

```c
int next(void) {
    static int n = 0;
    return ++n;
} // 1, 2, 3
```

**Interview takeaway:** Mutable shared static state needs synchronization; static does not inherently mean read-only.

### What is the difference between declaration and definition? {E}
**Short answer:** A declaration introduces a name and type; a definition supplies the object or function body.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Header: declaration|Source: definition|Linker: resolves" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Header: declaration</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Source: definition</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Linker: resolves</text></svg></div>

**How it works**

1. Put compatible declarations in headers.
2. Define an externally linked used object once.
3. The linker resolves references.

**Example**

```c
extern int speed; // declaration
int speed = 100;  // definition
```

**Interview takeaway:** Every definition is a declaration; a file-scope int x; is a tentative definition.

### What is the use of the extern keyword? {E}
**Short answer:** extern normally declares a name with external linkage or refers to a prior declaration's linkage.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="File A: extern|File B: definition" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">File A: extern</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">File B: definition</text></svg></div>

**How it works**

1. Declare the shared object in a header.
2. Define it in one source file.
3. Include the header wherever needed.

**Example**

```c
// config.h
extern int baud;
// config.c
int baud = 115200;
```

**Interview takeaway:** extern int x = 1; at file scope is a definition, not merely a declaration.

### What is the difference between const and #define? {E}
**Short answer:** const qualifies a type against modification through that lvalue; #define performs preprocessor substitution.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Preprocessor: LIMIT|Compiler: const object" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Preprocessor: LIMIT</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Compiler: const object</text></svg></div>

**How it works**

1. The preprocessor replaces macros before compilation.
2. The compiler type-checks const objects.
3. A macro does not itself allocate storage.

**Example**

```c
#define LIMIT 32
const int limit = 32;
```

**Interview takeaway:** In C, a const int is not generally an integer constant expression; use an enum or macro when needed.

### What does const int *p, int *const p and const int *const p mean? {M}
**Short answer:** const before the pointed-to type protects the target through that pointer; const after * protects the pointer itself.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="const int *: target|int *const: pointer|both const" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">const int *: target</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">int *const: pointer</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">both const</text></svg></div>

**How it works**

1. Read the declaration around *.
2. Check whether reassignment of the pointer is allowed.
3. Check whether writing through it is allowed.

**Example**

```c
int x=1, y=2;
const int *p=&x; // p can change
int *const q=&x; // *q can change
const int *const r=&y; // neither via r
```

**Interview takeaway:** A non-const object can still change through another valid non-const reference.

### What is the difference between a macro and an inline function? {M}
**Short answer:** A macro expands tokens; an inline function is a typed function that the compiler may inline.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Macro: text expansion|Inline: typed call" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Macro: text expansion</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Inline: typed call</text></svg></div>

**How it works**

1. Macros substitute argument expressions wherever used.
2. Function arguments are evaluated once per argument.
3. The compiler decides whether to inline.

**Example**

```c
#define SQUARE(x) ((x)*(x))
static inline int square(int x) { return x*x; }
```

**Interview takeaway:** SQUARE(i++) is undefined due to unsequenced modifications. inline is not a guarantee of inlining.

### Why should macro arguments and bodies be wrapped in parentheses? {E}
**Short answer:** Parentheses protect macro arguments and the replacement expression from unexpected operator precedence.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="1+2 and 3+4|Parenthesized product: 21" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">1+2 and 3+4</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Parenthesized product: 21</text></svg></div>

**How it works**

1. Wrap each parameter use.
2. Wrap the entire expression.
3. Avoid multiple evaluation of arguments with side effects.

**Example**

```c
#define MUL(a,b) ((a)*(b))
// MUL(1+2,3+4) gives 21
```

**Interview takeaway:** Parentheses fix precedence, not side effects or arithmetic overflow.

### Why are multi-line macros wrapped in do { } while(0)? {M}
**Short answer:** do { ... } while (0) makes a multi-statement macro behave syntactically like one statement.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="if (condition)|One macro statement|else branch" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">if (condition)</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">One macro statement</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">else branch</text></svg></div>

**How it works**

1. Place statements inside the block.
2. The loop executes once.
3. The caller adds a semicolon, preserving if/else syntax.

**Example**

```c
#define RESET(a,b) do { (a)=0; (b)=0; } while (0)
```

**Interview takeaway:** Avoid hidden break/continue semantics and repeated evaluation of arguments.

### What are # and ## in macros? {M}
**Short answer:** # stringifies a macro argument; ## pastes tokens into a single preprocessing token.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="# hello → &quot;hello&quot;|## reg + 1 → reg1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12"># hello → &quot;hello&quot;</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">## reg + 1 → reg1</text></svg></div>

**How it works**

1. Stringification produces a string literal.
2. Token pasting combines tokens.
3. Use an extra expansion layer when macro values must expand before these operations.

**Example**

```c
#define STR(x) #x
#define JOIN(a,b) a##b
// STR(hello) -> "hello"
// JOIN(reg,1) -> reg1
```

**Interview takeaway:** Token pasting must yield a valid preprocessing token.

### What is the difference between #include <file> and #include "file"? {E}
**Short answer:** Quoted includes and angle-bracket includes use implementation-defined search rules.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Project header search|Configured include paths" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Project header search</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Configured include paths</text></svg></div>

**How it works**

1. Quoted includes commonly search relative to the including source first.
2. Angle includes commonly search configured include directories.
3. Compilers may fall back between paths.

**Example**

```c
#include "board.h"
#include <stdint.h>
```

**Interview takeaway:** Exact search order depends on compiler options; do not assume angle brackets mean only system headers.

### What are include guards and #pragma once? {E}
**Short answer:** Include guards prevent repeated processing of a header within one translation unit.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="First include: process|Later include: skip" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">First include: process</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Later include: skip</text></svg></div>

**How it works**

1. Test a unique macro name.
2. Define it when first included.
3. Skip the contents on later includes.

**Example**

```c
#ifndef BOARD_H_INCLUDED
#define BOARD_H_INCLUDED
void board_init(void);
#endif
```

**Interview takeaway:** pragma once is widely supported but not standard C; guards are portable.

### What is the difference between typedef and #define for creating type names? {E}
**Short answer:** typedef creates a type alias understood by the compiler; a macro replaces tokens.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="typedef: type alias|macro: token replacement" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">typedef: type alias</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">macro: token replacement</text></svg></div>

**How it works**

1. A typedef participates in declarator rules.
2. A macro simply expands wherever its name appears.

**Example**

```c
typedef int *IntPtr;
IntPtr a,b; // both pointers
#define PTR int *
PTR c,d; // c pointer, d int
```

**Interview takeaway:** typedef does not create a distinct new type in C.

### What is undefined behaviour? Give examples. {M}
**Short answer:** Undefined behavior means the C standard places no requirements on the program's behavior for that operation.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Invalid operation|No guaranteed outcome" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Invalid operation</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">No guaranteed outcome</text></svg></div>

**How it works**

1. Examples include signed overflow, invalid pointer dereference and out-of-bounds access.
2. The optimizer may assume such operations never occur.
3. Validate preconditions instead.

**Example**

```c
int a[2]={0};
// a[2]=1; // undefined
// int x=INT_MAX; ++x; // signed overflow
```

**Interview takeaway:** A program that appears to work in debug mode may fail after optimization.

### What is a sequence point? {H}
**Short answer:** A sequence point is a point where preceding evaluations are complete and later evaluations have not begun; modern C also describes sequenced-before relations.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="First full expression|Sequence boundary|Next expression" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">First full expression</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Sequence boundary</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Next expression</text></svg></div>

**How it works**

1. Separate statements sequence their full expressions; && and || sequence their operands when the second is evaluated.
2. Unsequenced conflicting accesses to the same scalar can be undefined.

**Example**

```c
int i=0;
i++; i++; // defined
// i = i++ + 1; // undefined in C
```

**Interview takeaway:** Function argument evaluation order is generally unspecified; do not rely on it.

### What is the size of an int, and what are fixed-width types? {E}
**Short answer:** The size of int is implementation-defined subject to standard minimum ranges; fixed-width typedefs express exact widths when provided.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="16-bit int possible|32-bit int common|uint32_t: exactly 32 bits" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">16-bit int possible</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">32-bit int common</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">uint32_t: exactly 32 bits</text></svg></div>

**How it works**

1. Inspect sizeof and CHAR_BIT.
2. Use uint32_t for exactly 32 unsigned bits when available.
3. Choose size_t for object sizes.

**Example**

```c
#include <stdint.h>
uint32_t reg_value = 0;
// sizeof(int) depends on target
```

**Interview takeaway:** Use inttypes.h format macros for fixed-width values where needed.

### Is char signed or unsigned, and why does it matter? {M}
**Short answer:** Plain char may be signed or unsigned depending on the implementation.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="0xFF: signed often -1|0xFF: unsigned 255" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">0xFF: signed often -1</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">0xFF: unsigned 255</text></svg></div>

**How it works**

1. Use char for text.
2. Signed char or unsigned char when signedness matters.
3. Cast byte values before indexing or calling ctype functions.

**Example**

```c
unsigned char byte = 0xff;
// value is 255 on 8-bit-byte targets
```

**Interview takeaway:** Never assume plain char is unsigned. CHAR_BIT need not be 8.

### What is integer promotion? {M}
**Short answer:** Integer promotions convert small integer types to int if it can represent their values, otherwise to unsigned int.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="8-bit operands|Promoted arithmetic|Conversion on assignment" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">8-bit operands</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Promoted arithmetic</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Conversion on assignment</text></svg></div>

**How it works**

1. Promotions happen before many arithmetic and bitwise operations.
2. The operation uses the promoted type.
3. Assignment converts the result back.

**Example**

```c
uint8_t a=250,b=10;
int sum=a+b; // 260 on usual targets
uint8_t wrap=(uint8_t)sum; // 4
```

**Interview takeaway:** Use unsigned types of the intended width for bit operations; inspect promotion effects.

### What happens when you compare signed and unsigned integers? {M}
**Short answer:** Mixed signed/unsigned expressions follow usual arithmetic conversions, which can turn a negative value into a large unsigned one.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="-1 signed|Converted to UINT_MAX|Compare with 1" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">-1 signed</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Converted to UINT_MAX</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Compare with 1</text></svg></div>

**How it works**

1. Determine operand ranks and representable ranges.
2. Convert to the common type.
3. Compare the converted values.

**Example**

```c
int a=-1;
unsigned int b=1;
// a < b is false
```

**Interview takeaway:** Check for negativity before converting to an unsigned size or index.

### What is the difference between ++i and i++? {E}
**Short answer:** Prefix increment produces the incremented value; postfix produces the previous value while also incrementing the object.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Prefix: increment then value|Postfix: old value then update" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Prefix: increment then value</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Postfix: old value then update</text></svg></div>

**How it works**

1. Evaluate the expression.
2. Update the object.
3. Use the prefix or postfix result as required.

**Example**

```c
int i=3;
int a=++i; // a=4,i=4
int b=i++; // b=4,i=5
```

**Interview takeaway:** As standalone statements both increment once; avoid multiple unsequenced modifications.

### What is the difference between a structure and a union? {E}
**Short answer:** A struct stores separate members; a union overlays members in shared storage.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Struct: A | B|Union: overlapping A/B" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Struct: A</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">B</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Union: overlapping A/B</text></svg></div>

**How it works**

1. Struct members occupy distinct regions with possible padding.
2. Union members start at the same address.
3. The union is large and aligned enough for its members.

**Example**

```c
struct pair { int a,b; };
union word { uint32_t n; unsigned char bytes[4]; };
```

**Interview takeaway:** Union representation reinterpretation is implementation-sensitive and may produce invalid representations; use explicit conversions for protocols.

### What is structure padding and how do you avoid it? {M}
**Short answer:** Padding is unused space inserted to meet member and overall structure alignment.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="a + padding|b: 4 bytes|c + tail padding" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">a + padding</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">b: 4 bytes</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">c + tail padding</text></svg></div>

**How it works**

1. Lay out members at suitably aligned offsets.
2. Round structure size for array alignment.
3. Reorder members to reduce holes where appropriate.

**Example**

```c
struct s { char a; int b; char c; };
// Typical 4-byte int ABI: size 12, not 6.
```

**Interview takeaway:** Do not assume layout across compilers. Packed accesses can be unaligned; serialize fields explicitly.

### What are bit-fields and what are their drawbacks? {M}
**Short answer:** Bit-fields store members with specified bit widths inside implementation-defined allocation units.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="ready: 1 bit|mode: 3 bits|implementation layout" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">ready: 1 bit</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">mode: 3 bits</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">implementation layout</text></svg></div>

**How it works**

1. Declare widths.
2. The compiler selects layout and access strategy.
3. Reads and writes may use a whole-unit read-modify-write.

**Example**

```c
struct flags { unsigned ready:1; unsigned mode:3; };
```

**Interview takeaway:** Bit-field order, packing and access width are not portable; masks are usually safer for MMIO.

### What is an enum and how big is it? {E}
**Short answer:** An enum defines named integer constants and an enumerated type whose representation depends on language version and implementation.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="IDLE: 0|RUN: 1|ERROR: 2" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">IDLE: 0</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">RUN: 1</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">ERROR: 2</text></svg></div>

**How it works**

1. Assign explicit or automatic values.
2. Use names for state and configuration.
3. Check sizeof when ABI matters.

**Example**

```c
enum state { IDLE, RUN, ERROR };
enum state s=IDLE;
```

**Interview takeaway:** Do not assume sizeof(enum) equals sizeof(int), especially with compiler options or C23 fixed underlying types.

### What is the difference between malloc, calloc, realloc and free? {E}
**Short answer:** malloc allocates uninitialized storage, calloc allocates zeroed bytes, realloc changes allocation size, and free releases it.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Allocate|Resize if needed|Free" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Allocate</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Resize if needed</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Free</text></svg></div>

**How it works**

1. Check allocation results.
2. Use a temporary pointer for realloc.
3. Free only valid allocated pointers once.

**Example**

```c
int *p=calloc(4,sizeof *p);
if (p) {
    int *q=realloc(p,8*sizeof *p);
    if (q) p=q;
    free(p);
}
```

**Interview takeaway:** calloc zeroes bytes, not necessarily all typed representations; avoid realloc(p,0) portability issues.

### What is the difference between strcpy, strncpy and memcpy? {M}
**Short answer:** strcpy copies a terminated string; strncpy copies/pads up to n characters; memcpy copies exactly n bytes.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="String copy: includes NUL|Byte copy: exact length" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">String copy: includes NUL</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Byte copy: exact length</text></svg></div>

**How it works**

1. Determine source and destination bounds.
2. Ensure termination for strings.
3. Use memmove instead of memcpy for overlap.

**Example**

```c
char dst[8];
// source is a valid string of length <= 7:
strcpy(dst,"hello");
memcpy(dst,"OK",3);
```

**Interview takeaway:** strncpy may omit the terminator when source length is at least n; it is not a universal safe strcpy.

### What is the difference between an array and a pointer? {M}
**Short answer:** An array is an object containing consecutive elements; a pointer is a separate object that can refer to an element.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Array: 1 2 3 4|Pointer: address of a[0]" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Array: 1 2 3 4</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Pointer: address of a[0]</text></svg></div>

**How it works**

1. Array expressions usually decay to pointers.
2. Sizeof on an actual array measures all elements.
3. Pointer arithmetic follows the element type.

**Example**

```c
int a[4]={1,2,3,4};
int *p=a;
// sizeof a == 4*sizeof(int)
```

**Interview takeaway:** Arrays cannot be assigned as whole objects; a pointer does not carry an array length.

### What is a function pointer and where is it used? {M}
**Short answer:** A function pointer holds a callable function reference with a compatible signature.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Caller|Function pointer|Callback" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Caller</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Function pointer</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Callback</text></svg></div>

**How it works**

1. Declare the signature.
2. Assign a matching function.
3. Invoke it through the pointer.
4. Use it for callbacks or dispatch.

**Example**

```c
int add(int a,int b){return a+b;}
int (*op)(int,int)=add;
// op(2,3) returns 5
```

**Interview takeaway:** Calling through an incompatible function pointer type is undefined.

### What is the difference between call by value and call by reference? {E}
**Short answer:** C passes every argument by value. Passing a pointer value lets the callee modify the pointed-to object.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Caller x|Copied pointer|Write through pointer" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Caller x</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Copied pointer</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Write through pointer</text></svg></div>

**How it works**

1. A normal parameter is a copy.
2. Pass &object to share access.
3. Dereference inside the function.

**Example**

```c
void set(int *p){*p=10;}
int x=0;
// set(&x); // x=10
```

**Interview takeaway:** To change the caller's pointer itself, pass a pointer to that pointer.

### What is recursion and why is it avoided in embedded code? {E}
**Short answer:** Recursion is a function calling itself, directly or indirectly.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="fact(3)|fact(2)|fact(1)" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">fact(3)</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">fact(2)</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">fact(1)</text></svg></div>

**How it works**

1. Define a base case.
2. Reduce the problem at each call.
3. Each active invocation may require a stack frame.

**Example**

```c
unsigned fact(unsigned n){
    return n<=1 ? 1 : n*fact(n-1);
}
```

**Interview takeaway:** Limit input for stack and arithmetic bounds; iterative algorithms often have more predictable stack usage.

### What are the stages of compilation in C? {E}
**Short answer:** A typical C toolchain preprocesses, compiles, assembles and links source into an executable or firmware image.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Source|Preprocessor|Compiler / assembler|Linker" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="156" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="88" y="45" fill="#0c4a6e" font-size="12">Source</text><rect x="178" y="8" width="156" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="256" y="45" fill="#0c4a6e" font-size="12">Preprocessor</text><rect x="346" y="8" width="156" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="424" y="45" fill="#0c4a6e" font-size="12">Compiler / assembler</text><rect x="514" y="8" width="156" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="592" y="45" fill="#0c4a6e" font-size="12">Linker</text></svg></div>

**How it works**

1. Expand includes and macros.
2. Translate C to machine instructions via compiler/assembler.
3. Resolve symbols and place sections at link time.

**Example**

```sh
gcc -E main.c -o main.i
gcc -S main.i -o main.s
gcc -c main.s -o main.o
gcc main.o -o main
```

**Interview takeaway:** A linker script controls embedded section addresses; an ELF can be converted to a flashable binary.

### What is the difference between a .bss and a .data section? {E}
**Short answer:** .data normally contains initialized writable static objects; .bss reserves zero-initialized static storage.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Flash: initial data|RAM: .data copy|RAM: .bss zero" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Flash: initial data</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">RAM: .data copy</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">RAM: .bss zero</text></svg></div>

**How it works**

1. The linker records section locations.
2. Startup copies initial .data values from load storage to RAM when required.
3. Startup clears .bss before C code runs.

**Example**

```c
static int counter=5; // usually .data
static int flags;     // usually .bss
```

**Interview takeaway:** Actual section names and placement are toolchain-specific; explicit zero may also be placed in .bss.

### What is a dangling pointer, a wild pointer and a NULL pointer? {E}
**Short answer:** A dangling pointer refers to an object whose lifetime ended; a wild pointer is uninitialized; a null pointer intentionally refers to no object.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Wild: unknown|Dangling: expired|NULL: no object" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Wild: unknown</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Dangling: expired</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">NULL: no object</text></svg></div>

**How it works**

1. Initialize pointers.
2. Check allocations.
3. Avoid use after free or scope exit.
4. Clear a pointer when useful after releasing ownership.

**Example**

```c
int *p=malloc(sizeof *p);
if(p){free(p);p=NULL;}
```

**Interview takeaway:** Clearing one pointer does not repair other aliases to the released object.

### What is the volatile keyword? {E}
**Short answer:** volatile tells the compiler that accesses through a qualified lvalue have observable significance under implementation rules.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="CPU access|Volatile register|Hardware state" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">CPU access</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Volatile register</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Hardware state</text></svg></div>

**How it works**

1. Use it for appropriate MMIO and platform-defined interrupt flags.
2. Perform the actual required accesses.
3. Use locks/atomics for thread communication.

**Example**

```c
#define STATUS (*(volatile uint32_t *)0x40000000u)
// Read only if this address is valid on the target.
```

**Interview takeaway:** Volatile does not guarantee atomicity, cache coherency or ordering of ordinary memory.

### Can a variable be both const and volatile? What is the difference between them? {M}
**Short answer:** const volatile permits observation of externally changing data while preventing writes through that qualified lvalue.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Hardware updates|CPU reads|CPU writes disallowed" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Hardware updates</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">CPU reads</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">CPU writes disallowed</text></svg></div>

**How it works**

1. Const restricts modification through the lvalue.
2. Volatile preserves required observable accesses.
3. Hardware can still change the register.

**Example**

```c
const volatile uint32_t *status =
    (const volatile uint32_t *)0x40000000u;
```

**Interview takeaway:** Typical example is a read-only status register. Valid address and access width are platform-specific.

### What does the restrict keyword mean? {H}
**Short answer:** restrict expresses an access association that lets the compiler assume certain accesses to modified objects do not alias during the block execution.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Source region|Separate destination region" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Source region</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Separate destination region</text></svg></div>

**How it works**

1. Use it only when the caller satisfies its aliasing contract.
2. Optimize independent accesses.
3. Violations can cause undefined behavior.

**Example**

```c
void copy(int *restrict d,const int *restrict s,size_t n){
    for(size_t i=0;i<n;i++)d[i]=s[i];
}
```

**Interview takeaway:** This copy contract requires non-overlapping accessed regions; restrict is not a runtime check.

### What is the difference between exit() and return from main? {E}
**Short answer:** Returning from main in a hosted C program is equivalent to calling exit with the returned status; exit can terminate from other functions.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="main return|Normal termination|Exit status" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">main return</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Normal termination</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Exit status</text></svg></div>

**How it works**

1. Normal exit invokes registered atexit handlers and flushes/closes streams as specified.
2. Returning from another function only returns to its caller.

**Example**

```c
int main(void){ return 0; }
// equivalent normal termination: exit(0);
```

**Interview takeaway:** Bare-metal startup may define different behavior after main returns; _Exit and abort have different cleanup semantics.

### How do variadic functions work? {M}
**Short answer:** Variadic functions accept a variable number of arguments using stdarg.h.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Count / format|va_list|Read promoted arguments" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Count / format</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">va_list</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Read promoted arguments</text></svg></div>

**How it works**

1. Use va_start with the last named parameter in pre-C23 style.
2. Retrieve promoted argument types using va_arg.
3. Finish with va_end.

**Example**

```c
#include <stdarg.h>
int sum(int n,...){
    va_list ap; va_start(ap,n);
    int s=0;
    for(int i=0;i<n;i++)s+=va_arg(ap,int);
    va_end(ap);return s;
}
```

**Interview takeaway:** The caller and function must agree on argument count and types; float promotes to double.

### What is conditional compilation, and how is it used in embedded projects? {E}
**Short answer:** Conditional compilation includes or excludes source before compilation based on preprocessor conditions.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Board selection|Preprocessor|Selected source" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="116" y="45" fill="#0c4a6e" font-size="12">Board selection</text><rect x="234" y="8" width="212" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="340" y="45" fill="#0c4a6e" font-size="12">Preprocessor</text><rect x="458" y="8" width="212" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="564" y="45" fill="#0c4a6e" font-size="12">Selected source</text></svg></div>

**How it works**

1. Define configuration macros in build settings or headers.
2. Select code using #if.
3. Compile and test each supported configuration.

**Example**

```c
#if defined(BOARD_A)
#define LED_PIN 3
#else
#define LED_PIN 7
#endif
```

**Interview takeaway:** Unlike a runtime if, excluded code is not compiled; configuration combinations still need testing.

### What is _Static_assert and why is it useful? {M}
**Short answer:** _Static_assert checks a constant condition at compile time, failing compilation when false.

<div style="max-width:680px;margin:14px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 84" width="100%" role="img" aria-label="Compile-time condition|Pass or diagnostic" font-family="system-ui,sans-serif" text-anchor="middle"><rect x="10" y="8" width="324" height="66" rx="7" fill="#e0f2fe" stroke="#0369a1"/><text x="172" y="45" fill="#0c4a6e" font-size="12">Compile-time condition</text><rect x="346" y="8" width="324" height="66" rx="7" fill="#dcfce7" stroke="#0369a1"/><text x="508" y="45" fill="#0c4a6e" font-size="12">Pass or diagnostic</text></svg></div>

**How it works**

1. Express a required ABI, size or configuration invariant.
2. Give a diagnostic message.
3. Fix the violation before running firmware.

**Example**

```c
#include <stdint.h>
_Static_assert(sizeof(uint32_t)==4,"requires 8-bit bytes");
```

**Interview takeaway:** C11 introduced _Static_assert; C23 also uses static_assert as a keyword. It is not a runtime assertion.

