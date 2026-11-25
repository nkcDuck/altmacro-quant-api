"""LLM Function Calling toolkit for Alternative Macro & Economic Indices (RapidAPI v1.2.0).

Exports:
- `OPENAI_TOOLS`: OpenAI-compatible function-calling schemas across discovery,
  time-series, regime-summary, crisis-similarity, and batch endpoints.
- `AltMacroAgentToolkit`: Typed Python dispatcher with parameter validation,
  live RapidAPI Proxy support (`RAPIDAPI_KEY`), and faithful offline filtering
  over `examples/responses/*.json` (including strict non-fallback `month=YYYY-MM`
  and point-in-time `asOf=YYYY-MM` semantics).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None

RAPIDAPI_HOST = "alternative-macro-economic-indices.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"
RESPONSES_DIR = Path(__file__).resolve().parent / "responses"
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

ALL_SLUGS = [
    "bigmac",
    "lipstick",
    "underwear",
    "cardboard",
    "heavy-truck",
    "copper-gold",
    "rv-leisure",
    "alcohol-scissors",
    "electricity-pulse",
    "skyscraper",
    "gold-oil",
    "breakfast-inflation",
    "quits-confidence",
    "vegas-credit",
    "comfort-food",
]

ALL_CATEGORIES = ["consumer", "manufacturing", "commodities", "labor-credit"]

OPENAI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_macro_catalog",
            "description": (
                "List alternative macroeconomic index metadata, upstream sources, "
                "licensing classes, and redacted fields, optionally scoped by category or dimension."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category slug (consumer, manufacturing, commodities, labor-credit) or comma-separated list.",
                    },
                    "dimension": {
                        "type": "string",
                        "description": "Analytical dimension 1..4 or comma-separated list (mutually exclusive with category).",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_indices",
            "description": (
                "Fetch sanitized time series for all indices in a macroeconomic category "
                "with optional strict month, asOf point-in-time, or fromMonth/toMonth range filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ALL_CATEGORIES,
                        "description": "Target category slug.",
                    },
                    "limit": {"type": "integer", "minimum": 1, "maximum": 24},
                    "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "asOf": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "fromMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "toMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                },
                "required": ["category"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_index_series",
            "description": (
                "Fetch snapshot and historical series for one alternative index. "
                "Uses strict non-fallback `month=YYYY-MM` (returns null/[] when missing) "
                "or point-in-time `asOf=YYYY-MM` (latest observation <= YYYY-MM)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string", "enum": ALL_SLUGS},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 120},
                    "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "asOf": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "fromMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "toMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                },
                "required": ["slug"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_regime_summary",
            "description": (
                "Synthesize macro regime classification, breadth counts, and dimension averages "
                "across all 15 indices or a filtered category/dimension and month/asOf snapshot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "dimension": {"type": "string"},
                    "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "asOf": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crisis_similarity",
            "description": (
                "Compare current or historical (month/asOf) 14-indicator Z-Score vector against "
                "2001 Dot-Com, 2008 GFC, 2020 COVID-19, and 2022 Inflation crisis profiles."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "window": {"type": "string", "enum": ["latest"]},
                    "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "asOf": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_batch_indices",
            "description": (
                "Bulk fetch sanitized time series filtered by slugs, category, or dimension "
                "and optional month/asOf/fromMonth/toMonth filters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "slugs": {"type": "string"},
                    "category": {"type": "string"},
                    "dimension": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 24},
                    "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "asOf": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "fromMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                    "toMonth": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
                },
                "additionalProperties": False,
            },
        },
    },
]


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def _validate_month(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not MONTH_RE.match(cleaned):
        raise ValueError(f"{field_name} must be YYYY-MM, got: {value!r}")
    return cleaned


def _resolve_limit(limit: int | None, default: int, maximum: int) -> tuple[int, int]:
    if isinstance(limit, bool):
        raise ValueError(f"limit must be an integer >= 1, got: {limit!r}")
    raw = default if limit is None else int(limit)
    if raw < 1:
        raise ValueError(f"limit must be >= 1, got: {raw}")
    clamped = max(1, min(raw, maximum))
    return raw, clamped


def _parse_csv_tokens(value: str, *, lowercase: bool = False) -> list[str]:
    tokens = [part.strip() for part in value.split(",") if part.strip()]
    return [t.lower() for t in tokens] if lowercase else tokens


def _record_year_month(rec: dict[str, Any]) -> str:
    if isinstance(rec.get("dataMonth"), str) and rec["dataMonth"]:
        return rec["dataMonth"][:7]
    if isinstance(rec.get("timestamp"), str) and rec["timestamp"]:
        return rec["timestamp"][:7]
    if isinstance(rec.get("sourceDate"), str) and rec["sourceDate"]:
        return rec["sourceDate"][:7]
    return ""


def _validate_and_build_time_filter(
    *,
    month: str | None = None,
    asOf: str | None = None,
    fromMonth: str | None = None,
    toMonth: str | None = None,
    allow_range: bool = True,
) -> dict[str, str]:
    m = _validate_month(month, "month")
    a = _validate_month(asOf, "asOf")
    f = _validate_month(fromMonth, "fromMonth")
    t = _validate_month(toMonth, "toMonth")

    if not allow_range and (f is not None or t is not None):
        raise ValueError("fromMonth/toMonth range filters are not supported on this endpoint.")
    if m is not None and (a is not None or f is not None or t is not None):
        raise ValueError("month is mutually exclusive with asOf, fromMonth, and toMonth.")
    if a is not None and (f is not None or t is not None):
        raise ValueError("asOf is mutually exclusive with fromMonth and toMonth.")
    if f is not None and t is not None and f > t:
        raise ValueError(f"fromMonth ({f}) must be <= toMonth ({t}).")

    if m is not None:
        return {"mode": "month", "month": m}
    if a is not None:
        return {"mode": "asOf", "asOf": a}
    if f is not None or t is not None:
        tf: dict[str, str] = {"mode": "range"}
        if f is not None:
            tf["fromMonth"] = f
        if t is not None:
            tf["toMonth"] = t
        return tf
    return {"mode": "latest"}


def _filter_series_records(
    records: list[dict[str, Any]],
    time_filter: dict[str, str],
    limit: int,
) -> list[dict[str, Any]]:
    mode = time_filter["mode"]
    if mode == "month":
        target = time_filter["month"]
        return [r for r in records if _record_year_month(r) == target][:1]
    if mode == "asOf":
        cutoff = time_filter["asOf"]
        eligible = [r for r in records if (ym := _record_year_month(r)) and ym <= cutoff]
        return eligible[:1]
    if mode == "range":
        f = time_filter.get("fromMonth")
        t = time_filter.get("toMonth")
        filtered = [
            r
            for r in records
            if (ym := _record_year_month(r))
            and (f is None or ym >= f)
            and (t is None or ym <= t)
        ]
        return filtered[:limit]
    return records[:limit]


class AltMacroAgentToolkit:
    """Executes OpenAI-compatible tool calls against RapidAPI or offline sample payloads."""

    def __init__(
        self,
        api_key: str | None = None,
        demo_mode: bool | None = None,
        responses_dir: Path = RESPONSES_DIR,
    ) -> None:
        resolved_key = (api_key if api_key is not None else os.environ.get("RAPIDAPI_KEY", "")).strip()
        env_demo = os.environ.get("DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}
        self.api_key = resolved_key
        self.demo_mode = bool(demo_mode) if demo_mode is not None else (env_demo or not resolved_key)
        self.responses_dir = responses_dir

    def _load_sample(self, filename: str) -> dict[str, Any]:
        with (self.responses_dir / filename).open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _live_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        query = f"?{urllib.parse.urlencode(clean_params)}" if clean_params else ""
        url = f"{BASE_URL}{path}{query}"
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
            "Accept": "application/json",
        }
        if requests is not None:
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json()
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_macro_catalog(
        self,
        category: str | None = None,
        dimension: str | None = None,
    ) -> dict[str, Any]:
        if category and dimension:
            raise ValueError("category and dimension are mutually exclusive.")
        if not self.demo_mode:
            return self._live_get("/v1/catalog", {"category": category, "dimension": dimension})

        payload = self._load_sample("catalog-manufacturing.json")
        if category is not None:
            cats = set(_parse_csv_tokens(category, lowercase=True))
            if not cats or not cats.issubset({"manufacturing"}):
                raise ValueError(
                    "Offline catalog sample only bundles category='manufacturing' (dimension 2)."
                )
            filtered = [i for i in payload["data"]["indices"] if i.get("category") in cats]
            payload["data"]["indices"] = filtered
            payload["data"]["total"] = len(filtered)
        if dimension is not None:
            dims = set(_parse_csv_tokens(dimension))
            if not dims or not dims.issubset({"2"}):
                raise ValueError(
                    "Offline catalog sample only bundles dimension='2' (category 'manufacturing')."
                )
        return payload

    def get_category_indices(
        self,
        category: str,
        limit: int | None = 12,
        month: str | None = None,
        asOf: str | None = None,
        fromMonth: str | None = None,
        toMonth: str | None = None,
    ) -> dict[str, Any]:
        tf = _validate_and_build_time_filter(
            month=month, asOf=asOf, fromMonth=fromMonth, toMonth=toMonth, allow_range=True
        )
        _, clamped_limit = _resolve_limit(limit, default=1, maximum=24)
        if not self.demo_mode:
            return self._live_get(
                f"/v1/categories/{urllib.parse.quote(category)}",
                {
                    "limit": clamped_limit,
                    "month": month,
                    "asOf": asOf,
                    "fromMonth": fromMonth,
                    "toMonth": toMonth,
                },
            )

        if category.strip().lower() not in {"manufacturing", "2"}:
            raise ValueError("Offline sample only bundles category='manufacturing'.")
        payload = self._load_sample("category-manufacturing.json")
        effective_limit = 1 if tf["mode"] in {"month", "asOf"} else clamped_limit
        indices = payload["data"]["indices"]
        payload["data"]["indices"] = {
            slug: _filter_series_records(rows, tf, effective_limit)
            for slug, rows in indices.items()
        }
        payload["data"]["limit"] = effective_limit
        payload["data"]["timeFilter"] = tf
        return payload

    def get_index_series(
        self,
        slug: str,
        limit: int | None = 14,
        month: str | None = None,
        asOf: str | None = None,
        fromMonth: str | None = None,
        toMonth: str | None = None,
    ) -> dict[str, Any]:
        tf = _validate_and_build_time_filter(
            month=month, asOf=asOf, fromMonth=fromMonth, toMonth=toMonth, allow_range=True
        )
        raw_limit, clamped_limit = _resolve_limit(limit, default=14, maximum=120)
        if not self.demo_mode:
            return self._live_get(
                f"/v1/indices/{urllib.parse.quote(slug)}",
                {
                    "limit": clamped_limit,
                    "month": month,
                    "asOf": asOf,
                    "fromMonth": fromMonth,
                    "toMonth": toMonth,
                },
            )

        if slug != "cardboard":
            raise ValueError("Offline single-index sample only bundles slug='cardboard'.")
        payload = self._load_sample("index-cardboard-range.json")
        effective_limit = 1 if tf["mode"] in {"month", "asOf"} else clamped_limit
        filtered = _filter_series_records(payload["data"]["history"], tf, effective_limit)
        payload["data"]["history"] = filtered
        payload["data"]["latest"] = filtered[0] if filtered else None
        payload["timeFilter"] = tf
        payload["pagination"]["returnedCount"] = len(filtered)
        payload["pagination"]["requestedLimit"] = raw_limit
        payload["pagination"]["appliedLimit"] = effective_limit
        return payload

    def get_regime_summary(
        self,
        category: str | None = None,
        dimension: str | None = None,
        month: str | None = None,
        asOf: str | None = None,
    ) -> dict[str, Any]:
        if category and dimension:
            raise ValueError("category and dimension are mutually exclusive.")
        tf = _validate_and_build_time_filter(month=month, asOf=asOf, allow_range=False)
        if not self.demo_mode:
            return self._live_get(
                "/v1/regime-summary",
                {
                    "category": category,
                    "dimension": dimension,
                    "month": month,
                    "asOf": asOf,
                },
            )

        if category is not None:
            cats = set(_parse_csv_tokens(category, lowercase=True))
            if not cats or not cats.issubset({"manufacturing"}):
                raise ValueError(
                    "Offline regime summary sample only bundles category='manufacturing' (dimension 2)."
                )
        if dimension is not None:
            dims = set(_parse_csv_tokens(dimension))
            if not dims or not dims.issubset({"2"}):
                raise ValueError(
                    "Offline regime summary sample only bundles dimension='2' (category 'manufacturing')."
                )

        payload = self._load_sample("regime-summary-manufacturing.json")
        if tf["mode"] == "latest":
            return payload

        # Synthesize faithful point-in-time snapshot from captured manufacturing series
        # Thresholds mirror the AltMacro backend pro-cyclical polarity rules.
        cat_sample = self._load_sample("category-manufacturing.json")
        rows_by_slug = cat_sample["data"]["indices"]
        indices_out: dict[str, Any] = {}
        expansion = neutral = stress = missing = 0
        z_vals: list[float] = []
        idx_vals: list[float] = []
        for s, rows in rows_by_slug.items():
            matched = _filter_series_records(rows, tf, 1)
            if not matched:
                missing += 1
                indices_out[s] = {
                    "slug": s,
                    "dimension": 2,
                    "indexValue": None,
                    "zScore": None,
                    "signal": None,
                    "trend": None,
                    "dataMonth": None,
                    "stance": "no-data",
                }
                continue
            rec = matched[0]
            iv = rec.get("indexValue")
            zv = rec.get("zScore")
            if isinstance(iv, (int, float)):
                idx_vals.append(float(iv))
            if isinstance(zv, (int, float)):
                z_vals.append(float(zv))
            if isinstance(iv, (int, float)) and iv >= 55:
                stance = "expansion"
                expansion += 1
            elif isinstance(iv, (int, float)) and iv <= 45:
                stance = "stress"
                stress += 1
            else:
                stance = "neutral"
                neutral += 1
            indices_out[s] = {
                "slug": s,
                "dimension": 2,
                "indexValue": iv,
                "zScore": round(float(zv), 4) if isinstance(zv, (int, float)) and not isinstance(zv, bool) else zv,
                "signal": rec.get("signal"),
                "trend": rec.get("trend"),
                "dataMonth": rec.get("dataMonth"),
                "stance": stance,
            }

        available_count = len(idx_vals)
        avg_idx = round(sum(idx_vals) / available_count, 2) if available_count > 0 else None
        avg_z = round(sum(z_vals) / len(z_vals), 4) if z_vals else None

        overall_regime: str | None = None
        if available_count > 0:
            stress_threshold = max(2, math.ceil(available_count * 0.55))
            expansion_max_stress = math.floor(available_count * 0.3)
            overall_regime = "Balanced"
            if (avg_idx is not None and avg_idx < 42) or stress >= stress_threshold:
                overall_regime = "Defensive Contraction"
            elif avg_idx is not None and avg_idx >= 56 and stress <= expansion_max_stress:
                overall_regime = "Expansion"

        existing_dims = payload.get("data", {}).get("dimensions") or []
        dim_name = (
            existing_dims[0].get("name", "Physical Manufacturing, Packaging & Capex")
            if existing_dims
            else "Physical Manufacturing, Packaging & Capex"
        )
        payload["data"]["dimensions"] = [
            {
                "dimension": 2,
                "name": dim_name,
                "avgIndexValue": avg_idx,
                "avgZScore": avg_z,
                "slugs": list(rows_by_slug.keys()),
            }
        ]
        payload["data"]["indices"] = indices_out
        payload["data"]["avgProCyclicalIndex"] = avg_idx
        payload["data"]["overallRegime"] = overall_regime
        payload["data"]["breadth"] = {
            "expansionCount": expansion,
            "neutralCount": neutral,
            "stressCount": stress,
            "missingCount": missing,
        }
        payload["data"]["timeFilter"] = tf
        return payload

    def get_crisis_similarity(
        self,
        window: str = "latest",
        month: str | None = None,
        asOf: str | None = None,
    ) -> dict[str, Any]:
        if window != "latest":
            raise ValueError("window must be 'latest' (use month or asOf for historical snapshots).")
        tf = _validate_and_build_time_filter(month=month, asOf=asOf, allow_range=False)
        if not self.demo_mode:
            return self._live_get(
                "/v1/crisis-similarity",
                {"window": window, "month": month, "asOf": asOf},
            )

        if tf["mode"] != "latest":
            raise ValueError(
                "Offline sample only bundles the window='latest' crisis-similarity snapshot "
                "(historical month/asOf backtests require live RapidAPI ULTRA access)."
            )
        return self._load_sample("crisis-similarity.json")

    def get_batch_indices(
        self,
        slugs: str | None = None,
        category: str | None = None,
        dimension: str | None = None,
        limit: int | None = 6,
        month: str | None = None,
        asOf: str | None = None,
        fromMonth: str | None = None,
        toMonth: str | None = None,
    ) -> dict[str, Any]:
        non_empty = [bool(slugs), bool(category), bool(dimension)]
        if sum(non_empty) > 1:
            raise ValueError("slugs, category, and dimension are mutually exclusive.")
        tf = _validate_and_build_time_filter(
            month=month, asOf=asOf, fromMonth=fromMonth, toMonth=toMonth, allow_range=True
        )
        _, clamped_limit = _resolve_limit(limit, default=1, maximum=24)
        if not self.demo_mode:
            return self._live_get(
                "/v1/batch",
                {
                    "slugs": slugs,
                    "category": category,
                    "dimension": dimension,
                    "limit": clamped_limit,
                    "month": month,
                    "asOf": asOf,
                    "fromMonth": fromMonth,
                    "toMonth": toMonth,
                },
            )

        if category is not None:
            cats = set(_parse_csv_tokens(category, lowercase=True))
            if not cats or not cats.issubset({"commodities"}):
                raise ValueError(
                    "Offline batch sample only bundles category='commodities' (dimension 3)."
                )
        if dimension is not None:
            dims = set(_parse_csv_tokens(dimension))
            if not dims or not dims.issubset({"3"}):
                raise ValueError(
                    "Offline batch sample only bundles dimension='3' (category 'commodities')."
                )

        payload = self._load_sample("batch-commodities.json")
        indices = payload["data"]["indices"]
        if slugs is not None:
            wanted = _parse_csv_tokens(slugs, lowercase=True)
            if not wanted:
                raise ValueError("slugs must not be empty when provided.")
            unbundled = [s for s in wanted if s not in indices]
            if unbundled:
                raise ValueError(
                    f"Offline batch sample only bundles commodities slugs {list(indices.keys())}; "
                    f"unbundled slug(s): {unbundled}."
                )
            indices = {s: indices[s] for s in wanted}
            payload["data"].pop("scope", None)
        elif category is None and dimension is None:
            payload["data"].pop("scope", None)

        effective_limit = 1 if tf["mode"] in {"month", "asOf"} else clamped_limit
        payload["data"]["indices"] = {
            s: _filter_series_records(rows, tf, effective_limit) for s, rows in indices.items()
        }
        payload["data"]["count"] = len(payload["data"]["indices"])
        payload["data"]["limit"] = effective_limit
        payload["data"]["timeFilter"] = tf
        return payload

    def dispatch(self, tool_name: str, arguments: dict[str, Any] | str) -> dict[str, Any]:
        """Dispatch an OpenAI tool_call payload by name and JSON/dict arguments."""
        parsed_args = json.loads(arguments) if isinstance(arguments, str) else dict(arguments)
        handlers = {
            "get_macro_catalog": self.get_macro_catalog,
            "get_category_indices": self.get_category_indices,
            "get_index_series": self.get_index_series,
            "get_regime_summary": self.get_regime_summary,
            "get_crisis_similarity": self.get_crisis_similarity,
            "get_batch_indices": self.get_batch_indices,
        }
        if tool_name not in handlers:
            raise ValueError(f"Unknown tool name: {tool_name}")
        return handlers[tool_name](**parsed_args)


def run_demo(demo_mode: bool) -> int:
    toolkit = AltMacroAgentToolkit(demo_mode=demo_mode)
    mode_label = "OFFLINE DEMO" if toolkit.demo_mode else "LIVE RAPIDAPI"
    print(f"=== AltMacro AI Agent Tool Showcase [{mode_label}] ===")
    print(f"Registered OpenAI function tools: {[t['function']['name'] for t in OPENAI_TOOLS]}\n")

    simulated_calls: list[tuple[str, dict[str, Any]]] = [
        ("get_regime_summary", {"category": "manufacturing"}),
        ("get_index_series", {"slug": "cardboard", "month": "2026-10"}),
        ("get_index_series", {"slug": "cardboard", "asOf": "2026-10"}),
        ("get_crisis_similarity", {"window": "latest"}),
    ]

    for idx, (tool_name, args) in enumerate(simulated_calls, start=1):
        res = toolkit.dispatch(tool_name, args)
        data = res.get("data", {})
        if tool_name == "get_regime_summary":
            summary = {
                "overallRegime": data.get("overallRegime"),
                "avgProCyclicalIndex": data.get("avgProCyclicalIndex"),
                "breadth": data.get("breadth"),
                "scope": data.get("scope"),
            }
        elif tool_name == "get_index_series":
            latest = data.get("latest")
            summary = {
                "slug": data.get("slug"),
                "timeFilter": res.get("timeFilter"),
                "returnedCount": res.get("pagination", {}).get("returnedCount"),
                "latestDataMonth": latest.get("dataMonth") if latest else None,
                "latestIndexValue": latest.get("indexValue") if latest else None,
            }
        else:
            closest = data.get("closestCrisis") or {}
            summary = {
                "window": data.get("window"),
                "dimensionsAvailable": data.get("dimensionsAvailable"),
                "closestCrisisId": closest.get("id"),
                "similarityPct": closest.get("similarityPct"),
            }

        print(f"[{idx}] tool={tool_name} args={json.dumps(args)}")
        print(json.dumps(summary, indent=2, ensure_ascii=True))

    return 0


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Demonstrate OpenAI-compatible AltMacro agent tool calls."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Force offline demo mode using examples/responses/*.json.",
    )
    args = parser.parse_args(argv)
    demo_mode = True if args.demo else None
    if demo_mode is None:
        env_demo = os.environ.get("DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}
        demo_mode = env_demo or not os.environ.get("RAPIDAPI_KEY", "").strip()

    handled_errors: tuple[type[BaseException], ...] = (
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    )
    if requests is not None:
        handled_errors = (*handled_errors, requests.RequestException)

    try:
        return run_demo(demo_mode)
    except handled_errors as exc:
        print(f"ERROR: Agent tool showcase failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
