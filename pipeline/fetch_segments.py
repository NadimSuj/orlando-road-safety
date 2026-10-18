import requests
import pandas as pd
import geopandas as gpd
import os
import json

CACHE_FILE = "data/segments_raw.geojson"

SEGMENTS_URL = "https://gis.fdot.gov/arcgis/rest/services/sso/ssogis_flaris/FeatureServer/100850/query"
PAGE_SIZE = 5000
WHERE = ("DOT_CNTY_CD = '75' AND FLARIS_FUNCTIONAL_CLASS_CD <= 4.0 "
         "AND FLARIS_FUNCTIONAL_CLASS_CD <> 3.1")

FIELDS = ("ROADWAY,STREET_NAME,STATE_ROAD_NUMBER,US_ROAD_NUMBER,"
          "SEGMENT_LENGTH_MI,AADT,AADT_YEAR,NUMBER_OF_THROUGH_LANES,"
          "MEDIAN_TYPE_ID,SPEED_LIMIT,ONE_TWO_WAY_OPERATIONS,"
          "CONTROLLED_ACCESS_IND,FLARIS_FUNCTIONAL_CLASS_CD,"
          "URBAN_RURAL_IND,COUNTY_NAME,ROADSIDE")


if os.path.exists(CACHE_FILE):
    print(f"Loading from cache: {CACHE_FILE}")
    with open(CACHE_FILE) as f:
        data = json.load(f)
    all_features = data['features']
    print(f"Loaded {len(all_features)} segments from cache")
else:
    all_features = []
    offset = 0

    while True:
        params = {
            "where": WHERE,
            "outFields": FIELDS,
            "orderByFields": "OBJECTID",
            "returnGeometry": "true",
            "outSR": 4326,
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "geojson",
        }

        response = requests.get(SEGMENTS_URL, params=params)
        data = response.json()

        if "error" in data:
            print("API error:", data["error"])
            break

        features = data["features"]
        all_features.extend(features)

        first_roadway = features[0]["properties"]["ROADWAY"] if features else "none"
        print(f"offset={offset}, got {len(features)}, total {len(all_features)}, first={first_roadway}")

        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"Fetched {len(all_features)} segments")
    geojson_out = {"type": "FeatureCollection", "features": all_features}
    with open(CACHE_FILE, "w") as f:
        json.dump(geojson_out, f)
    print(f"Saved to {CACHE_FILE}")


gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")

print(f"Segments: {len(gdf)}")
print(f"Unique roadways: {gdf['ROADWAY'].nunique()}")
print(gdf[['ROADWAY', 'STREET_NAME', 'SEGMENT_LENGTH_MI', 'AADT',
           'NUMBER_OF_THROUGH_LANES', 'SPEED_LIMIT']].head(10))
print(gdf.geometry.head(3))

# --- diagnostic: check for directional duplication ---
i4 = gdf[gdf['ROADWAY'] == '75280000']
print(f"\nI-4 segments: {len(i4)}")
print(f"Summed length: {i4['SEGMENT_LENGTH_MI'].sum():.1f} mi")
print(f"ROADSIDE values:\n{i4['ROADSIDE'].value_counts()}")
print(f"AADT range: {i4['AADT'].min():.0f} to {i4['AADT'].max():.0f}")

print(f"\nROADSIDE across all segments:\n{gdf['ROADSIDE'].value_counts()}")

sides = gdf.groupby('ROADWAY')['ROADSIDE'].apply(lambda s: ''.join(sorted(set(s))))
print(f"\nROADSIDE patterns per roadway:\n{sides.value_counts()}")

# reproject to a projected CRS so lengths come out in meters
gdf_proj = gdf.to_crs("EPSG:6440")   # Florida East, NAD83(2011), meters

dissolved = gdf_proj.dissolve(by='ROADWAY')
dissolved['true_length_mi'] = dissolved.geometry.length / 1609.34

print(dissolved.loc['75280000', 'true_length_mi'])

by_side = gdf.groupby(['ROADWAY', 'ROADSIDE'])['SEGMENT_LENGTH_MI'].sum().unstack(fill_value=0)

for col in ['C', 'O', 'L', 'R']:
    if col not in by_side.columns:
        by_side[col] = 0

by_side['true_length_mi'] = by_side['C'] + by_side['O'] + by_side[['L', 'R']].max(axis=1)

print(by_side.loc['75280000'])
print(f"\nI-4 true length: {by_side.loc['75280000', 'true_length_mi']:.1f} mi")
print(by_side['true_length_mi'].describe())

# find Colonial / SR 50
colonial = gdf[gdf['STREET_NAME'].str.contains('COLONIAL', na=False)]
print(colonial[['ROADWAY','STREET_NAME','ROADSIDE','AADT','NUMBER_OF_THROUGH_LANES']].head(20))
print(f"\nRoadway IDs: {colonial['ROADWAY'].unique()}")