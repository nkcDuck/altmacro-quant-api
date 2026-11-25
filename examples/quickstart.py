"""Quickstart CLI for the Alternative Macro & Economic Indices API (RapidAPI v1.2.0).

Walks through all 7 endpoints with automatic BASIC/PRO/ULTRA previewMode handling.
Falls back to sanitized sample payloads in `examples/responses/` when RAPIDAPI_KEY
is unset, `--demo` is passed, or `DEMO_MODE=1`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
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


class RateLimitError(Exception):
    """Raised when RapidAPI / gateway returns HTTP 429 (rate limit exceeded)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.status_code = 429
        self.retry_after = retry_after
        self.message = message


class ApiHttpError(Exception):
    """Raised when RapidAPI / gateway returns a non-429 HTTP error."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def _is_demo_mode(force_demo: bool) -> bool:
    if force_demo:
        return True
    if os.environ.get("DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return not os.environ.get("RAPIDAPI_KEY", "").strip()


def _parse_retry_after(raw_value: str | None) -> int | None:
    if not raw_value:
        return None
    cleaned = raw_value.strip()
    if cleaned.isdigit():
        return max(1, int(cleaned))
    return None


def _extract_error_message(body_text: str, default_msg: str) -> str:
    try:
        parsed = json.loads(body_text)
        if isinstance(parsed, dict) and isinstance(parsed.get("error"), str) and parsed["error"].strip():
            return parsed["error"].strip()
    except (ValueError, TypeError):
        pass
    return default_msg


def _http_get_json(url: str, headers: dict[str, str], timeout: int = 20) -> dict[str, Any]:
    if requests is not None:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 429:
            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            msg = _extract_error_message(resp.text, "Rate limit exceeded (HTTP 429).")
            raise RateLimitError(msg, retry_after=retry_after)
        if resp.status_code >= 400:
            msg = _extract_error_message(resp.text, f"HTTP {resp.status_code} {resp.reason}")
            raise ApiHttpError(resp.status_code, msg)
        return resp.json()

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 429:
            retry_after = _parse_retry_after(exc.headers.get("Retry-After") if exc.headers else None)
            msg = _extract_error_message(body, "Rate limit exceeded (HTTP 429).")
            raise RateLimitError(msg, retry_after=retry_after)
        msg = _extract_error_message(body, f"HTTP {exc.code}: {exc.reason}")
        raise ApiHttpError(exc.code, msg) from exc


def fetch_endpoint(
    endpoint_path: str,
    fallback_filename: str,
    demo_mode: bool,
    *,
    pace: bool = False,
) -> tuple[dict[str, Any], str]:
    """Fetch JSON from RapidAPI Proxy or load cached sanitized payload offline."""
    if demo_mode:
        sample_path = RESPONSES_DIR / fallback_filename
        with sample_path.open("r", encoding="utf-8") as fh:
            return json.load(fh), f"offline:{fallback_filename}"

    api_key = os.environ["RAPIDAPI_KEY"].strip()
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Accept": "application/json",
    }
    url = f"{BASE_URL}{endpoint_path}"
    try:
        return _http_get_json(url, headers), f"live:{endpoint_path}"
    except RateLimitError as exc:
        brief_wait = exc.retry_after is not None and exc.retry_after <= 5
        if brief_wait or pace:
            wait_seconds = min(exc.retry_after if exc.retry_after else 61, 65)
            print(f"  [429] Waiting {wait_seconds}s for rate-limit window reset before retrying {endpoint_path}...")
            time.sleep(wait_seconds)
            return _http_get_json(url, headers), f"live:{endpoint_path}"
        raise


def _fetch_step(
    step_label: str,
    endpoint_path: str,
    fallback_filename: str,
    demo_mode: bool,
    *,
    pace: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    try:
        return fetch_endpoint(endpoint_path, fallback_filename, demo_mode, pace=pace)
    except RateLimitError as exc:
        src = f"live:{endpoint_path}"
        print(f"\n{step_label} ({src})")
        print(f"  [RATE LIMITED - BASIC 5 req/min] {exc.message}")
        print(
            "  Guidance: Re-run with `--pace` to pause for window reset, "
            "or upgrade to PRO (30 req/min) / ULTRA (120 req/min) on RapidAPI."
        )
        return None, src


def _print_preview_banner(payload: dict[str, Any]) -> None:
    if payload.get("previewMode"):
        upgrade_to = payload.get("upgradeRequired", "PRO/ULTRA")
        notice = payload.get("upgradeNotice", "Upgrade plan for full history and analytics.")
        print(f"  [PREVIEW MODE - upgrade to {upgrade_to}] {notice}")


def run_quickstart(demo_mode: bool, *, pace: bool = False) -> int:
    mode_label = "OFFLINE DEMO (examples/responses/)" if demo_mode else f"LIVE ({BASE_URL})"
    print(f"=== AltMacro Quant API Quickstart [{mode_label}] ===\n")
    rate_limited_steps = 0

    # 1. GET /v1/health
    health, src = _fetch_step("[1/7] Health", "/v1/health", "health.json", demo_mode, pace=pace)
    if health is None:
        rate_limited_steps += 1
    else:
        h_data = health.get("data", {})
        print(f"[1/7] Health ({src})")
        print(
            f"  status={h_data.get('status')} service={h_data.get('service')} "
            f"version={h_data.get('version')} tier={h_data.get('subscriptionTier', 'N/A')} "
            f"tracked={h_data.get('indicesTracked')} cached={h_data.get('l1CachedIndices', 'N/A')}"
        )

    # 2. GET /v1/catalog?category=manufacturing
    catalog, src = _fetch_step(
        "[2/7] Catalog",
        "/v1/catalog?category=manufacturing",
        "catalog-manufacturing.json",
        demo_mode,
        pace=pace,
    )
    if catalog is None:
        rate_limited_steps += 1
    else:
        c_data = catalog.get("data", {})
        print(f"\n[2/7] Catalog ({src}) total={c_data.get('total')}")
        for item in c_data.get("indices", []):
            print(
                f"  - {item.get('slug')}: {item.get('name')} "
                f"[{item.get('licenseClass')}] redacted={item.get('redactedRawFields', [])}"
            )

    # 3. GET /v1/categories/manufacturing?limit=12
    cat_resp, src = _fetch_step(
        "[3/7] Category Series",
        "/v1/categories/manufacturing?limit=12",
        "category-manufacturing.json",
        demo_mode,
        pace=pace,
    )
    if cat_resp is None:
        rate_limited_steps += 1
    else:
        cat_data = cat_resp.get("data", {})
        tf_mode = cat_data.get("timeFilter", {}).get("mode", "latest")
        print(
            f"\n[3/7] Category Series ({src}) category={cat_data.get('category')} "
            f"count={cat_data.get('count')} mode={tf_mode}"
        )
        _print_preview_banner(cat_resp)
        for slug, rows in cat_data.get("indices", {}).items():
            if rows:
                latest = rows[0]
                print(
                    f"  - {slug} ({len(rows)} obs): month={latest.get('dataMonth')} "
                    f"indexValue={latest.get('indexValue')} signal={latest.get('signal')}"
                )
            else:
                print(f"  - {slug}: [] (no observations)")

    # 4. GET /v1/indices/cardboard?fromMonth=2025-01&toMonth=2026-11&limit=24
    idx_resp, src = _fetch_step(
        "[4/7] Single Index Series",
        "/v1/indices/cardboard?fromMonth=2025-01&toMonth=2026-11&limit=24",
        "index-cardboard-range.json",
        demo_mode,
        pace=pace,
    )
    if idx_resp is None:
        rate_limited_steps += 1
    else:
        idx_data = idx_resp.get("data", {})
        top_tf = idx_resp.get("timeFilter", {})
        pagination = idx_resp.get("pagination", {})
        latest_obs = idx_data.get("latest")
        history = idx_data.get("history", [])
        print(
            f"\n[4/7] Single Index Series ({src}) slug={idx_data.get('slug')} "
            f"tier={pagination.get('subscriptionTier', 'N/A')} "
            f"returned={pagination.get('returnedCount', len(history))} "
            f"timeFilter={top_tf.get('mode')}"
        )
        _print_preview_banner(idx_resp)
        if latest_obs:
            print(
                f"  latest: month={latest_obs.get('dataMonth')} "
                f"indexValue={latest_obs.get('indexValue')} "
                f"zScore={latest_obs.get('zScore')} signal={latest_obs.get('signal')}"
            )

    # 5. GET /v1/regime-summary?category=manufacturing
    reg_resp, src = _fetch_step(
        "[5/7] Macro Regime Summary",
        "/v1/regime-summary?category=manufacturing",
        "regime-summary-manufacturing.json",
        demo_mode,
        pace=pace,
    )
    if reg_resp is None:
        rate_limited_steps += 1
    else:
        reg_data = reg_resp.get("data", {})
        print(
            f"\n[5/7] Macro Regime Summary ({src}) regime={reg_data.get('overallRegime')} "
            f"avgProCyclicalIndex={reg_data.get('avgProCyclicalIndex')}"
        )
        _print_preview_banner(reg_resp)
        print(f"  breadth={reg_data.get('breadth')}")
        for dim in reg_data.get("dimensions", []):
            print(
                f"  - dim={dim.get('dimension')} ({dim.get('name')}): "
                f"avgIndex={dim.get('avgIndexValue')} avgZ={dim.get('avgZScore')}"
            )
        for slug, summary in reg_data.get("indices", {}).items():
            print(
                f"    * {slug}: stance={summary.get('stance')} "
                f"indexValue={summary.get('indexValue')} month={summary.get('dataMonth')}"
            )

    # 6. GET /v1/crisis-similarity?window=latest
    crisis_resp, src = _fetch_step(
        "[6/7] Crisis Similarity",
        "/v1/crisis-similarity?window=latest",
        "crisis-similarity.json",
        demo_mode,
        pace=pace,
    )
    if crisis_resp is None:
        rate_limited_steps += 1
    else:
        cr_data = crisis_resp.get("data", {})
        closest = cr_data.get("closestCrisis")
        print(
            f"\n[6/7] Crisis Similarity ({src}) window={cr_data.get('window')} "
            f"dimensionsAvailable={cr_data.get('dimensionsAvailable')}"
        )
        _print_preview_banner(crisis_resp)
        if closest:
            sim_pct = closest.get("similarityPct")
            sim_text = f" similarityPct={sim_pct}%" if sim_pct is not None else " (preview summary only)"
            print(f"  closest={closest.get('id')} ({closest.get('period')}){sim_text}")
        for comp in cr_data.get("comparisons", []):
            print(
                f"  - {comp.get('id')}: similarityPct={comp.get('similarityPct')}% "
                f"cosine={comp.get('cosineSimilarity')}"
            )

    # 7. GET /v1/batch?category=commodities&limit=6
    batch_resp, src = _fetch_step(
        "[7/7] Batch Matrix",
        "/v1/batch?category=commodities&limit=6",
        "batch-commodities.json",
        demo_mode,
        pace=pace,
    )
    if batch_resp is None:
        rate_limited_steps += 1
    else:
        b_data = batch_resp.get("data", {})
        print(
            f"\n[7/7] Batch Matrix ({src}) count={b_data.get('count')} "
            f"limit={b_data.get('limit')} redactedRawFields={batch_resp.get('meta', {}).get('redactedRawFields', [])}"
        )
        _print_preview_banner(batch_resp)
        for slug, rows in b_data.get("indices", {}).items():
            if not rows:
                print(f"  - {slug}: []")
                continue
            row = rows[0]
            if "countries" in row:
                print(
                    f"  - {slug} ({len(rows)} obs): sourceDate={row.get('sourceDate')} "
                    f"basePriceUsd={row.get('basePrice')} countriesTracked={len(row.get('countries', []))}"
                )
            else:
                print(
                    f"  - {slug} ({len(rows)} obs): month={row.get('dataMonth')} "
                    f"indexValue={row.get('indexValue')} zScore={row.get('zScore')} "
                    f"signal={row.get('signal')}"
                )

    if rate_limited_steps > 0:
        print(
            f"\nQuickstart completed cleanly ({rate_limited_steps}/7 live requests hit BASIC 5 req/min rate limit)."
        )
    else:
        print("\nQuickstart completed cleanly.")
    return 0


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Run the AltMacro Quant API 7-endpoint quickstart walkthrough."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Force offline demo mode using examples/responses/*.json.",
    )
    parser.add_argument(
        "--pace",
        action="store_true",
        help="Wait for rate-limit window reset and retry when HTTP 429 occurs on live BASIC keys.",
    )
    args = parser.parse_args(argv)
    demo_mode = _is_demo_mode(args.demo)

    net_errors: tuple[type[BaseException], ...] = (
        ApiHttpError,
        urllib.error.URLError,
        OSError,
        ValueError,
    )
    if requests is not None:
        net_errors = (*net_errors, requests.RequestException)

    try:
        return run_quickstart(demo_mode, pace=args.pace)
    except net_errors as exc:
        print(f"ERROR: Quickstart failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
