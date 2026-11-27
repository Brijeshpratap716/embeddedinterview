---
slug: linux-system-programming
title: Linux System Programming
icon: 🐚
level: Intermediate
order: 11
desc: Signals, fork bombs and resource limits, pthread_exit, /proc /sys /dev, permissions, inodes and links, file system layouts, mmap and mprotect, the page cache, sockets, epoll and the networking stack.
---
Linux system programming questions test whether you can write and debug real programs on embedded Linux: how processes get signals, how files and permissions work, how memory mapping and the page cache behave, and how network servers handle many clients. Each answer gives the short version first, then working code or commands, and the follow-ups interviewers usually ask.

### What are signals, and how are they delivered and handled? {M}
Signals are asynchronous notifications delivered to a process or thread. They can originate from the kernel, another permitted process or the program itself.

#### Delivery
A signal becomes pending, then is delivered to an eligible thread when unblocked. The kernel applies the default action or arranges execution of an installed handler in userspace. On return, the saved context is restored.

```c
static volatile sig_atomic_t stop;
static void handler(int sig)
{
    (void)sig;
    stop = 1;
}
/* In main, check errors: */
struct sigaction sa = {0};
sa.sa_handler = handler;
sigemptyset(&sa.sa_mask);
sigaction(SIGINT, &sa, NULL);
```

Use sigaction rather than relying on historical signal() semantics. Standard signals can coalesce; real-time signals can queue. SIGKILL and SIGSTOP cannot be caught or blocked.

**Interview takeaway:** A handler is not a normal thread. Call only async-signal-safe functions there; use a flag, self-pipe or signalfd-based design to defer work.

### What happens when a program executes an illegal instruction or accesses invalid memory? {M}
Invalid instructions and invalid memory accesses typically cause synchronous CPU exceptions. The kernel examines the cause and either resolves it or delivers a signal.

```text
User instruction -> CPU exception -> kernel handler
   | valid demand-page / COW fault -> repair mapping -> retry
   + invalid access -> SIGSEGV or SIGBUS
   + illegal instruction -> SIGILL
```

For example, writing to an unmapped address may produce SIGSEGV with si_code indicating an unmapped address or protection violation. Some bus/alignment or file-backed mapping failures produce SIGBUS. An unsupported instruction may result in SIGILL.

#### Debug
```bash
gdb ./app core
# bt; info registers; x/i $pc
```
Core-dump generation depends on limits and system policy.

**Interview takeaway:** A page fault is not always a programming error; demand paging is normal. Do not attempt to blindly resume a faulting instruction from a signal handler.

### What is a fork bomb, and how do ulimit and cgroups protect against it? {M}
A fork bomb is a process-creation denial of service: uncontrolled creation of child processes can exhaust task slots, memory and CPU resources.

#### Protection
- RLIMIT_NPROC limits process/thread creation for a real user ID, with privilege-related exceptions.
- The cgroup v2 pids controller restricts the number of tasks in a workload hierarchy using pids.max.
- Service managers can set TasksMax and memory/CPU limits.

For example, a dedicated test service can have TasksMax=64 so a defective worker cannot create unlimited tasks. Monitor pids.current and pids.events. Creation beyond a task limit normally fails with EAGAIN.

**Interview takeaway:** Limit tasks at workload boundaries; user-level limits alone may be insufficient. Never test uncontrolled process creation on a shared or production system.

### How do you limit the CPU and memory used by processes on Linux? {M}
Linux uses resource limits and cgroups to restrict process or workload resource consumption.

| Mechanism | Example |
|---|---|
| RLIMIT_AS | Limit virtual address space per process |
| RLIMIT_CPU | Limit accumulated CPU time |
| cgroup v2 cpu.max | CPU bandwidth quota and period |
| cgroup v2 memory.max | Hard memory limit for a workload |
| cgroup v2 pids.max | Maximum task count |

#### Example
A service can use CPUQuota=50% and MemoryMax=256M with systemd resource controls. CPU quotas throttle usage over periods, rather than setting the CPU clock speed. A memory cgroup may reclaim memory and invoke its OOM policy if it cannot satisfy allocations.

