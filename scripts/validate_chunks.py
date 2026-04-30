import argparse
import json
import random


REQUIRED_FIELDS = ["chunk_id", "primary", "metadata"]
MAX_CHAR_COUNT = 5000
MAX_NEWLINES = 20
SAMPLE_SIZE = 5
PREVIEW_LENGTH = 200


def load_chunks(path):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  [WARN] Line {i} is not valid JSON, skipping.")
    return chunks


def check_missing_fields(chunk):
    return [field for field in REQUIRED_FIELDS if field not in chunk]


def run_validation(chunks):
    total = len(chunks)
    char_counts = []
    size_outliers = []
    missing_fields = []
    newline_outliers = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "<unknown>")
        text = chunk.get("primary", {}).get("text", "")
        char_count = len(text)
        char_counts.append(char_count)

        if char_count > MAX_CHAR_COUNT:
            size_outliers.append({"chunk_id": chunk_id, "char_count": char_count})

        missing = check_missing_fields(chunk)
        if missing:
            missing_fields.append({"chunk_id": chunk_id, "missing": missing})

        if text.count("\n") > MAX_NEWLINES:
            newline_outliers.append({"chunk_id": chunk_id, "newline_count": text.count("\n")})

    avg_chars = sum(char_counts) / total if total else 0
    min_chars = min(char_counts) if char_counts else 0
    max_chars = max(char_counts) if char_counts else 0

    sample = random.sample(chunks, min(SAMPLE_SIZE, total))
    previews = [
        {
            "chunk_id": c.get("chunk_id", "<unknown>"),
            "preview": c.get("primary", {}).get("text", "")[:PREVIEW_LENGTH],
        }
        for c in sample
    ]

    return {
        "summary": {
            "total_chunks": total,
            "avg_char_count": round(avg_chars, 1),
            "min_char_count": min_chars,
            "max_char_count": max_chars,
        },
        "issues": {
            "size_outliers_count": len(size_outliers),
            "missing_fields_count": len(missing_fields),
            "newline_outliers_count": len(newline_outliers),
            "size_outliers": size_outliers,
            "missing_fields": missing_fields,
            "newline_outliers": newline_outliers,
        },
        "sample_previews": previews,
    }


def print_report(report):
    s = report["summary"]
    issues = report["issues"]

    print("\n" + "=" * 60)
    print("  CHUNK VALIDATION REPORT")
    print("=" * 60)

    print("\n[SUMMARY]")
    print(f"  Total chunks      : {s['total_chunks']}")
    print(f"  Avg char count    : {s['avg_char_count']}")
    print(f"  Min char count    : {s['min_char_count']}")
    print(f"  Max char count    : {s['max_char_count']}")

    print("\n[ISSUES]")
    print(f"  Size outliers (>{MAX_CHAR_COUNT} chars) : {issues['size_outliers_count']}")
    print(f"  Missing required fields        : {issues['missing_fields_count']}")
    print(f"  Newline outliers (>{MAX_NEWLINES} newlines) : {issues['newline_outliers_count']}")

    if issues["missing_fields"]:
        print("\n  Missing fields detail:")
        for item in issues["missing_fields"]:
            print(f"    - {item['chunk_id']}: {item['missing']}")

    print("\n[SAMPLE PREVIEWS]")
    for p in report["sample_previews"]:
        print(f"\n  chunk_id : {p['chunk_id']}")
        print(f"  preview  : {p['preview']!r}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Validate a JSONL chunks file.")
    parser.add_argument("--input", required=True, help="Path to input JSONL file")
    parser.add_argument("--output", required=True, help="Path to write JSON report")
    args = parser.parse_args()

    print(f"Loading chunks from: {args.input}")
    chunks = load_chunks(args.input)
    print(f"Loaded {len(chunks)} chunks.")

    report = run_validation(chunks)
    print_report(report)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {args.output}\n")


if __name__ == "__main__":
    main()
