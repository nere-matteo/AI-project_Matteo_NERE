"""Deterministic checks and triage for the Week 9 invoices."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

GROUPS = {
    "identity": ["invoice_number", "purchase_order", "currency"],
    "amounts": ["net_amount", "vat_amount", "total_amount"],
}
ALL_FIELDS = [f for g in GROUPS.values() for f in g]

VAT_RATE = Decimal("0.17")
CENT = Decimal("0.01")
MAX_TOTAL_EUR = 10_000.0
INVOICE_RE = re.compile(r"^INV-\d{3}-LU$")
PO_RE = re.compile(r"^PO-\d{4}-\d{4}$")
CURRENCIES = {"EUR"}


def parse_amount(text: str | None) -> float | None:
    """Luxembourg prints one thousand as `1 129.23`. `float()` refuses it.

    Note what this does NOT do: it does not strip every space and hope. A
    space is removed only where it separates a digit from a group of exactly
    three, which is what a thousands separator is. Strip blindly instead and
    "12 34 56" becomes 123456, which is three numbers welded into one, and
    no later check will ever tell you that happened.
    """
    if text is None:
        return None
    s = str(text).replace("\u00a0", " ").replace("\u202f", " ").strip()
    s = s.removeprefix("EUR").removesuffix("EUR").strip()
    # A thousands separator groups digits in THREES. Requiring that is what
    # separates "1 129.23", which is one number, from "12 34 56", which is
    # three numbers that a blind strip would silently weld into 123456.
    s = re.sub(r"(?<=\d) (?=\d{3}\b)", "", s)
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+\.\d{1,2}", s):
        s = s.replace(",", "")           # 1,129.23
    elif re.fullmatch(r"-?\d+,\d{1,2}", s):
        s = s.replace(",", ".")          # 1129,23
    if not re.fullmatch(r"-?\d+(\.\d{1,2})?", s):
        return None
    amount = float(s)
    return amount if math.isfinite(amount) else None


@dataclass
class CheckReport:
    fired: list[str]
    parsed: dict[str, float | None]

    @property
    def clean(self) -> bool:
        return not self.fired


def run_checks(fields: dict[str, str | None]) -> CheckReport:
    """Validate completeness, arithmetic, identity format, and total range."""
    net = parse_amount(fields.get("net_amount"))
    vat = parse_amount(fields.get("vat_amount"))
    total = parse_amount(fields.get("total_amount"))
    fired = []

    if net is None or vat is None or total is None:
        fired.append("missing or unreadable amount")
    elif Decimal(str(net)) + Decimal(str(vat)) != Decimal(str(total)):
        fired.append("net plus VAT does not equal total")

    if net is not None and vat is not None:
        expected_cents = (Decimal(str(net)) * VAT_RATE / CENT).to_integral_value(
            rounding=ROUND_HALF_UP)
        if Decimal(str(vat)) / CENT != expected_cents:
            fired.append("VAT differs from the supplier rate")

    if not INVOICE_RE.fullmatch(fields.get("invoice_number") or ""):
        fired.append("invalid invoice number")
    purchase_order = fields.get("purchase_order")
    if purchase_order is not None and not PO_RE.fullmatch(purchase_order):
        fired.append("invalid purchase order")
    if fields.get("currency") not in CURRENCIES:
        fired.append("unsupported or missing currency")

    if total is not None and not 0 < total <= MAX_TOTAL_EUR:
        fired.append("total outside the plausible supplier range")

    return CheckReport(fired, {"net": net, "vat": vat, "total": total})


OUTCOMES = ("correct", "WRONG", "caught", "refused", "false_alarm")


def classify(truth: dict, report: CheckReport) -> str:
    """Five outcomes. Only one of them is a silent bad extraction.

    correct      every amount right, checks silent. What you wanted.
    false_alarm  every amount right, checks fired. A check that cries wolf
                 costs a human's attention, so it is a defect too, and a
                 cheap one to measure.
    caught       an amount wrong, checks fired. The system working.
    WRONG        an amount wrong, checks silent. THIS is the column that
                 matters, and it is the only row a human would have had to
                 open the image to find.
    refused      no usable amount came back, which is at least honest.

    Judged on all three amounts rather than on the total alone. A run that
    reads the total correctly out of the wrong column, and the net out of
    the wrong column too, is not a correct extraction, and scoring only the
    total would call it one.
    """
    got = report.parsed
    pairs = (("net", "net_amount"), ("vat", "vat_amount"),
             ("total", "total_amount"))

    # A value that came back and disagrees with the truth is an error, and it
    # is judged FIRST. Checking "did the total come back" first instead looks
    # reasonable and is wrong: a run that refuses the total while quietly
    # misreading the net would be filed as an honest refusal. That happens
    # for real on this corpus, on INV-003 under compression, where the net
    # comes back as 955.15 rather than 965.15 and the total comes back null.
    wrong = [f for k, f in pairs if got[k] is not None
             and Decimal(str(got[k])) != Decimal(str(truth[f]))]
    if wrong:
        return "WRONG" if report.clean else "caught"

    if any(got[k] is None for k, _ in pairs):
        return "refused"

    return "correct" if report.clean else "false_alarm"


def tally(rows: list[dict]) -> dict[str, int]:
    return {o: sum(1 for r in rows if r.get("outcome") == o) for o in OUTCOMES}