**Interview takeaway:** RLIMIT_AS is not the same as resident memory; nice affects relative scheduling weight rather than imposing a hard CPU cap. Prefer cgroups for a complete process tree.

### When should you call pthread_exit() instead of exit()? {M}
pthread_exit() terminates only the calling thread. exit() terminates the whole process, including its other threads.

```c
void *worker(void *arg)
{
    (void)arg;
    return NULL; /* equivalent to pthread_exit(NULL) */
}
int main(void)
{
    pthread_t t;
    if (pthread_create(&t,NULL,worker,NULL)!=0)
        return 1;
    pthread_join(t,NULL);
    return 0;
}
```

Returning from main is equivalent to exit, so other threads terminate. If the initial thread calls pthread_exit(NULL), other threads may continue until they terminate. A joinable thread's resources are reclaimed with pthread_join; detached threads are reclaimed automatically.

**Interview takeaway:** Do not return pointers to a terminating thread's stack. Prefer explicit joins and orderly shutdown over leaving background threads unmanaged.

### What are /proc, /sys and /dev used for? {E}
**Short answer:** They are virtual (in-memory) file systems that the kernel uses to talk to user space. **`/proc`** shows information about processes (`/proc/<pid>/...`) and many kernel statistics and settings (`/proc/meminfo`, `/proc/interrupts`, `/proc/sys/...`). **`/sys`** (sysfs) shows the device model: every bus, device, driver and class, with one value per file. **`/dev`** contains device nodes (character and block devices) that programs open to talk to drivers.

**`/proc` (procfs)**

| Path | Contents |
|---|---|
| `/proc/<pid>/status`, `stat`, `maps`, `fd/`, `cmdline`, `environ` | process state, memory map, open files |
| `/proc/meminfo`, `/proc/cpuinfo`, `/proc/loadavg` | memory, CPUs, load |
| `/proc/interrupts`, `/proc/softirqs` | interrupt counts per CPU |
| `/proc/cmdline` | kernel command line |
| `/proc/sys/...` (`sysctl`) | tunable kernel parameters, e.g. `/proc/sys/vm/swappiness`, `/proc/sys/net/ipv4/ip_forward` |
| `/proc/device-tree` | the device tree the kernel booted with |

**`/sys` (sysfs)**

- `/sys/class/net/eth0/`, `/sys/class/leds/`, `/sys/class/thermal/`: devices grouped by type.
- `/sys/bus/platform/devices/`, `/sys/bus/i2c/drivers/`: buses, devices and drivers; `bind`/`unbind` files attach or detach a driver.
- `/sys/kernel/debug` (debugfs, if mounted), `/sys/fs/cgroup` (cgroups), `/sys/firmware/devicetree`.
- One value per file, in text, e.g. `cat /sys/class/thermal/thermal_zone0/temp`.

**`/dev`**

