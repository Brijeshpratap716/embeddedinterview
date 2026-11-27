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
A memory pool preallocates a fixed number of blocks and manages their availability. It is useful for predictable allocation in firmware and RTOS applications.

#### 1. Pool design

- Reserve N equally sized and suitably aligned slots.
- Track free slots using a free list or bitmap.
- Allocate one slot and mark it occupied.
- Return the slot to the pool when the owner finishes.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 189" width="100%" role="img" aria-label="Fixed-size pool allocation and release do not split the underlying slots" font-family="system-ui,sans-serif"><text x="8" y="17" font-size="11" font-weight="600" fill="currentColor">Initial pool: 4 slots</text><rect x="8" y="24" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="48.5" y="43" font-size="10" fill="currentColor" text-anchor="middle">Free 0</text><rect x="89" y="24" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="129.5" y="43" font-size="10" fill="currentColor" text-anchor="middle">Free 1</text><rect x="170" y="24" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="210.5" y="43" font-size="10" fill="currentColor" text-anchor="middle">Free 2</text><rect x="251" y="24" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="291.5" y="43" font-size="10" fill="currentColor" text-anchor="middle">Free 3</text><text x="8" y="76" font-size="11" font-weight="600" fill="currentColor">After two allocations</text><rect x="8" y="83" width="81" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="48.5" y="102" font-size="10" fill="currentColor" text-anchor="middle">Used 0</text><rect x="89" y="83" width="81" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="129.5" y="102" font-size="10" fill="currentColor" text-anchor="middle">Used 1</text><rect x="170" y="83" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="210.5" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free 2</text><rect x="251" y="83" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="291.5" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free 3</text><text x="8" y="135" font-size="11" font-weight="600" fill="currentColor">After releasing slot 0</text><rect x="8" y="142" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="48.5" y="161" font-size="10" fill="currentColor" text-anchor="middle">Free 0</text><rect x="89" y="142" width="81" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="129.5" y="161" font-size="10" fill="currentColor" text-anchor="middle">Used 1</text><rect x="170" y="142" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="210.5" y="161" font-size="10" fill="currentColor" text-anchor="middle">Free 2</text><rect x="251" y="142" width="81" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="291.5" y="161" font-size="10" fill="currentColor" text-anchor="middle">Free 3</text></svg></div>

#### 2. Simple fixed-size block allocator in C

This pool stores a specific object type and uses a free-index stack. Initialization is O(N); allocation is O(1). Release validates the supplied pointer by checking the four slots.

```c
#include <stdbool.h>
#include <stddef.h>

#define N 4

struct Block {
    unsigned char data[32];
};

static struct Block pool[N];
static unsigned free_ids[N], top;
static bool used[N];

void pool_init(void)
{
    top = N;
    for (unsigned i = 0; i < N; i++) {
        free_ids[i] = i;
        used[i] = false;
    }
}

struct Block *pool_alloc(void)
{
    if (top == 0)
        return NULL;

    unsigned i = free_ids[--top];
    used[i] = true;
    return &pool[i];
}

bool pool_free(struct Block *p)
{
    for (unsigned i = 0; i < N; i++) {
        if (p == &pool[i] && used[i]) {
            used[i] = false;
            free_ids[top++] = i;
            return true;
        }
    }
    return false;
}
```

Call pool_init once before allocating. Do not reinitialize while blocks are in use. Each successful allocation returns one Block; a full pool returns NULL.

#### 3. Advantages and limitations

| Advantages | Limitations |
|---|---|
| Preallocated storage | Fixed capacity |
| Bounded allocation time | Fixed slot size |
| No external fragmentation within pool | Possible unused slot bytes |

The example is single-threaded. Protect shared pool state with an appropriate lock or interrupt-safe mechanism when used concurrently. A stale pointer to a slot that has since been reallocated cannot be detected merely with a used flag.

**Interview takeaway:** Pools trade flexibility for predictable resource use. Use typed, aligned slots or a carefully designed raw-storage allocator and validate ownership.

### How would you implement a simple malloc() and free()? {H}
A simple malloc/free implementation manages a reserved heap region using metadata. Allocation finds a suitable free block, and freeing makes its space reusable.

#### 1. Block layout

Each block typically contains a header with its payload size, allocation status and/or links to other blocks.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 189" width="100%" role="img" aria-label="Allocator splits a free block and later merges physically adjacent free blocks" font-family="system-ui,sans-serif"><text x="8" y="17" font-size="11" font-weight="600" fill="currentColor">Initial free region</text><rect x="8" y="24" width="54" height="30" fill="#94a3b8" fill-opacity=".16" stroke="#94a3b8"/><text x="35" y="43" font-size="10" fill="currentColor" text-anchor="middle">Header</text><rect x="62" y="24" width="270" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="197" y="43" font-size="10" fill="currentColor" text-anchor="middle">Free payload</text><text x="8" y="76" font-size="11" font-weight="600" fill="currentColor">After splitting for an allocation</text><rect x="8" y="83" width="54" height="30" fill="#94a3b8" fill-opacity=".16" stroke="#94a3b8"/><text x="35" y="102" font-size="10" fill="currentColor" text-anchor="middle">Hdr</text><rect x="62" y="83" width="108" height="30" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="116" y="102" font-size="10" fill="currentColor" text-anchor="middle">Used</text><rect x="170" y="83" width="54" height="30" fill="#94a3b8" fill-opacity=".16" stroke="#94a3b8"/><text x="197" y="102" font-size="10" fill="currentColor" text-anchor="middle">Hdr</text><rect x="224" y="83" width="108" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="278" y="102" font-size="10" fill="currentColor" text-anchor="middle">Free</text><text x="8" y="135" font-size="11" font-weight="600" fill="currentColor">After freeing and coalescing</text><rect x="8" y="142" width="54" height="30" fill="#94a3b8" fill-opacity=".16" stroke="#94a3b8"/><text x="35" y="161" font-size="10" fill="currentColor" text-anchor="middle">Header</text><rect x="62" y="142" width="270" height="30" fill="#16a34a" fill-opacity=".16" stroke="#16a34a"/><text x="197" y="161" font-size="10" fill="currentColor" text-anchor="middle">Free payload</text></svg></div>

