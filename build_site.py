# -*- coding: utf-8 -*-
"""
Generator for Dota 2 AI Coach Single-File Web App
Modular build system:
1. Combines src/template.html, src/styles.css, and src/app.js into index.html
2. Performs syntax check (node --check)
3. Validates forbidden symbols and emojis (Rule 1 & Rule 7)
4. Runs unit tests (node --test tests/*.test.js)
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
TEMPLATE_PATH = os.path.join(SRC_DIR, "template.html")
CSS_PATH = os.path.join(SRC_DIR, "styles.css")
JS_PATH = os.path.join(SRC_DIR, "app.js")
OUT_PATH = os.path.join(BASE_DIR, "index.html")

if not os.path.exists(TEMPLATE_PATH):
    print(f"Error: {TEMPLATE_PATH} not found.")
    sys.exit(1)

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = f.read()

with open(CSS_PATH, "r", encoding="utf-8") as f:
    css = f.read()

with open(JS_PATH, "r", encoding="utf-8") as f:
    js = f.read()

# Assemble single-file HTML
html_content = template.replace("/* {{CSS}} */\n", css).replace("/* {{JS}} */\n", js)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Updated index.html successfully! Size: {len(html_content)} bytes")

# Auto-check JS syntax via node --check
node_cmd = shutil.which("node") or (
    r"D:\programs\cursor\resources\app\resources\helpers\node.exe"
    if os.path.exists(r"D:\programs\cursor\resources\app\resources\helpers\node.exe")
    else "node"
)

m = re.search(r"<script>(.*)</script>", html_content, re.S)
if m:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
        t.write(m.group(1))
        t_name = t.name
    try:
        r = subprocess.run([node_cmd, "--check", t_name], capture_output=True, text=True)
        if r.returncode != 0:
            print("JS SYNTAX ERROR:\n", r.stderr)
            sys.exit(1)
        print("JS syntax OK")
    finally:
        if os.path.exists(t_name):
            os.remove(t_name)

# Auto-check forbidden symbols (Rule 1 & Rule 7)
forbidden_match = re.findall(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]", html_content)
if forbidden_match:
    print(f"FORBIDDEN SYMBOLS ERROR: Found {len(forbidden_match)} forbidden symbols from forbidden ranges: {[hex(ord(c)) for c in set(forbidden_match)]}")
    sys.exit(1)
print("No forbidden symbols found (Rule 1 OK)")

# Auto-run tests via node --test
test_files = sorted(glob.glob(os.path.join(BASE_DIR, "tests", "*.test.js")))
if test_files:
    test_run = subprocess.run([node_cmd, "--test"] + test_files, capture_output=True, text=True)
    if test_run.returncode != 0:
        print("UNIT TESTS FAILED:\n", test_run.stdout, test_run.stderr)
        sys.exit(1)
    print("Unit tests passed successfully:")
    # print summary line
    summary_lines = [l for l in test_run.stdout.splitlines() if "ℹ pass" in l or "ℹ tests" in l]
    for sl in summary_lines:
        print(" ", sl)
