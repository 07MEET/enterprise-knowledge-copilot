import ast
import json
import re


def clean_json_string(text: str) -> str:
    """
    Strips markdown code block wrappers (```json ... ```) from LLM output strings,
    and converts Python-style single quoted dicts into valid JSON.
    """
    text = text.strip()
    pattern = re.compile(
        r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE
    )
    match = pattern.match(text)
    if match:
        text = match.group(1).strip()

    # Preprocess escaped quotes to make it standard Python literal format
    text = text.replace("\\'", "'").replace('\\"', '"')

    # Try parsing python literal dict to fix single quotes/trailing commas
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (dict, list)):
            return json.dumps(parsed)
    except Exception:
        pass

    return text
