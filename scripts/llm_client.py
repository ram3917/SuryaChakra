# llm_client.py
import json
import re
from typing import Dict, Any, Optional

import ollama
from bs4 import BeautifulSoup  # pip install beautifulsoup4


# Default model; adjust if needed
OLLAMA_MODEL = "gpt-oss:120b-cloud"


def extract_article_text(html: str) -> str:
    """
    Best-effort HTML -> main article text cleaner.

    - Removes scripts/styles/noscript.
    - Prefers <article> content if present.
    - Falls back to body text otherwise.
    - Collapses whitespace and blank lines.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Prefer <article> tag if available
    article = soup.find("article")
    if article:
        root = article
    else:
        # Fallback: use <body> or entire document
        body = soup.find("body")
        root = body if body else soup

    text = root.get_text(separator="\n")

    # Collapse multiple newlines, strip surrounding spaces
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return text


def _extract_first_json_block(text: str) -> str:
    """
    Best-effort: find the first {...} block and return it.
    Useful when the model adds extra text around the JSON.
    """
    match = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if match:
        return match.group(0)
    return text


def extract_json(
    text: str,
    schema_description: str,
    system_prompt: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Use a local Ollama model to extract structured data as JSON.

    Parameters
    ----------
    text : str
        Cleaned article text (NOT raw HTML). You can get this from `extract_article_text`.
    schema_description : str
        A JSON-schema-like description of the expected output fields.
    system_prompt : str
        High-level instructions for the model (role + behaviour).
    model : str, optional
        Override the default model name if needed.

    Returns
    -------
    dict
        Parsed JSON object as a Python dict.

    Raises
    ------
    ValueError
        If the model output cannot be parsed as JSON.
    """
    model_name = model or OLLAMA_MODEL

    # Strong, explicit instructions for JSON-only output
    full_prompt = (
        f"{system_prompt}\n\n"
        "You MUST follow these rules exactly:\n"
        "1. Read the text below.\n"
        "2. Extract ONLY the fields described in the schema.\n"
        "3. Respond with ONE valid JSON object and NOTHING ELSE.\n"
        "4. Do NOT output any natural-language explanation, description, or commentary.\n"
        "5. Do NOT mention HTML, web pages, or structure.\n"
        "6. Do NOT wrap the JSON in backticks, code fences, or markdown.\n"
        "7. Do NOT include any text before or after the JSON.\n"
        "8. If you do not know a value, set it to null or 0 as appropriate.\n\n"
        f"Schema:\n{schema_description}\n\n"
        "Text to analyze:\n"
        f"{text}\n"
    )

    client = ollama.Client()

    response = client.chat(
        model=model_name,
        messages=[
            {"role": "user", "content": full_prompt},
        ],
    )

    raw = response["message"]["content"].strip()

    cleaned = raw

    # Remove code fences if present
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("` \n")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()

    # Try to isolate the first JSON object
    cleaned = _extract_first_json_block(cleaned)

    # Debug (optional; comment out once stable)
    # print("=== RAW MODEL OUTPUT ===")
    # print(raw)
    # print("=== CLEANED FOR JSON PARSE ===")
    # print(cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from model output: {e}\n\n"
            f"Raw output:\n{raw}\n\nCleaned output:\n{cleaned}"
        )

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object, got: {type(data)}")

    return data