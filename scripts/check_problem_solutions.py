#!/usr/bin/env python3
"""Compile and run each generated C/C++ reference solution with its harness."""
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build import load_problems, problem_sources

def main():
    failures = []
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        for problem in load_problems():
            for lang, (_, tests, solution) in problem_sources(problem).items():
                count += 1
                compiler, standard, ext = ("gcc", "gnu11", ".c") if lang == "c" else ("g++", "gnu++17", ".cpp")
                source = root / ("solution" + ext)
                exe = root / "solution"
                source.write_text(solution + "\n" + tests, encoding="utf-8")
                label = f"{problem['slug']} ({lang})"
                try:
                    result = subprocess.run([compiler, "-O1", "-std=" + standard, str(source), "-o", str(exe)], capture_output=True, text=True, timeout=20)
                    if result.returncode:
                        failures.append((label, result.stderr))
                        continue
                    result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=5)
                    if result.returncode or "All tests passed" not in result.stdout:
                        failures.append((label, result.stdout + result.stderr))
                except subprocess.TimeoutExpired:
                    failures.append((label, "Timed out"))
    for label, message in failures:
        print(label, message, sep=":\n")
    print(f"{count - len(failures)}/{count} reference solutions passed.")
    return bool(failures)

if __name__ == "__main__":
    sys.exit(main())