#### 2. Allocation algorithm (first fit)

1. Reject invalid sizes and check arithmetic overflow.
2. Round the requested payload up to the required alignment.
3. Search the free blocks for the first sufficiently large one.
4. Split the block only if the remainder can hold a valid aligned header and payload.
5. Mark the selected block allocated and return its payload address.

#### 3. Free algorithm

1. A null pointer is a no-op.
2. For a valid allocated pointer, find its associated header.
3. Mark the block free.
4. Merge with physically adjacent free neighbors.
5. Update the free-list or block metadata.

Freeing a foreign pointer, an interior pointer or an already freed allocation is invalid.

#### 4. Small educational allocator in C

The following is a bounded, fixed-block implementation of the allocation/free idea. It allocates one suitably aligned block per request and deliberately avoids splitting. It is useful for explaining allocator mechanics without unsafe header arithmetic.

```c
#include <stddef.h>
#include <stdbool.h>

#define N 8

static max_align_t storage[N];
static bool busy[N];

void *my_malloc(size_t n)
{
    if (n == 0 || n > sizeof storage[0])
        return NULL;

    for (unsigned i = 0; i < N; i++) {
        if (!busy[i]) {
            busy[i] = true;
            return &storage[i];
        }
    }
    return NULL;
}

bool my_free(void *p)
{
    if (p == NULL)
        return true;

    for (unsigned i = 0; i < N; i++) {
        if (p == &storage[i] && busy[i]) {
            busy[i] = false;
            return true;
        }
    }
    return false;
}
```

This is a demonstration of block reservation, not a conforming general-purpose malloc: the storage has a declared type, requests cannot span slots, and callers must not treat it as unrestricted malloc-provided storage for arbitrary incompatible object types. A real variable-size heap additionally requires the splitting/coalescing algorithm above, alignment guarantees, metadata bounds and synchronization.

#### 5. Allocation strategies

| Strategy | Selection rule |
|---|---|
| First fit | First sufficiently large free block |
| Best fit | Smallest suitable free block |
| Segregated lists | Search a size class |
| Buddy allocator | Split and merge power-of-two blocks |

**Interview takeaway:** Allocation is not just returning a pointer. Correct metadata, alignment, overflow checks, splitting, coalescing and ownership management are the difficult parts.

### How do you detect a stack overflow on a microcontroller? {M}
A stack overflow occurs when stack usage exceeds the memory reserved for a function context or RTOS task. On a microcontroller this may corrupt global data, another task's stack or control information.

#### 1. Common causes

- Deep recursion or call chains.
- Large automatic arrays.
- Nested interrupts or exception frames.
- Incorrect RTOS task stack sizing.

#### 2. Stack watermark technique

Fill unused stack memory with a known pattern during safe initialization. As the stack is used, the pattern is overwritten. Scan the remaining pattern to estimate the maximum observed usage.

<div style="max-width:600px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 178" width="100%" role="img" aria-label="Downward growing stack with used area, untouched pattern and overflow guard">
<text x="70" y="17" font-size="10" fill="currentColor" text-anchor="end">High address</text>
<rect x="80" y="5" width="160" height="65" fill="#3b82f6" fill-opacity=".16" stroke="#3b82f6"/><text x="160" y="30" text-anchor="middle" font-size="12" fill="currentColor">Used stack</text><text x="160" y="47" text-anchor="middle" font-size="10" fill="currentColor">Overwritten pattern</text>
<rect x="80" y="70" width="160" height="73" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="160" y="100" text-anchor="middle" font-size="12" fill="currentColor">Untouched pattern</text><text x="160" y="116" text-anchor="middle" font-size="10" fill="currentColor">Remaining margin</text>
<rect x="80" y="143" width="160" height="22" fill="#dc2626" fill-opacity=".18" stroke="#dc2626"/><text x="160" y="158" text-anchor="middle" font-size="11" fill="currentColor">Canary / MPU guard</text>
<path d="M258 12 V133 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><text x="267" y="75" font-size="10" fill="currentColor">Growth</text><text x="70" y="161" font-size="10" fill="currentColor" text-anchor="end">Low address</text></svg></div>

Do not overwrite the live stack when initializing a pattern.

#### 3. RTOS example (FreeRTOS)

```c
UBaseType_t remaining =
    uxTaskGetStackHighWaterMark(NULL);
```

This reports the minimum observed unused stack space, in stack units rather than necessarily bytes. Enable the relevant configuration and inspect task margins during stress testing.

#### 4. Other protection methods

| Method | Purpose |
|---|---|
| Stack canary | Detect overwritten boundary or protected frame |
| MPU guard region | Generate a fault on forbidden access |
| RTOS overflow hook | Detect supported overflow conditions |
| Stack analysis | Estimate worst-case call depth and frame sizes |

Inspect fault status registers and the saved exception frame when debugging Cortex-M faults, where available.

**Interview takeaway:** High-water marks are observations, not proof of a safe worst-case stack size. Combine runtime checks, static analysis, interrupt nesting estimates and an adequate safety margin.

### What is alignment and what happens on an unaligned access? {M}
Memory alignment means placing an object at an address that satisfies its required alignment. For example, a four-byte-aligned object must start at an address divisible by four.

#### 1. Aligned and unaligned addresses

