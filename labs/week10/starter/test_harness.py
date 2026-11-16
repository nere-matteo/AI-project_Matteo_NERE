"""Block 3: the gates. This is the file that fails a build.

Everything so far printed tables. A table is a thing you read once. A test
is a thing that stops you shipping, and the difference between an
evaluation and a report is exactly this file.

    pytest -q                    # all gates
    pytest -q -m "not judged"    # the free ones only, no model calls

Note what is asserted and what is not. These gates assert properties that
should hold for ANY healthy version of the system, not the specific numbers
this week produced. A test pinned to 0.42 accuracy fails the moment somebody
improves something, gets deleted in week 12, and protects nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

import judge as J
from dimensions import report
from loader import load_goldset, load_traces, source_of

TRACES = load_traces()
MIN_JUDGE_AGREEMENT = 0.80
THRESHOLD_NUDGE = 0.05


# --------------------------------------------------------------------------
# The free gates. No model calls, so these can run on every commit.
# --------------------------------------------------------------------------

def test_traces_exist():
    assert TRACES, "no traces recorded. Week 10 has nothing to evaluate."


def test_every_trace_carries_its_conditions():
    """A number without its conditions is not evidence.

    This is the gate that would have caught the defect in the course's own
    artifacts, where week 9 recorded its run condition under two different
    keys in the same file.
    """
    missing = [t["trace_id"] for t in TRACES
               if not t.get("conditions", {}).get("model")
               or not t["conditions"].get("run_date")]
    assert not missing, f"{len(missing)} traces without model or run_date"


def test_condition_keys_are_consistent_within_a_week():
    """One fact, one home. Two spellings of one condition is a defect.

    Checked per week AND per writer. Your application and a lab script run
    in the same week are two systems with two sets of conditions, and that
    is not a second spelling of anything.
    """
    by_week: dict[tuple[int, str], set[frozenset]] = {}
    for t in TRACES:
        week, source = t["week"], source_of(t)
        settings = (t.get("conditions", {}).get("settings") or {})
        keys = frozenset(settings) - {"replay"}
        # Week 4 added use_tools to later lab traces for the no-tools comparison.
        # Keep both historical shapes valid without inferring the omitted value.
        if (week, source) == (4, "lab") and keys == {"max_steps", "stall_limit"}:
            keys = keys | {"use_tools"}
        by_week.setdefault((week, source), set()).add(keys)
    for (week, source), shapes in by_week.items():
        assert len(shapes) <= 1, (
            f"week {week} ({source}) records its conditions under more than "
            f"one set of keys: {sorted(tuple(sorted(s)) for s in shapes)}")


def test_failures_flag_themselves():
    """Predictability floor. A failure that looks like a success cannot be
    routed by anything downstream, so a system where most of them are
    invisible is not ready for a gate."""
    dims = {d.name: d for d in report(TRACES)}
    value = dims["predictability"].value
    if value is None:
        pytest.skip("no failed runs recorded")
    assert value >= 0.5, (
        f"only {value:.0%} of failed runs flagged themselves. "
        f"{dims['predictability'].detail}")


def test_goldset_cases_are_unique():
    cases = load_goldset()
    ids = [c["case_id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case_id in the gold set"


def test_goldset_grew_with_the_project():
    """The gold set is the project's memory. A flat one means nobody added
    the cases their own week discovered."""
    weeks = {c.get("week_added") for c in load_goldset()}
    assert len(weeks) >= 3, f"gold set only has cases from weeks {weeks}"


# --------------------------------------------------------------------------
# The judged gates read recorded scores and can be skipped on commits.
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def judgments():
    path = J.fixture_path()
    if not path.exists():
        pytest.skip("no judge scores recorded; run 02_judge.py live")
    recorded = J.load_recorded(path)
    missing = [case.case_id for case in J.LABELS if case.case_id not in recorded]
    assert not missing, f"Incomplete judge scores in {path}: {', '.join(missing)}"
    return recorded


@pytest.mark.judged
def test_judge_agrees_with_human_labels(judgments):
    """TODO 5a. The gate that licenses every other judged number.

    Load the recorded judgments, validate them against the labels, and
    assert the agreement rate clears a bar you can defend. Skip, do not
    fail, when no judgments have been recorded yet.

    An unvalidated judge is not a control. If this gate fails, no judged
    metric anywhere in your report means anything, which is why it is a
    test and not a paragraph in a README.
    """
    agreement = J.validate(judgments)
    disagreements = [row["case_id"] for row in agreement.rows
                     if row["human"] != row["judge"]]
    assert agreement.rate >= MIN_JUDGE_AGREEMENT, (
        f"Only {agreement.agreed}/{agreement.n} match at {J.THRESHOLD:g}. "
        f"Need at least {MIN_JUDGE_AGREEMENT:.0%}. Disagreements: {disagreements}")


@pytest.mark.judged
def test_judge_makes_no_false_passes(judgments):
    """TODO 5b. The asymmetric gate.

    A false fail costs a human's attention. A false pass means your gate
    went green on an invented answer. Forbid only the second, and say in
    one comment why you are not forbidding both.
    """
    agreement = J.validate(judgments)
    false_passes = [f"{row['case_id']} ({row['score']:.2f})" for row in agreement.rows
                    if row["human"] == "fail" and row["judge"] == "pass"]
    # A false fail goes to review. A false pass can ship an invented fact.
    assert not false_passes, f"False passes at {J.THRESHOLD:g}: {', '.join(false_passes)}"


@pytest.mark.judged
def test_threshold_is_not_on_a_cliff(judgments):
    """TODO 5c. Would a small change to the threshold change the verdicts?

    Compute agreement at THRESHOLD and at plus and minus 0.05, and assert
    they are close. If nudging the threshold moves agreement, the number you
    are about to report is an artefact of a library default that nobody
    chose, and you should find that out now rather than in week 12.
    """
    baseline = J.validate(judgments)
    verdicts = {row["case_id"]: row["judge"] for row in baseline.rows}
    for shift in (-THRESHOLD_NUDGE, THRESHOLD_NUDGE):
        cutoff = min(1.0, max(0.0, round(J.THRESHOLD + shift, 10)))
        shifted = J.validate(judgments, cutoff)
        changed = [row["case_id"] for row in shifted.rows
                   if row["judge"] != verdicts[row["case_id"]]]
        assert not changed, (f"Threshold {J.THRESHOLD:g} to {cutoff:g} changed "
                             f"{', '.join(changed)}. Agreement went from "
                             f"{baseline.agreed}/{baseline.n} to "
                             f"{shifted.agreed}/{shifted.n}.")
