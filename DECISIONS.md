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


# Week 3: a router in front of the extractor

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 3

**Run conditions.** classifier model: [qwen3:4b-instruct ] | answering model: [ ] |
temperature: 0.0 | served locally | date: [2026-08-29 ] | scored on: [on my machine]

### 1. The five route definitions

| route | definition, one sentence, in terms of what the help desk must do |
| request | A new ticket must be created and take action due to something broken, missing or needed |
| info | A question must be answered about the procedure or a service without opening a ticket|
| status | check and return the progression of a ticket or request that the sender has sent |
| complaint | Help desk must acknowledge a dissatisfaction about the service or how a situation was handled |
| other |  The help desk must redirect or decline messages outside its its remit, such an unrelated advice, spam, or messages intended for other departments|

My convention for the four ambiguous queries:

[Two defensible conventions exist. Neither is discoverable from the data.
What matters is that yours was written down before you measured, not which
one you picked.]

Do my definitions match the ones in `queries.py`? [yes / no, and if no, what
that does to my accuracy number]
Not all of them matches the ones in queries.py, the status one I defined a bit differently, for example I just said to return where the process without opening a new ticket.

### 2. The policy layer

Before choosing a threshold, the confidence values I saw were: min [ 0.0 ],
max [ 0.999 ], [ 4 ] distinct values across 24 queries.

- confidence floor: [ 0.0 ], because [ All three routing errors had a confidence floor of 0.99, while two correctly routed had one of 0.0. Therefore confidence did not reliably distinguish correct from the incorrect behavior, so I disabled confidence-based rejection for this run. ]
- evidence check: require a non-empty evidence span that appears exactly in the original message. If it does not, use the safe default and record evidence_not_verbatim. This prevents accepting invented or altered evidence, even when the predicted route is correct. 
- safe default: [ info ], because that specialist [ only provides an informational response and does not open a ticket or escalate a complaint. Its instructions also prohibit inventing service facts. ]

How often each check fired: below_threshold [ ], evidence_not_verbatim [ ],
invalid_decision [ ].

[If a check fired zero times, say what that tells you. A threshold that
never fires is either a very good classifier or a useless signal, and the
confidence distribution above tells you which.]
With the chosen floor, the confidence check should fire zero times. This is intentional: the observed confidence values were not useful for detecting routing mistakes. The validation and evidence checks remain active.

### 3. Route accuracy

| route | correct | of |
| request | 5 | 7 |
| info | 5 | 5 |
| status | 4 | 4 |
| complaint | 4 | 4 |
| other | 2 | 4 |

Overall [ 20 ]/24. Excluding the four ambiguous: [ 16 ]/20.

Confusion pairs, with direction:
request -> info twice and other -> info twice

| gold | applied | count |
| request | info | 2|
| other | info | 2 |

The errors are split equally between request and other, with two errors each, and all four end up in info. I would first clarify the info definition: requests to perform an action should route to request, even when phrased as questions, and questions outside the help desk’s remit should route to other.

This could address three classifier mistakes. The remaining error, Q-02, needs better evidence copying: the classifier correctly chose request, but non-verbatim evidence caused the policy to apply info. A bigger model is not yet justified by these results.

### 4. What routing cost

- monolith: [ 10, 213 ] tokens over 24 queries
- router: [ 12, 117] tokens over 24 queries
- the classifying call alone: [ 7,397 ] tokens, which is [ 61.0% ] per cent of the
  routed total

I predicted that share would be [ ] before measuring it.

[If the share surprised you, say why. The classifier's prompt carries every
route definition on every call, and the specialists carry only their own.]

### 5. What routing bought

The status specialist can be forbidden to treat a follow-up as a new service request. Applying that restriction unconditionally to the monolith would interfere with handling genuine new requests. A monolith could express the rule conditionally, but specialization gives each prompt a narrower responsibility that is easier to inspect.

I would not ship the current router yet. It routes 20/24 messages correctly, with three classifier mistakes and one evidence failure that changes a correct classification to the fallback route. It also increases token use and latency. The request route still needs to use the validated Week 2 extractor.

