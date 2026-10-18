import pandas as pd
import geopandas as gpd
import json
import requests
import os

CRASH_CACHE = "data/crashes_raw.json"
SEGMENT_CACHE = "data/segments_raw.geojson"
OUTPUT = "data/orlando_roads.geojson"

YEARS = 5

WEIGHTS_FREQ = {"fatal": 10,  "serious": 5,  "other": 2,  "pdo": 1}
WEIGHTS_COST = {"fatal": 540, "serious": 55, "other": 12, "pdo": 1}


# =====================================================
# 1. LOAD CRASHES AND BUCKET BY SEVERITY
# =====================================================
# load CRASH_CACHE json into a DataFrame
# groupby ROADWAYID + INJSEVER, count
# pivot so each roadway is one row with severity columns
# collapse into four buckets: pdo, other, serious, fatal
# (this is the code you already wrote in fetch_crashes.py)

with open(CRASH_CACHE) as f:
    crash_rows = json.load(f)

df = pd.DataFrame(crash_rows)
counts = df.groupby(['ROADWAYID', 'INJSEVER']).size().reset_index(name='n')
pivot = counts.pivot(index='ROADWAYID', columns='INJSEVER', values='n').fillna(0)

crashes = pd.DataFrame({
    'pdo':     pivot['1'],
    'other':   pivot['2'] + pivot['3'],
    'serious': pivot['4'],
    'fatal':   pivot['5'],
})
crashes['total'] = crashes.sum(axis=1)

print(f"Crash roadways: {len(crashes)}, total crashes: {crashes['total'].sum():.0f}")

# =====================================================
# 2. LOAD SEGMENTS
# =====================================================
# load SEGMENT_CACHE into a GeoDataFrame

with open(SEGMENT_CACHE) as f:
    segment_data = json.load(f)
gdf = gpd.GeoDataFrame.from_features(segment_data['features'], crs="EPSG:4326")

print(f"Segments: {len(gdf)}, unique roadways: {gdf['ROADWAY'].nunique()}")

# =====================================================
# 3. AGGREGATE ATTRIBUTES BY ROADWAY
# =====================================================
# For each roadway you need, using the ROADSIDE rules:
#
#   true_length_mi  = C + O + max(L, R)
#   true_aadt       = C + O + (L + R)        length-weighted within each side
#   lanes_total     = C + O + (L + R)
#   speed_max       = plain max across all segments
#   speed_mean      = plain mean across all segments
#   street_name     = most common value
#   median_type     = most common value
#   func_class      = most common value
#
# Build this as a DataFrame indexed by ROADWAY.

# Treat C and O as "whole-road" representations, L and R as directional
gdf['side_group'] = gdf['ROADSIDE'].map(
    lambda s: 'whole' if s in ('C', 'O') else s
)

# --- length: sum within each side group ---
len_by_side = (gdf.groupby(['ROADWAY', 'side_group'])['SEGMENT_LENGTH_MI']
                  .sum()
                  .unstack(fill_value=0))

for col in ['whole', 'L', 'R']:
    if col not in len_by_side.columns:
        len_by_side[col] = 0

length_mi = len_by_side['whole'] + len_by_side[['L', 'R']].max(axis=1)


# --- AADT: length-weighted mean within each side group, then combine ---
# TODO: for each (ROADWAY, side_group), compute sum(AADT * length) / sum(length)
# then: aadt = whole + L + R


# --- lanes: same combination rule as AADT ---
# TODO


# --- speed: plain max and mean across all segments of the roadway ---
# TODO


# --- descriptive fields: most common value per roadway ---
# TODO: street_name, median_type, func_class


# --- assemble into one DataFrame indexed by ROADWAY ---
attrs = pd.DataFrame({
    'length_mi': length_mi,
    # ... the rest
})

print(attrs.head(10))
print(f"Roadways with attributes: {len(attrs)}")
print(f"\nI-4 check:\n{attrs.loc['75280000']}")


# =====================================================
# 4. DISSOLVE GEOMETRY
# =====================================================
# dissolve segments by ROADWAY to get one geometry per road
# keep only the geometry column — attributes come from step 3


# =====================================================
# 5. JOIN EVERYTHING
# =====================================================
# start from the dissolved geometry (this is your base)
# attach the step-3 attributes
# left join the step-1 crash counts
# fill missing crash counts with 0


# =====================================================
# 6. COMPUTE SCORES
# =====================================================
# W_freq and W_cost from the weight tables
# score = (W * 100_000_000) / (aadt * 365 * YEARS * length)
# guard against division by zero


# =====================================================
# 7. VALIDATE AND WRITE
# =====================================================
# print row count, crash total, score ranges
# print the top 10 roads by each score
# write to OUTPUT as GeoJSON