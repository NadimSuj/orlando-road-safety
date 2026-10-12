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
          "URBAN_RURAL_IND,COUNTY_NAME")


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