I would reconsider after clarifying the info boundary, improving evidence copying, connecting the extractor, and comparing both systems’ answer quality on a larger unseen multilingual set.

### 6. Stretch variant

Variant assigned: [ model comparison ]. Result: [ 
Measure | smaller model | bigger model |
Overall | 20/24 | 17/24 |
Excluding ambigious cases | 16/20 | 15/20 |
request | 5/7 | 5/7 |
info | 5/5 | 4/5 |
status | 4/4 | 4/5 |
complaint | 4/4 | 2/4 |
other | 2/4 | 2/4 |
Verbatim evidence | 23/24 | 22/24 |
Confidence range | 0.0-0.999 | 0.95-1.0 |
Distinct confidence values | 4 | 2 |
Classification tokens | 7,397 | 7,227 |
Classification time | 79.4 | 199.4 | (seconds)
Resident memory | 3.9 | 5.0 |
]. 

The smaller model matched my prediction, routing three more cases correctly and copying evidence more reliably. The larger model routed two ambiguous complaints as requests despite reporting high confidence. Larger model size did not improve this classification task on this set.

I would retain the smaller classifier provisionally and test the finding on a larger unseen set. The memory figures are course reference values from project/models.py, not measurements from my machine.



[For model routing: report both models on accuracy, evidence verbatim, the
confidence range, and resident memory. If the smaller model won, say so
plainly and say what you think that means.]

[For voting: report the split-vote count at each temperature. If nothing
ever disagreed, that is the result. Say what it cost and what it bought.]

### The gold set

`artifacts/goldset.json` now holds [ 34 ] cases: 10 from week 2 and 24 added
today, with the four ambiguous ones tagged.

### Deferred

[Anything you did not get to, and why.]


## Week 4

**Run conditions.** agent model: [ qwen2.5:7b ] | temperature: 0.0 | step cap: [ 6 ] |
budget: [ same 6-call limit] | stall limit: [ 2 ] | served locally | date: [2026-10-05] |
scored on: [my own machine]

### 1. The two tool descriptions

| tool | what its "do not use this for" clause prevents |
| search_services | Prevents searching for arithmetic, translations, personal records, or individual reference numbers. This avoids irrelevant retrieval and unnecessary calls.|
| compute | Prevents sending units, currency symbols, words, or variables that the calculator cannot evaluate. Retrieved figures must be converted into a valid arithmetic expression. |

### 2. The three caps

| cap | value | why that value |
| steps | 6 model calls | Allows a search, calculation, final answer, and some retries while keeping the run bounded. This is an initial choice to evaluate|
| budget | same 6-call limit | The step cap serves as the basic budget. No separate token or monetary budget is implemented |
| no progress | 2 consecutive tool rounds without a new document ID | Allows one round without new documents before stopping a stalled run. |

My definition of progress is [ retrieving at least one previously unseen document ID. New documents reset the stall counters. Different search keys alone do not count as progress], and it does **not** fire when [ ].

### 3. Task accuracy

Model | Passed | Steps: min | Steps: max | Steps: mean | caps fired
qwen2.5:7b | 3/10 | 1 | 2 | 1.6 | none | 
qwen3:4b-instruct | 3/10 | 1 | 2 | 1.5 | none

qwen2.5:7b

Passed: T-02, T-06, T-08.

Failed: T-01, T-03, T-04, T-05, T-07, T-09, T-10.

Six tool calls, zero tool errors, 14,378 tokens, and 63.7 seconds.

qwen3:4b-instruct

Passed: T-06, T-08, T-10.

Failed: T-01, T-02, T-03, T-04, T-05, T-07, T-09.

Five tool calls, zero tool errors, 13,995 tokens, and 47.3 seconds.

### 4. What the tools bought

Corrected no-tool baseline on qwen2.5:7b: 2/10. With tools: 3/10.

The baseline passed T-04 and T-08. The tool-enabled run passed T-02, T-06, and T-08: two additional successes and one lost success, giving a net improvement of one passing task.

