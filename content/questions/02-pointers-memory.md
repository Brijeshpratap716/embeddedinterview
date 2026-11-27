---
slug: pointers-memory
title: Pointers & Memory
icon: 🎯
level: Beginner
order: 2
desc: Pointer arithmetic, arrays vs pointers, the memory layout of a C program, stack vs heap, memory pools, alignment, endianness and strict aliasing.
---
Pointers are where interviewers separate people who have written C from people who have debugged it. Expect to draw memory on a whiteboard. Each answer gives the short version first, then the explanation, code, and the mistakes interviewers look for.

### What is a pointer? {E}
A pointer is a variable whose value refers to another object or function. Its type tells the compiler how to interpret the pointed-to object.

#### 1. Declaring and dereferencing a pointer

```c
int a = 10;
int *p = &a;

printf("%d", *p); // 10
*p = 20;
printf("%d", a);  // 20
```

- `&a` obtains the address of a.
- `p` stores that address.
- `*p` accesses the object at that address.

#### 2. Memory representation

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 114" width="100%" role="img" aria-label="Pointer at address 0x2004 contains the address 0x2000 of integer a">
<rect x="8" y="23" width="118" height="47" rx="5" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/>
<text x="67" y="40" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">p = 0x2000</text><text x="67" y="57" text-anchor="middle" font-size="11" fill="currentColor">Pointer variable</text>
<rect x="228" y="23" width="104" height="47" rx="5" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/>
<text x="280" y="40" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">a = 20</text><text x="280" y="57" text-anchor="middle" font-size="11" fill="currentColor">Integer object</text>
<path d="M126 47 H228 m-6-4 6 4-6 4" stroke="currentColor" fill="none"/><text x="177" y="40" text-anchor="middle" font-size="10" fill="currentColor">points to</text>
<text x="67" y="85" text-anchor="middle" font-size="10" fill="currentColor">Address 0x2004</text><text x="280" y="85" text-anchor="middle" font-size="10" fill="currentColor">Address 0x2000</text>
<text x="170" y="105" text-anchor="middle" font-size="10" fill="currentColor">Illustrative 32-bit memory addresses</text></svg></div>

#### 3. Pointer size and type

| Expression | Meaning |
|---|---|
| `sizeof(p)` | Size of the pointer itself |
| `sizeof(*p)` | Size of the pointed-to int |
| `p + 1` | Next int element, where valid |
| `p = NULL` | Pointer refers to no object |

Object pointers are commonly 4 bytes on Cortex-M and 8 bytes on AArch64 Linux, but the C language does not require either size or identical representations for all pointer types.

#### 4. Use in embedded systems

Pointers allow hardware register access, passing buffers without copying them, linked lists, callback functions and modifying caller-owned objects.

**Interview takeaway:** A pointer and its target are distinct objects. Never dereference a null, uninitialized, dangling or out-of-bounds pointer.

### How does pointer arithmetic work? {E}
Pointer arithmetic works in **units of the pointed-to type**, not simply bytes. Adding one to an int pointer moves to the next int element.

#### 1. Example

```c
uint32_t a[] = {10, 20, 30, 40};
uint32_t *p = a;

printf("%u", (unsigned)p[2]); // 30
p++;
// p now points to a[1]
```

Assuming four-byte uint32_t objects and an initial address of 0x2000:

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 110" width="100%" role="img" aria-label="Array addresses advance four bytes per uint32_t element">
<rect x="10" y="34" width="80" height="34" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="50" y="55" font-size="13" text-anchor="middle" fill="currentColor">10</text><text x="50" y="82" font-size="10" text-anchor="middle" fill="currentColor">0x2000</text><text x="50" y="98" font-size="10" text-anchor="middle" fill="currentColor">a[0]</text><rect x="90" y="34" width="80" height="34" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="130" y="55" font-size="13" text-anchor="middle" fill="currentColor">20</text><text x="130" y="82" font-size="10" text-anchor="middle" fill="currentColor">0x2004</text><text x="130" y="98" font-size="10" text-anchor="middle" fill="currentColor">a[1]</text><rect x="170" y="34" width="80" height="34" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="210" y="55" font-size="13" text-anchor="middle" fill="currentColor">30</text><text x="210" y="82" font-size="10" text-anchor="middle" fill="currentColor">0x2008</text><text x="210" y="98" font-size="10" text-anchor="middle" fill="currentColor">a[2]</text><rect x="250" y="34" width="80" height="34" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="290" y="55" font-size="13" text-anchor="middle" fill="currentColor">40</text><text x="290" y="82" font-size="10" text-anchor="middle" fill="currentColor">0x200c</text><text x="290" y="98" font-size="10" text-anchor="middle" fill="currentColor">a[3]</text><text x="50" y="12" font-size="11" text-anchor="middle" fill="currentColor">Original p</text><path d="M50 16 V34 m-4-5 4 5 4-5" stroke="#16a34a" fill="none"/><text x="130" y="12" font-size="11" text-anchor="middle" fill="currentColor">p + 1</text><path d="M130 16 V34 m-4-5 4 5 4-5" stroke="#16a34a" fill="none"/></svg></div>

#### 2. Common operations

| Expression (p initially points to a[0]) | Result |
|---|---|
| `p + 2` | Address of a[2] |
| `*(p + 2)` | 30 |
| `a + 4 - p` | 4 elements |
| `a + 4` | One-past-end pointer; cannot dereference |

Pointer subtraction returns ptrdiff_t. Addition and subtraction must remain within the same array or one past its end.

#### 3. Pointer increment and dereference

```c
*p++;     // *(p++): accesses old target, advances p
(*p)++;   // Increments pointed-to value
*++p;     // Advances p, then accesses new target
```

These are separate examples; ensure the resulting pointer and accessed element remain valid.

#### 4. Register offset example

```c
uintptr_t base = 0x40000000U;
volatile uint32_t *reg =
    (volatile uint32_t *)(base + 0x14U);
```

Integer address arithmetic adds the byte offset on the assumed platform. If base were a uint32_t pointer, adding 0x14 would instead advance 20 elements (80 bytes). Use the SoC's documented addresses and MMIO APIs.

**Interview takeaway:** Pointer arithmetic scales by element size. One-past-end is useful for iteration but cannot be dereferenced. Standard C does not support arithmetic on void pointers.

### What is a void pointer? {E}
A `void *` is a generic object pointer. It can carry a pointer to an object of any type, but it does not specify the object's type or size.

#### 1. Basic example

```c
int a = 100;
void *p = &a;

int *q = p;      // Implicit conversion in C
printf("%d", *q); // 100
```

You can also read the value using `*(int *)p`. The actual object must have a compatible type and valid lifetime, and the pointer must satisfy its alignment requirements.

#### 2. Why malloc returns void *

```c
int *buffer = malloc(10 * sizeof *buffer);

if (buffer != NULL) {
    buffer[0] = 42;
    free(buffer);
}
```

The allocator provides storage without knowing which object type the caller will use. A cast from void * is not required in C.

#### 3. Generic callback example

```c
struct Device {
    int id;
};

void callback(void *context)
{
    struct Device *dev = context;
    printf("%d", dev->id);
}
```

A driver or RTOS can pass an instance-specific object as context without changing the callback interface.

#### 4. Limitations

| Operation | Standard C |
|---|---|
| Convert object pointer to void * and back | Allowed |
| Directly dereference void * to read an object | Not allowed |
| Add an integer to void * | Not allowed |
| Convert a function pointer to void * | Not guaranteed portable |

For byte-wise access, use unsigned char *:

```c
unsigned char *bytes = p;
```

This can inspect an object's representation.

**Interview takeaway:** A void pointer provides a generic interface, not runtime type information. The caller and callee must agree on the actual object type, alignment and lifetime.