- Character devices (`/dev/ttyS0`, `/dev/i2c-1`, `/dev/gpiochip0`, `/dev/null`) and block devices (`/dev/mmcblk0`, `/dev/sda`).
- Created automatically by **devtmpfs** and managed by **udev**/**mdev**, which set permissions and create friendly symlinks (`/dev/disk/by-uuid/...`).
- A device node is identified by its **major/minor numbers**, which select the driver and the device instance.

**Role in system administration:** almost every monitoring and configuration tool reads these files. `ps`, `top` and `free` read `/proc`; `ip`, `lsblk`, `lsusb` and `udevadm` use `/sys`; and `sysctl -w` writes `/proc/sys`. Scripts can do the same with `cat` and `echo`, which is very handy on minimal embedded systems with only BusyBox.

**Rule of thumb for driver writers:** process and legacy information in `/proc`, device attributes in `/sys`, data streams and control through a `/dev` node, and debugging-only information in `debugfs`.

### How do Linux file permissions work? {E}
**Short answer:** Every file has an owner (UID), a group (GID) and three sets of permission bits: read, write and execute for the **owner**, the **group**, and **others**. When a process accesses a file, the kernel checks the process's effective UID and groups against these bits: owner bits if it owns the file, else group bits if it is in the group, else the "other" bits. Root (UID 0) bypasses most checks, and the special bits **setuid**, **setgid** and **sticky** add more behaviour.

```
$ ls -l /usr/bin/passwd report.txt
-rwsr-xr-x 1 root  root  68208 ... /usr/bin/passwd
-rw-r----- 1 brij  dev    1024 ... report.txt
 │└┬┘└┬┘└┬┘
 │ │  │  └ others: r-- 
 │ │  └ group: r-x
 │ └ owner: rws (s = setuid + execute)
 └ file type: - file, d directory, l symlink, c char device, b block device
```

**What r, w, x mean**

| | On a file | On a directory |
|---|---|---|
| r (4) | read contents | list names (`ls`) |
| w (2) | modify contents | create, delete, rename entries (deleting a file needs **w on the directory**, not on the file) |
| x (1) | execute as a program | enter it / access entries by name (`cd`, path lookup) |

```bash
chmod 640 report.txt         # rw- r-- ---
chmod u+x script.sh
chown brij:dev report.txt
umask 022                    # new files get 644, new directories 755
```

**Special bits**

- **setuid (4000)** on an executable: it runs with the **file owner's** UID. `passwd` is setuid root so a normal user can update `/etc/shadow`. Setuid programs are prime security targets and must be minimal.
- **setgid (2000)**: on an executable, runs with the file's group; on a directory, new files inherit the directory's group (useful for shared project directories).
- **sticky (1000)** on a directory: only a file's owner can delete it, even if others have write permission on the directory (`/tmp` is `drwxrwxrwt`).

**The kernel's role:** every `open()`, `execve()`, `unlink()` and so on goes through permission checks in the VFS (`inode_permission()`), using the process's **credentials** (real, effective and saved UID/GID, supplementary groups, capabilities). User space cannot bypass them.

**Beyond the basics**

- **Capabilities** split root's powers into pieces (`CAP_NET_BIND_SERVICE` to bind ports < 1024, `CAP_SYS_NICE`, `CAP_NET_ADMIN`), so a service can get only what it needs: `setcap cap_net_bind_service+ep ./server`.
- **ACLs** (`setfacl`) give permissions to additional specific users or groups.
- **LSMs** (SELinux, AppArmor, Smack) add mandatory access control on top.

**Embedded advice:** do not run the whole application as root. Create a dedicated user, give it access to only the device nodes it needs (udev rules setting group/mode), and add capabilities instead of root where necessary.

### What is an inode? What is the difference between a hard link and a symbolic link? {E}
**Short answer:** An **inode** is the on-disk structure that describes a file: its type, permissions, owner, size, timestamps, link count, and where its data blocks are. It does **not** contain the file name; names live in **directory entries**, which map a name to an inode number. A **hard link** is an additional directory entry pointing to the same inode. A **symbolic (soft) link** is a separate small file that contains a path to another file.

```bash
echo hello > a.txt
ln a.txt b.txt          # hard link: same inode
ln -s a.txt c.txt       # symbolic link: new inode containing the text "a.txt"
ls -li
# 1311 -rw-r--r-- 2 ... a.txt
# 1311 -rw-r--r-- 2 ... b.txt          <- same inode number, link count 2
# 1312 lrwxrwxrwx 1 ... c.txt -> a.txt
```

| | Hard link | Symbolic link |
|---|---|---|
| What it is | another name for the same inode | a file containing a path |
| Inode | same as the target | its own |
| Survives deleting the original name | yes, data stays until the link count is 0 | no, becomes a dangling link |
| Across file systems | no | yes |
| To directories | no (would allow loops) | yes |
| `ls -l` | looks like a normal file | shows `-> target` |

**How deleting works:** `rm` calls `unlink()`, which removes one directory entry and decrements the inode's link count. The data is freed only when the link count is 0 **and** no process has the file open. That is why deleting a large log file that a program still has open does not free disk space until the program closes it (find these with `lsof +L1`).

**"Everything is a file":** in Linux, many objects are accessed through the file interface: regular files, directories, devices (`/dev`), pipes, sockets, and kernel information (`/proc`, `/sys`). They all have inodes in the VFS, and programs use `open`/`read`/`write`/`close` on them. This uniformity is why shell tools can work with devices and kernel data directly.

**Inode limits:** a file system has a fixed number of inodes (ext4 sets it at `mkfs` time). You can run out of inodes with free space still available if you create millions of tiny files: `df -i` shows usage. Dividing free space by free inodes gives the average space available per future file.

### How do file systems store file data: contiguous, linked (FAT), indexed and extents? {M}
**Short answer:** **Contiguous** allocation stores a file in consecutive blocks (fast, simple, but suffers from fragmentation and files cannot grow easily). **Linked** allocation chains blocks together, as FAT does with its File Allocation Table (no external fragmentation, but random access must follow the chain). **Indexed** allocation keeps a list of block numbers per file in the inode (direct, indirect, double-indirect pointers in ext2/3). **Extents** (ext4, XFS, Btrfs) record runs of consecutive blocks as (start, length), which is compact for large, contiguous files.

| Method | Example | Random access | Growth | Metadata size |
|---|---|---|---|---|
| Contiguous | CD-ROM (ISO 9660), some flash images | O(1) | hard (need free space after the file) | tiny (start + length) |
| Linked list | FAT12/16/32, exFAT | O(n): walk the FAT chain | easy | one FAT entry per cluster |
| Indexed block map | ext2/ext3 (12 direct + indirect pointers) | O(1)–O(3) lookups | easy | one pointer per block |
| Extents | ext4, XFS, NTFS, APFS | O(log n) in an extent tree | easy | one entry per contiguous run |

**FAT in more detail:** the directory entry points to the first cluster; the FAT table entry for each cluster gives the next cluster, ending with an end-of-chain marker. Caching the FAT in RAM makes walking it fast. Interview follow-ups:

- *Why keep a pointer to the last block as well?* Appending (the most common write to log files) would not need to walk the whole chain.
- *A doubly linked FAT?* Seeking backwards becomes faster, but every entry doubles in size and the FAT is twice as large to cache and to write. Most access is sequential forwards, so the cost is usually not worth it.

**Extents vs block maps:** a contiguous 1 GB file with 4 KB blocks needs 262,144 block pointers (about 1 MB of metadata) but only **8 extents** in ext4 (each extent covers up to 128 MB = 32,768 blocks), each 12 bytes. A block map is better only for files that are badly fragmented, where every block is in a different place and each extent would describe one block.

**Hybrid (first N blocks contiguous, the rest linked):** small files get fast contiguous access with minimal metadata; large files can still grow. Downsides: two code paths, random access into the linked tail is slow, and reserving N contiguous blocks causes fragmentation.

**Embedded relevance:** SD cards and USB sticks use FAT/exFAT because every OS can read them, but FAT has no journal, so a power cut during a write can corrupt the file system. Use ext4/F2FS (or a journaled FAT driver) for data that must survive power loss, and keep FAT only for exchange partitions.

### What is mmap, and what is mprotect used for? {M}
**Short answer:** `mmap()` maps a file or anonymous memory into the process's address space, so the program can access it with normal pointers instead of `read()`/`write()`. Pages are loaded on demand by page faults, and with `MAP_SHARED` changes go back to the file (or are visible to other processes mapping it). `mprotect()` changes the access permissions (read, write, execute) of pages that are already mapped.

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void)
{
    int fd = open("data.bin", O_RDONLY);
    struct stat st;
    fstat(fd, &st);
    const unsigned char *p = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);                         /* the mapping stays valid */
    printf("first byte: %02x\n", p[0]);
    munmap((void *)p, st.st_size);
    return 0;
}
```

**Uses of mmap**

| Use | Flags |
|---|---|
| Read a large file randomly without copying it into a buffer | `MAP_PRIVATE`, `PROT_READ` |
| Share memory between processes | `MAP_SHARED` on a `shm_open()` fd or a file |
| Allocate large memory (glibc `malloc` does this above 128 KB) | `MAP_PRIVATE | MAP_ANONYMOUS` |
| Access device memory / frame buffers / DMA buffers from user space | `MAP_SHARED` on a `/dev` node (driver implements `mmap`) |
| Load executables and shared libraries | used by the kernel's ELF loader and `ld.so` |

**mprotect scenarios**

1. **Read-only after initialisation:** build a configuration table or lookup table at start-up, then `mprotect(p, len, PROT_READ)`. Any later accidental write causes an immediate `SIGSEGV` instead of silent corruption, and the table cannot be modified by an attacker exploiting a memory bug.
2. **JIT compilers (W^X):** write generated machine code into a `PROT_READ | PROT_WRITE` page, then switch it to `PROT_READ | PROT_EXEC` before running it. A page should never be writable and executable at the same time.
3. **Guard pages:** `PROT_NONE` pages around buffers or thread stacks catch overflows.
4. **Garbage collectors and checkpointing:** write-protect pages to detect which ones change (the fault handler records the page and re-enables writing).

**Rules:** addresses and lengths are page-aligned (`sysconf(_SC_PAGESIZE)`); `mprotect` works on whole pages; and accessing beyond the end of a mapped file (in the last partial page and beyond) gives `SIGBUS`.

**mmap vs read:** `mmap` avoids a copy and is great for random access to large files. For sequential reads, `read()` with a big buffer is often just as fast and handles errors (an I/O error becomes a `SIGBUS` with mmap, which is harder to handle).

### What is the page cache, and how do you write a file safely so it survives a power loss? {M}
**Short answer:** Linux keeps recently used file data in RAM in the **page cache**. `read()` is served from it when possible, and `write()` only copies data into it and marks the pages dirty; the kernel writes them to storage later (by default within about 30 seconds). To make data durable you must call `fsync()` (or `fdatasync()`). To replace a file atomically, write a temporary file, `fsync()` it, `rename()` it over the old one, and `fsync()` the directory.

**Safe update pattern**

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int save_config(const char *dir, const char *data, size_t len)
{
    char tmp[256], dst[256];
    snprintf(tmp, sizeof tmp, "%s/config.tmp", dir);
    snprintf(dst, sizeof dst, "%s/config", dir);

    int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) return -1;
    if (write(fd, data, len) != (ssize_t)len || fsync(fd) != 0) { close(fd); return -1; }
    close(fd);

    if (rename(tmp, dst) != 0) return -1;     /* atomic replace on POSIX file systems */

    int dfd = open(dir, O_RDONLY | O_DIRECTORY);
    if (dfd >= 0) { fsync(dfd); close(dfd); }  /* make the rename itself durable */
    return 0;
}
```

