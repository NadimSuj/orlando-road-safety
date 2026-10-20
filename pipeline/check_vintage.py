import json
import pandas as pd
import geopandas as gpd

with open("data/crashes_raw.json") as f:
    crashes = pd.DataFrame(json.load(f))

roads = gpd.read_file("data/orlando_roads.geojson")
roads = roads.set_index("ROADWAY")

# crash-era attributes: the typical value recorded across each road's crashes
era = (crashes[crashes["ROADWAYID"].isin(roads.index)]
       .groupby("ROADWAYID")
       .agg(era_aadt=("AVERAGE_DAILY_TRAFFIC", "median"),
            era_lanes=("CNTOFLANES", "median"),
            era_speed=("SPEED_LIMIT", "median"),
            n_crashes=("INJSEVER", "size")))

cmp = roads[["STREET_NAME", "rankable", "aadt", "lanes", "speed_mean"]].join(era, how="inner")

# only rankable roads with enough crashes for the median to mean something
cmp = cmp[cmp["rankable"] & (cmp["n_crashes"] >= 20)].copy()

cmp["aadt_ratio"] = cmp["aadt"] / cmp["era_aadt"]       # 2021 FLARIS vs crash era
cmp["lane_diff"]  = cmp["lanes"] - cmp["era_lanes"]
cmp["speed_diff"] = cmp["speed_mean"] - cmp["era_speed"]

print(f"Roads compared: {len(cmp)}")
print("\nAADT ratio (2021 / crash era):")
print(cmp["aadt_ratio"].describe())

flagged = cmp[(cmp["lane_diff"].abs() >= 2)
              | (cmp["speed_diff"].abs() >= 10)
              | (cmp["aadt_ratio"] < 0.67)
              | (cmp["aadt_ratio"] > 1.5)]

print(f"\nFlagged roads: {len(flagged)}")
print(flagged.sort_values("n_crashes", ascending=False)[
    ["STREET_NAME", "n_crashes", "era_aadt", "aadt", "aadt_ratio",
     "era_lanes", "lanes", "era_speed", "speed_mean"]
].head(20))

cmp.to_csv("data/vintage_check.csv")