from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_IN = ROOT / "data" / "bakery_data.xlsx"
DATA_OUT = ROOT / "data" / "bakery_clean.csv"
SUMMARY_OUT = ROOT / "data" / "summary_tables.xlsx"

# --------------------------------------------------------------------
# 1. Load
# --------------------------------------------------------------------
print("Loading raw dataset:", DATA_IN)
df_raw = pd.read_excel(DATA_IN)
print("Raw shape:", df_raw.shape)
print(df_raw.head())

# --------------------------------------------------------------------
# 2. Audit
# --------------------------------------------------------------------
print("\n--- Column dtypes ---")
print(df_raw.dtypes)

print("\n--- Null counts ---")
print(df_raw.isnull().sum())

print("\n--- Confectionary unique values (raw) ---")
print(sorted(df_raw["Confectionary"].dropna().unique()))

print("\n--- City unique values (raw) ---")
print(sorted(df_raw["City"].dropna().unique()))

# --------------------------------------------------------------------
# 3. Clean
# --------------------------------------------------------------------
df = df_raw.copy()

# 3a. Standardise column names so they are easier to use downstream
df.columns = [
    "Date", "City", "Confectionary",
    "Units_Sold", "Revenue", "Cost", "Profit",
]

# 3b. Strip whitespace & title-case the categorical fields
df["City"] = df["City"].astype(str).str.strip().str.title()
df["Confectionary"] = df["Confectionary"].astype(str).str.strip()

# 3c. Consolidate spelling variants ("Choclate" -> "Chocolate", "nut" -> "Nut")
category_map = {
    "Choclate Chunk":  "Chocolate Chunk",
    "Chocolate Chunk": "Chocolate Chunk",
    "Caramel nut":     "Caramel Nut",
    "Caramel Nut":     "Caramel Nut",
    "Caramel":         "Caramel",
    "Biscuit":         "Biscuit",
    "Biscuit Nut":     "Biscuit Nut",
    "Plain":           "Plain",
}
df["Confectionary"] = df["Confectionary"].map(category_map).fillna(df["Confectionary"])

# 3d. Coerce numerics
for col in ["Units_Sold", "Revenue", "Cost", "Profit"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 3e. Recompute Profit when both Revenue and Cost exist (some rows had
#     small rounding or empty Profit)
mask = df["Revenue"].notna() & df["Cost"].notna()
df.loc[mask, "Profit"] = df.loc[mask, "Revenue"] - df.loc[mask, "Cost"]

# 3f. Drop rows that still cannot be analysed
critical = ["Date", "City", "Confectionary", "Units_Sold", "Revenue", "Cost"]
before = len(df)
df = df.dropna(subset=critical).reset_index(drop=True)
print(f"\nDropped {before - len(df)} rows with critical nulls. Remaining: {len(df)}")

# 3g. Engineered fields
df["Date"] = pd.to_datetime(df["Date"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["YearMonth"] = df["Date"].dt.to_period("M").dt.to_timestamp()
df["Profit_Margin"] = df["Profit"] / df["Revenue"]
df["Unit_Price"] = df["Revenue"] / df["Units_Sold"]

# 3h. Sanity checks
assert df["Units_Sold"].min() > 0
assert df["Revenue"].min() > 0
print("\n--- Confectionary unique values (cleaned) ---")
print(sorted(df["Confectionary"].unique()))
print("--- City unique values (cleaned) ---")
print(sorted(df["City"].unique()))

# --------------------------------------------------------------------
# 4. Persist clean data + summary tables
# --------------------------------------------------------------------
DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(DATA_OUT, index=False)
print(f"\nClean dataset written to: {DATA_OUT}")

with pd.ExcelWriter(SUMMARY_OUT) as xl:
    df.describe(include="all").to_excel(xl, sheet_name="describe")

    by_city = (df.groupby("City")
                 .agg(Units_Sold=("Units_Sold", "sum"),
                      Revenue=("Revenue", "sum"),
                      Cost=("Cost", "sum"),
                      Profit=("Profit", "sum"),
                      Margin=("Profit_Margin", "mean"))
                 .sort_values("Profit", ascending=False))
    by_city.to_excel(xl, sheet_name="by_city")

    by_prod = (df.groupby("Confectionary")
                 .agg(Units_Sold=("Units_Sold", "sum"),
                      Revenue=("Revenue", "sum"),
                      Cost=("Cost", "sum"),
                      Profit=("Profit", "sum"),
                      Margin=("Profit_Margin", "mean"))
                 .sort_values("Profit", ascending=False))
    by_prod.to_excel(xl, sheet_name="by_product")

    by_cy = (df.groupby(["City", "Confectionary"])
               .agg(Profit=("Profit", "sum"),
                    Margin=("Profit_Margin", "mean"),
                    Units=("Units_Sold", "sum"))
               .reset_index())
    by_cy.to_excel(xl, sheet_name="city_product", index=False)

    by_year = (df.groupby(["Year", "City"])
                 .agg(Profit=("Profit", "sum"),
                      Revenue=("Revenue", "sum"))
                 .reset_index())
    by_year.to_excel(xl, sheet_name="year_city", index=False)

print(f"Summary tables written to: {SUMMARY_OUT}")
print("\nDone.")
