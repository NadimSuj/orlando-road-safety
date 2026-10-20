import json
import geopandas as gpd

with open("data/segments_raw.geojson") as f:
    gdf = gpd.GeoDataFrame.from_features(json.load(f)["features"])

for rid in ["75250000", "75270000", "75035000"]:
    sub = gdf[gdf["ROADWAY"] == rid].copy()
    sub["aadt_x_len"] = sub["AADT"] * sub["SEGMENT_LENGTH_MI"]

    summary = sub.groupby("ROADSIDE").agg(
        segments=("AADT", "size"),
        miles=("SEGMENT_LENGTH_MI", "sum"),
        aadt_x_len=("aadt_x_len", "sum"),
        lanes_max=("NUMBER_OF_THROUGH_LANES", "max"),
    )
    summary["aadt_wmean"] = summary["aadt_x_len"] / summary["miles"]

    print(f"\n{rid}  {sub['STREET_NAME'].mode().iloc[0]}")
    print(summary.drop(columns="aadt_x_len"))