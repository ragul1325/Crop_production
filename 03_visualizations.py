"""
Step 3: Data Visualization
Crop Production Analysis - India, 2021
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

DB_PATH = "/home/claude/crop_project/data/crop_production.db"
OUT_DIR = "/home/claude/crop_project/outputs/charts"
os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.0)
GREEN = "#2d6a4f"
EARTH = "#bc6c25"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM crop_production", conn)
conn.close()

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved", path)


# 1. Top 15 crops by production (horizontal bar, log-friendly given huge range)
fig, ax = plt.subplots(figsize=(9, 7))
top15 = df.nlargest(15, "Production_Tonnes").sort_values("Production_Tonnes")
ax.barh(top15["Item"], top15["Production_Million_Tonnes"], color=GREEN)
ax.set_xlabel("Production (Million Tonnes)")
ax.set_title("Top 15 Crops/Products by Production – India, 2021")
fig.tight_layout()
save(fig, "01_top15_crops.png")


# 2. Production by item category
fig, ax = plt.subplots(figsize=(7, 4.5))
cat = df.groupby("Item_Category")["Production_Tonnes"].sum().sort_values(ascending=False) / 1e6
ax.bar(cat.index, cat.values, color=[GREEN, EARTH, "#6c757d", "#a3b18a"])
ax.set_ylabel("Total Production (Million Tonnes)")
ax.set_title("Production by Item Category")
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
save(fig, "02_category_breakdown.png")


# 3. Cumulative concentration curve (Pareto-style)
fig, ax = plt.subplots(figsize=(8, 5))
sorted_df = df.sort_values("Production_Tonnes", ascending=False).reset_index(drop=True)
sorted_df["cum_pct"] = 100 * sorted_df["Production_Tonnes"].cumsum() / sorted_df["Production_Tonnes"].sum()
ax.plot(range(1, len(sorted_df) + 1), sorted_df["cum_pct"], color=GREEN, linewidth=2)
ax.axhline(80, color=EARTH, linestyle="--", linewidth=1, label="80% threshold")
ax.set_xlabel("Number of Items (ranked by production, descending)")
ax.set_ylabel("Cumulative % of Total Production")
ax.set_title("Production Concentration — How Few Crops Dominate Output")
ax.legend()
fig.tight_layout()
save(fig, "03_concentration_curve.png")


# 4. Staple grains comparison
fig, ax = plt.subplots(figsize=(7, 4.5))
grains = ["Rice", "Wheat", "Maize (corn)", "Millet", "Sorghum", "Barley"]
grain_df = df[df["Item"].isin(grains)].sort_values("Production_Tonnes", ascending=True)
ax.barh(grain_df["Item"], grain_df["Production_Million_Tonnes"], color=EARTH)
ax.set_xlabel("Production (Million Tonnes)")
ax.set_title("Staple Grain Production Comparison")
fig.tight_layout()
save(fig, "04_staple_grains.png")


# 5. Data reliability (flag) breakdown
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
flag_counts = df["Flag_Description"].value_counts()
axes[0].pie(flag_counts.values, labels=flag_counts.index, autopct="%1.0f%%",
            colors=sns.color_palette("Greens_r", len(flag_counts)))
axes[0].set_title("Share of Items by Data Source/Reliability")

flag_prod = df.groupby("Flag_Description")["Production_Tonnes"].sum().sort_values(ascending=False) / 1e6
axes[1].bar(range(len(flag_prod)), flag_prod.values, color=GREEN)
axes[1].set_xticks(range(len(flag_prod)))
axes[1].set_xticklabels(flag_prod.index, rotation=30, ha="right", fontsize=8)
axes[1].set_ylabel("Production (Million Tonnes)")
axes[1].set_title("Production Volume by Data Reliability")
fig.tight_layout()
save(fig, "05_data_reliability.png")


# 6. Fruit vs Vegetable vs Other
fig, ax = plt.subplots(figsize=(6, 4.5))
food_group = pd.read_sql_query("""
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
      SUM(Production_Tonnes) AS total_production
    FROM crop_production
    GROUP BY food_group
""", sqlite3.connect(DB_PATH))
ax.bar(food_group["food_group"], food_group["total_production"] / 1e6,
       color=[GREEN, EARTH, "#6c757d"])
ax.set_ylabel("Production (Million Tonnes)")
ax.set_title("Fruit vs Vegetable vs Other Production")
fig.tight_layout()
save(fig, "06_fruit_vegetable_other.png")


# 7. Distribution of production values (log scale histogram - huge skew)
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(df["Production_Tonnes"], bins=30, color=GREEN, edgecolor="white")
ax.set_xscale("log")
ax.set_xlabel("Production (Tonnes, log scale)")
ax.set_ylabel("Number of Items")
ax.set_title("Distribution of Production Values Across All 101 Items")
fig.tight_layout()
save(fig, "07_production_distribution.png")

print("\nAll charts generated.")
