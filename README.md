Lab 01 - The price of one request 
1. Prediction vs. Measured Value
Before running Part 2, I predicted the token cost based on the bytes/char numbers from Part 1. Since Cyrillic letters take up twice as many bytes as Latin letters, I guessed the token count would also be roughly double.
The actual measured numbers were:
RU/EN = 79/60 = 1.32
KK/EN = 149/60 = 2.48
So my prediction was wrong in both directions. I overestimated the cost for Russian and underestimated it for Kazakh. The reason is that a tokenizer doesn't just count bytes - it groups common letter patterns into single tokens based on what it was trained on. That's why the real numbers don't match the byte-based guess.

2. Annual Cost Table
5,000 requests per day as the volume, because that's a realistic amount of traffic for a mid-size bank or telecom call center in Kazakhstan serving customers in three languages.

Model                  EN ($/year)       RU ($/year)     KK ($/year)
haiku-4.5                  2,920               2,975              3,168
sonnet-5                   5,840               5,950              6,336
opus-5                      14,600             14,874            15,841
fable-5.1                  29,200              29,747           31,682
Switching from English to Kazakh on opus-5, at the same volume, costs $1,241 more per year (1.08× the price).

3. Which Model for a Kazakh Support Queue
I'd go with sonnet-5. Here's why:
Cost: sonnet-5 costs half as much as opus-5 for the same work (6,336 vs. 15,841 $/year in Kazakh), and the gap between haiku-4.5 and sonnet-5 isn't that big in dollar terms (3,168 vs. 6,336 $/year).
Quality: This lab's complaint text has a trap built in - it claims documents are attached, but they're not, and the system prompt says to only answer based on documents that were actually provided. In a real support queue, a wrong answer isn't just annoying — it's a legal and reputation risk. So the model needs to reliably refuse to make up a reason for the price change, not just be cheap. Haiku-4.5 would save $3,168/year, but without testing how it handles this exact kind of trap, I wouldn't trust it in production yet. That's a cost-vs-reliability tradeoff that really needs its own quality test (A/B comparison) before deciding.

4. Unused cost reduction lever
Caching of the system prompt (CACHE_READ_FRACTION in prices.py, not applied in cost_usd): system_prompt accounts for 38–40% of each request and is repeated in every call, so caching it after the first request is one of the cheapest ways to reduce the annual bill without changing the quality of the responses.
Declaration on the use of AI
Used Google Gemini for:
diagnosing environment errors on Windows (venv, the difference between the python and python3 commands, source vs .bat-activation);
analysis and interpretation of the code part2_measure.py, when it turned out that the script was written for the Anthropic API, and it was changed to the Google Gemini API because it was free; Part 2 was carried out using the Gemini API instead of Claude. The prices in the final tables of Part 3 are taken from the Claude price list (prices.py), but the tokens are calculated by the Gemini tokenizer.
