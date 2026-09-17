# Decisions
# Week 1: the stack, the first call, and what it costs

Copy this into your `DECISIONS.md` and fill it in. Keep the headings. In
week 13 this becomes a section of your project report that you do not have
to write.

---

## Week 1

**Run conditions.** Everything below was produced on:

- machine: [make, chip, RAM]
- model: [the model name, exactly as `ollama list` prints it]
- served by: Ollama, one request at a time, locally
- date: [YYYY-MM-DD]

Every number in this file is meaningless without those four lines, so they
are stated once here and referred to rather than repeated.

### 1. Machine and model set

I am running the [required / required plus optional] model set.

[If you could not run the optional models, say so and say what you will do
before week 9. This is a constraint on your project, not a failure, and
naming it now is worth more than discovering it in week 9.]

### 2. The first call

| | |
| finish reason | stop |
| prompt tokens | 25 |
| completion tokens | 45 |
| elapsed | 4.471647708996898 |

One sentence on the finish reason: what my program would do differently if
it came back as a truncation rather than a normal stop.

[It would return length as the finish reason, and you may be able to change it if you higher up the token limit]

### 3. Variance

| cell | distinct (recording) | distinct (mine) | median latency |
| closed_short, t=0.0 | 1/12 | | |
| closed_short, t=1.0 | 1/12 | | |
| open_list, t=0.0 | 1/12 | | |
| open_list, t=1.0 | 11/12 | | |

Which cell still returns a single answer at temperature 1.0, and why that
one:
The close list one still returns only one since it's asking for a capital and there is only one right answer for a capital so even increasing the temperature won't change that a country has more then one capital
[...]

Which cells a test asserting exact string equality would pass on, and what
that tells me about testing this system:
Everything except open list with temp 1.0 since there there could be a right answer that is stopped due to a wording mistake or similar issues. What would need to be done which means it would need a more in debt correctness and meaning check. 
[...]

**The sentence that carries into week 10.** [One sentence about when you can
and cannot rely on repeating an output. Week 10 will ask you to find this
again. It should not say "the model is random", because your own table shows
otherwise in most cells.]
In these experiments, outputs repeated for the constrained prompt at both temperatures and the open-ended prompt at temperature 0, but varied for the open-ended prompt at temperature 1.0, so repeatability depends on the task and settings and must be measured rather than assured.

### 4. The cold start

- cold call: [ 1.04 ] s
- warm call: [ 0.11 ] s
- ratio: [ 9.45 ]

What this implies for a system that uses more than one model, and what I
will do about it:
My cold call took 1.04 seconds and my warm call was 0.11 about 9.45 times quicker which means that if multiple models cannot fit together in memory then switching between them can repeatedly add loading delays. Meaning that I should group tasks by model and avoid unnecessary model switches within a single request. 
[...]

### 5. Cost, estimated

A 200-case golden set, at the token cost of my long case:

| | one run | nightly for the semester |
| small tier | 0.03 | 3.28 |
| large tier | 2.49 | 244.14 |

Estimates against the price list dated [date in `project/prices.py`], not
measurements. Running locally, my actual monetary cost was zero.

Which tier I would run nightly, which I would run before a release, and why
not the same one for both:

I would use the small tier to run nightly for the semester since it is much cheaper but before a release I would use the large tier, since it is to make sure everything is working 

### Deferred

[Anything you did not get to, and why. An explicit deferral with a reason is
engineering. Silence is not, and the project rubric can tell the
difference.]