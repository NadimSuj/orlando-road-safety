import pandas as pd
import geopandas as gpd
import json

CRASH_CACHE = "data/crashes_raw.json"
SEGMENT_CACHE = "data/segments_raw.geojson"
OUTPUT = "data/orlando_roads.geojson"

YEARS = 5

WEIGHTS_FREQ = {"fatal": 10,  "serious": 5,  "other": 2,  "pdo": 1}
WEIGHTS_COST = {"fatal": 540, "serious": 55, "other": 12, "pdo": 1}


# =====================================================
# 1. LOAD CRASHES AND BUCKET BY SEVERITY
# =====================================================
# Loads crash records, counts by ROADWAYID + INJSEVER, pivots to one row
# per roadway, then collapses INJSEVER codes into four buckets:
#   pdo=1, other=2+3, serious=4, fatal=5

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

with open(SEGMENT_CACHE) as f:
    segment_data = json.load(f)
gdf = gpd.GeoDataFrame.from_features(segment_data['features'], crs="EPSG:4326")

print(f"Segments: {len(gdf)}, unique roadways: {gdf['ROADWAY'].nunique()}")

# =====================================================
# 3. AGGREGATE ATTRIBUTES BY ROADWAY
# =====================================================
# Aggregates segment-level data to one row per ROADWAY using ROADSIDE rules:
#
#   length_mi  = whole + max(L, R)
#   aadt       = length-weighted mean within each side group,
#                then blended: (whole * whole_len + lr * lr_len) / total_len
#   lanes      = same blending method as aadt
#   speed_max  = max across all segments
#   speed_mean = mean across all segments
#   street_name, median_type, func_class = modal value across all segments

# C and O represent undivided (whole-road) segments; L and R are directional
gdf['side_group'] = gdf['ROADSIDE'].map(
    lambda s: 'whole' if s in ('C', 'O') else s
)

# --- length: summed within each side group, then whole + max(L, R) ---
len_by_side = (gdf.groupby(['ROADWAY', 'side_group'])['SEGMENT_LENGTH_MI']
                  .sum()
                  .unstack(fill_value=0))

for col in ['whole', 'L', 'R']:
    if col not in len_by_side.columns:
        len_by_side[col] = 0

length_mi = len_by_side['whole'] + len_by_side[['L', 'R']].max(axis=1)


# --- AADT: length-weighted mean per side group, blended across whole and L+R ---
gdf['aadt_x_len'] = gdf['AADT'] * gdf['SEGMENT_LENGTH_MI']
numerator = gdf.groupby(['ROADWAY','side_group'])['aadt_x_len'].sum()
denominator = gdf.groupby(['ROADWAY','side_group'])['SEGMENT_LENGTH_MI'].sum()

aadt_by_side = (numerator/denominator).unstack(fill_value=0)

for col in ['whole', 'L', 'R']:
    if col not in aadt_by_side.columns:
        aadt_by_side[col]=0

whole_len = len_by_side['whole']
lr_len    = len_by_side[['L', 'R']].max(axis=1)

lr_aadt = aadt_by_side['L'] + aadt_by_side['R']
aadt = (aadt_by_side['whole'] * whole_len + lr_aadt * lr_len) / (whole_len + lr_len)

# --- lanes: length-weighted within each side group, blended across whole and L+R ---
gdf['lanes_x_len'] = gdf['NUMBER_OF_THROUGH_LANES'] * gdf['SEGMENT_LENGTH_MI']
lanes_by_side = (
    gdf.groupby(['ROADWAY', 'side_group'])['lanes_x_len'].sum()
    / gdf.groupby(['ROADWAY', 'side_group'])['SEGMENT_LENGTH_MI'].sum()
).unstack(fill_value=0)

for col in ['whole', 'L', 'R']:
    if col not in lanes_by_side.columns:
        lanes_by_side[col] = 0

lr_lanes = lanes_by_side['L'] + lanes_by_side['R']
lanes = ((lanes_by_side['whole'] * whole_len + lr_lanes * lr_len)
         / (whole_len + lr_len)).round(1)

# --- speed: max and mean across all segments ---
speed_max  = gdf.groupby('ROADWAY')['SPEED_LIMIT'].max()
speed_mean = gdf.groupby('ROADWAY')['SPEED_LIMIT'].mean()

# --- descriptive fields: modal value across all segments ---
def most_common(s):
    m = s.mode()
    return m.iloc[0] if not m.empty else None

