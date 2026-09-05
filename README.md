# Team Allocation Simulator

> NTU SC1003 — Course Final Project (Graded A+) · 2025

A constraint-satisfaction algorithm that fairly allocates **6,000 students** across **120 tutorial groups** into teams of five, enforcing simultaneous balance across gender, CGPA, and school affiliation — in **0.075 seconds**.

---

## Try It in the Browser

`web/index.html` is a single-file web app — drop in a `records.csv`, get the allocation back with per-team constraint scoring and a downloadable results CSV.

```bash
# no build step, no server, no dependencies
open web/index.html          # macOS
start web/index.html         # Windows
```

It also deploys as-is to GitHub Pages or any static host (point the site at `/web`).

**What it does**

- Runs the full pipeline **client-side** — the CSV never leaves the browser.
- Opens empty — nothing is computed until you stage a file and press **Run allocation**. A **Load sample cohort** button generates a synthetic cohort if you want to try it without data of your own.
- Scores every team against all three constraints and charts CGPA deviation, gender composition, and school concentration.
- Lets you move the **±0.2 CGPA band** and the **±0.5 school swap tolerance** and re-run, to see how the thresholds trade off against each other.
- Browses the final rosters group by group, flagging the teams that carry an accepted violation.

The page is a direct port of [`src/allocator.py`](src/allocator.py) — `teamFormation`, `gpaChecker` and `finderSwapper` mirror their Python counterparts line for line, and the two implementations produce **identical team assignments** on the same 6,000-row input. Two deliberate generalisations let the page accept arbitrary uploads, where the Python assumes exactly 120 groups of 50:

- Tutorial groups are read from column 1, so any number of groups of any size (5 students and up) work.
- Students left over when a group size isn't divisible by 5 are dealt into the smallest teams rather than dropped.

---

## The Problem

Given 6,000 NTU students spread across 120 tutorial groups (50 students each), form teams of 5 that satisfy all three constraints at once:

| Constraint | Target |
|---|---|
| **Gender** | 3M2F or 2M3F per team; both genders present |
| **CGPA** | Team average within ±0.2 of tutorial group mean |
| **School** | Max 2 students from the same school per team |

A brute-force search across 1,200 teams is computationally infeasible — this simulator uses a **bounded deviation strategy** instead of searching for a perfect match.

---

## Algorithm Design

### Core Philosophy
> Bound the deviation from a target threshold, rather than loop until finding the best match.

Each constraint is handled in sequence, with later passes preserving the work of earlier ones.

### Pipeline

```
records.csv
    │
    ▼
1. file_reader()         — Parse CSV, group by tutorial group
    │
    ▼
2. team_formation()      — MergeSort by CGPA → split by gender → interleave into teams
    │
    ▼
3. gpaChecker()          — Swap same-gender students between high/low GPA teams (threshold ±0.2)
    │
    ▼
4. finder_swapper()      — Swap over-represented school students with GPA-compatible peers (tolerance ±0.5)
    │
    ▼
5. file_writer()         — Output final allocations to CSV
```

### Key Design Decisions

**MergeSort over Bubble Sort** — O(n log n) vs O(n²), critical for 6,000 records across 1,200 teams.

**Gender-split interleaving** — After sorting by CGPA, students are split into male/female lists. The lowest-GPA females are paired with the highest-GPA males per team, naturally stabilising CGPA spread without explicit GPA targeting.

**Targeted swapping** — Only out-of-band teams (deviation > threshold) are selected for GPA swaps, shrinking the execution pool dramatically.

**Graceful externalities** — If no valid swap candidate exists for a school diversity fix, the constraint violation is accepted rather than degrading GPA balance. Result: only ~2% of teams exceed the school cap.

---

## Results

| Metric | Result |
|---|---|
| Total runtime | **0.075 seconds** on 6,000 records |
| Teams with gender imbalance | **9 / 1,200** (0.75%) — groups with one dominant gender |
| Teams exceeding school cap | **24 / 1,200** (2%) — groups with 3+ from same school |