After a power cut you see either the complete old file or the complete new one, never a half-written mix.

**Why each step**

- `write()` returning success only means the data is in the page cache.
- `fsync(fd)` waits until the file's data and metadata are on the storage device (and asks the device to flush its own cache).
- `rename()` is atomic: the name points either to the old inode or the new one.
- `fsync(dir)` persists the directory entry change.

**Buffered vs direct I/O**

| | Buffered (default) | `O_DIRECT` |
|---|---|---|
| Path | through the page cache | straight between user buffer and device (DMA) |
| Benefits | read caching, write combining, read-ahead | no double caching, predictable memory use |
| Requirements | none | aligned buffers, offsets and sizes (typically 512 B or 4 KB) |
| Used by | almost everything | databases with their own cache, some video recorders |

**Useful knobs:** `vm.dirty_ratio`, `vm.dirty_background_ratio` and `vm.dirty_expire_centisecs` control how much dirty data may accumulate and how old it may get. `sync` flushes everything. `echo 3 > /proc/sys/vm/drop_caches` drops clean caches (for benchmarking only).

**Embedded relevance:** devices get their power pulled. Configuration and calibration data must be written with this pattern (or stored in a format with checksums and two alternating copies), and logs should not be `fsync`'d on every line, because that wears out flash.

### What is the sequence of socket calls for a TCP server and client? {E}
**Short answer:** **Server:** `socket()` → `bind()` (choose IP and port) → `listen()` → `accept()` (blocks until a client connects, returns a new socket for that connection) → `read()`/`write()` (or `recv`/`send`) → `close()`. **Client:** `socket()` → `connect()` (TCP three-way handshake) → `write()`/`read()` → `close()`.