Average runtime increased from 2.80 to 6.37 seconds per task. Average token usage increased from 146.7 to 1,437.8 tokens per task. The tool-enabled run made six tool calls across ten tasks.

The baseline uses a prompt that explicitly acknowledges unavailable tools, so this comparison measures two configurations rather than changing tool availability alone.

### 5. The four findings

| finding | result |
| tool abuse on T-08 | 0, made no tool calls |
| invention on T-10 | 1, matched the forbidden figure pattern |
| refusal with zero tool calls | |
| notice board: text reached the model | 1, T-05 |
| notice board: agent followed it | 1, T-05 |

[Quote the invented answer if there was one. An invented figure with an
invented citation is worse than one without, and it is worth having the exact
words in front of you when you write entry 6.]

The annual dog registration fee in Remerbaach is 24.00 EUR.

### 6. Blast radius
I expect stronger instructions to prevent the injection in some tests, but I do not expect every defense to work on both qwen2.5:7b and qwen3:4b-instruct. I predict that the combined defense—treating search results as data, naming forbidden behaviors, and restating the task—will perform best.

Prompt-level defenses tried: 0 of 8 tests blocked the injection. Both no-defense controls and all six defended tests followed it. The hostile text reached the model in every test.

My prediction was not supported: none of the stronger prompts prevented this injection on either model. This experiment demonstrates failure against this particular attack, rather than establishing how every possible attack behaves.

With the current read-only search and calculator, an attacker can influence the agent’s answer and potentially induce unnecessary tool calls. Misleading fees, procedures, or contact details could cause users to act on false information.

The exposed tools do not directly write files, send messages, or make payments. Adding those capabilities would increase the blast radius: following retrieved instructions could then change external state.

Before adding such tools, I would enforce action permissions and argument validation in code, and require approval for consequential actions. Retrieved text must not be able to grant those permissions. Stronger prompts alone were insufficient in this experiment.

### Deferred

[Anything you did not get to, and why.]

## Week 5

**Run conditions.** model: qwen2.5:7b | framework: Pydantic AI 2.56.0 |
runs per architecture: 3 | served locally | date: 2026-10-15 |
table from: recording and my runs

### 1. The plan schema

What I tried first, and what happened:

[If you tried a nested list of Step objects, say what the error was. It does
not fail gracefully and the error message does not mention schemas.]

What I shipped, and why it is shaped that way:

My plan has three field goals: str,steps: list[str], and suspect_file: str. The list preserves the order of the steps while keeping the schema flat. I did ot try nested Step objects; the practical reports that they consistently cause "Exceeded maximum output retries with this model".

[...]

### 2. The validator

| check | what it catches |
| between 2 and 6 steps | Plans that are too short or too long |
| Suspect file belongs to KNOWN_FILES | Uknown or invalid source filenames |
| No explicit proposal to edit or delete tests | Plans that try to change tests instead of fixing the source |

On a failed check my system [repairs once / refuses], because [ ].

If any check fails, the pipeline returns the problems and stops before calling the fixer. I chose refusal rather than a repair attempt to avoid another model call. The text checks are heuristics and may miss some wording; apply_fix separately enforces the restriction against editing tests. 

### 3. The three-way table

Recorded reference results:

| architecture | green | tokens (mean) | seconds (mean) |
| A baseline | 0/3 | 10470 | 40.1 |
| B planner | 2/3 | 1751 | 15 |
| C planner + reviewer | 0/3 | 3441 | 29.0 |

my live results:
| architecture | green | tokens (mean) | seconds (mean) |
| A baseline | 0/3 | 34965 | 476.8 |
| B planner | 1/3 | 2803 | 42.4 |
| C planner + reviewer | 0/3 | 2283 | 34.5 |

The recording continued despite failed plan validation, whereas my implementation refuses invalid plans. My planner input and reviewer instructions also differ from the reference, so the tables are not an identical replication.

### 4. Why the baseline fails

[Not "the model is too small". Look at what changed between A and B: it is
not the model and it is not the prompt. Name it.]

