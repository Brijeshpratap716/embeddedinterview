---
slug: coding-systems
title: "Coding: Systems, Bitmaps & Virtualization"
icon: 🧭
level: Advanced
order: 23
desc: Bitmap allocators, find-first-zero, count leading zeros, single number II, page-table walk simulation, guest memory lookup, an MMIO device model, a virtqueue parser, dirty-page tracking, graph cycle detection and topological sort for device init order.
---
These questions come from kernel, hypervisor, BSP and silicon-validation interviews (for example GPU, SoC and automotive hypervisor teams). They test whether you can turn OS and hardware concepts into small, correct C programs. Each answer is compact, tested C plus the points to explain.

### Count leading zeros of a 32-bit number. {E}
**Short answer:** Count how many zero bits come before the highest set bit. A fast portable method is a binary search on the bits: if the top 16 bits are zero, add 16 and shift left by 16; then test the top 8, 4, 2 and 1 bits the same way — five steps instead of 32. In real code use `__builtin_clz(x)`, which compiles to a single `CLZ` instruction on Cortex-M3 and later (but is undefined for x = 0, so handle 0 separately: the answer is 32).

```c
#include <stdint.h>

unsigned clz32(uint32_t x)
{
    if (x == 0) return 32;
    unsigned n = 0;
    if (!(x & 0xFFFF0000u)) { n += 16; x <<= 16; }    /* binary search on the top bits */
    if (!(x & 0xFF000000u)) { n += 8;  x <<= 8;  }
    if (!(x & 0xF0000000u)) { n += 4;  x <<= 4;  }
    if (!(x & 0xC0000000u)) { n += 2;  x <<= 2;  }
    if (!(x & 0x80000000u)) { n += 1; }
    return n;
}
/* clz32(1) = 31, clz32(0x00F00000) = 8 */
```

**Points:** five steps instead of 32; in production use `__builtin_clz(x)` (undefined for 0) which is one `CLZ` instruction on Armv5+ / Cortex-M3+. Uses: `31 - clz` = index of the highest set bit (floor log2), normalising fixed-point values, finding the highest-priority ready task in a bitmap scheduler.

**Dry run for x = 0x00F0_0000 (binary 0000 0000 1111 0000 …)**

| step | test | count | x after |
|---|---|---|---|
| top 16 bits zero? | `0x00F0` ≠ 0 → no | 0 | unchanged |
| top 8 zero? | `0x00` → yes | 8 | x <<= 8 → 0xF000_0000 |
| top 4 zero? | `0xF` → no | 8 | |
| top 2 zero? | no | 8 | |
| top 1 zero? | no | 8 | |

Result: 8 leading zeros (the highest set bit is bit 23 = 31 − 8).

**Uses that interviewers like**

| Need | Formula |
|---|---|
| Index of the highest set bit (floor log₂) | `31 - clz(x)` |
| Round up to the next power of two | `1u << (32 - clz(x - 1))` for x > 1 |
| Number of bits needed to store x | `32 - clz(x)` |
| Highest-priority ready task in a bitmap | `31 - clz(ready_bitmap)` (FreeRTOS port-optimised selection) |
| Normalise a fixed-point/float mantissa | shift left by `clz` |

**Related: count trailing zeros (CTZ)** gives the index of the lowest set bit: `__builtin_ctz(x)`, or `x & -x` isolates that bit. On Arm, CTZ = `RBIT` followed by `CLZ`.

### Find the element that appears once when all others appear three times. {M}
**Short answer:** Add up, for each bit position, how many numbers have that bit set. Every number that appears three times contributes a multiple of 3 to each of its bit positions, so `count % 3` leaves exactly the bits of the single number. The compact version keeps the per-bit count modulo 3 in two bitmasks (`ones` and `twos`) that act as a 2-bit counter for all 32 bits in parallel. O(n) time, O(1) space.

```c
#include <stddef.h>
#include <stdint.h>

int32_t single_number_thrice(const int32_t *a, size_t n)
{
    uint32_t ones = 0, twos = 0;            /* bits seen 1 time and 2 times (mod 3) */
    for (size_t i = 0; i < n; i++) {
        uint32_t x = (uint32_t)a[i];
        ones = (ones ^ x) & ~twos;
        twos = (twos ^ x) & ~ones;
    }
    return (int32_t)ones;
}
/* {2, 2, 3, 2} -> 3,  {0, 1, 0, 1, 0, 1, 99} -> 99 */
```

