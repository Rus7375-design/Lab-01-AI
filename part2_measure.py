from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types 

from texts import CORPUS, LANGUAGES

load_dotenv()

OUTPUT_PATH = Path(__file__).with_name("measurements.json")
MODEL_ID = "gemini-3.6-flash"


def count_tokens(client: genai.Client, model_id: str, text: str) -> int:
    """Return input token count for text using Gemini tokenizer."""
    response = client.models.count_tokens(
        model=model_id,
        contents=text,
    )
    return response.total_tokens


def count_request_tokens(client: genai.Client, model_id: str, lang: str) -> int:
    """Return input tokens for system prompt + complaint combined."""
    full_text = f"{CORPUS['system_prompt'][lang]}\n\n{CORPUS['complaint'][lang]}"
    response = client.models.count_tokens(
        model=model_id,
        contents=full_text,
    )
    return response.total_tokens


def one_real_request(
    client: genai.Client, model_id: str, lang: str
) -> Optional[Dict[str, int]]:
    """Attempt to send request to Gemini and return token counts."""
    system_instruction = CORPUS["system_prompt"][lang]
    prompt = CORPUS["complaint"][lang]

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=2048,
    )

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=config,
        )

        print("  --- answer ---")
        print("  " + (response.text or "").replace("\n", "\n  "))

        usage = response.usage_metadata
        if usage:
            in_tokens = usage.prompt_token_count
            out_tokens = usage.candidates_token_count
            print(f"  billed: {in_tokens} in, {out_tokens} out")
            return {"input_tokens": in_tokens, "output_tokens": out_tokens}
    except Exception as exc:
        print(f"  [Warning] Model call failed for {lang} ({exc}). Skipping generation.")
    
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="haiku-4.5",
        help="Model placeholder for Part 3",
    )
    parser.add_argument(
        "--call",
        action="store_true",
        help="Also answer the complaint in each language",
    )
    args = parser.parse_args()

    try:
        client = genai.Client()
    except Exception as exc:
        print(f"Could not build Gemini client: {exc}", file=sys.stderr)
        return 1

    counts: Dict[str, Dict[str, int]] = {}
    print(f"counting tokens on {MODEL_ID} (Gemini API)")

    try:
        for item_id, versions in CORPUS.items():
            counts[item_id] = {
                lang: count_tokens(client, MODEL_ID, versions[lang])
                for lang in LANGUAGES
            }
            row = "  ".join(f"{lang}={counts[item_id][lang]}" for lang in LANGUAGES)
            print(f"  {item_id:<14} {row}")

        request_tokens: Dict[str, int] = {
            lang: count_request_tokens(client, MODEL_ID, lang) for lang in LANGUAGES
        }
        row = "  ".join(f"{lang}={request_tokens[lang]}" for lang in LANGUAGES)
        print(f"  {'request':<14} {row}  (system + complaint, one call -- what Part 3 prices)")
    except Exception as exc:
        print(f"Error counting tokens: {exc}", file=sys.stderr)
        return 1

    billed: Dict[str, Dict[str, int]] = {}
    if args.call:
        print(f"\nanswering the same complaint on {MODEL_ID}, in each language:")
        for lang in LANGUAGES:
            print(f"\n[{lang}]")
            result = one_real_request(client, MODEL_ID, lang)
            if result is not None:
                billed[lang] = result

    payload = {
        "model": args.model,
        "model_id": MODEL_ID,
        "token_counts": counts,
        "request_tokens": request_tokens,
        "one_request_billed": billed or None,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())