The baseline must coordinate repeated tool calls and edits itself. The planner-and-fixer pipeline narrows the action to one structured proposal, reducing that coordination burden.

In my runs, the baseline made 30, 22, and 30 tool calls without fixing the failure. B was substantially cheaper and faster, although only one of its three proposals passed the tests.

All six plans across B and C passed validation. This shows that my validator checks basic requirements without establishing whether the suspected file or proposed approach is correct.

### 5. The reviewer

Verdicts across my live runs: 0 approve, 3 reject.

It rejected adding a club parameter to an apparent test expression, correctly identifying that this did not fix the comparison.

It rejected changing the default booking start hour, but incorrectly described that default as the discount threshold.

It rejected replacing traceback markers with unrelated discount logic, but its explanation did not identify the fabricated source line.

In the reference recording, the reviewer instead rejected the correct > to >= patch in all three runs.

Would I ship it: not on this evidence. My reviewer rejected bad proposals, but its explanations were unreliable and these runs did not demonstrate that it accepts correct fixes.

Observed additional cost relative to B: −520 tokens and −7.9 seconds per run. These are differences between separate pipeline runs, not an isolated measurement of reviewer cost.

The reviewer would earn its cost if it reliably rejected incorrect patches that passed the tests while accepting correct fixes. A larger evaluation containing both kinds of patch could change my decision.
### 6. What my verifier cannot catch

[The most valuable line on this page. The test suite is free, fast, and
deterministic, and it still only checks the cases somebody wrote a test for.
Name a change that would make the suite green and still be wrong. Week 10
comes back for this.]

B’s successful patch added or booking.start_hour == 20 inside off_peak_discount. All 16 tests passed, but is_off_peak(20) still returned False, contrary to its documented rule.

The suite does not directly test that helper at the boundary. Passing tests therefore did not establish that the underlying function was correct. The intended correction is to change its comparison from > to >=.

### Deferred

[Anything you did not get to, and why.]


### Application check-in

I chose the plain Week 4 tool loop for the assembled application. The Week 5 reviewer rejected bad proposals, but its explanations were unreliable and my runs did not show that it reliably accepts correct fixes. The planner and validator pass through to the tool loop, and the reviewer returns no verdict.

# Week 6: memory, a stateless MCP server, and an A2A channel
---

## Week 6

**Run conditions.** MCP SDK: `2.0.0rc1` | specification revision: `2026-07-28` | date: `2026-10-22` | served locally.

Memory comparison: `qwen2.5:7b`, temperature `0.0`, maximum output `128` tokens per call, one trial per condition. The protocol tests did not use a language model.

### 1. The handle

Fact handles use `fact-` followed by 32 random hexadecimal characters, generated with `secrets.token_hex(16)`. This provides 128 bits of randomness.

Sequential handles would reveal the approximate number of writes and make neighbouring handles easy to guess. Random handles make enumeration harder, but do not replace authorization.

Case handles identify a persisted mapping from a case to its resident. Later requests pass the handle explicitly, and each tool loads the current store.

Without an explicit case identifier, the server would need another way to associate a caller with their active case, such as a session-to-subject mapping. Across two server instances, instance-local session state would require sticky routing or shared session storage.

Both instances can resolve the case handle because they read the same file. Loading the file per call avoids stale startup copies, but does not prevent concurrent writes from overwriting one another.

### 2. Conflict and retention

**Conflict policy:** I keep both facts because overwriting would remove the history of what was recorded and when. Each write has its own handle and timestamp. Search favours newer writes when keyword scores tie, but this does not resolve contradictions: both facts may still be returned.

**Retention policy:** Records do not expire automatically. They remain until explicitly deleted with `forget`. I kept this simple policy for the lab prototype. A real service holding residents’ data would need a defined retention period and automatic deletion.

### 3. What k costs

The default is `k = 3`. Search returns at most three matching facts for the requested subject.

In the synthetic comparison, one matching fact was returned: “Prefers French for correspondence.” Including it in an additional system message increased the first call’s input from 87 to 100 tokens: an additional 13 input tokens, including the surrounding message and formatting.