**Points:** each bit position counts occurrences modulo 3 using two bitmasks as a 2-bit counter; after the loop, bits of numbers that appeared three times have cancelled. O(n), O(1). A simpler version to explain first: for each of the 32 bit positions, count how many numbers have that bit set and keep it if `count % 3 != 0`.

**Simple version to explain first**

```c
#include <stdint.h>
#include <stdio.h>

uint32_t single_number_bits(const uint32_t *a, int n)
{
    uint32_t result = 0;
    for (int bit = 0; bit < 32; bit++) {
        int count = 0;
        for (int i = 0; i < n; i++) count += (a[i] >> bit) & 1u;
        if (count % 3) result |= 1u << bit;
    }
    return result;
}

int main(void)
{
    uint32_t a[] = { 5, 3, 5, 5, 3, 9, 3 };
    printf("%u\n", single_number_bits(a, 7));     /* 9 */
    return 0;
}
```

32 × n operations — still O(n).

**Dry run of the counting idea with `{5, 5, 5, 3}`:** bit 0: three 5s (bit 0 = 1) + one 3 (1) → 4 → 4 % 3 = 1 → set; bit 1: only the 3 → 1 → set; bit 2: three 5s → 3 → 0. Result 0b011 = 3.

**The ones/twos trick:** `ones` holds bits seen 1 time (mod 3), `twos` bits seen 2 times. For each x: `ones = (ones ^ x) & ~twos; twos = (twos ^ x) & ~ones;`. A bit seen a third time is cleared from both, so at the end `ones` is the answer.

**The family of "single number" problems**

| Problem | Trick |
|---|---|
| Others appear twice | XOR of everything (pairs cancel) |
| Others appear three times | bit counts mod 3 |
| Two singles, others twice | XOR all → `x`; split numbers by the lowest set bit of `x`; XOR each group |
| Missing number in 0..n | XOR indices and values, or `n(n+1)/2 − sum` |

### Implement a bitmap allocator with find-first-zero. {M}
**Short answer:** Represent N equal-sized blocks with N bits (1 = used, 0 = free) packed into 32-bit words. To allocate, scan the words for one that is not all ones (`word != 0xFFFFFFFF`), find its first zero bit with `__builtin_ctz(~word)`, set that bit and return `word_index * 32 + bit`. To free, check the bit is set (to catch double frees) and clear it.

```c
#include <stdint.h>

#define NBLOCKS 256u
static uint32_t bitmap[NBLOCKS / 32];                 /* 1 = used, 0 = free */

int find_first_zero(void)
{
    for (unsigned w = 0; w < NBLOCKS / 32; w++) {
        if (bitmap[w] != 0xFFFFFFFFu) {               /* skip full words quickly */
            unsigned bit = (unsigned)__builtin_ctz(~bitmap[w]);   /* lowest 0 bit */
            return (int)(w * 32u + bit);
        }
    }
    return -1;                                        /* all used */
}

int bm_alloc(void)
{
    int i = find_first_zero();
    if (i >= 0) bitmap[i / 32] |= 1u << (i % 32);
    return i;
}

void bm_free(int i)
{
    bitmap[i / 32] &= ~(1u << (i % 32));
}

/* allocate n contiguous blocks (simple scan) */
int bm_alloc_range(unsigned n)
{
    unsigned run = 0;
    for (unsigned i = 0; i < NBLOCKS; i++) {
        if (bitmap[i / 32] & (1u << (i % 32))) { run = 0; continue; }
        if (++run == n) {
            unsigned start = i + 1 - n;
            for (unsigned j = start; j <= i; j++) bitmap[j / 32] |= 1u << (j % 32);
            return (int)start;
        }
    }
    return -1;
}
```

**Points:** one bit per block makes the metadata tiny (256 blocks → 32 bytes); scan word by word and use `ctz(~word)` to find the first free bit in O(1) per word; add a "next search position" hint to avoid rescanning full words; protect with a lock in concurrent code (or use atomic bit operations). Used for flash sector maps, file-system block allocation, PID and IRQ number allocation (Linux `ida`/`bitmap_find_next_zero_area`), and page-frame allocation in simple kernels.

**Dry run:** bitmap word 0 = `0b...0000_0111` (blocks 0–2 used). `~word` = `...1111_1000`; `ctz` = 3 → allocate block 3; word becomes `...0000_1111`.