| Address | 4-byte aligned? |
|---|---|
| 0x2000 | Yes |
| 0x2001 | No |
| 0x2004 | Yes |
| 0x2006 | No |

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 158" width="100%" role="img" aria-label="A four-byte unaligned access spans two naturally aligned four-byte regions" font-family="system-ui,sans-serif"><text x="10" y="16" font-size="11" font-weight="600" fill="currentColor">Aligned 32-bit access starts at 0x2000</text><rect x="10" y="24" width="40" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="30" y="43" text-anchor="middle" font-size="12" fill="currentColor">B0</text><text x="30" y="68" text-anchor="middle" font-size="10" fill="currentColor">2000</text><rect x="50" y="24" width="40" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="70" y="43" text-anchor="middle" font-size="12" fill="currentColor">B1</text><text x="70" y="68" text-anchor="middle" font-size="10" fill="currentColor">2001</text><rect x="90" y="24" width="40" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="110" y="43" text-anchor="middle" font-size="12" fill="currentColor">B2</text><text x="110" y="68" text-anchor="middle" font-size="10" fill="currentColor">2002</text><rect x="130" y="24" width="40" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="150" y="43" text-anchor="middle" font-size="12" fill="currentColor">B3</text><text x="150" y="68" text-anchor="middle" font-size="10" fill="currentColor">2003</text><rect x="170" y="24" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="190" y="43" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="190" y="68" text-anchor="middle" font-size="10" fill="currentColor">2004</text><rect x="210" y="24" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="230" y="43" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="230" y="68" text-anchor="middle" font-size="10" fill="currentColor">2005</text><rect x="250" y="24" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="270" y="43" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="270" y="68" text-anchor="middle" font-size="10" fill="currentColor">2006</text><rect x="290" y="24" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="310" y="43" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="310" y="68" text-anchor="middle" font-size="10" fill="currentColor">2007</text><text x="10" y="92" font-size="11" font-weight="600" fill="currentColor">Unaligned 32-bit access starts at 0x2002</text><rect x="10" y="100" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="30" y="119" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="30" y="144" text-anchor="middle" font-size="10" fill="currentColor">2000</text><rect x="50" y="100" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="70" y="119" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="70" y="144" text-anchor="middle" font-size="10" fill="currentColor">2001</text><rect x="90" y="100" width="40" height="30" fill="#dc2626" fill-opacity=".14" stroke="#dc2626"/><text x="110" y="119" text-anchor="middle" font-size="12" fill="currentColor">B0</text><text x="110" y="144" text-anchor="middle" font-size="10" fill="currentColor">2002</text><rect x="130" y="100" width="40" height="30" fill="#dc2626" fill-opacity=".14" stroke="#dc2626"/><text x="150" y="119" text-anchor="middle" font-size="12" fill="currentColor">B1</text><text x="150" y="144" text-anchor="middle" font-size="10" fill="currentColor">2003</text><rect x="170" y="100" width="40" height="30" fill="#dc2626" fill-opacity=".14" stroke="#dc2626"/><text x="190" y="119" text-anchor="middle" font-size="12" fill="currentColor">B2</text><text x="190" y="144" text-anchor="middle" font-size="10" fill="currentColor">2004</text><rect x="210" y="100" width="40" height="30" fill="#dc2626" fill-opacity=".14" stroke="#dc2626"/><text x="230" y="119" text-anchor="middle" font-size="12" fill="currentColor">B3</text><text x="230" y="144" text-anchor="middle" font-size="10" fill="currentColor">2005</text><rect x="250" y="100" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="270" y="119" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="270" y="144" text-anchor="middle" font-size="10" fill="currentColor">2006</text><rect x="290" y="100" width="40" height="30" fill="#94a3b8" fill-opacity=".14" stroke="#94a3b8"/><text x="310" y="119" text-anchor="middle" font-size="12" fill="currentColor">—</text><text x="310" y="144" text-anchor="middle" font-size="10" fill="currentColor">2007</text></svg></div>

#### 2. Check alignment in C

```c
#include <stdint.h>
#include <stdbool.h>

bool is_aligned(const void *p, uintptr_t a)
{
    return a != 0 && (a & (a - 1)) == 0 &&
           (((uintptr_t)p & (a - 1)) == 0);
}
```

This assumes a conventional flat byte-addressed target with uintptr_t. The mask works for power-of-two alignments.

#### 3. What happens on an unaligned access?

Some ARM processors support certain unaligned normal-memory accesses; others generate a fault or require software handling. Device-memory accesses may have stricter rules. Even if a processor supports an unaligned load, dereferencing a misaligned typed pointer can be undefined in C.

For ordinary byte buffers, a safe way to copy the representation is:

```c
uint32_t value;
memcpy(&value, buffer + 1, sizeof value);
```

The buffer must contain enough readable bytes. Convert byte order separately if the data comes from a protocol.

#### 4. Embedded use

DMA engines, cache maintenance and hardware descriptors may require alignment stronger than the C type's normal alignment. Follow the device specification rather than assuming four-byte alignment is sufficient.

**Interview takeaway:** Alignment is a requirement of the language, ABI and hardware. Misalignment may reduce performance, fault or cause undefined behaviour.

### What is endianness and how do you check it in code? {E}
Endianness defines the order in which the bytes of a multi-byte value are stored in memory.

#### 1. Little-endian vs big-endian

