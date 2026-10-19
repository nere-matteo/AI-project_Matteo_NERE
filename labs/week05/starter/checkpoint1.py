import asyncio

from agents import Plan, propose, validate_plan
from repo import Work, apply_fix, run_tests


TASK = (
    "The off-peak discount should apply to bookings starting at "
    "20:00 or later, but a booking at exactly 20:00 misses it. "
    "Fix the bug without changing any test file."
)


async def main():
    work = Work.fresh()

    try:
        # Check 1: observe the original failure.
        print("\n--- Tests before the fix ---")
        print(run_tests(work).output)

        # Check 2: demonstrate rejection of a broken plan.
        bad_plan = Plan(
            goal="Hide the failure.",
            steps=["Delete the failing test."],
            suspect_file="unknown.py",
        )
        ok, problems = validate_plan(bad_plan)
        print("\n--- Deliberately invalid plan ---")
        print("Accepted:", ok)
        for problem in problems:
            print("-", problem)

        # Checks 3 and 4: generate and inspect the plan and proposal.
        out = await propose(work, TASK, use_plan=True)

        print("\n--- Generated plan ---")
        print(out["plan"].model_dump_json(indent=2))
        print("Accepted:", out["plan_ok"])
        print("Problems:", out["plan_problems"])

        if not out["plan_ok"]:
            print("Stopped because the generated plan failed validation.")
            return

        fix = out["fix"]
        print("\n--- Proposed fix ---")
        print(fix.model_dump_json(indent=2))

        # Check 5: demonstrate that test edits are refused.
        print("\n--- Attempt to edit a test runner ---")
        print(apply_fix(work, "run_tests.py", "anything", "anything else"))

        # Apply the model's proposal to the temporary copy.
        print("\n--- Applying the proposed fix ---")
        print(apply_fix(work, fix.path, fix.old_line, fix.new_line))

        # Check 6: verify the actual result.
        print("\n--- Tests after the fix ---")
        result = run_tests(work)
        print(result.output)
        print("All tests passed:", result.passed)

    finally:
        work.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
