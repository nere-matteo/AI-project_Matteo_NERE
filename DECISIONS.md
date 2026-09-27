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

## Week 2

**Run conditions.** model: [ qwen3:4b-instruct] | temperature: 0.0 | prompt version: [ week02-zero-shot-v1] |
served locally with ollama| date: [2026-08-22] | scored on: [my own machine]

### 1. The output contract

The conventions I chose, and why:

- due_date, when the message states no date: [ JSON null, represented as None in Python. This explicitly indicates that no date was provided]
- due_date, when the message states only a relative expression: [ Also null. Expressions such as "tomorrow" or "before the end of the month" are not converted into calendar dates. ]
- quote, and what "verbatim" means in my scorer: [ A nonempty passage of at most 300 characters, copied from the source to support the urgency decision. The scorer uses record.quote in document_text, without changing capitalization, punctuation, or whitespace.]
- what my scorer does with a record that failed validation: [ It increments the invalid-record count and counts all four fields as wrong. THe record remains in the total.]

[One sentence on why the last one matters. A scorer that skips the records
it could not parse reports a number that improves as the model gets worse.]

Counting invalid records as wrong prevents the reported accuracy from improving simply because the extractor produced answers it could not validate. 

### 2. Zero-shot, per field

| field | correct | of |
| category | 8 | 10 |
| urgency | 8 | 10 |
| due_date | 8 | 10 |
| quote | 10 | 10 |
| invalid records | 0 | 10 |

My prediction, written before block 3: examples will help most on [ ]
because [ Examples will help most on due_date, because examples showing null for missing or relative dates should make that convention clearer. This field has the most room for improvement in my baseline. I will also check whether adding examples reduces the currently perfect quote score ].

### 3. Few-shot

Examples chosen, and the job each one does:

| example | why it is in the block | field it should move |
 EX-06 | The broken window is a facilities issue even though a printer is mentioned; worsening rain damage warrants urgent action without an explicit calendar deadline. | category, urgency, due_date |
| EX-03 | A German laptop request demonstrates hardware, standard urgency, and conversion of European 20/09/2026 to 2026-09-20. | category, urgency, due_date |
| EX-04 | An informational announcement requires no intervention; “next week” must remain null rather than become an invented date. | urgency, due_date |
| EX-02 | A French message about a person trapped in a lift demonstrates urgent facilities work and a null date when no deadline is stated. | category, urgency, due_date |


| field | zero-shot | few-shot | move |
| category | 8/10 | 8/10 | 0|
| urgency | 8/10 | 10/10 | + 2|
| due_date | 8/10 | 8/10| 0|
| quote | 10/10 | 10/10 | |

### 4. What got worse

[Name the field, if any, and diagnose it. If nothing got worse, say so and
say how you checked. Then look at the failure lines rather than the counts,
and say whether any error disappeared or merely changed shape. A wrong label
that became a different wrong label has not been fixed.]

No field's score got worse in the live comparison. Category stayed at 8/10 , due_date at 8/10, and quote at 10/10. Urgency improved from 8/10 to 10/10, and neither variant produced invalid records.

Inspecting the individual failures showed that the urgency errors on REQ-09 and REQ-10 were corrected. The category errors on REQ-08 and REQ-09 remained unchanged. REQ-01 and REQ-10 still received invented dates instead of null: the predicted dates changed between variants, but the errors were not fixed.

### 5. What the examples cost

- extra input tokens per call: [ 302 ]
- per thousand calls: [ 302 000 input extra tokens ]
- estimated euros per thousand calls on the small tier: [ 0.0604 euro ], against the
  price list dated [ 0.06 euro ]. Estimate, not a measurement.

### 6. Ship it or not

[Which variant, on what evidence, and what would change your mind. Ten
records is not enough to be confident and saying so is worth more than
claiming a win. If your answer is "keep one example and drop the rest", say
which one and why.]

I would provisionally choose the few-shot variant. In my live run, urgency improved from 8 to 10/10, while category and due_date stayed at 8/10 and quote stayed at 10/10. Neither variant produced invalid records. The examples added 302 input tokens per call, costing an estimated 0.06 euros per thousand calls on the course's small tier.

However, then documents are too few to establish a reliable improvement. Before deploying it, I would test both variants on a larger, unseen set covering all three languages, especially ambiguous urgency and date expression. 

I would change my mind if the urgency improvement disappeared on unseen cases or if the examples caused regressions in other fields. In that case, I would prefer zero-shot for its lower token cost. 

### Sensitivity variant

Variant tested: `role`.

I prepended “You are a senior service desk analyst.” to my few-shot prompt. I kept the examples, schema, scorer, and evaluation documents unchanged and ran both variants live.

| Field | Few-shot baseline | Role variant | Change |
| Category | 8/10 | 9/10 | +1 |
| Urgency | 10/10 | 10/10 | 0 |
| Due_date | 8/10 | 8/10 | 0 |
| Quote | 10/10 | 10/10 | 0 |

Neither variant produced invalid records. English field errors decreased from three to two; French stayed at one and German stayed at zero.

Adding the role instruction improved category accuracy by one correct answer on this set, with no decrease in any other field’s score. This shows that a small prompt change can affect measured results, but ten documents are too few to conclude that adding a role consistently improves extraction.

### The gold set

Ten cases written to `artifacts/goldset.json`, tagged by language.

One thing my scorer cannot currently detect:

[This is the most valuable line on the page. An example: "our scorer cannot
tell a correctly formatted date that is simply the wrong date from a
correctly extracted one, because it only compares strings."]

My scorer checks whether the quote appears verbatim in the source, but cannot determine whether it actually supports the urgency decision.

### Deferred

[Anything you did not get to, and why.]