For the value 0x12345678, assuming eight-bit bytes:

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 158" width="100%" role="img" aria-label="The same 32-bit value has different byte order on little-endian and big-endian systems" font-family="system-ui,sans-serif"><text x="10" y="16" font-size="11" font-weight="600" fill="currentColor">Little-endian: least significant byte at lowest address</text><rect x="10" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="50" y="43" text-anchor="middle" font-size="12" fill="currentColor">78</text><text x="50" y="68" text-anchor="middle" font-size="10" fill="currentColor">0x1000</text><rect x="90" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="130" y="43" text-anchor="middle" font-size="12" fill="currentColor">56</text><text x="130" y="68" text-anchor="middle" font-size="10" fill="currentColor">0x1001</text><rect x="170" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="210" y="43" text-anchor="middle" font-size="12" fill="currentColor">34</text><text x="210" y="68" text-anchor="middle" font-size="10" fill="currentColor">0x1002</text><rect x="250" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="290" y="43" text-anchor="middle" font-size="12" fill="currentColor">12</text><text x="290" y="68" text-anchor="middle" font-size="10" fill="currentColor">0x1003</text><text x="10" y="92" font-size="11" font-weight="600" fill="currentColor">Big-endian: most significant byte at lowest address</text><rect x="10" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="50" y="119" text-anchor="middle" font-size="12" fill="currentColor">12</text><text x="50" y="144" text-anchor="middle" font-size="10" fill="currentColor">0x1000</text><rect x="90" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="130" y="119" text-anchor="middle" font-size="12" fill="currentColor">34</text><text x="130" y="144" text-anchor="middle" font-size="10" fill="currentColor">0x1001</text><rect x="170" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="210" y="119" text-anchor="middle" font-size="12" fill="currentColor">56</text><text x="210" y="144" text-anchor="middle" font-size="10" fill="currentColor">0x1002</text><rect x="250" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="290" y="119" text-anchor="middle" font-size="12" fill="currentColor">78</text><text x="290" y="144" text-anchor="middle" font-size="10" fill="currentColor">0x1003</text></svg></div>

The integer value remains the same. Only its memory representation differs.

#### 2. Detect endianness in C

```c
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    uint16_t x = 0x0102;
    const unsigned char *p =
        (const unsigned char *)&x;

    if (p[0] == 0x02)
        puts("Little-endian");
    else if (p[0] == 0x01)
        puts("Big-endian");

    return 0;
}
```

This assumes eight-bit bytes and ordinary little- or big-endian representation. Access through unsigned char is allowed for inspecting object representations.

#### 3. Why it matters in embedded systems

Network protocols often use big-endian fields, while ARM Linux commonly runs little-endian. Peripheral registers and binary files can also define their own byte order.

```c
uint16_t value = ((uint16_t)buf[0] << 8) |
                  (uint16_t)buf[1];
```

This decodes a two-byte big-endian field regardless of CPU byte order. Both bytes must be valid unsigned eight-bit values.

**Interview takeaway:** Endianness is byte order, not bit order. Use explicit conversions such as ntohl/htonl or Linux endian helpers where appropriate.

### How do you swap the endianness of a 32-bit value? {E}
Swapping endianness of a 32-bit value means reversing its four bytes while preserving the bits within each byte.

#### 1. Example

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 158" width="100%" role="img" aria-label="Byte swapping reverses byte positions in a 32-bit integer" font-family="system-ui,sans-serif"><text x="10" y="16" font-size="11" font-weight="600" fill="currentColor">Input: 0x12345678 (shown most significant byte first)</text><rect x="10" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="50" y="43" text-anchor="middle" font-size="12" fill="currentColor">12</text><text x="50" y="68" text-anchor="middle" font-size="10" fill="currentColor">bits 31–24</text><rect x="90" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="130" y="43" text-anchor="middle" font-size="12" fill="currentColor">34</text><text x="130" y="68" text-anchor="middle" font-size="10" fill="currentColor">bits 23–16</text><rect x="170" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="210" y="43" text-anchor="middle" font-size="12" fill="currentColor">56</text><text x="210" y="68" text-anchor="middle" font-size="10" fill="currentColor">bits 15–8</text><rect x="250" y="24" width="80" height="30" fill="#3b82f6" fill-opacity=".14" stroke="#3b82f6"/><text x="290" y="43" text-anchor="middle" font-size="12" fill="currentColor">78</text><text x="290" y="68" text-anchor="middle" font-size="10" fill="currentColor">bits 7–0</text><text x="10" y="92" font-size="11" font-weight="600" fill="currentColor">Output: 0x78563412</text><rect x="10" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="50" y="119" text-anchor="middle" font-size="12" fill="currentColor">78</text><text x="50" y="144" text-anchor="middle" font-size="10" fill="currentColor">bits 31–24</text><rect x="90" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="130" y="119" text-anchor="middle" font-size="12" fill="currentColor">56</text><text x="130" y="144" text-anchor="middle" font-size="10" fill="currentColor">bits 23–16</text><rect x="170" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="210" y="119" text-anchor="middle" font-size="12" fill="currentColor">34</text><text x="210" y="144" text-anchor="middle" font-size="10" fill="currentColor">bits 15–8</text><rect x="250" y="100" width="80" height="30" fill="#16a34a" fill-opacity=".14" stroke="#16a34a"/><text x="290" y="119" text-anchor="middle" font-size="12" fill="currentColor">12</text><text x="290" y="144" text-anchor="middle" font-size="10" fill="currentColor">bits 7–0</text></svg></div>

#### 2. C implementation

```c
#include <stdint.h>

uint32_t swap32(uint32_t x)
{
    return ((x & 0x000000FFu) << 24) |
           ((x & 0x0000FF00u) <<  8) |
           ((x & 0x00FF0000u) >>  8) |
           ((x & 0xFF000000u) >> 24);
}
```

Each mask isolates one byte. Shifts move it to the opposite position, and OR combines the four results.

```c
uint32_t x = swap32(0x12345678u);
// x = 0x78563412
```

#### 3. Compiler and ARM alternatives

GCC and Clang provide:

```c
uint32_t x = __builtin_bswap32(value);
```

On supporting ARM targets the compiler can generate a REV instruction to reverse the byte order of a 32-bit register.

```asm
// AArch64
REV W0, W0
```

#### 4. When to swap

An unconditional byte swap always reverses the bytes. A host-to-network conversion swaps only when required by the host byte order. They are not interchangeable on every system.

