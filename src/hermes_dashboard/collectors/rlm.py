"""RLM trajectory collector — reads JSONL log files from RLM runs."""

from __future__ import annotations

import json
import time
from pathlib import Path

from hermes_dashboard.config import settings


def list_rlm_runs(agent_id: str = "") -> list[dict]:
    """List all RLM trajectory log files with summary metadata."""
    agents = settings.get_agents_for_query(agent_id)

    runs = []
    for ag in agents:
        rlm_dir = ag.rlm_logs_dir
        if not rlm_dir.exists():
            continue

        for f in sorted(rlm_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.name.startswith("."):
                continue
            stat = f.stat()
            run = _parse_run_summary(f)
            run["file"] = f.name
            run["path"] = str(f)
            run["size"] = stat.st_size
            run["modified"] = stat.st_mtime
            run["age_seconds"] = round(time.time() - stat.st_mtime, 1)
            run["agent_id"] = ag.id
            run["agent_name"] = ag.name
            runs.append(run)

    # Sort all agents' runs by modification time
    runs.sort(key=lambda r: r.get("modified", 0), reverse=True)
    return runs


def _parse_run_summary(filepath: Path) -> dict:
    """Parse a JSONL file and extract summary info (metadata + iteration count)."""
    metadata = {}
    iteration_count = 0
    final_answer = None
    has_errors = False
    total_code_blocks = 0
    total_sub_lm_calls = 0
    total_execution_time = 0.0
    context_question = ""

    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")

                if entry_type == "metadata":
                    metadata = {
                        "root_model": entry.get("root_model"),
                        "max_depth": entry.get("max_depth"),
                        "max_iterations": entry.get("max_iterations"),
                        "backend": entry.get("backend"),
                        "environment_type": entry.get("environment_type"),
                    }
                elif entry_type == "iteration":
                    iteration_count += 1

                    # Count code blocks
                    code_blocks = entry.get("code_blocks", [])
                    total_code_blocks += len(code_blocks)

                    # Execution time
                    iter_time = entry.get("iteration_time")
                    if iter_time is not None:
                        total_execution_time += iter_time
                    else:
                        for block in code_blocks:
                            result = block.get("result", {})
                            if result:
                                total_execution_time += result.get("execution_time", 0)

                    # Check for errors and sub-LM calls
                    for block in code_blocks:
                        result = block.get("result", {})
                        if result:
                            if result.get("stderr"):
                                has_errors = True
                            rlm_calls = result.get("rlm_calls", [])
                            total_sub_lm_calls += len(rlm_calls)

                    # Final answer
                    fa = entry.get("final_answer")
                    if fa:
                        if isinstance(fa, list) and len(fa) >= 2:
                            final_answer = fa[1]
                        elif isinstance(fa, str):
                            final_answer = fa

                    # Context question (from first iteration)
                    if iteration_count == 1 and not context_question:
                        context_question = _extract_context_question(entry)
    except OSError:
        pass

    return {
        "metadata": metadata,
        "iterations": iteration_count,
        "code_blocks": total_code_blocks,
        "sub_lm_calls": total_sub_lm_calls,
        "execution_time": round(total_execution_time, 2),
        "has_errors": has_errors,
        "final_answer": (final_answer[:200] + "...") if final_answer and len(final_answer) > 200 else final_answer,
        "context_question": context_question,
    }


def _extract_context_question(iteration: dict) -> str:
    """Extract the context question from the first iteration's prompt."""
    prompt = iteration.get("prompt", [])
    if not isinstance(prompt, list):
        return ""

    for msg in prompt:
        if msg.get("role") == "user" and msg.get("content"):
            content = msg["content"]
            # Try to extract quoted query
            import re
            match = re.search(r'original query: "([^"]+)"', content)
            if match:
                return match[1]
            # Take first substantial user message
            if len(content) > 20:
                return content[:200] + ("..." if len(content) > 200 else "")

    return ""


def get_rlm_run(filename: str, agent_id: str = "") -> dict | None:
    """Read full trajectory data from a specific JSONL file."""
    agents = settings.get_agents_for_query(agent_id)

    for ag in agents:
        filepath = ag.rlm_logs_dir / filename
        if not filepath.exists() or not filepath.is_file():
            continue

        iterations = []
        metadata = {}

        try:
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    entry_type = entry.get("type", "")
                    if entry_type == "metadata":
                        metadata = entry
                    else:
                        iterations.append(entry)
        except OSError:
            continue

        summary = _parse_run_summary(filepath)

        return {
            "file": filename,
            "metadata": metadata,
            "iterations": iterations,
            "summary": summary,
            "agent_id": ag.id,
            "agent_name": ag.name,
        }

    return None