### What is a double pointer and when do you need one? {M}
A double pointer is a **pointer to another pointer**. It is useful when a function needs to modify the caller's pointer itself.

#### 1. Understanding two levels of indirection

```c
int a = 10;
int *p = &a;
int **pp = &p;

**pp = 50;
```

Now a is 50. The expression *pp accesses p, while **pp accesses a.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 92" width="100%" role="img" aria-label="Double pointer pp points to p, which points to integer a">
<rect x="5" y="15" width="90" height="45" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="50" y="32" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">pp</text><text x="50" y="49" text-anchor="middle" font-size="12" fill="currentColor">&amp;p</text><rect x="125" y="15" width="90" height="45" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="32" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">p</text><text x="170" y="49" text-anchor="middle" font-size="12" fill="currentColor">&amp;a</text><rect x="245" y="15" width="90" height="45" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="290" y="32" text-anchor="middle" font-size="12" font-weight="600" fill="currentColor">a</text><text x="290" y="49" text-anchor="middle" font-size="12" fill="currentColor">50</text><path d="M95 37 H125 m-5-4 5 4-5 4 M215 37 H245 m-5-4 5 4-5 4" stroke="currentColor" fill="none"/><text x="170" y="80" text-anchor="middle" font-size="11" fill="currentColor">*pp is p; **pp is a</text></svg></div>

#### 2. Changing the caller's pointer

```c
void assign(int **p, int *target)
{
    *p = target;
}

int a = 10;
int *ptr = NULL;
assign(&ptr, &a);
```

After the call, ptr points to a. Passing ptr alone would only pass a copy of its pointer value.

#### 3. Linked-list insertion example

```c
struct node {
    int data;
    struct node *next;
};

int insert_front(struct node **head, int value)
{
    struct node *n = malloc(sizeof *n);
    if (!n)
        return -1;

    n->data = value;
    n->next = *head;
    *head = n;
    return 0;
}
```

Call with `insert_front(&head, 10)` after initializing head to NULL. The function updates the caller's list head, including when the list is empty. Release allocated nodes when no longer needed.

**Interview takeaway:** Use a double pointer when the object to modify is itself a pointer. It is common in linked lists, allocation output parameters and APIs returning handles.

### What is the difference between char *s = "hello" and char s[] = "hello"? {M}
The first declaration creates a pointer to a string literal, while the second creates an array containing a copy of the literal.

#### 1. Pointer to a string literal

```c
char *s = "hello";

// s[0] = 'H';  // Undefined behaviour
s = "world";    // Allowed
```

In C, string literals are arrays of char with static storage duration, but modifying them is undefined. They may be placed in read-only memory such as .rodata or flash.

Prefer:

```c
const char *s = "hello";
```

#### 2. Character array

```c
char s[] = "hello";

s[0] = 'H';
printf("%s", s);  // Hello
```

The array has six elements, including the terminating null character. Its elements can be modified.

#### 3. Memory representation

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 148" width="100%" role="img" aria-label="String pointer refers to literal storage, while character array has its own writable copy">
<text x="8" y="13" font-size="11" font-weight="600" fill="currentColor">const char *s = "hello"</text><rect x="8" y="23" width="70" height="30" rx="4" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="43" y="42" font-size="11" text-anchor="middle" fill="currentColor">s</text><path d="M78 38 H126 m-5-4 5 4-5 4" stroke="currentColor" fill="none"/>
<rect x="126" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="143" y="42" font-size="12" text-anchor="middle" fill="currentColor">h</text><rect x="160" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="177" y="42" font-size="12" text-anchor="middle" fill="currentColor">e</text><rect x="194" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="211" y="42" font-size="12" text-anchor="middle" fill="currentColor">l</text><rect x="228" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="245" y="42" font-size="12" text-anchor="middle" fill="currentColor">l</text><rect x="262" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="279" y="42" font-size="12" text-anchor="middle" fill="currentColor">o</text><rect x="296" y="23" width="34" height="30" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="313" y="42" font-size="12" text-anchor="middle" fill="currentColor">\0</text><text x="228" y="66" font-size="10" text-anchor="middle" fill="currentColor">Literal: do not modify</text>
<text x="8" y="91" font-size="11" font-weight="600" fill="currentColor">char s[] = "hello"; s[0] = 'H';</text>
<rect x="68" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="85" y="120" font-size="12" text-anchor="middle" fill="currentColor">H</text><rect x="102" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="119" y="120" font-size="12" text-anchor="middle" fill="currentColor">e</text><rect x="136" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="153" y="120" font-size="12" text-anchor="middle" fill="currentColor">l</text><rect x="170" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="187" y="120" font-size="12" text-anchor="middle" fill="currentColor">l</text><rect x="204" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="221" y="120" font-size="12" text-anchor="middle" fill="currentColor">o</text><rect x="238" y="101" width="34" height="30" fill="#16a34a" fill-opacity=".15" stroke="#16a34a"/><text x="255" y="120" font-size="12" text-anchor="middle" fill="currentColor">\0</text></svg></div>

#### 4. Comparison

| Feature | char *s | char s[] |
|---|---|---|
| Storage | Pointer plus referenced literal | Own character array |
| Modify characters in this example | Undefined behaviour | Allowed |
| Assign another address to s | Allowed | Not allowed |
| sizeof(s) | Pointer size | 6 bytes |

**Interview takeaway:** Use const char * for read-only strings and char arrays for writable string buffers. Array lifetime and location depend on its declaration; a local automatic array is commonly stored on the stack.

### What does int (*p)[10] mean versus int *p[10]? {M}
The parentheses determine whether the declaration describes a pointer to an array or an array containing pointers.

#### 1. Pointer to an array

```c
int a[2][10] = {{0}};
int (*p)[10] = a;

p[1][3] = 50;
```

p points to a row containing ten ints. Adding one to p moves to the next row. On a target with four-byte ints, this is a 40-byte step.

#### 2. Array of pointers

```c
int x = 10, y = 20;
int *p[10] = {&x, &y};

printf("%d", *p[1]); // 20
```

p is an array of ten int pointers. Each pointer can refer to a different object; the remaining initialized elements are null pointers.

#### 3. Memory representation

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 180" width="100%" role="img" aria-label="Pointer to contiguous array row compared with array of pointers to independent integer objects">
<text x="8" y="13" font-size="12" font-weight="600" fill="currentColor">int (*p)[10]</text><rect x="8" y="25" width="50" height="32" rx="4" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="33" y="45" text-anchor="middle" font-size="12" fill="currentColor">p</text><path d="M58 41 H85 m-5-4 5 4-5 4" stroke="currentColor" fill="none"/><rect x="85" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="97" y="45" text-anchor="middle" font-size="10" fill="currentColor">0</text><rect x="109" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="121" y="45" text-anchor="middle" font-size="10" fill="currentColor">1</text><rect x="133" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="145" y="45" text-anchor="middle" font-size="10" fill="currentColor">2</text><rect x="157" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="169" y="45" text-anchor="middle" font-size="10" fill="currentColor">3</text><rect x="181" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="193" y="45" text-anchor="middle" font-size="10" fill="currentColor">4</text><rect x="205" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="217" y="45" text-anchor="middle" font-size="10" fill="currentColor">5</text><rect x="229" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="241" y="45" text-anchor="middle" font-size="10" fill="currentColor">6</text><rect x="253" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="265" y="45" text-anchor="middle" font-size="10" fill="currentColor">7</text><rect x="277" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="289" y="45" text-anchor="middle" font-size="10" fill="currentColor">8</text><rect x="301" y="25" width="24" height="32" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="313" y="45" text-anchor="middle" font-size="10" fill="currentColor">9</text><text x="205" y="71" text-anchor="middle" font-size="10" fill="currentColor">One contiguous row of 10 ints</text>
<text x="8" y="96" font-size="12" font-weight="600" fill="currentColor">int *p[10]</text><rect x="8" y="108" width="76" height="26" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="46" y="125" text-anchor="middle" font-size="11" fill="currentColor">p[0]</text><rect x="84" y="108" width="76" height="26" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="122" y="125" text-anchor="middle" font-size="11" fill="currentColor">p[1]</text><rect x="160" y="108" width="172" height="26" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="246" y="125" text-anchor="middle" font-size="11" fill="currentColor">... p[9]</text><path d="M46 134 V149 M122 134 V149" stroke="currentColor"/><rect x="8" y="149" width="76" height="24" rx="3" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="46" y="165" text-anchor="middle" font-size="11" fill="currentColor">x = 10</text><rect x="84" y="149" width="76" height="24" rx="3" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="122" y="165" text-anchor="middle" font-size="11" fill="currentColor">y = 20</text></svg></div>