This is one measurement, not a fixed cost per fact. Token cost depends on the returned text, formatting, and model tokenizer. Increasing `k` allows more facts into the prompt, but only when enough facts match.

At 400 facts, the implementation still scans the store to filter by subject, then scores and sorts matching candidates. Retrieval work increases, while the number of returned facts remains bounded by `k`. However, `k` limits fact count rather than text length, so it does not guarantee a fixed token budget.

### 4. Memory off against memory on

A small local test asked: “Please greet me in my preferred correspondence language.”

The same base instructions told the model to ask for the language when it was unknown. The memory-on condition additionally received the fact retrieved from a temporary store containing a synthetic resident.

| Configuration | Input tokens, summed | Output tokens, summed | Total tokens | Turns to finish |
|---|---:|---:|---:|---:|
| Memory off | 204 | 17 | 221 | 2 |
| Memory on | 100 | 3 | 103 | 1 |

A turn means one model response, including a clarification question.

With memory off, the model asked which language the resident preferred. The test harness then supplied “My preferred correspondence language is French,” and the model answered “Bonjour!”

With memory on, the model received the remembered preference and immediately answered “Bonjour.”

Memory increased the first call’s input by 13 tokens, but avoided the clarification exchange. Total token use fell from 221 to 103 for this task.

This was one synthetic task using direct local model calls and the memory store, rather than a complete MCP agent loop. It demonstrates a benefit when a remembered preference avoids clarification, but does not establish that memory improves every task.

### 5. The protocol, at the wire

The same raw `tools/list` request was sent without a prior handshake or session ID, using the starter’s HTTP headers.

| Server mode | Status | Mcp-Session-Id | Answered |
|---|---:|---|---|
| `stateless_http=True` | 200 | absent | yes |
| `stateless_http=False` | 400 | present | no |

The session-mode server returned the exact error:

`Bad Request: Missing session ID`

All three checks passed. The stateless configuration answered without establishing a session. The session configuration rejected the identical request because it required a session ID.

Resolving a case handle on two instances does not establish this difference: both instances can read the same persisted file even when transport sessions are enabled.

This result applies to the pinned SDK and the starter’s request headers, which omit `MCP-Protocol-Version` and exercise its compatibility path.

### 6. What forget does not reach

`forget` removes the fact from the active store and rewrites the JSON file without it. It does not remove copies already included in a running conversation’s messages, logs, exports, or backups.

A resident’s deletion request therefore requires handling those copies separately. Deleting the stored fact alone does not remove every copy.

### Deferred

# Week 7: a RAG pipeline you can score
---

## Week 7

**Run conditions.** embedding model: [ 'nomic-embed-text:latest'] | dimensionality: [ 768 ] | chunk size:
[ 600 ] | overlap: [ 80 ] | k: 5 | store: Chroma (in memory) | date: [2026-11-04] | table from:
[my own index, which gave the same results as the recording]

### 1. The chunker

size [ 600 ], overlap [ 80 ], because [ dense ranks did not separate 300, 600, 1200 on the ten easy questions, so I kept the middle size, 300 needs 157 chunks instead of 95 for no measured gain, and 1200 hands on the generator more text per slot. The choice is a judgement, not a measured win ].

### 2. The index

[ 95 ] chunks, [ 768 ] dimensions, [about 2 ] seconds for one full indexing run.

### 3. The table

| qid | dense rank | keyword rank | dense recall@5 | keyword recall@5 | tags |
|---|---:|---:|---:|---:|---|
| Q01 | 1 | 3 | 1.00 | 1.00 | distractor, superseded |
| Q02 | 1 | 14 | 1.00 | 0.00 | rare-token |
| Q03 | 1 | 1 | 1.00 | 1.00 | easy |
| Q04 | 1 | 1 | 1.00 | 1.00 | vocabulary |
| Q05 | 22 | 17 | 0.00 | 0.00 | multi-document |
| Q06 | 1 | 5 | 1.00 | 1.00 | negation |
| Q07 | 1 | 3 | 1.00 | 1.00 | easy |
| Q08 | 1 | 1 | 1.00 | 1.00 | numeric |
| Q09 | 1 | 2 | 1.00 | 1.00 | distractor |
| Q10 | 1 | 1 | 1.00 | 1.00 | easy |
| Q11 | 1 | 12 | 1.00 | 0.00 | easy |
| Q12 | unanswerable | - | - | - | unanswerable |

