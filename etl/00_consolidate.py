import pandas as pd
import os
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────

RAW_DIR   = Path.home() / "Desktop" / "foodics_raw_feb2026"
CLEAN_DIR = Path.home() / "Desktop" / "Restaurant-Data-Stack" / "data" / "clean"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

TARGET_BRANCHES = [
    "بروستد الريف - المهدية",
    "بروستد الريف - طويق",
    "بروستد الريف  - العزيزية",
    "بروستد الريف -  بدر",
    "بروستد الريف -  النهضة",
    "بروستد الريف - العليا",
    "بروستد الريف - الياسمين",
    "بروستد الريف - لبن",
    "بروستد الريف - الرمال",
    "بروستد الريف - قرطبه",
]

# ── HELPERS ─────────────────────────────────────────────────────────────────

def load_all_excels(folder: Path) -> dict[str, pd.DataFrame]:
    """Read every CSV file in folder, return dict of filename → DataFrame."""
    frames = {}
    # 1. Changed the search from *.xlsx to *.csv
    for f in sorted(folder.glob("*.csv")):
        try:
            # 2. Changed pd.read_excel to pd.read_csv
            df = pd.read_csv(f, dtype=str)   
            frames[f.name] = df
        except Exception as e:
            print(f"  ⚠️  Could not read {f.name}: {e}")
    return frames


def detect_table_type(df: pd.DataFrame, filename: str) -> str:
    """Guess which of the 4 table types this file is, by its columns."""
    cols = set(df.columns.str.strip().str.lower())

    if "payment_method_name" in cols:
        return "payments"
    if "tag_name" in cols:
        return "tags"
    if "unit_price" in cols or "sku" in cols:
        return "order_items"
    if "subtotal" in cols or "total_price" in cols:
        return "orders"
    return "unknown"


def filter_by_branch(df: pd.DataFrame, branch_col: str) -> pd.DataFrame:
    """Keep only rows belonging to TARGET_BRANCHES."""
    if branch_col not in df.columns:
        return df   # can't filter — return as-is and flag later
    return df[df[branch_col].isin(TARGET_BRANCHES)].copy()


# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Project Marcus — 00_consolidate.py")
    print("=" * 60)

    print(f"\n📂 Reading all CSV files from:\n   {RAW_DIR}\n")
    all_files = load_all_excels(RAW_DIR)
    print(f"   Found {len(all_files)} files.\n")

    buckets = {"orders": [], "order_items": [], "payments": [], "tags": [], "unknown": []}

    for filename, df in all_files.items():
        table_type = detect_table_type(df, filename)
        buckets[table_type].append((filename, df))
        print(f"   {filename[:45]:<45}  →  {table_type}")

    print()

    # Branch column name per table type
    branch_col_map = {
        "orders":      "branch_name",
        "order_items": "branch_name",
        "payments":    "branch_name",
        "tags":        "order_branch_name",
    }

    results = {}

    for table_type, file_list in buckets.items():
        if table_type == "unknown":
            if file_list:
                print(f"⚠️  {len(file_list)} file(s) could not be classified:")
                for fn, _ in file_list:
                    print(f"     {fn}")
            continue

        if not file_list:
            print(f"⚠️  No files found for: {table_type}")
            continue

        # Combine all files for this table type
        combined = pd.concat([df for _, df in file_list], ignore_index=True)
        total_rows_before = len(combined)

        # Filter to target brand
        branch_col = branch_col_map[table_type]
        filtered = filter_by_branch(combined, branch_col)
        total_rows_after = len(filtered)

        results[table_type] = filtered

        # Save to clean/
        out_path = CLEAN_DIR / f"{table_type}.csv"
        filtered.to_csv(out_path, index=False, encoding="utf-8-sig")

        print(f"✅  {table_type:<15} | {total_rows_before:>7} rows total → {total_rows_after:>7} after brand filter | saved to clean/{table_type}.csv")

    # ── BRANCH COVERAGE CHECK ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("BRANCH COVERAGE CHECK (Orders table)")
    print("=" * 60)

    if "orders" in results:
        found_branches = sorted(results["orders"]["branch_name"].dropna().unique())
        print(f"\nBranches found in data ({len(found_branches)}):")
        for b in found_branches:
            print(f"   ✓  {b}")

        missing = [b for b in TARGET_BRANCHES if b not in found_branches]
        if missing:
            print(f"\n⚠️  Branches in target list but NOT in data ({len(missing)}):")
            for b in missing:
                print(f"   ✗  {b}")
        else:
            print("\n✅  All target branches are present in the data.")

    print("\n" + "=" * 60)
    print("Consolidation complete. Check Desktop/Restaurant-Data-Stack/data/clean/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()