#### 4. Comparison

| Declaration | Meaning | sizeof(p) |
|---|---|---|
| int (*p)[10] | One pointer to a ten-int array | Pointer size |
| int *p[10] | Array of ten int pointers | Ten times pointer size |

A pointer to an array is useful for multidimensional image buffers and matrices. An array of pointers is useful for independently allocated rows, lookup tables and lists of strings.

**Interview takeaway:** Array brackets bind more tightly than the pointer declarator unless parentheses change the grouping.

### What is the memory layout of a C program? {E}
A C program typically contains code, read-only data, initialized data, zero-initialized data, heap and stack. The actual layout depends on the executable format, linker script and operating system.

#### 1. Typical memory layout

<div style="max-width:560px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 289" width="100%" role="img" aria-label="Illustrative virtual process layout from low address code to high address stack">
<rect x="45" y="5" width="280" height="35" rx="3" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="55" y="19" font-size="11" font-weight="600" fill="currentColor">Stack</text><text x="55" y="32" font-size="10" fill="currentColor">Automatic objects, saved registers</text><rect x="45" y="45" width="280" height="35" rx="3" fill="#94a3b8" fill-opacity=".13" stroke="#94a3b8"/><text x="55" y="59" font-size="11" font-weight="600" fill="currentColor">Unmapped / mapped regions</text><text x="55" y="72" font-size="10" fill="currentColor">Shared libraries, mmap, guard pages</text><rect x="45" y="85" width="280" height="35" rx="3" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="55" y="99" font-size="11" font-weight="600" fill="currentColor">Heap</text><text x="55" y="112" font-size="10" fill="currentColor">Dynamically allocated storage</text><rect x="45" y="125" width="280" height="35" rx="3" fill="#eab308" fill-opacity=".13" stroke="#eab308"/><text x="55" y="139" font-size="11" font-weight="600" fill="currentColor">.bss</text><text x="55" y="152" font-size="10" fill="currentColor">Zero-initialized static objects</text><rect x="45" y="165" width="280" height="35" rx="3" fill="#f97316" fill-opacity=".13" stroke="#f97316"/><text x="55" y="179" font-size="11" font-weight="600" fill="currentColor">.data</text><text x="55" y="192" font-size="10" fill="currentColor">Initialized writable static objects</text><rect x="45" y="205" width="280" height="35" rx="3" fill="#a855f7" fill-opacity=".13" stroke="#a855f7"/><text x="55" y="219" font-size="11" font-weight="600" fill="currentColor">.rodata</text><text x="55" y="232" font-size="10" fill="currentColor">Read-only data</text><rect x="45" y="245" width="280" height="35" rx="3" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="55" y="259" font-size="11" font-weight="600" fill="currentColor">.text</text><text x="55" y="272" font-size="10" fill="currentColor">Executable instructions</text><text x="38" y="19" font-size="9" text-anchor="end" fill="currentColor">High</text><text x="38" y="277" font-size="9" text-anchor="end" fill="currentColor">Low</text></svg></div>

This is conceptual, not a fixed Linux address map. ASLR, shared libraries, mmap and thread stacks can change the arrangement.

#### 2. C example

```c
int g = 10;                 // Usually .data
int flag;                   // Usually .bss
static const int limit = 5;  // Often .rodata

void fun(void)
{
    int local = 20;         // Stack or register
    static int count;       // Usually .bss
    int *p = malloc(16);    // Allocation from heap
    free(p);
}
```

The pointer p itself is an automatic local object; the allocated storage is separate.

#### 3. What happens on an MCU before main?

1. Startup code establishes the stack and required CPU state.
2. The initialized .data image is copied from flash to RAM.
3. The .bss region is zeroed.
4. Runtime initialization completes and main is called.

Code and read-only data may execute or be read directly from flash if the target supports it. A linker script controls placement.

#### 4. How to inspect it

```sh
size firmware.elf
readelf -S firmware.elf
```

Use a linker map file to locate individual symbols. On Linux, /proc/PID/maps shows process virtual memory mappings.

**Interview takeaway:** Static storage duration is a language property; stack, heap and section placement are implementation details. Do not assume every local variable occupies a stack slot or every constant lives in flash.

### What is the difference between stack and heap? {E}
The stack typically stores function-call state and automatic local variables. The heap provides dynamically allocated storage whose lifetime is controlled by the program.

#### 1. Stack example

```c
void fun(void)
{
    int a = 10;
    int buffer[16];
}
```

These automatic objects normally cease to exist when the function returns. The compiler may keep some values in registers instead of reserving stack space.

#### 2. Heap example

```c
int *create(void)
{
    int *p = malloc(sizeof *p);
    if (p)
        *p = 100;
    return p;
}

// Caller:
int *p = create();
if (p) {
    printf("%d", *p);
    free(p);
}
```

The allocation survives the return from create. The caller must release it when finished.

#### 3. Memory representation

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 165" width="100%" role="img" aria-label="Automatic pointer in a stack frame refers to dynamically allocated object on heap">
<text x="76" y="15" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">Stack</text><text x="264" y="15" font-size="12" font-weight="600" text-anchor="middle" fill="currentColor">Heap</text>
<rect x="8" y="25" width="136" height="115" rx="5" fill="#3b82f6" fill-opacity=".08" stroke="#3b82f6"/><rect x="196" y="25" width="136" height="115" rx="5" fill="#16a34a" fill-opacity=".08" stroke="#16a34a"/>
<rect x="18" y="38" width="116" height="34" rx="3" fill="#3b82f6" fill-opacity=".18" stroke="#3b82f6"/><text x="76" y="59" font-size="12" text-anchor="middle" fill="currentColor">local pointer p</text>
<rect x="206" y="38" width="116" height="34" rx="3" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="264" y="59" font-size="12" text-anchor="middle" fill="currentColor">allocated int: 100</text>
<path d="M134 55 H206 m-5-4 5 4-5 4" fill="none" stroke="currentColor"/><text x="76" y="96" font-size="11" text-anchor="middle" fill="currentColor">Function frame</text><text x="76" y="111" font-size="10" text-anchor="middle" fill="currentColor">Ends on return</text><text x="264" y="96" font-size="11" text-anchor="middle" fill="currentColor">Allocation</text><text x="264" y="111" font-size="10" text-anchor="middle" fill="currentColor">Ends on free</text>
<text x="170" y="155" font-size="10" text-anchor="middle" fill="currentColor">Typical placement, not guaranteed by C.</text></svg></div>

| Feature | Stack | Heap |
|---|---|---|
| Lifetime | Normally automatic | Until released |
| Allocation | Usually frame adjustment | Allocator-managed |
| Failure risk | Stack overflow | Allocation failure, fragmentation |
| Timing | Usually predictable | Depends on allocator |