```
Server                                  Client
socket()                                socket()
bind(port 8080)
listen()
accept()  ◄──── SYN / SYN-ACK / ACK ──── connect()
recv()    ◄──────── request ─────────── send()
send()    ───────── response ─────────► recv()
close()   ◄──────── FIN/ACK ──────────► close()
```

**Minimal TCP echo server**

```c
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void)
{
    int ls = socket(AF_INET, SOCK_STREAM, 0);
    int on = 1;
    setsockopt(ls, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);

    struct sockaddr_in a = { .sin_family = AF_INET, .sin_port = htons(8080),
                             .sin_addr.s_addr = htonl(INADDR_ANY) };
    if (bind(ls, (struct sockaddr *)&a, sizeof a) < 0) { perror("bind"); return 1; }
    listen(ls, 16);                               /* backlog of pending connections */

    for (;;) {
        int c = accept(ls, NULL, NULL);           /* blocks */
        if (c < 0) continue;
        char buf[512];
        ssize_t n;
        while ((n = recv(c, buf, sizeof buf, 0)) > 0)
            send(c, buf, (size_t)n, 0);
        close(c);
    }
}
```

**Details interviewers check**

- **Byte order:** ports and addresses are in network byte order (big-endian): `htons`, `htonl`, `ntohs`.
- **`SO_REUSEADDR`** lets the server restart immediately instead of failing with "Address already in use" while old connections are in `TIME_WAIT`.
- **TCP is a byte stream:** one `send()` of 1000 bytes may arrive as several `recv()` calls, and several sends may arrive together. Applications need framing (length prefix or delimiter).
- **Partial writes:** `send()` may send fewer bytes than requested; loop until all are sent.
- **`SIGPIPE`:** writing to a connection the peer closed kills the process unless you ignore `SIGPIPE` or use `MSG_NOSIGNAL`.
- **UDP** is different: `socket(AF_INET, SOCK_DGRAM, 0)`, no `listen`/`accept`/`connect` needed, `sendto`/`recvfrom` with addresses; each datagram is delivered whole or not at all.

