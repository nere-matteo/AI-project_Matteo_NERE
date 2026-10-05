

## Week 4

**Run conditions.** agent model: [ qwen2.5:7b ] | temperature: 0.0 | step cap: [ 6 ] |
budget: [ ] | stall limit: [ 2 ] | served locally | date: [YYYY-MM-DD] |
scored on: [the recording / my own machine]

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

[ ]/10 passed. Failed: [ids].

Steps: min [ ], max [ ], mean [ ]. Caps fired: [ ].

### 4. What the tools bought

No-tool baseline: [ ]/10. With tools: [ ]/10.

One sentence on what the tools bought, and at what cost per task:

[...]

### 5. The four findings

| finding | result |
| tool abuse on T-08 | |
| invention on T-10 | |
| refusal with zero tool calls | |
| notice board: text reached the model | |
| notice board: agent followed it | |

[Quote the invented answer if there was one. An invented figure with an
invented citation is worse than one without, and it is worth having the exact
words in front of you when you write entry 6.]

### 6. Blast radius

Prompt-level defenses tried: [ ] of 8 blocked the injection.

Given that an attacker **can** make this agent say anything, the worst thing
they can make it **do** is:

[...]

That answer depends on the fact that this agent's only tools are a read-only
search and a calculator. It changes the moment the agent gains a tool that
writes, sends, or pays, because [ ].

What I would build first to bound that, and the week I expect to build it in:

[...]

[Week 12 will ask you to find this entry. Writing down a vulnerability you
have found and not yet fixed, with the week you expect to fix it, is exactly
what a security backlog is.]

### Deferred

[Anything you did not get to, and why.]
