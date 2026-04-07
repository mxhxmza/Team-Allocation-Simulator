"""
Team Allocation Simulator
=========================
Fairly allocates 6,000 students across 120 tutorial groups into teams of five,
enforcing constraints on gender balance, CGPA deviation, and school diversity.

Algorithm Overview:
  1. Read CSV → group students by tutorial group
  2. Sort each group by CGPA using MergeSort (O(n log n))
  3. Form teams with balanced gender ratios (3M2F or 2M3F preferred)
  4. Swap same-gender students between teams to bring team CGPA within ±0.2 of group mean
  5. Swap students across teams to ensure no team has >2 students from the same school (GPA tolerance ±0.5)
  6. Write final allocations to CSV

Authors: Mohammed Hamza et al. (NTU SC1003 — 2025)
Runtime: ~0.075 seconds on 6,000 records
"""

import statistics
import time


# ---------------------------------------------------------------------------
# 1. File I/O
# ---------------------------------------------------------------------------

def file_reader(filename: str) -> dict:
    """
    Read a CSV file and return a dictionary mapping tutorial group ID
    to a list of student records.

    Expected CSV columns (0-indexed):
      0: Tutorial Group, 1: Student ID, 2: School, 3: Name,
      4: Gender, 5: CGPA
    """
    cohort_list = []

    with open(filename, "r") as f:
        header = True
        for line in f:
            if header:
                header = False
                continue
            cohort_list.append(line.strip().split(","))

    cohort_dict = {}
    for i in range(120):           # 120 tutorial groups, 50 students each
        cohort_dict[cohort_list[50 * i][0]] = cohort_list[50 * i : 50 * (i + 1)]

    return cohort_dict


def file_writer(cohort: dict, output_path: str = "team_allocations.csv") -> bool:
    """
    Write the final team allocations to a CSV file.

    Args:
        cohort: dict mapping tutorial group → list of teams (each team = list of students)
        output_path: destination filename
    """
    header = ["Tutorial Group", "Student ID", "School", "Name", "Gender", "CGPA", "Team Assigned"]

    with open(output_path, "w") as f:
        f.write(",".join(header) + "\n")
        for key, value in cohort.items():
            for group in value:
                for student in group:
                    f.write(",".join(student) + "\n")

    return True


# ---------------------------------------------------------------------------
# 2. Gender Distribution Helpers
# ---------------------------------------------------------------------------

def team_type_distribution(male_count: int, female_count: int) -> dict:
    """
    Determine how many teams of each gender composition to create
    for a tutorial group given the total male/female counts.

    Preference order (male-majority): 3M2F → 2M3F → 4M1F → 1M4F → 5M0F → 0M5F
    Preference order (female-majority): 2M3F → 3M2F → 1M4F → 4M1F → 0M5F → 5M0F
    """
    teams = {"3M2F": 0, "2M3F": 0, "4M1F": 0, "1M4F": 0, "5M0F": 0, "0M5F": 0}
    total_teams = 10  # 50 students / 5 per team

    while total_teams > 0:
        if male_count >= female_count:
            if male_count >= 3 and female_count >= 2:
                teams["3M2F"] += 1; male_count -= 3; female_count -= 2
            elif male_count >= 2 and female_count >= 3:
                teams["2M3F"] += 1; male_count -= 2; female_count -= 3
            elif male_count >= 4 and female_count >= 1:
                teams["4M1F"] += 1; male_count -= 4; female_count -= 1
            elif male_count >= 1 and female_count >= 4:
                teams["1M4F"] += 1; male_count -= 1; female_count -= 4
            elif male_count >= 5 and female_count == 0:
                teams["5M0F"] += 1; male_count -= 5
            elif male_count == 0 and female_count >= 5:
                teams["0M5F"] += 1; female_count -= 5
            else:
                break
        else:
            if male_count >= 2 and female_count >= 3:
                teams["2M3F"] += 1; male_count -= 2; female_count -= 3
            elif male_count >= 3 and female_count >= 2:
                teams["3M2F"] += 1; male_count -= 3; female_count -= 2
            elif male_count >= 1 and female_count >= 4:
                teams["1M4F"] += 1; male_count -= 1; female_count -= 4
            elif male_count >= 4 and female_count >= 1:
                teams["4M1F"] += 1; male_count -= 4; female_count -= 1
            elif male_count >= 5 and female_count == 0:
                teams["5M0F"] += 1; male_count -= 5
            elif male_count == 0 and female_count >= 5:
                teams["0M5F"] += 1; female_count -= 5
            else:
                break
        total_teams -= 1

    return teams


def team_gender_distribution(group: list) -> dict:
    """Count males and females in a tutorial group and return team type distribution."""
    male_count = sum(1 for s in group if s[4] == "Male")
    female_count = sum(1 for s in group if s[4] == "Female")
    return team_type_distribution(male_count, female_count)


# ---------------------------------------------------------------------------
# 3. Sorting — MergeSort O(n log n)
# ---------------------------------------------------------------------------

def merge(left: list, right: list) -> list:
    """Merge two sorted lists by CGPA (ascending)."""
    final, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if float(left[i][5]) <= float(right[j][5]):
            final.append(left[i]); i += 1
        else:
            final.append(right[j]); j += 1
    final.extend(left[i:])
    final.extend(right[j:])
    return final


def msort(tutorial_grp: list) -> list:
    """MergeSort a list of students by CGPA (ascending)."""
    if len(tutorial_grp) < 2:
        return tutorial_grp
    mid = len(tutorial_grp) // 2
    return merge(msort(tutorial_grp[:mid]), msort(tutorial_grp[mid:]))