**Why `ctz(~word)`:** inverting turns free bits into ones; counting trailing zeros finds the lowest free bit in one instruction (`RBIT` + `CLZ` on Arm), so each word is examined in O(1) and the scan costs O(N/32).

**Allocating a run of k contiguous blocks:** search for k consecutive zero bits (slide a window, or use `__builtin_ctz`/shifts to skip quickly); this is what file systems and DMA memory allocators need.

**Improvements**

- **Next-fit hint:** remember where the last allocation ended and start searching there — avoids rescanning full words at the start.
- **Summary bitmap:** one bit per word saying "this word has a free bit" — two-level search for large maps.
- **Concurrency:** a lock, or atomic `fetch_or` to claim a bit (retry if someone else got it first).

**Memory cost:** 1 bit per block — 4096 blocks need only 512 bytes of metadata, compared with a pointer-based free list that needs space in every block.

**Real uses:** Linux IDA/IDR (IDs, minor numbers), page and block allocation in file systems (ext4 block bitmaps), flash sector maps in FTLs, interrupt vector and PID allocation, and RTOS memory pools.

### Simulate a two-level page-table walk. {H}
**Short answer:** Split the virtual address into fields: for a 32-bit address with 4 KB pages, bits 31–22 index the first-level table (1024 entries), bits 21–12 index the second-level table, and bits 11–0 are the offset within the page. Read the level-1 entry; if it is not valid, report a translation fault; otherwise it gives the physical address of the level-2 table. Read the level-2 entry, check valid and permission bits, then combine its physical frame number with the unchanged offset.

```c
#include <stdint.h>
#include <stdbool.h>

/* 32-bit VA: [31:22] L1 index, [21:12] L2 index, [11:0] page offset; 4-byte entries */
#define PTE_VALID (1u << 0)
#define PTE_WRITE (1u << 1)
#define PTE_USER  (1u << 2)
#define PTE_ADDR(e) ((e) & 0xFFFFF000u)

typedef enum { XLATE_OK, FAULT_L1, FAULT_L2, FAULT_PERM } xlate_t;

/* phys_read32 simulates reading physical memory where the tables live */
uint32_t phys_read32(uint32_t pa);

xlate_t translate(uint32_t l1_base, uint32_t va, bool write, bool user, uint32_t *pa)
{
    uint32_t l1e = phys_read32(l1_base + ((va >> 22) & 0x3FFu) * 4u);
    if (!(l1e & PTE_VALID)) return FAULT_L1;

    uint32_t l2e = phys_read32(PTE_ADDR(l1e) + ((va >> 12) & 0x3FFu) * 4u);
    if (!(l2e & PTE_VALID)) return FAULT_L2;

    if ((write && !(l2e & PTE_WRITE)) || (user && !(l2e & PTE_USER))) return FAULT_PERM;

    *pa = PTE_ADDR(l2e) | (va & 0xFFFu);              /* frame + offset */
    return XLATE_OK;
}
```

**Points:** split the VA into indexes and offset; each level's entry gives the physical address of the next table; check valid and permission bits and return a precise fault type (the OS needs it to decide between demand paging, copy-on-write and SIGSEGV); combine the final frame with the unchanged offset. Follow-ups: add a small TLB cache in front (array indexed by VPN with tags), large pages (an L1 entry that maps 4 MB directly), accessed/dirty bit updates, and the 4-level 9-9-9-9-12 split of ARM64.

**Worked example (VA = 0x0040_3A10)**

| field | bits | value |
|---|---|---|
| L1 index | 31–22 | 0x001 |
| L2 index | 21–12 | 0x003 |
| offset | 11–0 | 0xA10 |

If `L1[1]` points to a table at 0x8000_0000 and that table's entry 3 maps frame 0x1234 with valid + read/write bits, the physical address is `0x1234 << 12 | 0xA10 = 0x0123_4A10`.

**Fault types the walk should distinguish**

| Condition | Fault | What the OS does |
|---|---|---|
| L1 or L2 entry not valid | translation fault | demand paging, or SIGSEGV if the address is not mapped |
| Write to a read-only page | permission fault | copy-on-write, or SIGSEGV |
| User access to a kernel page | permission fault | SIGSEGV |
| Execute from a non-executable page (XN/NX) | permission fault | SIGSEGV (security) |

**Why multiple levels:** a flat table for 4 GB of 4 KB pages needs 1 M entries (4 MB) per process even if most of the address space is unused; with two levels, unused regions need no second-level tables.

