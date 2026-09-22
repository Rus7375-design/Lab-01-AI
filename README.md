# Lab 01 — The price of one request

Week 1 · LLMs, Agentic AI and Reinforcement Learning · Narxoz University

You will measure what the same piece of work costs in English, Russian and
Kazakh, and you will get the number by measuring it rather than by looking it
up. The tokenizer is the reason the three numbers differ, and it is the first
engineering constraint in this course that has a currency attached.

## Setup

Requires **Python 3.10+** — the `anthropic` SDK's 1.x line dropped 3.9.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste in a real ANTHROPIC_API_KEY
```

`.env` is gitignored; `.env.example` is the template that ships in the repo.
`part2_measure.py` loads `.env` automatically — no need to `export` anything.
The key must be scoped to a **workspace** in the Console, not the
organization level, or the API rejects every request with a 400 asking for
an `anthropic-workspace-id` header.

No API key is needed for Part 0, Part 1 or Part 3.

## Part 0 — the OpenAI pair (no key, no network, no cost)

```bash
python3 part0_tokenizers.py
```

Anthropic publishes no offline tokenizer, so Part 2 can only show Claude's
own counts. This script fills that gap with `tiktoken`'s `o200k_base` and
`cl100k_base` — the two public tokenizers that bracket the six-tokenizer
spread shown in lecture 2 (`o200k_base` kindest to Kazakh, `cl100k_base`
harshest). It reproduces that lecture's numbers exactly, corpus item by
corpus item — a good sanity check that nothing has drifted.

## Part 1 — predict (no key, no network, no cost)

```bash
python3 part1_offline.py
```

Characters, UTF-8 bytes and words for the three texts, in three languages.
Write down your prediction for the token ratio **before** Part 2 runs. A
prediction you did not write down is a prediction you will not remember
getting wrong.

## Part 2 — measure (instructor's key, on the projector)

```bash
python3 part2_measure.py --call
```

Two things happen. `count_tokens` asks the tokenizer how many tokens each text
costs — free, and the model never runs, including a combined count for the
actual request shape (system prompt + complaint, one call) that Part 3 prices.
Then the same complaint is actually answered in each of the three languages,
so the *answer* length is measured too rather than assumed. Results land in
`measurements.json`.

`claude-opus-5` runs adaptive thinking by default, and thinking tokens are
billed at the output rate but never shown in the reply — on this corpus they
ran 175–345 tokens per answer before a single visible word. That is exactly
the invisible-cost trap lecture 2 warns about; it is not a bug to fix by
turning thinking off. `MAX_TOKENS` (2048) is sized to clear it with margin —
watch for `stop_reason: max_tokens` in the output, which means an answer got
cut off and the measurement for that language is unusable.

Without `--call` the script only counts tokens and spends nothing; Part 3 then
has to assume an answer length and will say so loudly.

## Part 3 — cost it out (no key)

```bash
python3 part3_cost.py
python3 part3_cost.py --requests-per-day 5000
```

Per-request cost across four models, the annual bill at a volume you choose,
and the two ratios that get confused in public: the input-token ratio (a
property of the tokenizer) and the total-bill ratio (what you actually pay,
which moves with answer length).

## What you hand in

One page.

1. Your Part 1 prediction, and the measured value next to it.
2. The annual cost table for a volume you justify in one sentence.
3. Which model you would put in production for a Kazakh-language support
   queue, and the cost and quality argument for it.
4. One sentence naming a cost lever this lab did **not** use.

## Extension tasks

Each task names the exact edit, the exact command, what to hand in, what to
expect, and the mistake that produces a plausible but wrong number. Numbers
under "Expect" are from the reference run (`measurements.example.json`) or
from running `part0_tokenizers.py` / `part1_offline.py` yourself — not
invented.

Adding a corpus item needs no code change: `CORPUS` is walked automatically
by Parts 0, 1 and 2's token-counting loop. But `part2_measure.py` hardcodes
`CORPUS["system_prompt"]` and `CORPUS["complaint"]` for the priced request, so
a new item is counted in Parts 0-2 but **never priced by Part 3**.

### Core — no API key, everyone does these

**1. Add your own corpus item.**
Do: add a fourth key to `CORPUS` in `texts.py` with parallel EN/RU/KK text
(a contract clause, an NBK notice, a real complaint). Run
`python3 part0_tokenizers.py` and `python3 part1_offline.py`.
Hand in: the KK/EN and RU/EN token ratios on both tokenizers.
Expect: in the same neighbourhood as `complaint` — `o200k_base` ≈1.4–2.0×,
`cl100k_base` ≈2.5–4.5×. Far outside that band usually means the three
versions are not saying the same thing.
Trap: don't expect it to show up in Part 3's cost tables — it can't, per the
hardcoding above.

**2. Locate the Kazakh premium.**
Do: write two similar-length Kazakh sentences — one using only letters shared
with Russian, one dense with ә ғ қ ң ө ұ ү һ і. Add both to `CORPUS`, run both
scripts.
Hand in: `bytes/char` from Part 1 and the token counts from Part 0 for both.
Expect: `bytes/char` nearly identical for both (both Cyrillic, 2 bytes/letter
either way — Part 1 shows RU and KK both around 1.83–1.88 regardless of which
Kazakh-only letters appear). The token counts will not be identical:
`cl100k_base` penalizes the Kazakh-specific letters much harder than
`o200k_base` does. The cost lives in the tokenizer's merge table, not in the
alphabet.
Trap: don't conclude from `bytes/char` alone that the two sentences cost the
same — that measure cannot see tokenizer behaviour at all.

**3. Prose vs. JSON.**
Do: re-express `complaint` as a JSON object (`{"opened": "March", ...}`) in
all three languages, add it as a corpus item, run `part0_tokenizers.py`.
Hand in: the token increase over prose, in absolute tokens, per language —
predict the direction before running.
Expect: JSON costs more in every language, but the *absolute* extra token
count from braces/quotes/field names is roughly constant across languages
(the punctuation and field names stay ASCII regardless of the language of the
values) — so it inflates the EN ratio proportionally more than RU or KK,
since EN starts from a smaller token count.
Trap: don't compare percentages without checking the underlying absolute
counts — a "smaller relative increase" for Kazakh is a division artifact if
the raw token overhead is actually the same.

### Advanced — extra credit, pick one

**4. Make the system prompt cheaper.**
Do: write two more `system_prompt` variants — a terser RU one, and an
English system prompt paired with the RU/KK complaint (mixed-language
request). Run `python3 part2_measure.py` (no `--call` — this step is free)
for each and read the printed `request` row.
Hand in: the new `request_tokens` for RU and KK against the baseline
(en=145, ru=209, kk=317 in the reference run).
Expect: `system_prompt` is already ~38–40% of every language's request in the
reference run (system_prompt/request_tokens: 58/145 EN, 80/209 RU, 124/317
KK) — trimming it is one of the largest single input-side levers available,
proportionally bigger than anything translation quality can fix.
Trap: never sum `system_prompt`'s and `complaint`'s standalone token counts
to estimate the combined request — that double-counts per-call message
framing; only `count_request_tokens`'s combined count (the `request` row) is
correct.

**5. Implement the cost lever this lab doesn't use.**
Do: `prices.py` defines `BATCH_DISCOUNT` (0.50) and `CACHE_READ_FRACTION`
(0.10 on opus-5/sonnet-5/haiku-4.5, 0.025 on fable-5.1) — neither is ever
applied by `cost_usd`. Write a script that re-prices the KK annual bill from
`part3_cost.py`, applying prompt caching to the `system_prompt` share of the
input (`token_counts.system_prompt`, cached after the first call) and the
`complaint` share at full price.
Hand in: the re-priced annual figure next to the uncached one from Part 3.
Expect: most of the saving comes from the system prompt being the repeated
part of every call — the bigger `system_prompt`'s share of `request_tokens`
(see Task 4), the bigger this lever's payoff.
Trap: batch discount assumes asynchronous processing — say explicitly why it
does not apply to a live support queue; and this model ignores the one-time
cache-write cost, which real caching is not free of.

**6. Shorten the answer, not the question.**
Do: append "Answer in at most two sentences." to each `system_prompt`. Run
`python3 part2_measure.py --call` and compare `output_tokens` to the
reference run (en=955, ru=1226, kk=1337).
Hand in: the new output token counts and the resulting cost change via
`part3_cost.py --output-tokens <value>`.
Expect: a large drop — output is priced at exactly 5× input on every model in
`prices.py` (e.g. opus-5: $5/$25, haiku-4.5: $1/$5), so this lever moves the
bill more per token saved than any input-side change.
Trap: check `stop_reason` in the printed output before trusting the number —
`claude-opus-5` runs adaptive thinking by default, billed as output tokens
but never shown in the reply (176–342 tokens per answer on this corpus); a
`stop_reason: max_tokens` means the answer was cut off, not shortened.

**7. Haiku vs. Opus, cost and quality.**
Do: before running anything, write down a pass/fail checklist for one answer.
Start from the trap already built into the corpus: `COMPLAINT` (`texts.py`)
claims "I have attached the contract and the statement," but nothing is
attached, and `SYSTEM_PROMPT` says to answer only from provided documents —
so a compliant answer must decline to explain why the rate changed, not
invent a plausible-sounding reason. A minimum checklist: (1) declines to
explain the rate change rather than fabricating a cause; (2) invents no
number not present in the complaint (no rate, no account number, no date
beyond March/August/twelve months); (3) answers entirely in the question's
language; (4) names a concrete next step. Then run
`python3 part2_measure.py --model haiku-4.5 --call | tee run-haiku.txt`, copy
the resulting `measurements.json` aside — the next run overwrites it — then
repeat for `opus-5`. Price both with
`python3 part3_cost.py --measurements <file> --model <key>`.
Hand in: the cost ratio, the checklist as written *before* the first run, and
the pass/fail scorecard for both models across all three languages (six
answers) — this is hand-in question 3 above, made concrete.
Expect: haiku-4.5's list price is exactly 1/5th of opus-5's on both input and
output (`prices.py`: $1/$5 vs. $5/$25), so the cost side is not the
interesting number — the quality comparison is. A fluent answer that
fabricates a reason for the rate change fails the lab's own system prompt no
matter how well it reads.
Trap: a cost argument alone does not answer hand-in question 3 — the lab
explicitly asks for the quality trade-off too. And a checklist written after
reading the answers is not a checklist, it is rationalization — the same
discipline Part 1's predict-before-you-measure rule exists to enforce.

Keep any new corpus item semantically parallel across the three languages —
`texts.py` says so directly — or the comparison measures translation length,
not tokenization.

## Files

| File | Needs a key | What it does |
|---|---|---|
| `texts.py` | no | The parallel corpus: three texts × three languages |
| `prices.py` | no | List prices, with source URL and the date they were checked |
| `part0_tokenizers.py` | no | `tiktoken` counts on `o200k_base` and `cl100k_base` |
| `part1_offline.py` | no | Characters, bytes, words, and the prediction prompt |
| `part2_measure.py` | **yes** | `count_tokens` for everything; one real answer per language |
| `part3_cost.py` | no | Reads `measurements.json`, prints the cost tables |

`measurements.json` is produced by Part 2. It is not in the repository, on
purpose: token counts are model-specific and dated, and a stale file is worse
than no file. `measurements.example.json` **is** in the repository — a
reference run from 2026-09-12, so Part 3 has something to work against
before your own Part 2 run, or if the projector key is unavailable. Copy it
to `measurements.json` to use it: `cp measurements.example.json measurements.json`.
