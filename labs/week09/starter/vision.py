"""Week 9 model boundary for extracting structured fields from images."""

from __future__ import annotations

import base64
import io
import json
import time
import urllib.request
from dataclasses import dataclass, field, replace
from http.client import HTTPException
from pathlib import Path

MODEL = "qwen3-vl:4b"
ENDPOINT = "http://127.0.0.1:11434/api/chat"
TIMEOUT_S = 300

SYSTEM = (
    "You read Luxembourg invoices. Return each requested field exactly as it "
    "is printed on the page, as a string, including any spaces used as "
    "thousands separators. If a field is NOT PRESENT on the page, return null "
    "for it. Never guess a value that is not printed."
)


@dataclass
class VisionResult:
    """One call. `failure` is None only when the result is usable."""

    doc: str
    group: str
    variant: str
    fields: dict[str, str | None] = field(default_factory=dict)
    failure: str | None = None
    elapsed_s: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    done_reason: str = ""
    raw_content: str = ""

    @property
    def ok(self) -> bool:
        return self.failure is None


def encode(path: Path, variant: str = "clean") -> str:
    """Base64 PNG of the image after one named degradation."""
    from perturb import apply_variant

    buf = io.BytesIO()
    apply_variant(path, variant).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def flat_schema(fields: list[str]) -> dict:
    """Flat, nullable, and required. Nested schemas fail on this model."""
    return {"type": "object",
            "properties": {f: {"type": ["string", "null"]} for f in fields},
            "required": list(fields)}


def guard(content: str, thinking: str, done_reason: str,
          fields: list[str]) -> tuple[dict[str, str | None] | None, str | None]:
    """Accept only a complete object with at least one usable field."""
    if done_reason == "length":
        return None, "context limit reached (done_reason=length)"
    if not isinstance(content, str) or not content.strip():
        hint = " (thinking was present)" if thinking else ""
        return None, f"empty response content{hint}"
    try:
        parsed = json.loads(content)
    except ValueError:
        return None, "invalid JSON in response content"
    if not isinstance(parsed, dict):
        return None, "response JSON is not an object"

    missing = [name for name in fields if name not in parsed]
    if missing:
        return None, f"missing required fields: {', '.join(missing)}"
    selected = {name: parsed[name] for name in fields}
    if any(value is not None and not isinstance(value, str)
           for value in selected.values()):
        return None, "field values must be strings or null"
    if not any(value and value.strip() for value in selected.values()):
        return None, "all requested values are blank or null"
    return selected, None


def read_group(image_path: Path, group: str, fields: list[str],
               variant: str = "clean", replay: Fixture | None = None,
               record: Fixture | None = None,
               system: str | None = None, prompt: str | None = None
               ) -> VisionResult:
    """Read one group over local Ollama or validate the recorded response."""
    doc = image_path.stem
    if replay is not None:
        hit = replay.get(doc, group, variant)
        if hit is None:
            return VisionResult(doc, group, variant, failure="no matching replay response")
        if not hit.ok:
            return hit
        parsed, failure = guard(hit.raw_content, "", hit.done_reason, fields)
        return replace(hit, fields=parsed or {}, failure=failure)

    started = time.perf_counter()
    out = VisionResult(doc, group, variant)
    try:
        payload = {
            "model": MODEL,
            "stream": False,
            "format": flat_schema(fields),
            "options": {"temperature": 0.0},
            "messages": [
                {"role": "system", "content": system or SYSTEM},
                {"role": "user",
                 "content": prompt or f"Read these fields: {', '.join(fields)}.",
                 "images": [encode(image_path, variant)]},
            ],
        }
        request = urllib.request.Request(
            ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        # qwen3-vl returns unusable blank fields when thinking is disabled.
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise ValueError("Ollama response is not an object")
        message = data.get("message") or {}
        if not isinstance(message, dict):
            raise ValueError("Ollama response message is not an object")

        content = message.get("content")
        out.raw_content = content if isinstance(content, str) else ""
        out.done_reason = data.get("done_reason") or ""
        out.prompt_tokens = data.get("prompt_eval_count") or 0
        out.output_tokens = data.get("eval_count") or 0
        parsed, out.failure = guard(out.raw_content, message.get("thinking") or "",
                                    out.done_reason, fields)
        out.fields = parsed or {}
    except (OSError, ValueError, ImportError, HTTPException) as exc:
        out.failure = f"{type(exc).__name__}: {exc}"
    out.elapsed_s = time.perf_counter() - started

    if record is not None:
        record.put(out)
    return out


def read_naive(image_path: Path, fields: list[str], variant: str = "clean",
               replay: "Fixture | None" = None,
               record: "Fixture | None" = None) -> VisionResult:
    """Read all six fields in one call for the architecture comparison."""
    return read_group(image_path, "naive", fields, variant=variant,
                      replay=replay, record=record)


# --------------------------------------------------------------------------
# Replay. Vision calls are slow, so a recorded run is what makes the lab
# fit in ninety minutes. Keyed on what varies: doc, group, variant.
# --------------------------------------------------------------------------

class Fixture:
    """A recorded set of vision calls, keyed by (doc, group, variant)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.entries: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.entries[self._key(row["doc"], row["group"],
                                           row["variant"])] = row

    @staticmethod
    def _key(doc: str, group: str, variant: str) -> str:
        return f"{doc}|{group}|{variant}"

    def get(self, doc: str, group: str, variant: str) -> VisionResult | None:
        row = self.entries.get(self._key(doc, group, variant))
        if row is None:
            return None
        return VisionResult(**{k: v for k, v in row.items()
                               if k in VisionResult.__dataclass_fields__})

    def has(self, doc: str, group: str, variant: str) -> bool:
        return self._key(doc, group, variant) in self.entries

    def put(self, result: VisionResult) -> None:
        row = {"doc": result.doc, "group": result.group,
               "variant": result.variant,
               "fields": result.fields, "failure": result.failure,
               "elapsed_s": round(result.elapsed_s, 2),
               "prompt_tokens": result.prompt_tokens,
               "output_tokens": result.output_tokens,
               "done_reason": result.done_reason,
               "raw_content": result.raw_content}
        self.entries[self._key(result.doc, result.group,
                               result.variant)] = row
        # Appended immediately rather than at the end, so a run that is
        # interrupted keeps everything it already paid for.
        with self.path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")


def find_fixture(name: str = "vision_runs.jsonl") -> Path:
    """Look where the lab is, then where the student copied the script."""
    here = Path(__file__).resolve()
    for base in (here.parent, here.parent.parent, Path.cwd(),
                 Path.cwd().parent):
        candidate = base / "fixtures" / name
        if candidate.exists():
            return candidate
    return here.parent.parent / "fixtures" / name


if __name__ == "__main__":
    examples = (
        ("", "", "length", "context limit"),
        (" ", '{"net":"","total":""}', "stop", "thinking"),
        ('{"net":"', "", "stop", "invalid JSON"),
        ('["19.00","22.23"]', "", "stop", "not an object"),
        ('{"net":"19.00"}', "", "stop", "missing required fields"),
        ('{"net":" ","total":""}', "", "stop", "blank or null"),
        ('{"net":null,"total":null}', "", "stop", "blank or null"),
    )
    for content, thinking, reason, expected in examples:
        parsed, failure = guard(content, thinking, reason, ["net", "total"])
        assert parsed is None and failure and expected in failure, (parsed, failure)
        print(f"Refused: {failure}")

    parsed, failure = guard('{"net":"19.00","total":null}', "", "stop",
                            ["net", "total"])
    assert parsed == {"net": "19.00", "total": None} and failure is None
