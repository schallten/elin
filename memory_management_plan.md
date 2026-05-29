
# ELIN Memory Subsystem Roadmap
## Segmented Bump Heaps with Handle Indirection
### Target: Embedded (real-time) + PC (general-purpose)

---

## Overview

The memory subsystem is designed for deterministic allocation, zero hidden pauses, and portability across 8-bit microcontrollers to 64-bit PCs. It replaces the current static pools with a tiered allocation model where each memory segment serves a distinct lifetime pattern.

---

## Phase 1: Core Bump Allocator
**Goal:** Enable dynamic allocation with explicit manual lifetime management.

| Item | Description |
|------|-------------|
| **What** | A single heap segment using bump-pointer allocation. Each allocation returns a handle (integer ID) rather than a raw address. |
| **Handle Table** | Flat fixed-size array mapping handle IDs to block metadata (pointer, size, validity flag). |
| **Allocation** | Increment a pointer. O(1). No searching, no splitting. |
| **Deallocation** | Explicit `FREE` invalidates the handle and recycles its slot via a free-list. Memory is not reclaimed; the bump pointer only advances. |
| **Access** | `LOAD_H` and `STORE_H` opcodes read/write cells within a handle's block, with bounds checking against stored size. |
| **Safety** | Use-after-free, double-free, and out-of-bounds access are caught at runtime and logged. No silent memory corruption. |
| **Deliverable** | Programs can allocate, use, and manually free dynamic arrays. All existing static pools remain untouched. |
| **Risk** | Low — additive change, no existing code paths modified. |

---

## Phase 2: Multi-Segment Architecture
**Goal:** Separate long-lived data from temporary scratch data.

| Item | Description |
|------|-------------|
| **Segments** | Four logical segments: Main (0), Temp (1), Interrupt (2), Spare (3). Each is an independent bump-allocated arena. |
| **Main (0)** | Default segment for explicitly managed allocations. Survives until `FREE` or program exit. |
| **Temp (1)** | Scratch-pad for function-local allocations. Compiler auto-inserts `REGION_ENTER`/`REGION_EXIT` around function bodies. |
| **Interrupt (2)** | Tiny reserved segment for ISR-safe allocations. Sized at compile time to worst-case interrupt needs. |
| **Spare (3)** | Overflow or special-purpose segment. Unused until explicitly requested. |
| **Region System** | `REGION_ENTER` saves a segment's bump pointer. `REGION_EXIT` resets it and invalidates all handles in that segment. |
| **Temp Reclamation** | Function returns → entire temp segment wiped. No per-object tracking. O(n) handle-table scan, bounded by fixed `MAX_HANDLES`. |
| **Deliverable** | Recursive functions and loops can allocate temporaries without leaking. No manual `FREE` needed for local arrays. |
| **Risk** | Low — compiler change is limited to wrapping function prologues/epilogues with region markers. |

---

## Phase 3: Embedded Hardening
**Goal:** Eliminate all dynamic allocation from the C++ runtime; make memory usage fully predictable at link time.

| Item | Description |
|------|-------------|
| **Static Binding** | Segments bind to externally provided memory blocks (e.g., `static ll main_heap[2048]`) instead of `malloc`/`new`. |
| **Zero C++ Heap** | The VM itself performs no runtime allocation. All memory is accounted for in the linker map. |
| **Bounds & Failure** | `ALLOC` returns null handle (0) on segment full. Programs can check and handle gracefully. No exceptions, no crashes. |
| **Timing Guarantees** | Published worst-case cycle counts for `ALLOC`, `FREE`, `LOAD_H`, `STORE_H`, and `REGION_EXIT`. Suitable for hard real-time scheduling analysis. |
| **Generation Counters** | Optional optimization: per-segment generation number incremented on `REGION_EXIT`. Handle validity check becomes generation comparison instead of table scan. Makes temp reclamation O(1). |
| **Diagnostics** | `SEG_USED` opcode pushes current segment utilization. Enables runtime memory pressure monitoring without debug symbols. |
| **Deliverable** | ELIN runs on bare-metal microcontrollers with known RAM budget. Worst-case memory usage calculable before flashing. |
| **Risk** | Medium — requires target-specific segment size tuning and timing verification on actual hardware. |

---

## Phase 4: PC Comfort Features
**Goal:** Match the ergonomics expected on desktop/server environments without compromising the embedded core.

| Item | Description |
|------|-------------|
| **Dynamic Growth** | Segments backed by `malloc`/`new` can grow on demand when full. Triggered automatically or via explicit `GROW` opcode. |
| **Compaction** | Optional background pass moves live objects to segment start, updates cached pointers in handle table, resets bump pointer. Triggered by memory pressure or explicit `COMPACT` opcode. |
| **Incremental** | Compaction can be split across multiple VM instruction cycles to avoid visible pauses in interactive programs. |
| **Profiling Hooks** | Runtime callbacks for allocation events, segment pressure thresholds, and handle table saturation. Integrates with external memory profilers. |
| **Deliverable** | Long-running PC scripts and servers can run indefinitely without manual memory management. Embedded binary remains unchanged. |
| **Risk** | Low — all PC features are additive and gated behind build flags or explicit opcodes. |

---

## Design Principles

| Principle | Application |
|-----------|-------------|
| **Determinism over convenience** | No hidden GC pauses. All reclamation paths have bounded, documented worst-case timing. |
| **Pay for what you use** | Bare-metal targets compile out PC features entirely. Segment count and sizes are compile-time constants. |
| **Fail safe** | Every handle access is validated. Out-of-memory returns null, never crashes. Debug builds log violations. |
| **Layered complexity** | Each phase builds on the previous. You can ship after Phase 2 for embedded, or continue to Phase 4 for PC. |
| **No raw pointers in bytecode** | All heap access goes through handles. The VM retains freedom to relocate, compact, or change backing storage without invalidating programs. |

---

## Cross-Cutting Concerns

| Concern | Resolution |
|---------|------------|
| **Fragmentation** | Bump allocation within segments is fragmentation-free. Cross-segment fragmentation is managed by lifetime segregation (temp vs. main). Compaction (Phase 4) addresses long-term main-heap fragmentation if needed. |
| **Cyclic references** | Not collected by design. ELIN does not support arbitrary object graphs in core memory model. Cycles must be broken explicitly by the programmer or avoided by language design (e.g., no back-pointers in structs). |
| **Multi-threading** | Not addressed in core model. Each thread would receive its own Temp and Interrupt segments. Main segment requires external synchronization or thread-local handles. |
| **Large allocations** | Single allocations cannot exceed segment capacity. Multi-segment objects or streaming APIs are the programmer's responsibility. |

---

## Success Criteria

| Phase | Criterion |
|-------|-----------|
| 1 | Binary search on dynamic array produces correct results. Valgrind reports zero leaks after explicit `FREE`. |
| 2 | Recursive function allocating 1000-element temp arrays at each level completes without manual deallocation and without OOM. |
| 3 | ELIN binary runs on a 64KB RAM microcontroller, memory usage within 5% of static analysis prediction. |
| 4 | Server-style benchmark (alloc/free loop) runs for 24 hours on PC with stable memory usage and no manual management. |

---

## Current Status

| Phase | Status |
|-------|--------|
| 1 — Core Bump Allocator | **Planned** |
| 2 — Multi-Segment + Regions | **Planned** |
| 3 — Embedded Hardening | **Planned** |
| 4 — PC Comfort | **Planned** |

---

*Last updated: 2026-05-29*