**Interview takeaway:** Use unsigned fixed-width types for bit manipulation. Prefer platform conversion APIs for protocol fields and a byte-swap builtin when unconditional reversal is required.

### What is strict aliasing? {H}
Strict aliasing refers to C's rules restricting which lvalue types may access an object's stored value. These rules allow compilers to assume certain incompatible typed pointers do not refer to the same object.

#### 1. Incorrect type punning

```c
float f = 1.0f;
uint32_t bits = *(uint32_t *)&f; // Not portable
```

Casting the pointer does not make accessing a float through a uint32_t lvalue valid. It may violate effective-type rules, and alignment and size can also differ.

#### 2. Correct representation copy

```c
#include <stdint.h>
#include <string.h>

uint32_t float_bits(float f)
{
    uint32_t bits;
    _Static_assert(sizeof bits == sizeof f,
                   "Different object sizes");

    memcpy(&bits, &f, sizeof bits);
    return bits;
}
```

This copies bytes into an object of the correct declared type. The resulting representation still depends on the floating-point format and byte ordering. Compilers often optimize such small copies into register moves.

#### 3. Why the compiler cares

```c
int update(int *a, float *b)
{
    *a = 10;
    *b = 2.0f;
    return *a;
}
```

For valid calls, the write through b cannot modify the int object through an incompatible access. The compiler can often return 10 without reloading *a.

#### 4. Permitted aliases

C allows access through compatible types, certain corresponding signed/unsigned types and qualified versions, applicable aggregate/union types and character types. For examining raw memory bytes, unsigned char * is particularly useful.

#### 5. Embedded impact

Avoid arbitrary pointer casts when parsing packet buffers or examining floating-point representations. Use memcpy, explicit byte decoding or documented platform-specific mechanisms. A compiler flag disabling strict-aliasing optimization does not fix unrelated alignment or lifetime problems.

**Interview takeaway:** A pointer cast changes the pointer type, not the actual object's type. Access memory only through permitted types.

### How do you access a memory-mapped register at a fixed address? {E}
Memory-mapped I/O (MMIO) assigns hardware registers addresses in the processor's memory map. Firmware reads or writes these registers through appropriately typed volatile accesses.

#### 1. Bare-metal example

Assume the hardware manual defines a 32-bit control register at address 0x40000010.

```c
#include <stdint.h>

#define CTRL (*(volatile uint32_t *)0x40000010U)

void enable(void)
{
    CTRL |= (1U << 3);
}
```

The processor performs a register read, modifies bit 3 and writes the result back. This is appropriate only if the register permits read-modify-write.

#### 2. Hardware access flow

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 174" width="100%" role="img" aria-label="CPU issues an MMIO address through a system interconnect to a peripheral register">
<rect x="95" y="5" width="150" height="32" rx="5" fill="#3b82f6" fill-opacity=".12" stroke="#3b82f6"/><text x="170" y="25" text-anchor="middle" font-size="12" fill="currentColor">CPU load / store</text><path d="M170 37 V65 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/><text x="180" y="53" font-size="10" fill="currentColor">Address + data</text>
<rect x="75" y="65" width="190" height="31" rx="5" fill="#eab308" fill-opacity=".12" stroke="#ca8a04"/><text x="170" y="84" text-anchor="middle" font-size="12" fill="currentColor">Interconnect / address decode</text><path d="M170 96 V121 m-4-5 4 5 4-5" stroke="currentColor" fill="none"/>
<rect x="65" y="121" width="210" height="45" rx="5" fill="#16a34a" fill-opacity=".12" stroke="#16a34a"/><text x="170" y="139" text-anchor="middle" font-size="12" fill="currentColor">Peripheral CTRL register</text><text x="170" y="155" text-anchor="middle" font-size="11" fill="currentColor">0x40000010 (illustrative)</text></svg></div>

The address decoder routes the transaction to the correct peripheral instead of ordinary RAM.

#### 3. Read-only register

```c
#define STATUS (*(const volatile uint32_t *)0x40000014U)

uint32_t value = STATUS;
```

Const prevents writes through this lvalue; volatile preserves required hardware reads.

#### 4. Linux driver example

```c
void __iomem *base;

base = devm_platform_ioremap_resource(pdev, 0);
if (IS_ERR(base))
    return PTR_ERR(base);

writel(1, base + 0x10);
value = readl(base + 0x14);
```

This is a driver probe fragment. The resource index, offsets and access width must match the actual device. Use kernel MMIO APIs rather than directly dereferencing physical addresses.

#### 5. Important precautions

Check register width, alignment, reserved bits, read/write side effects and memory-ordering requirements. A write-one-to-clear register typically needs a direct mask write rather than OR-based read-modify-write. Volatile does not replace CPU barriers.

**Interview takeaway:** Fixed-address pointers are common on bare metal. Linux uses mapped I/O addresses and MMIO accessors. Always follow the hardware's register semantics.

### Why is sizeof not a function? {E}
`sizeof` is a built-in C operator, not a library function. It returns the size of a type or object representation in units of C bytes, as a value of type size_t.

#### 1. Syntax

```c
int a = 10;

sizeof(int);  // Type
sizeof(a);    // Expression
sizeof a;     // Parentheses optional for expression
```

On a target with four-byte int, all three produce 4.

#### 2. Is its operand evaluated?

For ordinary non-VLA operands, it is not evaluated.

```c
int i = 5;
size_t n = sizeof(i++);

printf("%d", i); // 5
```

The compiler determines the size from the expression's type without executing the increment.

#### 3. Variable-length array exception

On implementations supporting variable-length arrays:

```c
void fun(size_t n)
{
    int a[n];    // Assume n > 0 and a valid bounded size
    printf("%zu", sizeof a);
}
```

The array's size depends on n at runtime. Some VLA-related sizeof operands therefore require runtime evaluation.