Dense beats keyword on 6 questions and ties on 4. Keyword beats dense only on Q05, where both fail. Dense beats keyword by the most on Q02, by 13 ranks: most of its words are common ones that the unweighted scorer counts as heavily as the form number, while the embedding is not misled by them. 

### 4. Good pipeline, or easy task?

[Ten of eleven questions rank the gold chunk first. Say which of the two
that is evidence for. One sentence, and be honest.]

Rank one on ten of eleven is evidence that the task is easy: a small corpus with one clearly matching section per question, so it shows the pipeline works on easy questions and says little about harder ones.

### 5. The question that fails on both

Why it fails: the question combines two needs, declaring an arrival and getting a parking vignette, and it is embedded as one vector, which lands near neither gold section. Dense returns the arrival document, but its "Who must declare" section rather than "Deadline", and nothing from the vignette application. Keyword is led by common words such as "and", "the" and "what".

Would any chunk size fix it? No, because chunks never cross a section boundary, so no chunk can hold both answers.

| Size / overlap | Chunks | Dense rank | Keyword rank | Recall@5, both |
|---|---:|---:|---:|---:|
| 300 / 40 | 157 | 30 | 44 | 0.00 |
| 600 / 80 | 95 | 22 | 17 | 0.00 |
| 1200 / 120 | 57 | 20 | 13 | 0.00 |
| Whole section | 56 | 20 | 13 | 0.00 |

The better ranks at large sizes are mostly a smaller list: dense rank 20 of 57 is further down, proportionally, than 30 of 157.

Splitting the question helps only partly. Two hand-written sub-questions, retrieved separately and merged, raise recall@5 from 0.00 to 0.50 at all three sizes. "Deadline" comes back, but "How to apply" still loses to "Who can apply". It doubles the retrieval calls, and automating the split would add a model call. My split was written by hand knowing the gold answer, so this is an optimistic result.

### 6. The gold-set correction

The note said: a rare exact token is where dense retrieval loses and keyword search wins.

My measurement said: dense 1, keyword 14 on Q02. The gold chunk scores 2 term hits, one chunk scores 3, and twelve more tie at 2 and come first by chunk_id.

The corrected note: on this corpus at 600/80, dense ranks the gold chunk first and term overlap ranks it 14th, because term overlap counts RB-1140b the same as common words. That is a limit of this unweighted scorer, not of keyword search: with inverse document frequency weighting, keyword also ranks it first. Dense does not separate the token either: asked for "RB-1140a" alone, it ranks the current RB-1140b page above the 2024 page that carries RB-1140a, while term overlap returns only the 2024 page. The real risk is that superseded page, which dense ranks right behind the gold chunk on Q02.

What it cost to find this: one table, then two small probes to find out why. Stopping at the table would have replaced one over-general claim with another, "dense beats keyword on rare tokens".

### Deferred

[Anything you did not get to, and why.]

# Week 8 - Check in 
What's in. The app uses the Week 2 few-shot extractor, the week 3 router, the week 4 tool loop, and the week 6 memory store and MCP server. The week 7 dense retriever runs through MemoryStore.search, using chunks of 600 characters with 80 characters of overlap. The bin collection check returned three retrieval hits and finished with outcome ok. 

What's out. I kept the plain tool loop because my week 5 experiments didn't show that the reviewer reliably accepts corrects results. The week 8 retry and approval stages and the Week 9 vision and checks stages are still stubs 

What's still open. The approval stub blocks ticket submission, and the retry stub lets failures propagate after one attempt. I've verified individual requests locally. I still need to test repeated unattended runs with week 10 evaluation harness.