#!/usr/bin/env python3
"""End-to-end integration test for fetch_cdp_api against live maker.taptap.cn.

Uses the chrome-cdp skill's cdp.mjs via subprocess for CDP communication.
"""

import json
import os
import subprocess
import sys

TARGET = "BFF5C248"  # maker.taptap.cn page


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, repo_root)

    cdp_script = os.path.join(repo_root, ".agents/skills/chrome-cdp/scripts/cdp.mjs")

    def cdp_eval(js_expr: str) -> str | None:
        """Call cdp.mjs evalraw to evaluate JS in the live browser page."""
        payload = json.dumps({
            "expression": js_expr,
            "awaitPromise": True,
            "returnByValue": True,
        })
        result = subprocess.run(
            ["node", cdp_script, "evalraw", TARGET, "Runtime.evaluate", payload],
            cwd=repo_root, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"  cdp.mjs error: {result.stderr[:200]}", file=sys.stderr)
            return None
        try:
            data = json.loads(result.stdout)
            return data.get("result", {}).get("value")
        except json.JSONDecodeError:
            print(f"  cdp.mjs invalid JSON: {result.stdout[:200]}", file=sys.stderr)
            return None

    # Load strategy
    strategy_path = os.path.join(repo_root, "sites/strategies/maker.taptap.cn/strategy.md")
    with open(strategy_path) as f:
        content = f.read()
    parts = content.split("---")
    import yaml
    strategy = yaml.safe_load(parts[1])

    domain = strategy["domain"]
    project_id = "f22c9896-2e7b-47db-bcb3-cd934ceef612"

    from scripts.pipeline.pipeline.phases.fetch_cdp_api import run_fetch_cdp_api

    print(f"Testing fetch_cdp_api against {domain} (project={project_id})")
    print(f"Target CDP page: {TARGET}")
    print()

    # Step 1: List API + Content
    print("--- Fetching design/ docs ---")
    results = run_fetch_cdp_api(
        eval_fn=cdp_eval,
        strategy=strategy,
        domain=domain,
        repo_root=repo_root,
        project_id=project_id,
        path_prefix="design/",
        batch_delay_sec=0.5,
    )

    print(f"Files found: {len(results)}")
    for path, entry in list(results.items())[:5]:
        status = entry['status']
        length = len(entry['content']) if entry['content'] else 0
        print(f"  [{status}] {path} ({length} chars)")

    # Step 2: Content for one file
    print()
    print("--- Content preview (first file) ---")
    if results:
        first_key = list(results.keys())[0]
        entry = results[first_key]
        if entry["status"] == "ok":
            print(f"  File: {first_key}")
            preview = entry["content"][:200].replace("\n", "\\n")
            print(f"  Preview: {preview}...")
            print(f"  Total: {len(entry['content'])} chars")
        else:
            print(f"  Error: {entry.get('error', 'unknown')}")

    succeeded = sum(1 for r in results.values() if r["status"] == "ok")
    failed = sum(1 for r in results.values() if r["status"] == "error")
    print(f"\n--- Summary: {succeeded} ok, {failed} failed ---")

    if succeeded > 0:
        print("✅ PASS")
        return 0
    print("❌ FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