#### 4. Embedded considerations

RTOS tasks commonly have separate bounded stacks. Large local buffers or deep call chains may overflow them. Heap allocation can introduce variable timing and fragmentation; static allocation or fixed-size pools are often preferred in hard real-time paths.

**Interview takeaway:** Never return the address of an automatic local variable. Heap objects may outlive a function, but ownership and cleanup must be explicit.

### What is a memory leak? {E}
A memory leak occurs when allocated storage is not released after it is no longer required. Repeated leaks reduce available memory and may eventually cause allocation failure.

#### 1. Example of a leak

```c
void fun(void)
{
    int *p = malloc(100 * sizeof *p);

    if (p == NULL)
        return;

    p[0] = 10;
    // Missing free(p)
}
```

The local pointer disappears when fun returns, but the allocation remains reserved. If no other pointer owns it, the program can no longer release it.

#### 2. Correct implementation

```c
void fun(void)
{
    int *p = malloc(100 * sizeof *p);
    if (!p)
        return;

    p[0] = 10;
    free(p);
}
```

A common leak occurs on an error path:

```c
int ret = -1;
char *buf = malloc(256);

if (!buf)
    return -1;

if (read_packet(buf, 256) < 0)
    goto out;

ret = 0;
out:
    free(buf);
    return ret;
```

The shared cleanup path releases the allocation on success and failure.

#### 3. How to detect leaks

- Linux userspace: Valgrind or AddressSanitizer/LeakSanitizer where supported.
- Bare metal and RTOS: track allocation/free counts, outstanding bytes and heap statistics.
- Linux kernel: use kmemleak or relevant tracing/debugging facilities when configured.

A growing heap alone is not proof of a leak; an allocator may retain freed storage for reuse.

**Interview takeaway:** Every successful allocation needs a clear owner and a matching release when no longer needed. A long-running embedded system may fail after hours or days because of a small repeated leak.

### What is heap fragmentation and why does it matter in embedded systems? {M}
Heap fragmentation occurs when memory becomes divided into blocks that cannot efficiently satisfy allocation requests.

#### 1. External fragmentation

Suppose a heap contains six equal 16-byte blocks. After some allocations are released, three separate 16-byte holes remain.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 130" width="100%" role="img" aria-label="Three nonadjacent 16-byte free regions cannot satisfy a contiguous 32-byte request" font-family="system-ui,sans-serif"><text x="8" y="17" font-size="11" font-weight="600" fill="currentColor">Before freeing blocks</text><rect x="8" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="35" y="43" font-size="10" fill="currentColor" text-anchor="middle">A</text><rect x="62" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="89" y="43" font-size="10" fill="currentColor" text-anchor="middle">B</text><rect x="116" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="143" y="43" font-size="10" fill="currentColor" text-anchor="middle">C</text><rect x="170" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="197" y="43" font-size="10" fill="currentColor" text-anchor="middle">D</text><rect x="224" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="251" y="43" font-size="10" fill="currentColor" text-anchor="middle">E</text><rect x="278" y="24" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="305" y="43" font-size="10" fill="currentColor" text-anchor="middle">F</text><text x="8" y="76" font-size="11" font-weight="600" fill="currentColor">After freeing B, D and F</text><rect x="8" y="83" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="35" y="102" font-size="10" fill="currentColor" text-anchor="middle">A</text><rect x="62" y="83" width="54" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="89" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free</text><rect x="116" y="83" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="143" y="102" font-size="10" fill="currentColor" text-anchor="middle">C</text><rect x="170" y="83" width="54" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="197" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free</text><rect x="224" y="83" width="54" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="251" y="102" font-size="10" fill="currentColor" text-anchor="middle">E</text><rect x="278" y="83" width="54" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="305" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free</text></svg></div>

Total free space is 48 bytes, but the largest contiguous free block is only 16 bytes. A 32-byte allocation cannot fit in this simplified heap, even before metadata overhead.

#### 2. Internal fragmentation

An allocator may round a 20-byte request up to a 32-byte block. The unused 12 bytes inside that allocated block cannot serve another allocation.

| Type | Wasted space |
|---|---|
| External | Between allocated blocks |
| Internal | Inside allocated blocks |

#### 3. How to reduce fragmentation

1. Use static allocation for objects with known lifetime and size.
2. Use fixed-size pools for messages or descriptors.
3. Group objects with similar lifetimes.
4. Use an allocator that coalesces adjacent free blocks.
5. Avoid repeated variable-size allocations in timing-critical paths.

Coalescing cannot merge free blocks separated by live allocations.

#### 4. Embedded impact

A firmware system can run out of sufficiently large contiguous heap blocks despite having considerable total free space. Variable allocation/search times can also complicate real-time guarantees.

**Interview takeaway:** Monitor both total free memory and the largest available free block. Fixed-size pools eliminate external fragmentation within that pool, but may still waste space inside slots.

### What is a memory pool, and how do you implement a fixed-size block allocator? {M}
**Short answer:** A memory pool pre-allocates a block of memory divided into equal-sized chunks and keeps the free chunks in a linked list (the "free list"), with the link stored inside each free chunk. Allocation takes the first chunk from the list and freeing pushes it back, both in O(1) with no fragmentation, which makes pools ideal for real-time and embedded systems.

```c
#include <stddef.h>
#include <stdint.h>

#define BLOCK_SIZE  32u
#define BLOCK_COUNT 16u

typedef union block {
    union block *next;                 /* used while the block is free */
    uint8_t data[BLOCK_SIZE];          /* used while it is allocated  */
} block_t;

static block_t pool[BLOCK_COUNT];
static block_t *free_list;

void pool_init(void)
{
    for (size_t i = 0; i < BLOCK_COUNT - 1; i++)
        pool[i].next = &pool[i + 1];
    pool[BLOCK_COUNT - 1].next = NULL;
    free_list = &pool[0];
}

void *pool_alloc(void)
{
    block_t *b = free_list;            /* in an RTOS/ISR context: protect with a critical section */
    if (b) free_list = b->next;
    return b;                          /* NULL when the pool is exhausted */
}

void pool_free(void *p)
{
    if (p == NULL) return;
    block_t *b = p;
    b->next = free_list;
    free_list = b;
}
```

**Why a union:** a free block does not need its data, so its first bytes can hold the `next` pointer, costing no extra memory. The union also makes every block aligned for a pointer.

**Properties**

| | Memory pool | General `malloc` |
|---|---|---|
| Time | O(1), constant | varies with heap state |
| External fragmentation | none | possible |
| Internal fragmentation | yes, if objects are smaller than the block | small (headers, alignment) |
| Sizes | one per pool (use several pools for several sizes) | any |

**Production details**

- **Thread/ISR safety:** wrap alloc/free in a critical section, or use a lock-free stack (watch out for the ABA problem).
- **Debug checks:** fill freed blocks with a pattern, check that a freed pointer is inside the pool and on a block boundary, detect double free with a bitmap.
- **Statistics:** track the minimum number of free blocks ever (high-water mark) to size the pool.
- **Alignment:** if blocks hold types with stricter alignment (e.g. `double`, DMA buffers needing 32-byte alignment), align the pool array and round the block size up.

