import requests
import pandas as pd
import os
import json

CACHE_FILE = "data/crashes_raw.json"

CRASH_URL = "https://gis.fdot.gov/arcgis/rest/services/Crashes_All/FeatureServer/0/query"
PAGE_SIZE = 1000
WHERE = ("COUNTY_TXT = 'ORANGE' AND CALENDAR_YEAR >= 2014 AND CALENDAR_YEAR <= 2018 "
         "AND INJSEVER IN ('1','2','3','4','5')")

if os.path.exists(CACHE_FILE):
    print(f"Loading from cache: {CACHE_FILE}")
    with open(CACHE_FILE) as f:
        all_rows = json.load(f)
    print(f"Loaded {len(all_rows)} records from cache")
else:
    all_rows = []
    offset = 0

    while True:
        params = {
            "where": WHERE,
            "outFields": "ROADWAYID,INJSEVER",
            "orderByFields": "OBJECTID",
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "f": "json",
        }

        response = requests.get(CRASH_URL, params=params)
        data = response.json()

        if "error" in data:
            print("API error:", data["error"])
            break

        features = data["features"]
        all_rows.extend(f["attributes"] for f in features)

        print(f"offset={offset}, got {len(features)}, total {len(all_rows)}")

        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    print(f"Fetched {len(all_rows)} crash records")
    with open(CACHE_FILE, "w") as f:
        json.dump(all_rows, f)
    print(f"Saved to {CACHE_FILE}")


print(f"Working with {len(all_rows)} crash records")

df = pd.DataFrame(all_rows)
print(df.head())
print(df['ROADWAYID'].str[:2].value_counts().head())

counts = df.groupby(['ROADWAYID', 'INJSEVER']).size().reset_index(name='n')
print(counts.head(10))
print(f"Unique roadway-severity combinations: {len(counts)}")

pivot = counts.pivot(index='ROADWAYID', columns='INJSEVER', values='n').fillna(0)
print(pivot.head())

roads = pd.DataFrame({
    'pdo':     pivot['1'],
    'other':   pivot['2'] + pivot['3'],
    'serious': pivot['4'],
    'fatal':   pivot['5'],
})
roads['total'] = roads.sum(axis=1)
print(roads.head(10))
print(f"Roadways: {len(roads)}")
print(f"Total crashes: {roads['total'].sum()}")