**Real hardware:** ARMv8-A uses 4 levels for 48-bit addresses with 4 KB granules (9 bits per level), x86-64 uses 4 or 5 levels; the TLB caches translations so most accesses skip the walk; a cache-friendly simulator would add a small TLB array in front (tag = VPN, data = frame + permissions) and count hits and misses.

**Virtualisation follow-up:** with two-stage translation (guest page tables + hypervisor stage 2), each guest table access is itself translated, so a TLB miss can take up to 24 memory accesses with 4-level tables in both stages.

### Look up which guest memory region contains a guest physical address. {M}
**Short answer:** Keep the guest's RAM regions (guest physical start, size, host virtual address) in an array sorted by start address and binary-search for the last region whose start is ≤ the address. If the address (and the whole access length) lies inside that region, translate it with `host = region.hva + (gpa − region.gpa)`; otherwise it is not RAM — typically an MMIO address that must be emulated by a device model.

```c
#include <stdint.h>
#include <stddef.h>

typedef struct {
    uint64_t gpa_start;      /* guest physical start */
    uint64_t size;
    uint8_t *hva;            /* host virtual address where it is mapped */
} mem_region_t;

/* regions sorted by gpa_start and non-overlapping */
uint8_t *gpa_to_hva(const mem_region_t *r, size_t n, uint64_t gpa, uint64_t len)
{
    size_t lo = 0, hi = n;
    while (lo < hi) {                                 /* binary search for the last start <= gpa */
        size_t mid = lo + (hi - lo) / 2;
        if (r[mid].gpa_start <= gpa) lo = mid + 1; else hi = mid;
    }
    if (lo == 0) return NULL;
    const mem_region_t *m = &r[lo - 1];
    uint64_t off = gpa - m->gpa_start;
    if (off >= m->size || len > m->size - off) return NULL;   /* outside, or crosses the end */
    return m->hva + off;
}
```