**Handling many clients:** one process per client (`fork()` after `accept`), one thread per client, or one thread with `select`/`poll`/`epoll` (see the next question).

### Which socket calls block, and how do select, poll and epoll handle many connections? {M}
**Short answer:** By default `accept()` (until a client connects), `connect()` (until the handshake completes), `recv()`/`read()` (until data arrives), and `send()`/`write()` (until there is room in the send buffer) can all block. To handle many connections in one thread, make the sockets non-blocking and use an I/O multiplexer: `select()` and `poll()` scan a list of descriptors on every call (O(n)), while **`epoll`** registers descriptors once and returns only the ready ones (O(ready)), which scales to tens of thousands of connections.

**Why they block:** each call waits for something outside the program's control: a remote peer, the network, or buffer space. Blocking is efficient (the thread sleeps), but a thread blocked on one socket cannot serve others.

**Options for concurrency**

| Approach | Pros | Cons |
|---|---|---|
| fork per client | simple, isolated | heavy; one process per connection |
| thread per client | simple code | memory per thread (stack), context switches, locking |
| `select` | portable | limited to `FD_SETSIZE` (1024) descriptors, O(n) scan, fd sets rebuilt every call |
| `poll` | no fd limit | still O(n) per call |
| `epoll` (Linux) | O(1) per event, edge or level triggered | Linux-specific |
| `io_uring` | async I/O with few syscalls | newer, more complex |

**epoll event loop sketch**

```c
#include <sys/epoll.h>

int ep = epoll_create1(0);
struct epoll_event ev = { .events = EPOLLIN, .data.fd = listen_fd };
epoll_ctl(ep, EPOLL_CTL_ADD, listen_fd, &ev);

struct epoll_event events[64];
for (;;) {
    int n = epoll_wait(ep, events, 64, -1);       /* sleeps until something is ready */
    for (int i = 0; i < n; i++) {
        int fd = events[i].data.fd;
        if (fd == listen_fd) {
            int c = accept4(listen_fd, NULL, NULL, SOCK_NONBLOCK);
            struct epoll_event cev = { .events = EPOLLIN, .data.fd = c };
            epoll_ctl(ep, EPOLL_CTL_ADD, c, &cev);
        } else {
            handle_client(fd);                    /* non-blocking recv/send */
        }
    }
}
```

