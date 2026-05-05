#!/usr/bin/env python3
"""
bitty_core.py — Bitty's local inference engine (GPU-accelerated via Ollama)

Loads Llama 3.2 3B (Q4_K_M quantization) via Ollama REST API.
memory_check() prevents model loading if system RAM usage > 80%.
Agents call this for local-only, privacy-first file operations.
"""

import os
import sys
import json
import subprocess
import requests
import psutil
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))  # seconds

# Memory safety threshold (% of total RAM)
MEMORY_THRESHOLD = 70.0

# ─── State ───────────────────────────────────────────────────────────────────
_session = None  # Ollama client session (lazy init)


def memory_check() -> dict:
    """
    Returns dict with current RAM usage stats.
    Raises RuntimeError if RAM usage exceeds MEMORY_THRESHOLD.
    """
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    available_gb = mem.available / (1024 ** 3)
    used_percent = mem.percent

    result = {
        "total_gb": round(total_gb, 1),
        "available_gb": round(available_gb, 1),
        "used_percent": round(used_percent, 1),
    }

    if used_percent > MEMORY_THRESHOLD:
        raise RuntimeError(
            f"[bitty_core] RAM check failed: {used_percent:.1f}% used "
            f"({available_gb:.1f}GB available). Threshold is {MEMORY_THRESHOLD}%. "
            f"Model loading blocked to prevent OOM."
        )

    return result


def _ollama_generate(prompt: str, system: str = None, options: dict = None) -> str:
    """
    Internal: send a /generate call to the local Ollama server.
    Falls back to CPU if GPU VRAM is insufficient.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": options or {},
    }
    if system:
        payload["system"] = system

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def ask(prompt: str, system: str = None, temperature: float = 0.3) -> str:
    """
    Primary interface for agents to get a response from Bitty.
    Performs memory_check() before loading/generating.
    
    Args:
        prompt: The user's question / task description
        system: Optional system prompt (e.g., "You are a file analysis assistant")
        temperature: Lower = more deterministic (0.0–1.0)
    
    Returns:
        The model's text response
    
    Raises:
        RuntimeError: if memory_check() fails
        requests.RequestException: if Ollama is unreachable
    """
    memory_check()

    return _ollama_generate(
        prompt,
        system=system,
        options={"temperature": temperature},
    )


# ─── File Operation Wrappers ────────────────────────────────────────────────
# These are the lightweight, privacy-first tasks Bitty handles locally.
# The model reads the file content and answers questions about it.

SYSTEM_FILE_ANALYST = """You are a precise file analysis assistant.
Answer based strictly on the provided file content. Do not invent information.
Keep responses concise and factual."""

SYSTEM_SUMMARIZER = """You are a document summarizer.
Summarize the provided text in 2-3 sentences. Capture the key points only."""


def summarize_text(text: str) -> str:
    """Summarize a block of text (e.g., log output, notes)."""
    memory_check()
    return _ollama_generate(text, system=SYSTEM_SUMMARIZER, options={"temperature": 0.2})


def answer_about_file(filepath: str, question: str) -> str:
    """
    Read a file or directory and answer a question about its contents.
    Uses the content as context for the model.

    Args:
        filepath: Path to the file or directory to analyze
        question: What you want to know about it

    Returns:
        The model's answer based on the content
    """
    memory_check()

    path = Path(filepath)
    if not path.exists():
        return f"[bitty_core] File not found: {filepath}"

    if path.is_dir():
        entries = sorted(path.iterdir())
        content = "\n".join(
            f"{'[DIR] ' if e.is_dir() else '[FILE] '} {e.name}"
            for e in entries
        )
        prompt = f"""Directory: {filepath}

--- Contents ---
{content}
--- End Contents ---

Question: {question}"""
    else:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[bitty_core] Could not read {filepath}: {e}"

        MAX_CHARS = 30_000
        truncation_note = f"(File truncated from {len(content)} chars)"
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS] + f"\n\n[{truncation_note}]"

        prompt = f"""File: {filepath}

--- File Content ---
{content}
--- End Content ---

Question: {question}"""

    return _ollama_generate(
        prompt,
        system=SYSTEM_FILE_ANALYST,
        options={"temperature": 0.1, "num_predict": 512},
    )


def parse_csv_summary(filepath: str, question: str = "Give me a brief summary of this CSV.") -> str:
    """Parse a CSV file and answer questions about its contents."""
    memory_check()

    path = Path(filepath)
    if not path.exists():
        return f"[bitty_core] File not found: {filepath}"

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[bitty_core] Could not read {filepath}: {e}"

    MAX_CHARS = 20_000
    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + f"\n\n[...{len(content) - MAX_CHARS} chars truncated...]"

    prompt = f"""CSV File: {filepath}

--- CSV Content ---
{content}
--- End CSV ---

Question: {question}"""

    return _ollama_generate(
        prompt,
        system="You are a data analysis assistant. Answer questions about the CSV data precisely.",
        options={"temperature": 0.1, "num_predict": 512},
    )


# ─── Health Check ────────────────────────────────────────────────────────────
def health() -> dict:
    """
    Returns Bitty's current status: memory state, Ollama connectivity,
    and whether the model is loaded and ready.
    """
    status = {
        "memory": memory_check(),
        "ollama_reachable": False,
        "model_loaded": False,
        "model_name": OLLAMA_MODEL,
        "gpu_active": False,
    }

    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        status["ollama_reachable"] = True
        model_names = [m.get("name") for m in data.get("models", [])]
        status["model_loaded"] = OLLAMA_MODEL in model_names
        status["available_models"] = model_names
    except Exception as e:
        status["ollama_error"] = str(e)

    return status


# ─── CLI Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="bitty_core — Local Bitty inference engine")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check Bitty's health and Ollama status")

    ask_p = sub.add_parser("ask", help="Ask the model a question")
    ask_p.add_argument("prompt", help="Question or task description")
    ask_p.add_argument("--system", default=None, help="System prompt override")
    ask_p.add_argument("--temp", type=float, default=0.3, help="Temperature (0–1)")

    file_p = sub.add_parser("file", help="Answer a question about a file")
    file_p.add_argument("filepath", help="Path to the file")
    file_p.add_argument("question", help="Question about the file")
    file_p.add_argument("--csv", action="store_true", help="Treat as CSV")

    args = parser.parse_args()

    if args.command == "health":
        print(json.dumps(health(), indent=2))

    elif args.command == "ask":
        result = ask(args.prompt, system=args.system, temperature=args.temp)
        print(result)

    elif args.command == "file":
        if args.csv:
            result = parse_csv_summary(args.filepath, args.question)
        else:
            result = answer_about_file(args.filepath, args.question)
        print(result)

    else:
        parser.print_help()