#### 4. Array vs pointer

```c
int arr[10];
int *p = arr;

sizeof arr;  // 10 * sizeof(int)
sizeof p;    // Size of int pointer
```

sizeof includes structure padding, but cannot discover an allocation's size from a pointer.

**Interview takeaway:** sizeof operates on types and expressions, not on runtime function arguments. Its result is size_t, so use the %zu printf format.

### How do you find the number of elements in an array? {E}
The number of elements in an actual array can be calculated by dividing its total size by the size of one element.

#### 1. Example

```c
int arr[] = {10, 20, 30, 40, 50};

size_t count = sizeof(arr) / sizeof(arr[0]);

printf("%zu", count);
```

**Output:** 5

With four-byte ints, the total size is 20 bytes and each element occupies four bytes.

#### 2. Reusable macro

```c
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

int arr[] = {1, 2, 3};
size_t n = ARRAY_SIZE(arr); // 3
```

This simple macro is valid only for actual arrays. It does not reject pointer arguments. The Linux kernel's ARRAY_SIZE macro includes additional checking.

#### 3. Common mistake inside a function

```c
void fun(int arr[])
{
    size_t n = sizeof(arr) / sizeof(arr[0]);
    // Wrong: arr is a pointer parameter.
}
```

An array parameter is adjusted to a pointer. Its original array length is not carried in the pointer.

Correct implementation:

```c
void fun(const int *arr, size_t n)
{
    for (size_t i = 0; i < n; i++)
        printf("%d ", arr[i]);
}

// Caller:
int a[] = {1, 2, 3};
fun(a, ARRAY_SIZE(a));
```

#### 4. Multidimensional array

```c
int matrix[3][4];
size_t rows = sizeof matrix / sizeof matrix[0];
size_t cols = sizeof matrix[0] / sizeof matrix[0][0];
```

The results are three rows and four columns.

**Interview takeaway:** Compute array length before array-to-pointer decay and pass it explicitly to functions. sizeof cannot recover the length of a dynamically allocated buffer.

### What is the difference between memcpy and memmove? {E}
Both memcpy and memmove copy a specified number of bytes. The difference is that **memmove supports overlapping source and destination regions**, while memcpy requires them not to overlap.

#### 1. memcpy example

```c
int src[] = {10, 20, 30};
int dst[3];

memcpy(dst, src, sizeof src);
```

Both arrays are separate objects, so memcpy is appropriate.

#### 2. Overlapping memory example

```c
char s[] = "ABCDE";

memmove(s + 1, s, 4);

printf("%s", s); // AABCD
```

The destination starts inside the source range. Using memcpy for this operation would cause undefined behaviour.

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 162" width="100%" role="img" aria-label="Overlapping copy from indices zero through three into indices one through four, producing AABCD">
<text x="12" y="13" font-size="11" font-weight="600" fill="currentColor">Before: ABCDE</text><rect x="12" y="20" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="38" y="38" font-size="12" text-anchor="middle" fill="currentColor">A</text><rect x="64" y="20" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="90" y="38" font-size="12" text-anchor="middle" fill="currentColor">B</text><rect x="116" y="20" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="142" y="38" font-size="12" text-anchor="middle" fill="currentColor">C</text><rect x="168" y="20" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="194" y="38" font-size="12" text-anchor="middle" fill="currentColor">D</text><rect x="220" y="20" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="246" y="38" font-size="12" text-anchor="middle" fill="currentColor">E</text><rect x="272" y="20" width="52" height="28" fill="#94a3b8" fill-opacity=".13" stroke="#3b82f6"/><text x="298" y="38" font-size="12" text-anchor="middle" fill="currentColor">\0</text><text x="12" y="95" font-size="11" font-weight="600" fill="currentColor">After: AABCD</text><rect x="12" y="102" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="38" y="120" font-size="12" text-anchor="middle" fill="currentColor">A</text><rect x="64" y="102" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="90" y="120" font-size="12" text-anchor="middle" fill="currentColor">A</text><rect x="116" y="102" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="142" y="120" font-size="12" text-anchor="middle" fill="currentColor">B</text><rect x="168" y="102" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="194" y="120" font-size="12" text-anchor="middle" fill="currentColor">C</text><rect x="220" y="102" width="52" height="28" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="246" y="120" font-size="12" text-anchor="middle" fill="currentColor">D</text><rect x="272" y="102" width="52" height="28" fill="#94a3b8" fill-opacity=".13" stroke="#3b82f6"/><text x="298" y="120" font-size="12" text-anchor="middle" fill="currentColor">\0</text>
<path d="M12 53 H220 M12 49 V57 M220 49 V57" stroke="#16a34a" fill="none"/><text x="116" y="66" text-anchor="middle" font-size="10" fill="currentColor">Source: bytes 0–3</text><path d="M64 135 H272 M64 131 V139 M272 131 V139" stroke="#ca8a04" fill="none"/><text x="168" y="151" text-anchor="middle" font-size="10" fill="currentColor">Destination: bytes 1–4</text></svg></div>

#### 3. How memmove handles overlap

Conceptually, memmove behaves as if the source bytes were copied into a temporary buffer before copying them to the destination. Implementations often avoid temporary storage by choosing a suitable copy direction:

- When a higher-address destination overlaps the source, copy backward.
- When a lower-address destination overlaps the source, copy forward.
- When regions do not overlap, either direction can work.

This direction logic assumes a conventional flat-address implementation.

| Feature | memcpy | memmove |
|---|---|---|
| Overlapping regions | Undefined behaviour | Supported |
| Copy length | Exact byte count | Exact byte count |
| Performance | May allow extra optimizations | Depends on implementation |

**Interview takeaway:** Choose memmove when buffers might overlap and memcpy when non-overlap is guaranteed. Neither function automatically checks bounds or adds a string terminator.

