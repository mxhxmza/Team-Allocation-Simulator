# Design Notes

## Problem Analysis

**Ideal Output**: Minimised variance of gender, CGPA, and school affiliation across all 1,200 teams.

### Constraints

| Constraint | Threshold | Rationale |
|---|---|---|
| Gender | 3M2F or 2M3F preferred; both genders required | Ensures diversity; all-same-gender teams accepted only when unavoidable |
| CGPA | Team average within ±0.2 of tutorial group mean | Relative to group, not global mean — groups have different CGPA profiles |
| School | Max 2 students from same school per team | GPA tolerance ±0.5 for swap candidates |

### Why relative thresholds?
The distribution of CGPA and school affiliation differs significantly across tutorial groups. Fixing thresholds to the tutorial group average (rather than a global benchmark) makes the constraints meaningful and achievable for every group.

---

## Challenges & Solutions

### 1. Scale (6,000 students)
**Problem**: Brute-force team search across 6,000 students × 1,200 teams is infeasible.  
**Solution**: Constrain all swapping to within each tutorial group (50 students). This reduces the search space by 120x.

### 2. Sorting Algorithm Choice
**Problem**: Initial bubble sort implementation was too slow for the dataset size.  
**Solution**: Switched to MergeSort (O(n log n)). Sorting 50 students per group, 120 groups, completes in milliseconds.

### 3. Inconsistent CGPA Profiles Across Groups
**Problem**: A threshold calibrated to the global mean is unfair to groups with naturally higher/lower CGPAs.  
**Solution**: Compute the mean for each tutorial group independently and apply the ±0.2 threshold relative to that.

### 4. Constraint Ordering
**Problem**: Fixing one constraint (e.g. school) could undo work done for another (e.g. CGPA).  
**Solution**: Apply constraints sequentially with continuity preservation:
  1. Gender (structurally determined during team formation)
  2. CGPA balancing (swaps only same-gender students — gender not disturbed)
  3. School diversity (swaps require same gender AND similar GPA — previous two not disturbed)

### 5. Imperfect Inputs
**Problem**: Some tutorial groups have 20+ students from a single school, or 45M/5F ratios. No perfect solution exists.  
**Solution**: Accept externalities gracefully with a hard cap:
  - School: if no valid swap exists within the GPA tolerance, keep the violation
  - Gender: all-same-gender teams are formed only as a last resort
  - Result: 98% of teams satisfy all constraints simultaneously

---

## Computational Thinking Principles Applied

1. **Decomposition** — Broken into independent, testable functions: `file_reader`, `msort`, `gender_div`, `team_formation`, `gpaChecker`, `finder_swapper`, `file_writer`

2. **Abstraction** — `main()` orchestrates the full pipeline cleanly; individual functions hide implementation complexity

3. **Pattern Recognition** — Recognising that GPA and school swaps share the same structure (find violating teams, find swap candidate, validate, swap) led to a unified approach

4. **Algorithm Selection** — Deliberate choice of MergeSort over BubbleSort after benchmarking; targeted swapping over exhaustive search