**Level vs edge triggered:** level-triggered (default) reports a descriptor as long as it is readable; edge-triggered (`EPOLLET`) reports only when new data arrives, so you must read until `EAGAIN` or you miss data.

**Timeouts without blocking forever:** `SO_RCVTIMEO`/`SO_SNDTIMEO`, a timeout argument to `poll`/`epoll_wait`, or non-blocking `connect()` followed by waiting for writability.

**Embedded relevance:** a gateway with a UART, a CAN socket, a few TCP connections and a timer can run everything in one `epoll` loop (using `timerfd`, `signalfd`, `eventfd`), which avoids threads and locks entirely. Event libraries such as libevent, libuv and Boost.Asio wrap this pattern.

### Why does Linux have a separate socket API instead of using only open/read/write? {M}
**Short answer:** Sockets **are** file descriptors, so `read()`, `write()`, `close()`, `poll()` and `epoll` work on them. But networking needs things a file path cannot express: choosing a protocol family and type (TCP vs UDP vs raw, IPv4 vs IPv6 vs Unix vs CAN), binding to local addresses and ports, connecting to or accepting from remote endpoints that may not exist yet, per-message addresses for datagrams, and many options. The socket API (`socket`, `bind`, `listen`, `accept`, `connect`, `sendto`, `recvfrom`, `setsockopt`, `shutdown`) adds exactly those operations.

**What the file API cannot express**

- **Creation without a name:** `socket(AF_INET6, SOCK_STREAM, 0)` creates an endpoint; there is nothing in the file system to `open()`.
- **Addresses:** a network peer is identified by an address and port (or a CAN ID, or a Bluetooth address), not a path. `bind()`/`connect()` take a generic `struct sockaddr`.
- **Connection set-up:** `listen()`/`accept()` create a **new** descriptor for each incoming connection, a concept files do not have.
- **Datagram semantics:** for UDP, each `sendto()` is one message with its own destination, and `recvfrom()` reports who sent each one. Message boundaries are preserved.
- **Options and control data:** `setsockopt()` (buffer sizes, `TCP_NODELAY`, keepalive, multicast membership, timestamps) and ancillary data with `sendmsg()`/`recvmsg()` (passing file descriptors over Unix sockets, packet info).
- **Half-close:** `shutdown(fd, SHUT_WR)` sends FIN but keeps reading.

**The design choice still unifies a lot:** because sockets are descriptors, they can be inherited across `fork()`, redirected by shells, passed to `poll()`/`epoll()` together with pipes, serial ports and timers, and closed with `close()`.

**Historical note:** the API came from 4.2BSD (1983) and became the POSIX standard. Plan 9 took the opposite approach and represented network connections as files (`/net/tcp/clone`), showing it is possible; it never became mainstream.

**Linux-specific families worth knowing in embedded work:** `AF_CAN` (SocketCAN for CAN bus), `AF_PACKET` (raw Ethernet frames), `AF_NETLINK` (configuring the kernel: routes, interfaces), `AF_UNIX` (local IPC), `AF_VSOCK` (host ↔ VM communication).

### How is the Linux networking stack structured, what is an sk_buff, and how does it compare with the OSI model? {H}
**Short answer:** In Linux, the socket layer and the protocols (TCP, UDP, IP) run in the kernel, network device drivers sit at the bottom, and the application layer is in user space. Packets travel through the layers in a **`struct sk_buff`** (socket buffer), which holds the packet data plus metadata (device, protocol, header offsets, timestamps). Headers are added or removed by moving pointers within the buffer rather than copying data. Linux follows the practical TCP/IP 4-layer model rather than the 7-layer OSI model.

**Layers (receive path, bottom to top)**

```
NIC hardware → DMA into ring buffer → IRQ → NAPI poll (driver)
  → netif_receive_skb()                 link layer (Ethernet, VLAN, bridge)
  → ip_rcv() → routing, netfilter       network layer (IPv4/IPv6)
  → tcp_v4_rcv() / udp_rcv()            transport layer
  → socket receive queue
  → recv() in the application           (copy to user space)
```

Transmit goes the other way: `send()` → TCP segments → IP routing/neighbour lookup → queueing discipline (qdisc, traffic shaping) → driver `ndo_start_xmit()` → DMA to the NIC.