**Where you see pools:** RTOS memory pools (Zephyr `k_mem_slab`, ThreadX block pools, CMSIS-RTOS `osMemoryPool`), network stacks (lwIP `pbuf` pools, Linux's `kmem_cache` slab allocator), and USB/CAN message buffers.

### How would you implement a simple malloc() and free()? {H}
**Short answer:** Manage a fixed memory region as a list of blocks, each starting with a small header (size and a free flag, or a link to the next free block). `malloc` searches the free list for a block that is big enough (first fit or best fit), splits off the remainder if it is large, marks the block used and returns the address just after the header. `free` marks the block free and **coalesces** it with adjacent free neighbours to fight fragmentation.

```c
#include <stddef.h>
#include <stdint.h>

#define HEAP_SIZE 4096u
#define ALIGN8(x) (((x) + 7u) & ~(size_t)7u)

typedef struct hdr {
    size_t size;              /* payload size in bytes */
    struct hdr *next;         /* next block in address order */
    int free;
} hdr_t;

static _Alignas(8) uint8_t heap[HEAP_SIZE];
static hdr_t *head;

static void heap_init(void)
{
    head = (hdr_t *)heap;
    head->size = HEAP_SIZE - sizeof(hdr_t);
    head->next = NULL;
    head->free = 1;
}

void *my_malloc(size_t n)
{
    if (head == NULL) heap_init();
    if (n == 0) return NULL;
    n = ALIGN8(n);
    for (hdr_t *b = head; b; b = b->next) {
        if (b->free && b->size >= n) {
            if (b->size >= n + sizeof(hdr_t) + 8) {           /* split */
                hdr_t *rest = (hdr_t *)((uint8_t *)(b + 1) + n);
                rest->size = b->size - n - sizeof(hdr_t);
                rest->next = b->next;
                rest->free = 1;
                b->size = n;
                b->next = rest;
            }
            b->free = 0;
            return b + 1;                                      /* memory after the header */
        }
    }
    return NULL;                                               /* out of memory */
}

void my_free(void *p)
{
    if (p == NULL) return;
    hdr_t *b = (hdr_t *)p - 1;
    b->free = 1;
    for (hdr_t *c = head; c; c = c->next) {                   /* coalesce neighbours */
        while (c->free && c->next && c->next->free) {
            c->size += sizeof(hdr_t) + c->next->size;
            c->next = c->next->next;
        }
    }
}
```

**Design points to discuss**

- **Alignment:** every returned pointer must be suitably aligned for any type (8 bytes on Cortex-M with `double`/`uint64_t`; 16 on ARM64/x86-64). The header size must keep payloads aligned (it is 12 bytes on 32-bit here, so add padding or use `_Alignas` on the header in a real allocator).
- **Placement policy:** first fit (fast, fragments the start of the heap), best fit (less wasted space, slower search), next fit, or segregated free lists by size class (what real allocators do).
- **Coalescing:** this version scans the whole list; real allocators use **boundary tags** (a footer with the size) or doubly linked lists to merge in O(1).
- **Thread safety:** a lock around both functions (newlib's `__malloc_lock`, FreeRTOS suspends the scheduler).
- **Safety checks:** detect double free and invalid pointers, add canaries to catch overruns.
- **Determinism:** for real-time code, use TLSF or pools instead, because search time here grows with the number of blocks.

**Where real implementations come from:** newlib/newlib-nano malloc (dlmalloc-based), FreeRTOS `heap_2/4/5`, Zephyr `sys_heap`, TLSF, and the Linux kernel's buddy allocator plus slab caches.

### How do you detect a stack overflow on a microcontroller? {M}
**Short answer:** Combine several techniques: **stack painting** (fill the stack with a known pattern at boot and check how much was overwritten), a **guard region** below the stack using the MPU, **hardware stack limit registers** on Armv8-M (`MSPLIM`/`PSPLIM`), the **RTOS's overflow checks**, and **static worst-case stack analysis** at build time.

**1. Stack painting (high-water mark)**

```c
extern uint32_t _sstack, _estack;          /* from the linker script */
#define STACK_FILL 0xDEADBEEFu

void stack_paint(void)                     /* call very early, before the stack is deep */
{
    uint32_t *p = &_sstack;
    uint32_t *sp = (uint32_t *)__get_MSP();
    while (p < sp - 16) *p++ = STACK_FILL; /* leave a margin below the current SP */
}

size_t stack_unused_bytes(void)
{
    const uint32_t *p = &_sstack;
    while (p < &_estack && *p == STACK_FILL) p++;
    return (size_t)((const uint8_t *)p - (const uint8_t *)&_sstack);
}
```

Report the minimum ever over long tests; keep a safety margin (e.g. 25%).

**2. MPU guard region:** configure a small no-access region just below each stack. An overflow triggers a MemManage fault immediately, at the instruction that overflowed, instead of corrupting other data. FreeRTOS-MPU and Zephyr (`CONFIG_MPU_STACK_GUARD`) do this per thread.

**3. Stack limit registers (Cortex-M23/M33/M55/M85):** set `MSPLIM` and `PSPLIM`; any instruction that moves SP below the limit raises a UsageFault (STKOF). No MPU region needed.

**4. RTOS checks:** FreeRTOS `configCHECK_FOR_STACK_OVERFLOW` = 1 checks the stack pointer at each context switch; = 2 also checks that the last 16 bytes of the stack still contain the fill pattern; `vApplicationStackOverflowHook()` is called on detection. `uxTaskGetStackHighWaterMark()` reports the minimum free stack per task.

**5. Static analysis:** compile with `-fstack-usage` (a `.su` file per source with each function's frame size) and combine with the call graph (`-fcallgraph-info`, puncover, StackAnalyzer) to compute the worst case. Recursion and function pointers break the analysis, which is one reason they are restricted in safety code.

**6. Canaries:** `-fstack-protector-strong` puts a guard value between local buffers and the return address and checks it on return; this detects buffer overruns within a frame (a security feature, not a full overflow detector).

**Symptoms of an undetected overflow:** random variable corruption, HardFaults with nonsense addresses, crashes that depend on interrupt timing, and bugs that disappear when you add a `printf` (which changes stack usage).

### What is alignment and what happens on an unaligned access? {M}
**Short answer:** An object is **aligned** when its address is a multiple of its alignment requirement, which for basic types is usually their size (a `uint32_t` at an address divisible by 4). The compiler aligns variables and adds struct padding automatically. Unaligned accesses usually come from casting byte pointers; depending on the CPU they are slower, need extra instructions, or fault.

**Behaviour by core**

| Core | Unaligned `LDR`/`STR` (word/halfword) | Notes |
|---|---|---|
| Cortex-M0/M0+/M23 (Armv6-M/v8-M baseline) | HardFault | no unaligned support at all |
| Cortex-M3/M4/M7/M33 | supported in hardware, slower (split into two accesses) | `LDRD`/`STRD`, `LDM`/`STM` still fault; can be made to trap with `CCR.UNALIGN_TRP` |
| Cortex-A (ARMv7-A/ARMv8-A) | supported for normal memory | faults on **Device** memory (peripherals) and for exclusive/atomic instructions |
| x86 | supported, small penalty | atomics across cache lines are very slow (split locks) |

**The classic bug**

```c
void parse(const uint8_t *buf)            /* buf from a UART or network packet */
{
    uint32_t len = *(const uint32_t *)(buf + 1);   /* unaligned if buf+1 is not a multiple of 4,
                                                      and also a strict-aliasing violation */
}
```

**Correct, portable approaches**

```c
uint32_t len;
memcpy(&len, buf + 1, sizeof len);        /* compiler emits the best sequence for the target */

uint32_t len_le = (uint32_t)buf[1] | (uint32_t)buf[2] << 8 |
                  (uint32_t)buf[3] << 16 | (uint32_t)buf[4] << 24;   /* also fixes byte order */
```

**Controlling alignment**

- `_Alignas(32) uint8_t dma_buf[512];` (C11) or `__attribute__((aligned(32)))` for cache-line-aligned DMA buffers.
- `alignof(T)` (C11 `_Alignof`) gives a type's requirement.
- `aligned_alloc(align, size)` for aligned heap memory.
- Packed structs remove padding but may create unaligned members (see the C topic).

**Why alignment matters beyond correctness:** aligned data never spans two cache lines or two bus transactions; DMA controllers often require aligned buffers; and atomic operations generally require natural alignment.

### What is endianness and how do you check it in code? {E}
**Short answer:** Endianness is the order in which the bytes of a multi-byte value are stored in memory. **Little-endian** stores the least significant byte at the lowest address (x86, almost all Arm systems in practice, RISC-V). **Big-endian** stores the most significant byte first (network byte order, older PowerPC, some DSPs and Motorola parts). You can check it at run time by looking at the first byte of a known integer.

```
value 0x12345678 at address 0x100
               0x100 0x101 0x102 0x103
little-endian:  78    56    34    12
big-endian:     12    34    56    78
```

```c
#include <stdint.h>

int is_little_endian(void)
{
    uint32_t x = 1;
    return *(const uint8_t *)&x == 1;     /* lowest-addressed byte holds the LSB */
}

/* same idea with a union */
int is_little_endian_union(void)
{
    union { uint32_t u; uint8_t b[4]; } v = { .u = 1 };
    return v.b[0] == 1;
}
```

Reading an object through `char *`/`unsigned char *`/`uint8_t *` is always allowed (it does not violate strict aliasing), so the pointer version is valid C.

**Compile-time check (GCC/Clang):**

```c
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
/* little-endian target */
#endif
```

**Where endianness matters**

- **Communication:** network protocols (TCP/IP headers are big-endian), CAN signals (Intel vs Motorola byte order in DBC files), Modbus (big-endian registers), USB and Bluetooth (little-endian).
- **Files and flash data** shared between different processors.
- **Casting byte buffers to structs** or integers.

**The portable way:** never depend on the host's endianness. Build and split values from bytes explicitly with shifts, which work on any host:

```c
uint32_t get_be32(const uint8_t *b)
{
    return (uint32_t)b[0] << 24 | (uint32_t)b[1] << 16 | (uint32_t)b[2] << 8 | b[3];
}
void put_le16(uint8_t *b, uint16_t v) { b[0] = (uint8_t)v; b[1] = (uint8_t)(v >> 8); }
```

Note the casts to `uint32_t` before shifting: without them, `b[0]` is promoted to `int`, and `0x80 << 24` overflows a signed int.

**Arm detail:** Arm cores are bi-endian in architecture, but Cortex-M endianness is fixed at chip design (almost always little-endian), and Linux on Arm is almost always little-endian.

### How do you swap the endianness of a 32-bit value? {E}
**Short answer:** Move each byte to its mirrored position with shifts and masks, or use the compiler built-in `__builtin_bswap32()`, which compiles to a single `REV` instruction on Arm. For network code use `htonl()`/`ntohl()`, which swap only when the host is little-endian.

```c
#include <stdint.h>

static inline uint32_t bswap32(uint32_t x)
{
    return  (x >> 24)               |
           ((x >>  8) & 0x0000FF00u) |
           ((x <<  8) & 0x00FF0000u) |
            (x << 24);
}

static inline uint16_t bswap16(uint16_t x)
{
    return (uint16_t)((x >> 8) | (x << 8));
}
/* bswap32(0x12345678) == 0x78563412 */
```

**Use unsigned types.** A version written with `int`:

```c
int a = 0x12345678, out = 0;
out |= (a & 0x000000ff) << 24;   /* 0x78 << 24 sets the sign bit of int: overflow, UB */
out |= (a & 0xff000000) >> 24;   /* for a negative a, >> is implementation-defined */
```

works on most compilers for this particular value, but it relies on undefined and implementation-defined behaviour. With `uint32_t` every shift is well-defined.

**Other ways**

| Method | Notes |
|---|---|
| `__builtin_bswap16/32/64` | GCC/Clang; one instruction on Arm (`REV`, `REV16`), x86 (`BSWAP`) |
| `__REV()`, `__REV16()`, `__REVSH()` | CMSIS intrinsics for Cortex-M |
| `htonl`, `htons`, `ntohl`, `ntohs` | POSIX/socket APIs: host ↔ network (big-endian) |
| `htobe32`, `le32toh` (`<endian.h>`) | Linux/BSD: explicit target byte order |
| `cpu_to_be32`, `le32_to_cpu` | Linux kernel; also annotate types (`__be32`) so `sparse` can check |
| Shifts from a byte array | best for parsing buffers (also avoids alignment problems) |

**The pattern most firmware should use:** do not swap integers in place. Convert at the boundary: parse incoming bytes with `get_be32(buf)` and serialise outgoing data with `put_be32(buf, v)`. That handles byte order and alignment in one step and works unchanged on any CPU.

### What is strict aliasing? {H}
**Short answer:** The strict aliasing rule says that an object may only be accessed through an expression of its own type (or a compatible type, its signed/unsigned variant, a qualified version, an aggregate or union containing it), or through a character type (`char`, `unsigned char`). The compiler uses this rule to assume that pointers to different types do not point to the same memory, so it can keep values in registers and reorder loads and stores. Breaking the rule is undefined behaviour.

```c
#include <stdint.h>
#include <string.h>

uint32_t float_bits_bad(float f)
{
    return *(uint32_t *)&f;               /* UB: accessing a float through a uint32_t lvalue */
}

uint32_t float_bits_ok(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);             /* defined; compiles to a single register move */
    return u;
}
```

**How it breaks code in practice**

```c
int foo(int *i, float *f)
{
    *i = 1;
    *f = 2.0f;           /* compiler assumes f cannot point to the same object as i */
    return *i;           /* so it returns 1 without reloading, even if i and f alias */
}
```

Code like this often works at `-O0` and silently changes behaviour at `-O2`.

**Allowed ways to reinterpret bytes**

- `memcpy` into an object of the target type (the standard, recommended way; free after optimisation).
- Reading through `unsigned char *` / `uint8_t *` (character types may alias anything).
- A union (allowed in C; undefined in C++, where `std::bit_cast` in C++20 is the tool).

**Embedded situations where it appears**

- Casting a received `uint8_t` buffer to a struct pointer (`struct hdr *h = (struct hdr *)buf;`), which is also an alignment risk. Copy into a struct with `memcpy`, or parse field by field.
- Treating a `uint32_t` array as `float` samples.
- Checksums computed by reading a struct as `uint32_t` words.

**Escape hatch:** `-fno-strict-aliasing` disables the optimisation; the Linux kernel and many embedded projects build with it. That makes such code work with GCC, but it is still non-portable C and gives up some optimisation, so prefer `memcpy` in new code. GCC's `-Wstrict-aliasing` catches some violations.

### How do you access a memory-mapped register at a fixed address? {E}
**Short answer:** Convert the register's address into a pointer to a `volatile` fixed-width integer and dereference it. The `volatile` makes the compiler perform every read and write exactly as written. Vendor headers (CMSIS) do the same with a struct that overlays a whole peripheral's registers.

```c
#include <stdint.h>

#define GPIOA_BASE  0x40020000u
#define GPIOA_MODER (*(volatile uint32_t *)(GPIOA_BASE + 0x00u))
#define GPIOA_ODR   (*(volatile uint32_t *)(GPIOA_BASE + 0x14u))

void led_on(void)
{
    GPIOA_MODER = (GPIOA_MODER & ~(3u << 10)) | (1u << 10);   /* PA5 as output */
    GPIOA_ODR |= (1u << 5);                                     /* drive PA5 high */
}
```

**The struct-overlay style (CMSIS)**

```c
typedef struct {
    volatile uint32_t MODER;    /* 0x00 */
    volatile uint32_t OTYPER;   /* 0x04 */
    volatile uint32_t OSPEEDR;  /* 0x08 */
    volatile uint32_t PUPDR;    /* 0x0C */
    volatile const uint32_t IDR;/* 0x10  read-only */
    volatile uint32_t ODR;      /* 0x14 */
    volatile uint32_t BSRR;     /* 0x18  write-only set/reset */
} GPIO_TypeDef;

#define GPIOA ((GPIO_TypeDef *)GPIOA_BASE)

GPIOA->BSRR = 1u << 5;          /* atomic set of PA5, no read-modify-write */
```

Use `_Static_assert(offsetof(GPIO_TypeDef, ODR) == 0x14, "")` to check the layout.

**Important details**

- **`volatile` is required**, or the compiler may combine, reorder or remove accesses (e.g. a polling loop reading a status register once).
- **Access width:** some peripherals require 32-bit accesses; using `uint8_t` pointers to them may fault or be ignored. Match the width the reference manual specifies.
- **Read-modify-write is not atomic.** `GPIOA->ODR |= x` can race with an ISR modifying the same register; use set/clear registers (`BSRR`), bit-banding, or a critical section.
- **Write-1-to-clear** status bits: `SR |= FLAG` would clear **every** flag that is set; write only the bit you mean: `SR = FLAG`.
- **Ordering:** `volatile` orders accesses in the compiler, but on cores with write buffers (Cortex-M7, Cortex-A) you may need `__DSB()` before relying on a write having reached the peripheral (e.g. before sleeping or after clearing an interrupt flag).
- On Linux, user space cannot use physical addresses directly; drivers use `ioremap()` + `readl()`/`writel()`, and user space can `mmap()` `/dev/mem` or a UIO device for experiments.

### Why is sizeof not a function? {E}
**Short answer:** `sizeof` is a compile-time **operator**, not a function. The compiler evaluates it from the type of its operand, so no code runs and the operand expression is **not evaluated** (except for variable-length arrays). Parentheses are required only around a type name: `sizeof(int)`; for an expression, `sizeof x` is valid.

```c
int i = 5;
size_t s = sizeof(i++);      /* s = 4, and i is still 5: i++ never executes */

int arr[10];
sizeof arr;                  /* 40 */
sizeof arr[0];               /* 4 */
sizeof(int[10]);             /* 40 */

void f(int n) { int vla[n]; sizeof vla; }   /* VLA: evaluated at run time */
```

**Facts interviewers check**

- The result type is `size_t` (unsigned). Mixing it with negative signed values in comparisons is a classic bug: `if (-1 < sizeof(int))` is false.
- `sizeof(char)` is always 1. In C, `sizeof('a')` is `sizeof(int)` because a character constant is an `int`.
- `sizeof` on a struct includes padding.
- `sizeof` on an array parameter gives the pointer size, because the parameter is really a pointer.
- `sizeof` on a function name is invalid in standard C.
- Because the result is a constant expression (except for VLAs), it can be used in `#define`s, array sizes and `_Static_assert`, but **not** in `#if` (the preprocessor runs before types exist).

**Printing it:** use `%zu`: `printf("%zu\n", sizeof arr);`.

**Good style:** `malloc(n * sizeof *p)` rather than `malloc(n * sizeof(struct foo))`; the expression form stays correct if the type of `p` changes.

### How do you find the number of elements in an array? {E}
**Short answer:** Divide the size of the whole array by the size of one element: `sizeof(a) / sizeof((a)[0])`, usually wrapped in an `ARRAY_SIZE` macro. It only works on a real array whose declaration is in scope; on a pointer (including an array passed to a function) it silently gives a wrong result.

```c
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

static const uint16_t baud_table[] = { 9600, 19200, 38400, 57600 };

for (size_t i = 0; i < ARRAY_SIZE(baud_table); i++) { /* 4 iterations */ }

void f(const uint16_t *t)
{
    size_t n = ARRAY_SIZE(t);    /* WRONG: sizeof(pointer) / sizeof(uint16_t) = 2 on 32-bit */
}
```

**Making it safe (GCC/Clang):** the Linux kernel's version fails to compile when given a pointer:

```c
#define __must_be_array(a) \
    (sizeof(struct { int : -!!(__builtin_types_compatible_p(__typeof__(a), __typeof__(&(a)[0]))); }))
#define ARRAY_SIZE_SAFE(a) (sizeof(a) / sizeof((a)[0]) + __must_be_array(a))
```

C23 and C++17 make this easier: C++ has `std::size(a)`, which refuses pointers.

**Why `(a)[0]` and not `*a`:** both work for arrays; the brackets are just a common idiom. The parentheses around `a` protect expressions passed to the macro.

**Best practice for functions:** always pass the element count with the pointer (`void send(const uint8_t *buf, size_t len)`), or pass a struct that contains both.

**Static check for tables that must match an enum:**

```c
enum mode { MODE_IDLE, MODE_RUN, MODE_COUNT };
static const char *const mode_name[] = { "idle", "run" };
_Static_assert(ARRAY_SIZE(mode_name) == MODE_COUNT, "mode_name out of sync with enum mode");
```

### What is the difference between memcpy and memmove? {E}
**Short answer:** Both copy `n` bytes from source to destination. `memcpy` assumes the two regions **do not overlap**; if they do, the behaviour is undefined. `memmove` handles overlap correctly, as if the data were first copied to a temporary buffer, usually by copying backwards when the destination is above the source.

```c
char buf[] = "abcdef";

memmove(buf + 2, buf, 4);   /* "ababcd" - correct */
memcpy(buf + 2, buf, 4);    /* undefined: may give "ababab" with a simple forward copy */
```

**Why a forward copy breaks with overlap:** copying `buf[0..3]` to `buf[2..5]` one byte at a time from the front overwrites `buf[2]` and `buf[3]` before they are read.

**How `memmove` decides direction**

```c
void *my_memmove(void *dst, const void *src, size_t n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    if (d < s) {
        while (n--) *d++ = *s++;          /* copy forward */
    } else if (d > s) {
        d += n; s += n;
        while (n--) *--d = *--s;          /* copy backward */
    }
    return dst;
}
```

(Comparing pointers into different objects with `<` is technically unspecified in C; library implementations do it with integer addresses.)

**When to use which**

- `memcpy` when the buffers are distinct (most cases); it can be slightly faster because it may copy in any order and use the widest possible loads.
- `memmove` when shifting data inside one buffer: removing bytes from the front of a receive buffer, inserting into an array, scrolling a display buffer.

**Embedded notes**

- Neither function respects `volatile` or peripheral access widths: do not use them to copy to or from hardware registers or device memory; write an explicit loop with `volatile` accesses of the right width.
- For large copies on an MCU, a DMA memory-to-memory transfer can free the CPU.
- Compilers often replace small fixed-size `memcpy` calls with inline loads and stores, and they may also turn a hand-written copy loop into a `memcpy` call (which matters if you are writing the `memcpy` implementation itself: build it with `-fno-builtin` or `-ffreestanding`).

### What is a NULL pointer dereference on a Cortex-M and why might it not crash? {H}
**Short answer:** On most Cortex-M microcontrollers, address `0x00000000` is valid memory: flash (or an alias of it) containing the vector table. Reading through a NULL pointer therefore returns real data (the initial stack pointer value and the reset vector) instead of faulting, so the bug goes unnoticed. Writes to that area are usually ignored or cause a bus fault, depending on the part.

**Example**

```c
struct sensor *s = NULL;        /* forgot to initialise */
uint32_t v = s->value;          /* reads address 0x00000000 + offset: valid flash, no fault */
s->value = 5;                   /* write to flash: ignored, or a BusFault (imprecise on some cores) */
```

On Linux, the first page (and more) of every process is unmapped, so the same bug gives an immediate `SIGSEGV`.

**How to catch NULL dereferences on an MCU**

1. **MPU:** configure a region at address 0 (e.g. 256 bytes to a few KB) as no-access. If the vector table has been relocated to RAM or another flash address with `SCB->VTOR`, nothing legitimate reads address 0 any more, and the MPU turns a NULL access into a MemManage fault with the faulting address in `MMFAR`.
2. **Some MCUs** let you remap address 0 to non-existent memory, or have the flash at another base address with nothing at 0 (then a NULL access is a precise BusFault).
3. **Static analysis** and compiler warnings (`-Wnull-dereference`, clang analyzer, cppcheck).
4. **Unit-test the code on the host** with sanitizers, where NULL dereferences crash reliably.
5. **Defensive coding:** check pointers returned by allocation and lookup functions; initialise every pointer.

**Why it matters:** a NULL function pointer call (`cb()` where `cb == NULL`) loads the PC from address 0 — the initial stack pointer value — and the core tries to execute at an address in RAM, usually ending in a HardFault far from the cause. Knowing this pattern helps you recognise it in a fault dump: a PC equal to the initial MSP value is a strong hint.

### How do you write a function that returns multiple values? {E}
**Short answer:** C functions return only one value, so either return a **struct** containing all the results, or return a **status code** and write the results through **pointer parameters** (output parameters). Embedded APIs usually use the second form so errors are explicit.

```c
#include <stdint.h>

typedef struct { int16_t x, y, z; } accel_t;

/* 1. return a small struct by value */
accel_t accel_read(void);

/* 2. status + output parameters */
typedef enum { OK = 0, ERR_TIMEOUT, ERR_BUS } status_t;
status_t accel_read2(int16_t *x, int16_t *y, int16_t *z);

/* 3. status + output struct (common and extensible) */
status_t accel_read3(accel_t *out);

/* usage */
accel_t a;
if (accel_read3(&a) != OK) { /* handle error */ }
```

**Trade-offs**

| Approach | Pros | Cons |
|---|---|---|
| Return a struct | clean, no pointers, no aliasing issues | no separate error channel (unless the struct has a status field); large structs are copied |
| Output pointers | explicit status, caller owns the memory | callers can pass NULL; function must check |
| Output struct pointer + status | extensible (add fields without changing the signature) | slightly more code |
| Global variables | none worth mentioning | not reentrant, hidden coupling |

**Performance:** on Arm (AAPCS), a struct of up to 4 bytes is returned in `r0`; larger structs are returned through a hidden pointer to memory reserved by the caller, so returning a 6-byte `accel_t` is still cheap. On AArch64, structs up to 16 bytes come back in registers.

**Good API habits:** document whether outputs are written on failure (usually "not modified" or "undefined"), use `const` for inputs, and mark the function `[[nodiscard]]` (C23) or `__attribute__((warn_unused_result))` so callers cannot ignore the status.

### What is a flexible array member? {M}
**Short answer:** A flexible array member is an array with no size declared as the **last** member of a struct (C99). The struct describes a header followed by a variable amount of data, allocated in one block: `malloc(sizeof(struct packet) + n)`. `sizeof` the struct does not include the array.

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct packet {
    uint16_t len;
    uint8_t  type;
    uint8_t  data[];          /* flexible array member: must be last */
};

struct packet *packet_new(uint8_t type, const uint8_t *payload, uint16_t n)
{
    struct packet *p = malloc(sizeof *p + n);   /* header + n bytes, one allocation */
    if (p == NULL) return NULL;
    p->len = n;
    p->type = type;
    memcpy(p->data, payload, n);
    return p;                                   /* one free(p) releases everything */
}
```

**Why use it**

- One allocation and one `free` instead of a header plus a separately allocated buffer.
- The data is contiguous with the header (good for cache and for sending the whole thing with one DMA or `write` call).

**Rules**

- It must be the last member, and the struct must have at least one other member.
- A struct with a flexible array member cannot be an element of an array or a member of another struct (GCC allows the latter as an extension).
- `sizeof(struct packet)` may include padding before `data`; using `offsetof(struct packet, data) + n` gives the minimum size.
- Assigning or copying such structs by value copies only the header.

**Older tricks you will see in legacy code:** `uint8_t data[1];` (the "struct hack": accessing beyond index 0 is technically undefined) and `uint8_t data[0];` (a GNU extension). Modern compilers with `-fstrict-flex-arrays` and bounds checking treat these differently, so convert them to `[]`. The Linux kernel completed this conversion and uses `__counted_by(len)` annotations so the compiler can bounds-check the array.

**Embedded note:** with static allocation, you can use the same type over a fixed buffer: `static uint8_t storage[sizeof(struct packet) + 64]` and a pointer to it, keeping the alignment of the struct in mind.

### What are offsetof and container_of? {M}
**Short answer:** `offsetof(type, member)` (from `<stddef.h>`) gives the byte offset of a member within a struct, as a compile-time constant. `container_of(ptr, type, member)` (a Linux kernel macro) uses it the other way round: given a pointer to a member, it computes the address of the struct that contains it. Together they let generic code (lists, queues, callbacks) work with embedded "hook" members.

```c
#include <stddef.h>
#include <stdint.h>

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

struct list_node { struct list_node *next; };

struct uart_msg {
    uint8_t len;
    uint8_t data[16];
    struct list_node node;          /* hook used by a generic queue */
};

void process(struct list_node *n)
{
    struct uart_msg *m = container_of(n, struct uart_msg, node);
    /* m->len, m->data are now accessible */
}
```

**How `offsetof` can be implemented** (the classic version, technically undefined but historically common):

```c
#define my_offsetof(type, member) ((size_t)&(((type *)0)->member))
```

Modern compilers provide `__builtin_offsetof`, which `<stddef.h>` uses; always use the standard macro.

**Uses**

- **Intrusive linked lists** (Linux `list_head`, Zephyr `sys_slist`, FreeRTOS list items inside the TCB): the list code only knows about the node; `container_of` gets back to the object. No separate allocation per list entry.
- **Callbacks with embedded context:** a driver registers a `struct timer` embedded in its own state struct; the timer callback receives `struct timer *` and recovers the driver state.
- **Checking layouts:** `_Static_assert(offsetof(struct regs, CTRL) == 0x08, "")` to verify that a register struct matches the datasheet.
- **Serialisation** code that needs member positions.

**Cautions:** `container_of` is only correct if the pointer really points to that member of that type of struct; a wrong type gives a silently wrong address. The kernel's version adds a type check using `typeof` to catch mismatches at compile time.

### How do you allocate a 64-byte-aligned buffer without malloc? {M}
**Short answer:** Use the C11 alignment specifier on a fixed-size object, or a compiler/platform alignment facility.

```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
_Alignas(64) static unsigned char buffer[256];

bool is_aligned(const void *p, uintptr_t a)
{
    return a && !(a & (a - 1u)) &&
           !((uintptr_t)p & (a - 1u));
}
```

**Example:** 0x1000 is 64-byte aligned because its low six bits are zero; 0x1004 is not.

```text
0x1000      0x1040      0x1080      0x10C0
| 64 bytes  | 64 bytes  | 64 bytes  | 64 bytes  |
^ buffer start
```

**Why:** Alignment can be needed for SIMD, cache-line isolation and DMA buffers. Extended alignment support depends on the compiler and target. DMA mapping and cache ownership are separate requirements; alignment alone does not make the buffer DMA-safe.

**Interview takeaway:** Static aligned storage avoids heap allocation and provides the required address boundary when supported.
