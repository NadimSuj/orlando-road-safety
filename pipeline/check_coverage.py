import json
import requests
import pandas as pd
import geopandas as gpd

SEGMENT_CACHE = "data/segments_raw.geojson"
SEGMENTS_URL = "https://gis.fdot.gov/arcgis/rest/services/sso/ssogis_flaris/FeatureServer/100850/query"

with open(SEGMENT_CACHE) as f:
    gdf = gpd.GeoDataFrame.from_features(json.load(f)['features'])

# raw length we kept, per roadway (same counting basis as the query below)
kept = gdf.groupby('ROADWAY')['SEGMENT_LENGTH_MI'].sum()

ids = ",".join(f"'{r}'" for r in kept.index)
params = {
    "where": (f"ROADWAY IN ({ids}) AND "
              "(FLARIS_FUNCTIONAL_CLASS_CD > 4.0 OR FLARIS_FUNCTIONAL_CLASS_CD = 3.1)"),
    "groupByFieldsForStatistics": "ROADWAY",
    "outStatistics": '[{"statisticType":"sum","onStatisticField":"SEGMENT_LENGTH_MI","outStatisticFieldName":"excluded_mi"}]',
    "returnGeometry": "false",
    "f": "json",
}

data = requests.post(SEGMENTS_URL, data=params).json()
if "error" in data:
    raise SystemExit(f"API error: {data['error']}")

rows = [f['attributes'] for f in data['features']]
excluded = pd.DataFrame(rows).set_index('ROADWAY')['excluded_mi'] if rows else pd.Series(dtype=float)
print(f"Rows returned: {len(rows)}")

cov = pd.DataFrame({'kept_mi': kept, 'excluded_mi': excluded}).fillna(0)
cov['excluded_share'] = cov['excluded_mi'] / (cov['kept_mi'] + cov['excluded_mi'])

print(f"Roadways with any excluded length: {(cov['excluded_mi'] > 0).sum()} of {len(cov)}")
print(f"Roadways with >20% excluded:       {(cov['excluded_share'] > 0.2).sum()}")
print(cov.sort_values('excluded_share', ascending=False).head(15))

cov.to_csv("data/coverage.csv")

#check_coverage.py asked FDOT, for all 220 roadways, how much length each had in the excluded classes. 
# Result: 28 roadways affected, and every one shown was a tiny fragment.