**Points:** this is what a VMM (QEMU, Firecracker, KVM's memslots) does to turn a guest physical address from a device or exit into a host pointer. Keep regions sorted for O(log n) lookup (KVM caches the last-used slot too); check that the whole access fits inside one region (an access crossing two regions must be split); return NULL for MMIO holes so the caller emulates a device instead. Never trust guest-supplied addresses and lengths: overflow-safe checks (`len > size - off`) matter here because the guest is untrusted.

**Example memory map**

| region | guest physical | size | host virtual |
|---|---|---|---|
| low RAM | 0x0000_0000 | 2 GB | 0x7f00_0000_0000 |
| MMIO hole | 0x8000_0000 | 1 GB | — (devices) |
| high RAM | 0x1_0000_0000 | 2 GB | 0x7f80_0000_0000 |

GPA 0x1_0000_2000 → high RAM → HVA 0x7f80_0000_2000. GPA 0x9000_0000 → no RAM region → MMIO exit → device emulation.

**Points interviewers check**

- **Bounds of the whole access:** `gpa + len <= region.end`. An access that straddles two regions (or RAM and MMIO) must be split or rejected — otherwise a guest could make the VMM read past the end of a host buffer.
- **Overflow:** compute `gpa - region.start < region.size` instead of `gpa + len` comparisons that can overflow.
- **Never trust guest addresses:** every address coming from the guest (descriptors, DMA addresses, MMIO writes) must be validated this way before use.

**Performance:** binary search is O(log n); KVM additionally caches the last used memslot and uses a tree for large numbers of slots; QEMU uses a flattened view of its MemoryRegion tree (FlatView) for lookups.

**Where this happens:** KVM memslots (`KVM_SET_USER_MEMORY_REGION`), QEMU `address_space_translate`, Firecracker/Cloud Hypervisor `GuestMemoryMmap`, and virtio device emulation translating descriptor addresses.

### Write a simple MMIO device model (register read/write callbacks). {H}
**Short answer:** A device model is a state structure plus two callbacks, `read(offset, size)` and `write(offset, value, size)`, that the VMM calls whenever the guest accesses the device's address range. Each callback switches on the register offset and implements the register's behaviour: return state for reads, update state and trigger side effects (start an operation, clear flags, raise or lower the interrupt) for writes. Invalid offsets or sizes are logged and ignored, never allowed to crash the VMM.

```c
#include <stdint.h>
#include <stdbool.h>

/* a timer device: CTRL @0x00 (bit0 enable, bit1 irq_en), COUNT @0x04 (ro), LOAD @0x08, STATUS @0x0C (w1c) */
typedef struct {
    uint32_t ctrl, count, load, status;
    void (*set_irq)(int level);
} timer_dev_t;

static void update_irq(timer_dev_t *d)
{
    d->set_irq((d->ctrl & 2u) && (d->status & 1u));
}

uint32_t timer_mmio_read(timer_dev_t *d, uint64_t off)
{
    switch (off) {
    case 0x00: return d->ctrl;
    case 0x04: return d->count;
    case 0x08: return d->load;
    case 0x0C: return d->status;
    default:   return 0;                               /* log "guest error: bad offset" */
    }
}

void timer_mmio_write(timer_dev_t *d, uint64_t off, uint32_t val)
{
    switch (off) {
    case 0x00: d->ctrl = val & 3u; if (val & 1u) d->count = d->load; break;
    case 0x08: d->load = val; break;
    case 0x0C: d->status &= ~val; break;              /* write-1-to-clear */
    default:   break;                                  /* COUNT is read-only: ignore writes */
    }
    update_irq(d);
}

void timer_tick(timer_dev_t *d)                        /* called by the emulator's clock */
{
    if (!(d->ctrl & 1u)) return;
    if (d->count && --d->count == 0) {
        d->status |= 1u;                               /* expired */
        d->count = d->load;                            /* auto-reload */
        update_irq(d);
    }
}
```

**Points:** a device model is a state struct plus read/write handlers keyed by register offset, exactly like QEMU's `MemoryRegionOps`; implement access semantics faithfully (read-only, write-1-to-clear, side effects on write); recompute the interrupt line after every state change; ignore or log invalid offsets and sizes instead of crashing (the guest can be malicious); a reset function should restore documented reset values. In QEMU you would also add migration state (`VMStateDescription`).

**Typical register behaviours to model**

| Register | Behaviour |
|---|---|
| ID / VERSION | read-only constant (helps the guest driver probe the device) |
| CTRL | read/write; writing START bit begins an operation |
| STATUS | read-only, reflects state (BUSY, DONE) |
| INT_STATUS | write-1-to-clear: `status &= ~value` |
| INT_ENABLE | read/write mask |
| DATA | read pops a FIFO / write pushes data |

**Interrupt line update after every state change**

`irq_level = (int_status & int_enable) != 0` → call the VMM's `set_irq(level)` when it changes. Level-triggered semantics are the most common for emulated devices.

**Flow of a guest access**

1. The guest executes a load/store to the device's guest physical address.
2. No RAM is mapped there, so the CPU exits to the hypervisor (EPT/stage-2 fault, data abort with syndrome giving address, size and register).
3. KVM returns `KVM_EXIT_MMIO` to the VMM with the address, data and length.
4. The VMM finds the device by address and calls its callback.
5. For reads, the VMM puts the result back into the vCPU register and resumes the guest.

**Robustness and security:** the guest is untrusted — check offset alignment and size, bound FIFO indices, handle reentrancy (a device that DMAs into its own MMIO region), and implement `reset()` to restore power-on values.

**Real examples:** QEMU's `MemoryRegionOps` (`.read`, `.write`, `.valid` sizes), the PL011 UART and virtio-mmio transport models, Firecracker's minimal devices; MMIO exits are slow (microseconds), which is why virtio batches requests in shared memory and uses only occasional doorbell writes.

### Parse a virtqueue descriptor chain. {H}
**Short answer:** Start at the head descriptor index taken from the available ring and follow the `next` field while the NEXT flag is set. For each descriptor, validate the index, translate its guest physical address and length into a host buffer (checking the bounds), and sort it into device-readable buffers (request header and data to write) and device-writable buffers (data to read back and the status byte). Stop with an error if the chain is longer than the queue size (a loop) or a readable buffer follows a writable one.

```c
#include <stdint.h>
#include <stddef.h>

#define VRING_DESC_F_NEXT  1
#define VRING_DESC_F_WRITE 2       /* device writes into this buffer */

struct vring_desc { uint64_t addr; uint32_t len; uint16_t flags; uint16_t next; };

typedef struct { uint8_t *ptr; uint32_t len; int device_writable; } iov_t;

uint8_t *gpa_to_hva_simple(uint64_t gpa, uint32_t len);   /* NULL if invalid */

/* walk the chain starting at `head`; returns number of buffers, or -1 if malformed */
int parse_chain(const struct vring_desc *desc, uint16_t qsize, uint16_t head,
                iov_t *iov, int max_iov)
{
    int n = 0;
    uint16_t i = head;
    for (int hops = 0; ; hops++) {
        if (i >= qsize || hops >= qsize || n >= max_iov) return -1;   /* bad index, loop, too long */
        const struct vring_desc *d = &desc[i];                        /* copy fields once in real code */
        uint8_t *p = gpa_to_hva_simple(d->addr, d->len);
        if (!p) return -1;                                            /* buffer outside guest RAM */
        iov[n].ptr = p;
        iov[n].len = d->len;
        iov[n].device_writable = (d->flags & VRING_DESC_F_WRITE) != 0;
        n++;
        if (!(d->flags & VRING_DESC_F_NEXT)) break;
        i = d->next;
    }
    return n;
}
```

**Points:** a request (e.g. a virtio-blk read) is a chain of descriptors linked by `next`: device-readable buffers (header, data to write) followed by device-writable ones (data to read, status byte). The device takes chain heads from the **available** ring, processes them, and puts `(head, bytes written)` into the **used** ring, then notifies the guest. Security checks are the core of the question: index range, loop detection (a chain can be at most `qsize` long), address translation with length checks, and reading each descriptor once (the guest can change shared memory while you read it: "double fetch" bugs). Indirect descriptors and the packed ring layout are follow-ups.

**Split virtqueue structures (virtio 1.x)**

| Structure | Written by | Content |
|---|---|---|
| Descriptor table | driver (guest) | `{addr, len, flags (NEXT, WRITE, INDIRECT), next}` |
| Available ring | driver | indices of chain heads ready for the device + `idx` |
| Used ring | device (host) | `{id = head index, len = bytes written}` + `idx` |

**virtio-blk read request as a chain**

```
desc 0: header {type = IN, sector}   device-readable,  flags NEXT
desc 1: data buffer (4096 bytes)     device-writable,  flags NEXT | WRITE
desc 2: status byte                  device-writable,  flags WRITE
```

The device reads the header, reads the disk sector into desc 1, writes the status, then puts `{id = 0, len = 4097}` into the used ring and notifies the guest.

**Security checks (the core of the question)**

1. Head and every `next` index < queue size.
2. Count descriptors; more than the queue size means a loop → reject.
3. `addr + len` does not overflow and lies entirely inside guest RAM (memory region lookup).
4. Readable descriptors come before writable ones; the request has the minimum required parts.
5. Read the descriptor once into a local copy — the guest can change shared memory at any time (double-fetch/TOCTOU bugs).
6. Use the correct memory barriers when reading `avail->idx` and before publishing `used->idx`.

**Notifications:** the guest "kicks" the device with an MMIO/PIO write (or `ioeventfd`), the device interrupts the guest (or `irqfd`); event-index fields let each side suppress unnecessary notifications. Packed virtqueues (virtio 1.1) merge the three structures into one ring for better cache behaviour.

### Track dirty pages with a bitmap (for live migration). {M}
**Short answer:** Keep one bit per guest page. Whenever the guest (or an emulated device doing DMA) writes to a page, set its bit. Live migration copies all memory once, then repeatedly reads-and-clears the bitmap and re-sends only the pages that were dirtied since the previous pass, until the remaining dirty set is small enough to send during a brief pause of the guest.

```c
#include <stdint.h>
#include <string.h>

#define PAGE_SHIFT 12
#define GUEST_PAGES 4096u                          /* 16 MB guest */
static uint64_t dirty[GUEST_PAGES / 64];

static inline void mark_dirty(uint64_t gpa)
{
    uint64_t pfn = gpa >> PAGE_SHIFT;
    if (pfn < GUEST_PAGES) dirty[pfn / 64] |= 1ull << (pfn % 64);   /* atomic OR if called concurrently */
}

/* migration loop: send every dirty page once, then clear the bitmap for the next round */
unsigned sync_dirty(void (*send_page)(uint64_t pfn))
{
    unsigned sent = 0;
    for (unsigned w = 0; w < GUEST_PAGES / 64; w++) {
        uint64_t bits = dirty[w];
        dirty[w] = 0;                                /* real code: atomic exchange */
        while (bits) {
            unsigned b = (unsigned)__builtin_ctzll(bits);
            send_page((uint64_t)w * 64 + b);
            bits &= bits - 1;                        /* clear lowest set bit */
            sent++;
        }
    }
    return sent;
}
```

**Points:** one bit per guest page; pages are marked dirty when the guest writes them (KVM write-protects pages in stage-2 or uses hardware dirty tracking/PML, and reports a bitmap with `KVM_GET_DIRTY_LOG`; device emulation marks pages it DMAs into); migration repeatedly sends dirty pages while the guest runs, until the remaining set is small, then pauses the guest for the final copy. Read-and-clear must be atomic per word, or writes between the read and the clear are lost. Iterating set bits with `ctz` and `bits &= bits - 1` skips clean pages quickly.

**Bitmap size:** 4 GB of guest RAM with 4 KB pages = 1,048,576 pages → 1 M bits = **128 KB** of bitmap.

**Marking a page dirty:** `bitmap[pfn / 64] |= 1ull << (pfn % 64)` with an atomic OR when several vCPUs or device threads can mark at once.

**How hypervisors detect guest writes**

| Method | How |
|---|---|
| Write protection | stage-2/EPT entries made read-only; the first write faults to the hypervisor, which sets the bit and makes the page writable again |
| Hardware dirty bits | the MMU sets a dirty flag in the stage-2/EPT entry (Arm FEAT_HAFDBS, x86 A/D bits) |
| Page Modification Logging (Intel PML) | hardware logs dirtied guest physical addresses into a buffer |
| Dirty ring (KVM) | per-vCPU ring of dirtied pages instead of a full bitmap scan |

**Migration loop**

1. Enable dirty logging, copy all RAM (pass 1).
2. Loop: get-and-clear the dirty bitmap (`KVM_GET_DIRTY_LOG`), send those pages.
3. When the dirty rate is low enough (or after a maximum number of passes), pause the vCPUs, send the last dirty pages and device state, resume on the destination.

**Read-and-clear must be atomic with respect to new writes:** otherwise a page written between reading and clearing its bit would be lost. Swap the bitmap atomically (or use atomic exchange per word) and re-protect the pages.

**Convergence problem:** if the guest dirties memory faster than the network can send it, migration never finishes → auto-converge (throttle the vCPUs), post-copy migration (start on the destination and fetch pages on demand), or compress/delta-encode pages.

**Other uses of dirty tracking:** incremental snapshots/checkpoints, framebuffer updates in display emulation (only redraw changed regions), and fault-tolerant VM replication.

### Detect a cycle in a directed graph. {M}
**Short answer:** Run a depth-first search that colours each node: **white** (not visited), **grey** (on the current DFS path), **black** (finished). Reaching a grey node from the current node means the edge points back into the current path — a cycle. If every node finishes without that happening, the graph is acyclic. O(V + E) time.

```c
#include <stdbool.h>

#define MAXN 16
static int adj[MAXN][MAXN], deg[MAXN];       /* adjacency lists */
static int color[MAXN];                      /* 0 = white (unvisited), 1 = grey (on stack), 2 = black (done) */

static bool dfs_cycle(int u)
{
    color[u] = 1;
    for (int k = 0; k < deg[u]; k++) {
        int v = adj[u][k];
        if (color[v] == 1) return true;                 /* back edge to a node on the current path */
        if (color[v] == 0 && dfs_cycle(v)) return true;
    }
    color[u] = 2;
    return false;
}

bool has_cycle(int n)
{
    for (int i = 0; i < n; i++) color[i] = 0;
    for (int i = 0; i < n; i++)
        if (color[i] == 0 && dfs_cycle(i)) return true;
    return false;
}
```

**Points:** three-colour DFS: reaching a **grey** node (still on the recursion stack) means a back edge, i.e. a cycle; black nodes are finished and safe. O(V + E). For undirected graphs, track the parent instead. Embedded and systems uses: lock-order validation (Linux lockdep builds a graph of lock dependencies and reports cycles = potential deadlocks), detecting circular dependencies between drivers or build targets. Recursion depth equals the path length, so use an explicit stack on small MCUs.

**Dry run (edges A→B, B→C, C→A, C→D)**

| step | visit | colours | note |
|---|---|---|---|
| 1 | A | A grey | |
| 2 | B | A,B grey | |
| 3 | C | A,B,C grey | |
| 4 | C→A | A is grey | back edge → **cycle A→B→C→A** |

If the edge C→A were removed: C→D visits D (grey → black), C black, B black, A black → no cycle.

**Why two "visited" states are needed:** with only a visited flag, reaching a node that was finished in an earlier branch (black) would falsely look like a cycle. Black nodes are safe — all paths from them were already explored.

**Iterative version (avoids deep recursion on embedded targets):** keep an explicit stack of `(node, next edge index)`; mark grey when pushed, black when all edges are processed.

**Kahn's algorithm alternative:** repeatedly remove nodes with in-degree 0 (topological sort, next question); if some nodes are never removed, they are on or behind a cycle.

**Undirected graphs:** a cycle exists if DFS reaches an already visited node that is not the current node's parent (or use union-find: an edge joining two nodes already in the same set closes a cycle).

**Systems uses:** Linux **lockdep** records "lock A taken while holding lock B" edges and reports a cycle as a possible deadlock; detecting circular dependencies between drivers, services (systemd ordering cycles) or build targets; wait-for graphs in deadlock detection.

### Order device initialisation with a topological sort. {M}
**Short answer:** Treat each device as a node and each dependency ("the I2C controller must be ready before the sensor") as an edge from the supplier to the consumer. Use Kahn's algorithm: count incoming edges for every device, put all devices with no dependencies in a queue, and repeatedly take one, initialise it and decrement the count of each device that depends on it — any device whose count reaches zero joins the queue. If fewer than N devices get initialised, the remaining ones form a dependency cycle. O(V + E).

```c
#include <stdio.h>

/* edge u -> v means "u must be initialised before v" (e.g. clock -> i2c -> pmic -> display) */
#define MAXN 16
static int adj[MAXN][MAXN], deg[MAXN], indeg[MAXN];

void add_dep(int before, int after) { adj[before][deg[before]++] = after; indeg[after]++; }

/* Kahn's algorithm: returns number of devices ordered; less than n means a cycle */
int init_order(int n, int *order)
{
    int queue[MAXN], qh = 0, qt = 0, cnt = 0;
    int in[MAXN];
    for (int i = 0; i < n; i++) { in[i] = indeg[i]; if (in[i] == 0) queue[qt++] = i; }
    while (qh < qt) {
        int u = queue[qh++];
        order[cnt++] = u;
        for (int k = 0; k < deg[u]; k++)
            if (--in[adj[u][k]] == 0) queue[qt++] = adj[u][k];
    }
    return cnt;
}
```

**Points:** start with devices that depend on nothing, "initialise" them, and remove their outgoing edges; any device whose remaining dependency count reaches zero becomes ready. If fewer than `n` devices come out, there is a dependency cycle (report it). O(V + E). Real systems: the Linux driver core handles probe ordering with **deferred probing** (a driver returns `-EPROBE_DEFER` when a supplier such as a clock or regulator is not ready) and **fw_devlink**, which builds supplier/consumer links from the device tree; systemd orders units with the same idea; Zephyr uses initialisation levels and priorities.

**Dry run**

Dependencies: clock → gpio, clock → i2c, gpio → i2c (pins), i2c → sensor, i2c → pmic, pmic → display.

| step | queue | initialise | in-degree changes |
|---|---|---|---|
| start | clock | — | clock 0, gpio 1, i2c 2, sensor 1, pmic 1, display 1 |
| 1 | gpio | clock | gpio 0, i2c 1 |
| 2 | i2c | gpio | i2c 0 |
| 3 | sensor, pmic | i2c | sensor 0, pmic 0 |
| 4 | pmic | sensor | — |
| 5 | display | pmic | display 0 |
| 6 | — | display | done: 6 of 6 |

Order: clock, gpio, i2c, sensor, pmic, display.

**Cycle report:** if, for example, display also depended on sensor and sensor on display, neither would reach in-degree 0; print the devices still with a non-zero count as the cycle participants.

**Shutdown and suspend:** use the **reverse** order (consumers before suppliers).

**Parallel initialisation:** all devices in the queue at the same time are independent and could be initialised in parallel (faster boot).

**How real systems do it**

- **Linux:** device tree phandles create device links (fw_devlink); drivers that probe too early return `-EPROBE_DEFER` and are retried later; initcall levels give a coarse static order.
- **Zephyr:** init levels (PRE_KERNEL_1, POST_KERNEL, APPLICATION) plus priorities within each level, checked at build time from devicetree dependencies.
- **systemd:** `After=`/`Requires=` units are ordered with the same graph algorithms; ordering cycles are reported and broken.