### What is a NULL pointer dereference on a Cortex-M and why might it not crash? {H}
Dereferencing a null pointer is **undefined behaviour in C**. However, whether the hardware raises a fault depends on the processor, memory mapping, access type and protection configuration.

#### 1. Why Cortex-M may not fault

```c
int *p = NULL;
// int value = *p;  // Invalid C
```

On many Cortex-M systems, the numerical address 0x00000000 is mapped or aliased to boot memory. The vector table may be located there after reset.

If an actual load from address zero is emitted and the region permits that access, the hardware can return data instead of raising an exception.

<div style="max-width:620px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 155" width="100%" role="img" aria-label="Example Cortex-M reset vector table when mapped at address zero">
<text x="10" y="15" font-size="12" font-weight="600" fill="currentColor">Example reset vector table</text>
<rect x="10" y="25" width="105" height="27" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="62" y="42" text-anchor="middle" font-size="11" fill="currentColor">0x00000000</text><rect x="115" y="25" width="215" height="27" fill="#16a34a" fill-opacity=".10" stroke="#16a34a"/><text x="222" y="42" text-anchor="middle" font-size="11" fill="currentColor">Initial MSP value</text><rect x="10" y="52" width="105" height="27" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="62" y="69" text-anchor="middle" font-size="11" fill="currentColor">0x00000004</text><rect x="115" y="52" width="215" height="27" fill="#16a34a" fill-opacity=".10" stroke="#16a34a"/><text x="222" y="69" text-anchor="middle" font-size="11" fill="currentColor">Reset handler address</text><rect x="10" y="79" width="105" height="27" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="62" y="96" text-anchor="middle" font-size="11" fill="currentColor">0x00000008</text><rect x="115" y="79" width="215" height="27" fill="#16a34a" fill-opacity=".10" stroke="#16a34a"/><text x="222" y="96" text-anchor="middle" font-size="11" fill="currentColor">NMI handler address</text><rect x="10" y="106" width="105" height="27" fill="#3b82f6" fill-opacity=".13" stroke="#3b82f6"/><text x="62" y="123" text-anchor="middle" font-size="11" fill="currentColor">0x0000000C</text><rect x="115" y="106" width="215" height="27" fill="#16a34a" fill-opacity=".10" stroke="#16a34a"/><text x="222" y="123" text-anchor="middle" font-size="11" fill="currentColor">HardFault handler address</text><text x="170" y="146" font-size="10" text-anchor="middle" fill="currentColor">Memory mapping is specific to the SoC and boot configuration.</text></svg></div>

The initial MSP word is not a valid value to obtain by dereferencing NULL in a C program.

#### 2. When can a fault occur?

- The address is unmapped or the bus rejects the access.
- An MPU region prohibits the access.
- The instruction violates access or alignment requirements.
- A configurable fault may escalate to HardFault.

Reads and writes can behave differently. A flash alias may allow reads but reject ordinary writes.

#### 3. Why Linux usually behaves differently

Linux normally leaves the null virtual-address page inaccessible to userspace. An invalid user access generally triggers a processor exception and may result in SIGSEGV.

#### 4. Debugging and prevention

Check pointers before use, respect object lifetimes and use MPU protection where available. On supporting Cortex-M cores, inspect CFSR, HFSR, applicable fault address registers and the saved exception PC.

**Interview takeaway:** A hardware access succeeding does not make null dereferencing valid C. The compiler can optimize on the assumption that undefined behaviour never occurs, so the emitted instruction itself is not guaranteed.

### How do you write a function that returns multiple values? {E}
C functions return one value directly. To return multiple results, use output pointer parameters or return a structure containing the results.

#### 1. Using output pointers

```c
#include <stdbool.h>
#include <limits.h>

bool divide(int a, int b, int *q, int *r)
{
    if (!q || !r || q == r || b == 0 ||
        (a == INT_MIN && b == -1))
        return false;

    *q = a / b;
    *r = a % b;
    return true;
}
```

Example call:

```c
int quotient, remainder;

if (divide(17, 5, &quotient, &remainder))
    printf("%d %d", quotient, remainder);
```

**Output:** 3 2

The function returns a success indicator and writes both results into caller-provided objects.

#### 2. Returning a structure

```c
struct Result {
    int quotient;
    int remainder;
};

struct Result divide_valid(int a, int b)
{
    return (struct Result){a / b, a % b};
}
```

Use this function only with valid division operands (nonzero divisor and representable quotient).

```c
struct Result result = divide_valid(17, 5);
```

Both results are returned as a single structure value. A compiler may return small structures in registers depending on the ABI.

#### 3. Embedded driver example

```c
int sensor_read(int *temperature, int *humidity);
```

The return value can communicate success or failure, while output parameters carry measured data. This pattern is common in firmware and Linux drivers.

| Method | Common use |
|---|---|
| Output pointers | Status plus multiple results, caller-owned storage |
| Structure return | Grouped related values |

**Interview takeaway:** Prefer clear ownership and error contracts. Do not return a pointer to a local automatic array or structure that ceases to exist on function return.

### What is a flexible array member? {M}
A flexible array member is an unsized array declared as the final member of a structure. It allows a fixed-size header and variable-length payload to occupy one allocation.

#### 1. Declaration

```c
#include <stddef.h>

struct Packet {
    size_t len;
    unsigned char data[];
};
```

The structure has a fixed header containing len. The flexible array has no fixed element count in the declaration.