> **Note:** these figures were measured on the original NTU `records.csv` before the `finder_swapper` early-exit fix (see below). The fix strictly reduces school-cap violations, so the current code should do at least this well — re-run `python allocator.py` on that dataset to refresh the table.

### `finder_swapper` early exit

The school-diversity pass was written around Python's `for...else` idiom, but the inner loop was missing its `break`. The `else` clause therefore ran on every pass, making the outer `break` unreachable: instead of taking the first valid swap candidate, each surplus student's slot was traded again with *every* qualifying candidate in the tutorial group, so the final occupant was whichever match happened to come last — and the extra swaps churned students that `gpaChecker` had already balanced.

Adding the missing `break` restores the intended "first valid candidate wins" behaviour. Measured over five synthetic 6,000-student cohorts — 1,200 teams each, 6,000 teams scored per version — with both versions run on identical inputs:

| Constraint | Before | After |
|---|---|---|
| School cap ≤ 2 | 88.8% | **90.0%** |
| CGPA within ±0.2 | 85.9% | **87.4%** |
| Both genders present | 89.8% | 89.8% (unchanged) |
| **All three at once** | 73.0% | **75.0%** |

Runtime is unchanged. Gender is unaffected because swaps were always same-gender; the CGPA gain is a side effect of no longer churning teams the GPA pass had already balanced. These cohorts are deliberately harsher than the real dataset (one group in eight is heavily skewed), so treat the percentages as a before/after comparison rather than as absolute results.

---

## Project Structure

```
team-allocation-simulator/
├── src/
│   └── allocator.py          # Core algorithm (all functions + main pipeline)
├── web/
│   └── index.html            # Single-file browser app (upload CSV → allocations)
├── notebooks/
│   └── Team_Allocation_Simulator.ipynb   # Original Colab notebook with visualizations
├── data/
│   ├── README.txt            # Where to place your records.csv
│   └── records.csv           # Input file (not included — see Data Format below)
├── docs/
│   └── design_notes.md       # Algorithm design rationale and challenge writeup
└── README.md
```

---

## Getting Started

### Requirements
```
Python 3.8+
matplotlib   # for visualizations in the notebook
```

Install dependencies:
```bash
pip install matplotlib
```

### Running the Allocator
```bash
cd src
python allocator.py
```

By default it reads `records.csv` from the working directory and writes `team_allocations.csv`.

You can also import and call it directly:
```python
from allocator import main
main(input_file="records.csv", output_file="results.csv")
```

### Data Format

`records.csv` must have the following columns (with a header row):

```
Tutorial Group, Student ID, School, Name, Gender, CGPA
G-1, S001, EEE, John Doe, Male, 4.20
G-1, S002, CoB (NBS), Jane Tan, Female, 3.85
...
```

- 120 tutorial groups, 50 students each (6,000 rows total)
- Gender values: `Male` or `Female`
- CGPA: float between 0.0 and 5.0

---

## Visualizations

The Jupyter notebook includes Matplotlib charts for validating constraint satisfaction:

- **Gender distribution** — male/female ratio per tutorial group and per team
- **CGPA distribution** — team GPA spread vs group mean across all 120 groups
- **School spread** — school representation per team across all groups

Open the notebook:
```bash
jupyter notebook notebooks/Team_Allocation_Simulator.ipynb
```

Or run directly on [Google Colab](https://colab.research.google.com).

---

## Limitations

- **Gender externality** — Tutorial groups with a strong gender majority (e.g., 45M/5F) will inevitably produce single-gender teams. 9 of 1,200 teams are affected.
- **School externality** — Groups dominated by one school (e.g., 20+ EEE students in 50) cannot satisfy the ≤2 cap without violating GPA constraints. 24 of 1,200 teams are affected; the algorithm correctly accepts this.
- **Fixed group size** — The current implementation assumes exactly 50 students per tutorial group. Adapting to variable group sizes would require minor changes to `file_reader()` and `team_formation()`.

---

## Authors

Mohammed Hamza · NTU Computer Engineering (Class of 2029)  
Built as part of NTU SC1003 — Introduction to Computational Thinking
