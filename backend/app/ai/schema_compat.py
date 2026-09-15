"""Convert a Pydantic JSON Schema into Google's schema subset.

Gemini's `responseSchema` accepts an OpenAPI 3.0 subset, not full JSON Schema.
Pydantic emits keys Gemini rejects (`title`, `additionalProperties`,
`exclusiveMinimum`, ...) and expresses optional fields as
`anyOf: [{...}, {"type": "null"}]`, where Gemini wants `nullable: true`.

Rather than weakening our Pydantic models to suit one vendor, we translate at
the boundary. The models stay strict, validation stays strict, and the
vendor-specific compromise lives in one file.

`minItems` / `maxItems` are a documented part of Google's Schema proto but are
rejected in practice by the generateContent endpoint - a plain
`400 INVALID_ARGUMENT` naming no field. This was established by bisecting the
real schema against the live API, not from the docs. They are dropped here and
their intent is folded into the field description instead, so the model still
receives the guidance. Nothing is lost: the Pydantic model re-checks every
list length when the response comes back, and that is the check that actually
enforces anything.
"""
from typing import Any

# Keys Gemini accepts. Everything else is dropped.
ALLOWED = {
    "type", "format", "description", "nullable", "enum",
    "properties", "required", "items",
}

# Accepted by the schema proto, rejected by the endpoint. See module docstring.
REJECTED_IN_PRACTICE = {"minItems", "maxItems"}


def to_gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return _convert(schema)


def _count_hint(node: dict[str, Any]) -> str:
    """Express dropped list-length limits as prose the model can still use."""
    low, high = node.get("minItems"), node.get("maxItems")
    if low and high:
        return f"Provide {low} to {high} items."
    if high:
        return f"Provide at most {high} items."
    if low:
        return f"Provide at least {low} items."
    return ""


def _convert(node: Any) -> Any:
    if isinstance(node, list):
        return [_convert(item) for item in node]
    if not isinstance(node, dict):
        return node

    # Optional[X] arrives as anyOf: [X, null] -> X with nullable: true
    if "anyOf" in node:
        variants = [v for v in node["anyOf"] if v.get("type") != "null"]
        nullable = len(variants) != len(node["anyOf"])
        if len(variants) == 1:
            converted = _convert(variants[0])
            if nullable:
                converted["nullable"] = True
            if "description" in node and "description" not in converted:
                converted["description"] = node["description"]
            return converted
        # A genuine union - Gemini cannot express it; fall back to a string.
        return {"type": "string", "description": node.get("description", "")}

    hint = _count_hint(node)

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key not in ALLOWED:
            continue
        if key == "properties":
            out[key] = {k: _convert(v) for k, v in value.items()}
        elif key == "items":
            out[key] = _convert(value)
        else:
            out[key] = value

    # Keep the guidance the dropped keywords carried.
    if hint:
        existing = out.get("description", "").strip()
        out["description"] = f"{existing} {hint}".strip()

    # Gemini requires an explicit type on every object node.
    if "properties" in out and "type" not in out:
        out["type"] = "object"

    return out