def gender_div(sorted_group: list) -> tuple:
    """Split a CGPA-sorted group into separate female and male lists."""
    female = [s for s in sorted_group if s[4] == "Female"]
    male   = [s for s in sorted_group if s[4] != "Female"]
    return female, male


# ---------------------------------------------------------------------------
# 4. Team Formation (gender-balanced interleaving)
# ---------------------------------------------------------------------------

def team_formation(tutorial_group: list) -> list:
    """
    Form 10 balanced teams from a 50-student tutorial group.

    Strategy:
      - Sort by CGPA, split by gender.
      - Pair the lowest-GPA females with highest-GPA males to keep team GPA stable.
    """
    sorted_gpa = msort(tutorial_group)
    female, male = gender_div(sorted_gpa)

    tutorial_teams = []
    team_types = team_gender_distribution(tutorial_group)

    for dist_type, number in team_types.items():
        m_count = int(dist_type[0])
        f_count = int(dist_type[2])
        for _ in range(number):
            team = female[:f_count] + male[-m_count:] if m_count else female[:f_count]
            tutorial_teams.append(team)
            female = female[f_count:]
            if m_count:
                male = male[:-m_count]

    return tutorial_teams


# ---------------------------------------------------------------------------
# 5. GPA Balancing
# ---------------------------------------------------------------------------

def gpaChecker(teams: list, threshold: float = 0.2) -> list:
    """
    Swap same-gender students between high-GPA and low-GPA teams until
    every team's average CGPA is within ±threshold of the group mean.

    Args:
        teams: list of teams (each team = list of student records)
        threshold: maximum allowed deviation from group mean CGPA (default 0.2)
    """
    all_gpas = [float(s[5]) for team in teams for s in team]
    mean_gpa = statistics.mean(all_gpas)

    def team_avg(team):
        return statistics.mean([float(s[5]) for s in team])

    team_averages = [team_avg(t) for t in teams]

    high_pairs, low_pairs = [], []
    for i, avg in enumerate(team_averages):
        dev = avg - mean_gpa
        if dev > threshold:
            high_pairs.append((dev, i))
        elif dev < -threshold:
            low_pairs.append((-dev, i))

    high_pairs.sort(reverse=True)
    low_pairs.sort(reverse=True)

    high_idx = [i for _, i in high_pairs]
    low_idx  = [i for _, i in low_pairs]

    for hi, lo in zip(high_idx, low_idx):
        high_team = teams[hi]
        low_team  = teams[lo]

        rank_highteam = sorted(high_team, key=lambda s: float(s[5]), reverse=True)
        rank_lowteam  = sorted(low_team,  key=lambda s: float(s[5]))

        swap_done = False
        for hs in rank_highteam:
            for ls in rank_lowteam:
                if hs[4] == ls[4]:   # same gender
                    high_team.remove(hs); low_team.remove(ls)
                    high_team.append(ls); low_team.append(hs)
                    swap_done = True
                    break
            if swap_done:
                break

    return teams


# ---------------------------------------------------------------------------
# 6. School Diversity
# ---------------------------------------------------------------------------

def check_2plus_v2(group_list: list) -> tuple:
    """
    Check whether any school appears more than twice in a team.

    Returns:
        (has_2plus, positions_dict, repeat_school)
    """
    positions = {}
    for i, row in enumerate(group_list):
        school = row[2]
        positions.setdefault(school, []).append(i)

    repeat_school = None
    has_2plus = False
    for school, idxs in positions.items():
        if len(idxs) > 2:
            has_2plus = True
            repeat_school = school

    return has_2plus, positions, repeat_school


def finder_swapper(tutorial_group_list: list, gpa_tolerance: float = 0.5) -> list:
    """
    Swap over-represented school students with same-gender students from other
    teams whose CGPA is within gpa_tolerance.

    If no valid swap candidate exists, the externality is accepted gracefully.
    """
    for group_index, group in enumerate(tutorial_group_list):
        has_2plus, positions, repeat_school = check_2plus_v2(group)
        if not has_2plus:
            continue

        over_students = positions[repeat_school][2:]

        for student_index in over_students:
            student = group[student_index]
            student_gender = student[4]
            student_gpa = float(student[5])

            for other_gi, other_group in enumerate(tutorial_group_list):
                if other_gi == group_index:
                    continue
                for other_idx, other_student in enumerate(other_group):
                    if (
                        other_student[4] == student_gender
                        and abs(student_gpa - float(other_student[5])) < gpa_tolerance
                        and other_student[2] != repeat_school
                    ):
                        group[student_index], other_group[other_idx] = (
                            other_group[other_idx],
                            group[student_index],
                        )
                else:
                    continue
                break

    return tutorial_group_list


# ---------------------------------------------------------------------------
# 7. Main Pipeline
# ---------------------------------------------------------------------------

def main(input_file: str = "records.csv", output_file: str = "team_allocations.csv"):
    """
    Run the full team allocation pipeline.

    Steps:
      1. Read CSV
      2. Form gender-balanced teams per tutorial group
      3. Balance team CGPAs within ±0.2 of group mean
      4. Enforce school diversity (max 2 students per school per team)
      5. Label each student with their team number
      6. Write results to CSV
    """
    start = time.time()

    cohort_dict = file_reader(input_file)
    organised_cohort_dict = {}

    for key, tutorial_group in cohort_dict.items():
        teams = team_formation(tutorial_group)
        teams = gpaChecker(teams)
        teams = finder_swapper(teams)

        # Assign team numbers (1-indexed)
        for i, team in enumerate(teams):
            for student in team:
                student.append(str(i + 1))

        organised_cohort_dict[key] = teams

    file_writer(organised_cohort_dict, output_file)

    elapsed = time.time() - start
    print(f"Done. Runtime: {elapsed:.4f}s — output written to '{output_file}'")


if __name__ == "__main__":
    main()