**`sk_buff` essentials**

| Field | Purpose |
|---|---|
| `head`, `data`, `tail`, `end` | buffer boundaries; `data`..`tail` is the current packet |
| `skb_push()` / `skb_pull()` | add/remove a header by moving `data` (no copy) |
| `skb_reserve()` | leave headroom so lower layers can prepend headers |
| `dev`, `protocol`, `mark`, `tstamp` | metadata |
| `transport_header`, `network_header`, `mac_header` | offsets of each header |
| fragments / `skb_shinfo` | scatter-gather pages for large packets (GSO/GRO) |

**OSI vs Linux (TCP/IP)**

| OSI | Linux / TCP/IP | Where |
|---|---|---|
| 7 Application, 6 Presentation, 5 Session | Application (HTTP, MQTT, TLS) | user space |
| 4 Transport | TCP, UDP, SCTP | kernel |
| 3 Network | IPv4, IPv6, ICMP, routing, netfilter | kernel |
| 2 Data link | Ethernet, Wi-Fi (mac80211), bridge, VLAN | kernel + driver |
| 1 Physical | PHY, cable, radio | hardware (PHY driver configures it) |

OSI's presentation and session layers have no separate kernel layer; their functions (encryption, encoding, session management) are in applications or libraries (kernel TLS, `kTLS`, is a partial exception).

**Performance features:** NAPI (polling under load), GRO/GSO (combine or split large packets to reduce per-packet work), checksum and segmentation offload to the NIC, RSS/RPS (spread flows across cores), XDP (eBPF programs at the driver level), and AF_XDP or DPDK for user-space packet processing when the kernel stack is too slow.

**Why networking is treated differently from other I/O:** data arrives unsolicited and at unpredictable times, must be demultiplexed to the right socket by protocol and port, may be lost or reordered (TCP must handle retransmission and flow control), and rates can reach millions of packets per second, so per-packet overhead dominates.

### How do you find out why a Linux program is slow or stuck? {M}
**Short answer:** First look at what the process is doing and waiting for: `top`/`htop` (CPU, state), `ps -o stat,wchan` (where it sleeps), `strace -p PID` (system calls), `cat /proc/PID/stack` (kernel stack, as root), and `gdb -p PID` / `thread apply all bt` (user stacks). Then measure the right resource: `perf top`/`perf record` for CPU, `vmstat`/`iostat` for memory and I/O, `ss` for sockets, and PSI files for contention.

**Step by step**

1. **Is it using CPU?** `top -H -p PID` (per thread). High CPU → profile with `perf record -g -p PID` then `perf report`, or `perf top`.
2. **If not, what is it waiting for?** State `S` or `D` in `ps`. `strace -f -p PID` shows the blocking call (`read` on a socket, `futex` = waiting on a lock, `poll` with a timeout). `/proc/PID/wchan` names the kernel function it sleeps in.
3. **Deadlock?** `gdb -p PID`, `thread apply all bt`: look for threads waiting in `pthread_mutex_lock` on each other's locks.
4. **Memory?** `/proc/PID/status` (`VmRSS`, `VmSwap`), `smem`, `valgrind --tool=massif`, or `heaptrack` for growth; `vmstat 1` for swapping.
5. **I/O?** `iostat -x 1` (device utilisation and latency), `iotop`, `pidstat -d`.
6. **Network?** `ss -tinp` (per-connection queues, retransmits, RTT), `tcpdump`/Wireshark.
7. **System-wide pressure:** `/proc/pressure/{cpu,memory,io}` shows how much time tasks were stalled waiting for each resource.

**Tracing tools for deeper problems:** `ftrace` (`trace-cmd`, function graph, scheduler events), `perf sched latency` (scheduling delays), `bpftrace`/BCC tools (`offcputime`, `biolatency`, `runqlat`), and `ltrace` for library calls.

**Embedded tip:** many of these tools are missing from a minimal image. Build a debug image variant with `perf`, `strace`, `gdbserver` and `trace-cmd`, and use `gdbserver` + a cross `gdb` on your PC with the unstripped binaries from the build system.
