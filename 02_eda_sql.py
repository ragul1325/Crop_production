"""
Step 2: Exploratory Data Analysis via SQL queries against SQLite.
Crop Production Analysis - India, 2021
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "/home/claude/crop_project/data/crop_production.db"
OUT_DIR = "/home/claude/crop_project/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
q = lambda sql: pd.read_sql_query(sql, conn)
results = {}

print("=" * 70)
print("1. TOP 15 CROPS BY PRODUCTION VOLUME")
print("=" * 70)
r = q("""
    SELECT Item, Item_Category, Production_Tonnes, Production_Million_Tonnes, Flag_Description
    FROM crop_production
    ORDER BY Production_Tonnes DESC
    LIMIT 15
""")
print(r.to_string(index=False))
results["top15_crops"] = r

print("\n" + "=" * 70)
print("2. BOTTOM 10 CROPS BY PRODUCTION VOLUME")
print("=" * 70)
r = q("""
    SELECT Item, Item_Category, Production_Tonnes, Flag_Description
    FROM crop_production
    ORDER BY Production_Tonnes ASC
    LIMIT 10
""")
print(r.to_string(index=False))
results["bottom10_crops"] = r

print("\n" + "=" * 70)
print("3. PRODUCTION BY ITEM CATEGORY")
print("=" * 70)
r = q("""
    SELECT Item_Category,
           COUNT(*) AS num_items,
           SUM(Production_Tonnes) AS total_production,
           ROUND(AVG(Production_Tonnes),0) AS avg_production
    FROM crop_production
    GROUP BY Item_Category
    ORDER BY total_production DESC
""")
print(r.to_string(index=False))
results["category_summary"] = r

print("\n" + "=" * 70)
print("4. DATA RELIABILITY (FLAG) BREAKDOWN")
print("=" * 70)
r = q("""
    SELECT Flag, Flag_Description, COUNT(*) AS num_items,
           SUM(Production_Tonnes) AS total_production
    FROM crop_production
    GROUP BY Flag, Flag_Description
    ORDER BY num_items DESC
""")
print(r.to_string(index=False))
results["flag_breakdown"] = r

print("\n" + "=" * 70)
print("5. SHARE OF TOTAL PRODUCTION HELD BY TOP N CROPS")
print("=" * 70)
r = q("""
    WITH total AS (SELECT SUM(Production_Tonnes) AS grand_total FROM crop_production)
    SELECT Item, Production_Tonnes,
           ROUND(100.0 * Production_Tonnes / (SELECT grand_total FROM total), 2) AS pct_of_total,
           ROUND(100.0 * SUM(Production_Tonnes) OVER (ORDER BY Production_Tonnes DESC) /
                 (SELECT grand_total FROM total), 2) AS cumulative_pct
    FROM crop_production
    ORDER BY Production_Tonnes DESC
    LIMIT 10
""")
print(r.to_string(index=False))
results["concentration_top10"] = r

print("\n" + "=" * 70)
print("6. STAPLE GRAINS COMPARISON (Rice, Wheat, Maize, Barley, Sorghum, Millet)")
print("=" * 70)
r = q("""
    SELECT Item, Production_Tonnes, Production_Rank
    FROM crop_production
    WHERE Item IN ('Rice', 'Wheat', 'Maize (corn)', 'Barley', 'Sorghum', 'Millet')
    ORDER BY Production_Tonnes DESC
""")
print(r.to_string(index=False))
results["staple_grains"] = r

print("\n" + "=" * 70)
print("7. FRUIT vs VEGETABLE PRODUCTION (keyword-based subset)")
print("=" * 70)
r = q("""
    SELECT
      CASE
        WHEN Item LIKE '%fruit%' OR Item IN ('Bananas','Mangoes, guavas and mangosteens',
             'Apples','Grapes','Oranges','Papayas','Pineapples','Watermelons',
             'Lemons and limes','Tangerines, mandarins, clementines') THEN 'Fruit'
        WHEN Item LIKE '%vegetable%' OR Item IN ('Tomatoes','Onions and shallots, dry (excluding dehydrated)',
             'Cabbages','Cauliflowers and broccoli','Eggplants (aubergines)','Okra',
             'Cucumbers and gherkins','Potatoes') THEN 'Vegetable'
        ELSE 'Other'
      END AS food_group,
      COUNT(*) AS num_items,
      SUM(Production_Tonnes) AS total_production
    FROM crop_production
    GROUP BY food_group
    ORDER BY total_production DESC
""")
print(r.to_string(index=False))
results["fruit_vs_vegetable"] = r

print("\n" + "=" * 70)
print("8. ESTIMATED/IMPUTED VS OFFICIAL FIGURES")
print("=" * 70)
r = q("""
    SELECT Is_Estimated_Or_Imputed, COUNT(*) AS num_items,
           SUM(Production_Tonnes) AS total_production
    FROM crop_production
    GROUP BY Is_Estimated_Or_Imputed
""")
print(r.to_string(index=False))
results["data_quality_split"] = r

# Save all results to Excel
xlsx_path = os.path.join(OUT_DIR, "eda_query_results.xlsx")
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    for name, df in results.items():
        df.to_excel(writer, sheet_name=name[:31], index=False)
print(f"\nAll query results saved -> {xlsx_path}")

conn.close()
