import os
import sys

# Ensure the project folder is always on sys.path so that
# Python finds OUR analyzer.py / tokens.py / parser.py
# (not any same-named stdlib module).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, request
from analyzer import analyze_code          # our W++ analyzer
import importlib
_parser_mod = importlib.import_module("parser")   # our parser.py, safe on all Python versions
Parser = _parser_mod.Parser

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────
#  HOME PAGE
# ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────
#  UPLOAD PAGE
# ─────────────────────────────────────────────────────────────
@app.route("/upload", methods=["GET"])
def upload():
    return render_template("upload.html")


# ─────────────────────────────────────────────────────────────
#  ANALYZE ROUTE
# ─────────────────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("file")

    if not file or file.filename == "":
        return "No file uploaded. Please go back and try again.", 400

    if not file.filename.endswith(".wpp"):
        return "Invalid file type. Please upload a .wpp file.", 400

    try:
        code = file.read().decode("utf-8")
    except Exception:
        return "Error reading file. Make sure it is a valid UTF-8 text file.", 400

    # ── Lexer + Analyzer ──────────────────────────────────────
    result = analyze_code(code)

    # ── Parser ────────────────────────────────────────────────
    parser       = Parser(result["tokens"])
    parse_errors = parser.parse()
    syntax_valid = len(parse_errors) == 0

    # ── Convert sets → sorted lists for Jinja2 templates ─────
    # summary["lines"] is a set; templates need a sorted list
    summary_clean = {}
    for token_type, info in result["summary"].items():
        summary_clean[token_type] = {
            **info,
            "lines": sorted(info["lines"]),
        }

    identifiers_clean = {}
    for name, info in result["identifiers"].items():
        identifiers_clean[name] = {
            **info,
            "lines": sorted(info["lines"]),
        }

    literals_clean = {}
    for value, info in result["literals"].items():
        literals_clean[value] = {
            **info,
            "lines": sorted(info["lines"]),
        }

    return render_template(
        "result.html",
        tokens           = result["tokens"],
        summary          = summary_clean,
        line_distribution= result["line_distribution"],
        identifiers      = identifiers_clean,
        literals         = literals_clean,
        overall          = result["overall"],
        parse_errors     = parse_errors,
        syntax_valid     = syntax_valid,
        source_code      = code,
    )


# ─────────────────────────────────────────────────────────────
#  RUN SERVER
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)