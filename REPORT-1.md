# Crop Production Analysis — India, 2021

**FAOSTAT QCL Domain | Production Snapshot**

---

## 1. Important Scope Note (read this first)

The original project brief calls for a **regression model predicting crop
Production from Area harvested, Yield, and Year**, across multiple years.

The FAOSTAT file actually supplied (`FAOSTAT_data_en_6-27-2026.csv`) contains:

| Field | What's in the file |
|---|---|
| Area | India only |
| Element | **Production only** — no Area harvested, no Yield |
| Year | **2021 only** — no other years |
| Items | 103 crops/products (101 after cleaning) |

**This means the regression task as specified cannot be built from this
data** — there is no `Area harvested` or `Yield` column to use as predictors,
and with only one year there's no trend to learn from or validate against.

**To do the original predictive-modeling project**, re-download from
[FAOSTAT QCL](https://www.fao.org/faostat/en/#data/QCL) with:
- **Elements:** Area harvested, Yield, *and* Production (currently only Production is checked)
- **Years:** a multi-year range (e.g. 2000–2022)

Once that file is available, the same project structure here (clean → SQL EDA
→ visualize → model → Streamlit) extends directly — the modeling script would
add `Area_Harvested_ha` and `Yield_kg_ha` as features and `Production_t` as
the target, split by year for train/test, and compare Linear Regression vs.
Random Forest as planned.

**What this report delivers instead:** a complete, rigorous cross-sectional
analysis of India's 2021 crop production landscape — which crops dominate
output, how reliable the underlying data is, and what that means for
planning — using everything the supplied data actually supports.

---

## 2. Data Cleaning & Preprocessing

| Step | Detail |
|---|---|
| Raw rows | 103 |
| Duplicates removed | 0 |
| Missing values | 2 rows dropped (`Pomelos and grapefruits`, `Poppy seed`) — flagged `M` = "data cannot exist" for India, not a data error |
| Outlier check | Zero negative or zero-value production figures found |
| Derived fields | `Production_Million_Tonnes`, `Item_Category` (Primary Crop / Processed Oils / Processed Other / Fibre), `Is_Estimated_Or_Imputed`, `Production_Rank` |

**Final cleaned dataset: 101 rows**, loaded into both CSV and SQLite
(`crop_production.db`, table `crop_production`).

One important cleaning decision: FAOSTAT's QCL domain mixes **primary crops**
(e.g. Rice, Wheat) with **processed products** (e.g. Raw cane sugar, Soya
bean oil, Beer of barley) in the same `Item` list, since they share the same
domain code. These were split into an `Item_Category` field so analysis
doesn't conflate "how much sugar cane India grows" with "how much sugar
India refines from it" — both appear in the data as separate, very large
numbers.

---

## 3. Key Findings

### 3.1 Sugar cane and rice dominate by a wide margin

**Sugar cane** alone accounts for **32.2%** of all production volume in the
dataset (405 million tonnes), more than double **Rice** in second place
(195 million tonnes, 15.5%). Together with Wheat (8.7%) and Potatoes (4.3%),
just **4 items account for over 60% of total recorded production volume**.

![Top 15 crops](outputs/charts/01_top15_crops.png)

### 3.2 Production is highly concentrated

A Pareto-style concentration analysis shows the top **10 items** (out of 101)
already account for **~75%** of total production volume. This reflects how
a small number of staple/bulk crops dominate raw tonnage — naturally, since
sugar cane and cereals are grown and measured in much greater bulk than, say,
spices or berries, even where the latter may matter more economically per
hectare.

![Concentration curve](outputs/charts/03_concentration_curve.png)

### 3.3 Staple grain ranking

Among India's staple cereal grains, **Rice (195M t) and Wheat (110M t)**
lead by a wide margin over Maize (33M t), Millet (12M t), Sorghum (4.4M t),
and Barley (1.7M t) — consistent with India's well-documented role as one of
the world's largest rice and wheat producers.

![Staple grains](outputs/charts/04_staple_grains.png)

### 3.4 Most data is high-confidence, but watch the "X" and "I" flagged figures

**82 of 101 items (81%)** carry an **"A" (Official figure)** flag — the
highest confidence tier. However, a few high-volume items carry lower-
confidence flags worth noting for any downstream use:
- **Raw cane/beet sugar (33.8M t)** is flagged **"X" — figure from an
  external organization**, not an official government figure.
- **Seed cotton, unginned (17.2M t)** and **Cotton seed (11.2M t)** are also
  **"X"**-flagged.
- **Molasses (12.3M t)** is flagged **"I" — imputed by a receiving agency**.

Collectively, these lower-confidence items make up **~7% of total
production volume** (item *count* share is higher, at 19 of 101 items, but
their typical volume is smaller) — still a useful caveat for any policy or
business use case relying on precise totals for sugar and cotton products
specifically.

![Data reliability](outputs/charts/05_data_reliability.png)

### 3.5 Category breakdown

Of the 101 items, **86 are primary crops** and 15 are processed products
(10 oils, 4 other processed goods, 1 fibre product). Primary crops account
for the overwhelming majority of total volume (~1.19 billion tonnes vs. ~64
million tonnes for all processed categories combined) — expected, since
processing inherently reduces mass (e.g. cane → sugar, seeds → oil).

![Category breakdown](outputs/charts/02_category_breakdown.png)

---

## 4. Business Use Case Takeaways

- **Food Security Planning:** Sugar cane, rice, and wheat are the volume
  backbone of India's agricultural output — any food security risk
  assessment should weight these three far more heavily than the long tail
  of minor crops.
- **Supply Chain Optimization:** The top 10 items concentrating ~75% of
  volume suggests storage/transport infrastructure planning can prioritize
  a short list of high-volume commodities for the greatest impact.
- **Policy Development:** ~7% of total volume comes from non-official
  (estimated/imputed/external) figures, concentrated especially in sugar
  and cotton products — these categories may benefit from improved official
  data collection before being used as a sole basis for subsidy or insurance
  policy.
- **Precision Farming / Agro-Tech:** The dataset format does not currently
  support resource-allocation recommendations (would need Area harvested
  and Yield) — see Section 1 for what's needed to unlock that.

---

## 5. Deliverables

| File | Description |
|---|---|
| `data/crop_production_clean.csv` | Cleaned dataset |
| `data/crop_production.db` | SQLite database (table: `crop_production`) |
| `data/cleaning_report.txt` | Cleaning step log |
| `scripts/01_clean_data.py` | Cleaning pipeline |
| `scripts/02_eda_sql.py` | SQL-based EDA (8 analysis queries) |
| `scripts/03_visualizations.py` | Static chart generation |
| `outputs/eda_query_results.xlsx` | All SQL query outputs |
| `outputs/charts/*.png` | 7 EDA chart images |
| `dashboard/app.py` | Interactive Streamlit + Plotly explorer |

### Running the dashboard
```bash
pip install streamlit plotly pandas
cd dashboard
streamlit run app.py
```

---

## 6. What's Needed to Complete the Original Brief

To deliver the regression/prediction component as originally scoped:

1. Re-download FAOSTAT QCL data for India with **Elements = Area harvested,
   Yield, Production** and a **multi-year range** (10+ years recommended for
   a meaningful train/test split).
2. Pivot the long-format data so each (Item, Year) row has all three
   elements as columns: `Area_Harvested_ha`, `Yield_kg_ha`, `Production_t`.
3. Train Linear Regression and Random Forest models with `Area_Harvested_ha`,
   `Yield_kg_ha`, and `Year` (and optionally `Item` as a categorical feature)
   predicting `Production_t`.
4. Compare R², MSE, and MAE between the two models, as the brief's evaluation
   metrics specify.
5. Extend the Streamlit app with input widgets for Area harvested, Yield,
   Year, and Crop, returning a live predicted production value.

This cleaning/EDA/SQL/dashboard pipeline already built here will not need to
be redone — only the modeling and a small dashboard extension would be added
once the right data is available.
