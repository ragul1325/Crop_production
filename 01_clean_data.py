"""
Step 1: Data Cleaning & Preprocessing
Crop Production Analysis - India, 2021 (FAOSTAT QCL domain)

NOTE ON SCOPE: The source file contains only the 'Production' element for a
single year (2021) for India - it does not include 'Area harvested' or
'Yield', and no other years. The original project brief assumes all three
elements across multiple years to support a regression model (Production as
a function of Area harvested, Yield, Year). That model is NOT possible with
this data. This pipeline instead delivers a thorough cross-sectional EDA of
India's 2021 crop production landscape, with clear documentation of why the
predictive-modeling step is out of scope for the data actually supplied.
"""

import pandas as pd
import numpy as np
import sqlite3
import os

RAW_PATH = "/mnt/user-data/uploads/FAOSTAT_data_en_6-27-2026.csv"
OUT_DIR = "/home/claude/crop_project/data"
os.makedirs(OUT_DIR, exist_ok=True)

# Manual category mapping: primary agricultural crops vs. processed products.
# FAOSTAT QCL mixes "Crops Primary" with "Crops Processed" in one Item list.
PROCESSED_KEYWORDS = [
    "oil", "flour", "beer", "molasses", "sugar (centrifugal", "raw cane or beet sugar",
    "cottonseed oil", "margarine", "lint, ginned", "tea leaves", "green tea", "coir, raw",
]

def categorize_item(item):
    item_lower = item.lower()
    if "oil," in item_lower or item_lower.endswith(" oil") or "oil of" in item_lower:
        return "Processed (Oils)"
    if any(k in item_lower for k in ["beer", "molasses", "margarine", "sugar (centrifugal", "raw cane or beet sugar"]):
        return "Processed (Other)"
    if "lint, ginned" in item_lower or "cottonseed" in item_lower:
        return "Fibre / Cotton Products"
    return "Primary Crop"


def main():
    df = pd.read_csv(RAW_PATH)
    report = {}

    report["raw_rows"] = len(df)
    report["raw_cols"] = len(df.columns)

    # --- Duplicates ---
    before = len(df)
    df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)

    # --- Missing values ---
    # 2 rows have Value = NaN with Flag 'M' = "Missing value; data cannot exist"
    # These are legitimate structural missingness (e.g. India doesn't grow Poppy seed
    # in a way FAO tracks) - drop them rather than impute, since there's no sensible value.
    missing_before = df["Value"].isna().sum()
    dropped_items = df.loc[df["Value"].isna(), "Item"].tolist()
    df = df.dropna(subset=["Value"])
    report["missing_value_rows_dropped"] = int(missing_before)
    report["dropped_items"] = dropped_items

    # --- Column cleanup ---
    # Drop columns that are constant / not useful for this single-country, single-year, single-element slice
    constant_cols = ["Domain Code", "Domain", "Area Code (M49)", "Area", "Element Code",
                      "Element", "Year Code", "Year", "Unit"]
    for col in constant_cols:
        report[f"unique_{col}"] = df[col].nunique()

    # Keep them (for traceability / SQL joins) but rename for clarity
    df = df.rename(columns={
        "Item Code (CPC)": "Item_Code",
        "Area Code (M49)": "Area_Code",
        "Element Code": "Element_Code",
        "Year Code": "Year_Code",
        "Flag Description": "Flag_Description",
    })

    # --- Note column: almost entirely empty, only informative for unofficial figures ---
    df["Note"] = df["Note"].fillna("")

    # --- Outlier check: flag any negative or zero production (shouldn't exist, but verify) ---
    report["zero_or_negative_values"] = int((df["Value"] <= 0).sum())

    # --- Derived fields ---
    df["Production_Tonnes"] = df["Value"]
    df["Production_Million_Tonnes"] = df["Value"] / 1_000_000
    df["Item_Category"] = df["Item"].apply(categorize_item)
    df["Is_Estimated_Or_Imputed"] = df["Flag"].isin(["E", "I", "X"])

    # Rank within full set
    df["Production_Rank"] = df["Production_Tonnes"].rank(ascending=False, method="min").astype(int)

    report["final_rows"] = len(df)
    report["item_categories"] = df["Item_Category"].value_counts().to_dict()

    # --- Save outputs ---
    csv_path = os.path.join(OUT_DIR, "crop_production_clean.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved cleaned CSV -> {csv_path}")

    db_path = os.path.join(OUT_DIR, "crop_production.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    df.to_sql("crop_production", conn, index=False, if_exists="replace")
    conn.close()
    print(f"Saved SQLite DB -> {db_path}")

    summary_path = os.path.join(OUT_DIR, "cleaning_report.txt")
    with open(summary_path, "w") as f:
        f.write("DATA CLEANING SUMMARY\n")
        f.write("=" * 60 + "\n")
        f.write(f"Raw rows: {report['raw_rows']}\n")
        f.write(f"Duplicate rows removed: {report['duplicates_removed']}\n")
        f.write(f"Rows with missing Value dropped: {report['missing_value_rows_dropped']}\n")
        f.write(f"  Dropped items: {report['dropped_items']}\n")
        f.write(f"  Reason: Flag 'M' = data cannot exist for these items in India\n")
        f.write(f"Zero/negative production values found: {report['zero_or_negative_values']}\n")
        f.write(f"Final cleaned rows: {report['final_rows']}\n\n")
        f.write("Scope constraint:\n")
        f.write("  Source file contains only Element='Production', Year=2021, Area='India'.\n")
        f.write("  No Area harvested or Yield data, and no multi-year data were supplied.\n")
        f.write("  This means: (a) no regression model can be trained as the original\n")
        f.write("  brief specifies, since Production cannot be predicted from Area\n")
        f.write("  harvested/Yield/Year without those columns; (b) no temporal trend\n")
        f.write("  analysis is possible. This pipeline instead delivers a thorough\n")
        f.write("  cross-sectional EDA of India's 2021 production landscape.\n\n")
        f.write("Derived columns added: Production_Million_Tonnes, Item_Category,\n")
        f.write("  Is_Estimated_Or_Imputed, Production_Rank\n\n")
        f.write("Item category breakdown:\n")
        for cat, cnt in report["item_categories"].items():
            f.write(f"  {cat}: {cnt}\n")
    print(f"Saved cleaning report -> {summary_path}")
    print("\nReport:", report)


if __name__ == "__main__":
    main()