#### 2. Memory representation

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 112" width="100%" role="img" aria-label="One allocation contains packet header followed by five payload bytes">
<text x="10" y="15" font-size="11" font-weight="600" fill="currentColor">One allocation: sizeof(struct Packet) + 5</text>
<rect x="10" y="31" width="100" height="38" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="60" y="54" font-size="12" text-anchor="middle" fill="currentColor">len = 5</text>
<rect x="110" y="31" width="44" height="38" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="132" y="54" text-anchor="middle" font-size="12" fill="currentColor">A</text><text x="132" y="83" font-size="9" text-anchor="middle" fill="currentColor">data[0]</text><rect x="154" y="31" width="44" height="38" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="176" y="54" text-anchor="middle" font-size="12" fill="currentColor">B</text><text x="176" y="83" font-size="9" text-anchor="middle" fill="currentColor">data[1]</text><rect x="198" y="31" width="44" height="38" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="220" y="54" text-anchor="middle" font-size="12" fill="currentColor">C</text><text x="220" y="83" font-size="9" text-anchor="middle" fill="currentColor">data[2]</text><rect x="242" y="31" width="44" height="38" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="264" y="54" text-anchor="middle" font-size="12" fill="currentColor">D</text><text x="264" y="83" font-size="9" text-anchor="middle" fill="currentColor">data[3]</text><rect x="286" y="31" width="44" height="38" fill="#16a34a" fill-opacity=".13" stroke="#16a34a"/><text x="308" y="54" text-anchor="middle" font-size="12" fill="currentColor">E</text><text x="308" y="83" font-size="9" text-anchor="middle" fill="currentColor">data[4]</text><text x="60" y="83" font-size="10" text-anchor="middle" fill="currentColor">Header</text><text x="170" y="102" font-size="10" text-anchor="middle" fill="currentColor">Conceptual layout; actual header may include padding.</text></svg></div>

#### 3. Allocation and use

```c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

struct Packet *make_packet(const void *src, size_t n)
{
    if (n > SIZE_MAX - sizeof(struct Packet))
        return NULL;

    struct Packet *p = malloc(sizeof *p + n);

    if (p != NULL) {
        p->len = n;
        if (n != 0)
            memcpy(p->data, src, n);
    }

    return p;
}
```

The caller must provide n readable bytes if n is nonzero.

```c
struct Packet *p = make_packet("hello", 5);
if (p != NULL) {
    // p->data contains five bytes, no NUL terminator
    free(p);
}
```

Only one free is needed because header and data belong to the same allocation.

#### 4. Difference from a pointer member

| Flexible array member | Pointer member |
|---|---|
| Payload follows header in same allocation | May refer to a separate allocation |
| No separate pointer field | Stores a pointer value |
| Payload copied explicitly | Structure assignment copies pointer, not pointed-to data |

A flexible array must be the last member of a structure with more than one named member. sizeof the structure excludes the flexible array elements, though it may include trailing padding. Structure assignment does not copy the variable-length payload.

**Interview takeaway:** Flexible arrays are useful for packets, variable-length messages and Linux kernel objects. Check allocation-size overflow and track payload length explicitly.

### What are offsetof and container_of? {M}
`offsetof` returns the byte offset of a structure member. `container_of` uses a member's address to recover a pointer to its enclosing structure.

#### 1. offsetof example

```c
#include <stddef.h>
#include <stdio.h>

struct Device {
    char type;
    int id;
};

printf("%zu", offsetof(struct Device, id));
```

On a typical ABI with four-byte int alignment, the result is 4, not 1, because the compiler inserts padding.

#### 2. How container_of works

<div style="max-width:680px;margin:16px 0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 154" width="100%" role="img" aria-label="Subtract offset four from member address 0x1004 to obtain enclosing structure address 0x1000">
<text x="10" y="14" font-size="11" font-weight="600" fill="currentColor">Example struct Device at 0x1000</text>
<rect x="10" y="34" width="40" height="33" fill="#16a34a" fill-opacity=".18" stroke="#16a34a"/><text x="30" y="54" font-size="10" text-anchor="middle" fill="currentColor">type</text><rect x="50" y="34" width="120" height="33" fill="#94a3b8" fill-opacity=".15" stroke="#94a3b8"/><text x="110" y="54" font-size="11" text-anchor="middle" fill="currentColor">3 padding bytes</text><rect x="170" y="34" width="160" height="33" fill="#3b82f6" fill-opacity=".15" stroke="#3b82f6"/><text x="250" y="54" font-size="12" text-anchor="middle" fill="currentColor">id (4 bytes)</text>
<path d="M10 72 V95 M170 72 V95 M170 83 H10 m5-4 -5 4 5 4" stroke="currentColor" fill="none"/><text x="90" y="79" font-size="10" text-anchor="middle" fill="currentColor">Subtract 4 bytes</text><text x="10" y="108" font-size="10" fill="currentColor">0x1000</text><text x="170" y="108" font-size="10" fill="currentColor">0x1004</text><text x="170" y="137" font-size="12" text-anchor="middle" fill="currentColor">base = member address − member offset</text></svg></div>

A simplified implementation for conventional flat-address environments:

```c
#define MY_CONTAINER_OF(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))
```

Example:

```c
struct Device dev = {'A', 10};
int *p = &dev.id;

struct Device *owner =
    MY_CONTAINER_OF(p, struct Device, id);

printf("%d", owner->id); // 10
```

This idiom relies on the platform/compiler's support for enclosing-object pointer recovery. Do not assume the simplified macro is a fully portable replacement for a kernel implementation.

#### 3. Linux kernel example

```c
struct my_device {
    int id;
    struct work_struct work;
};

static void my_work(struct work_struct *work)
{
    struct my_device *dev =
        container_of(work, struct my_device, work);

    pr_info("Device %d\n", dev->id);
}
```

The workqueue callback receives the embedded work member. container_of retrieves the original device object, allowing access to device-specific state.

The same pattern is used with embedded list_head nodes and other kernel objects.

**Interview takeaway:** The supplied pointer must refer to the correct member of a live enclosing object. Use the kernel's container_of macro in Linux rather than recreating it. offsetof cannot be used on a bit-field.

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