desc_fields = gdf.groupby('ROADWAY')[
    ['STREET_NAME', 'MEDIAN_TYPE_ID', 'FLARIS_FUNCTIONAL_CLASS_CD']
].agg(most_common)

# --- assemble into one DataFrame indexed by ROADWAY ---
attrs = pd.DataFrame({
    'length_mi': length_mi,
    'aadt':      aadt,
    'lanes':     lanes,
    'speed_max': speed_max,
    'speed_mean': speed_mean,
})

attrs = attrs.join(desc_fields)

print(attrs.head(10))
print(f"Roadways with attributes: {len(attrs)}")
print(f"\nI-4 check:\n{attrs.loc['75280000']}")


# =====================================================
# 4. DISSOLVE GEOMETRY
# =====================================================
# Dissolves segments by ROADWAY into a single geometry per road;
# attributes come from step 3, not from this dissolve.

geom = gdf[['ROADWAY', 'geometry']].dissolve(by='ROADWAY')

print(f"Dissolved to {len(geom)} geometries")
print(geom.head(3))

# =====================================================
# 5. JOIN EVERYTHING
# =====================================================
# Joins step-3 attributes and step-1 crash counts onto the dissolved geometry;
# roads with no crashes get zero-filled counts.

roads = geom.join(attrs)
roads = roads.join(crashes, how='left')

crash_cols = ['pdo', 'other', 'serious', 'fatal', 'total']
roads[crash_cols] = roads[crash_cols].fillna(0)

print(f"Final roadways: {len(roads)}")
print(f"Roads with zero crashes: {(roads['total'] == 0).sum()}")
print(f"Crashes matched: {roads['total'].sum():.0f} of 140584")

# =====================================================
# 6. COMPUTE SCORES
# =====================================================
# Applies frequency and cost weight tables to crash counts, then normalizes
# by vehicle-miles traveled: score = (W * 100_000_000) / (aadt * 365 * YEARS * length_mi)
def weighted(w):
    return (roads['fatal']   * w['fatal']
          + roads['serious'] * w['serious']
          + roads['other']   * w['other']
          + roads['pdo']     * w['pdo'])

roads['w_freq'] = weighted(WEIGHTS_FREQ)
roads['w_cost'] = weighted(WEIGHTS_COST)

# vehicle-miles traveled over the study period
vmt = roads['aadt'] * 365 * YEARS * roads['length_mi']

roads['score_freq'] = (roads['w_freq'] * 100_000_000 / vmt).where(vmt > 0)
roads['score_cost'] = (roads['w_cost'] * 100_000_000 / vmt).where(vmt > 0)

print(roads[['score_freq', 'score_cost']].describe())
print(f"\nRoads with no score (zero VMT): {roads['score_freq'].isna().sum()}")

# =====================================================
# 7. VALIDATE AND WRITE
# =====================================================

MIN_LENGTH_MI = 0.1

cov = pd.read_csv("data/coverage.csv", dtype={'ROADWAY': str}).set_index('ROADWAY')
roads = roads.join(cov[['excluded_share']])
roads['excluded_share'] = roads['excluded_share'].fillna(0)

MAX_EXCLUDED_SHARE = 0.2

roads['rankable'] = (roads['STREET_NAME'].notna()
                     & (roads['length_mi'] >= MIN_LENGTH_MI)
                     & (roads['excluded_share'] <= MAX_EXCLUDED_SHARE))

ranked = roads[roads['rankable']]
print(f"\nRankable roads: {len(ranked)} of {len(roads)}")

# named roads >= 0.1 mi that have some excluded segment length
partial = roads[(roads['excluded_share'] > 0)
                & roads['STREET_NAME'].notna()
                & (roads['length_mi'] >= MIN_LENGTH_MI)]
print(f"\nNamed roads >= {MIN_LENGTH_MI} mi with excluded length: {len(partial)}")
print(partial[['STREET_NAME', 'length_mi', 'excluded_share', 'total', 'score_freq']])
cols = ['STREET_NAME', 'length_mi', 'aadt', 'lanes', 'speed_max', 'total', 'fatal']

print("\n--- Top 10 by frequency-weighted score ---")
print(ranked.nlargest(10, 'score_freq')[cols + ['score_freq']])

print("\n--- Top 10 by cost-weighted score ---")
print(ranked.nlargest(10, 'score_cost')[cols + ['score_cost']])

roads.to_file(OUTPUT, driver='GeoJSON')
print(f"\nWrote {len(roads)} roadways to {OUTPUT}")
