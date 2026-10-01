import requests

CRASH_URL = "https://gis.fdot.gov/arcgis/rest/services/Crashes_All/FeatureServer/0/query"

params = {
    "where": "COUNTY_TXT = 'ORANGE' AND CALENDAR_YEAR >= 2014 AND CALENDAR_YEAR <= 2018 AND INJSEVER IN ('1','2','3','4','5')",
    "groupByFieldsForStatistics": "ROADWAYID,INJSEVER", 
    "outStatistics": '[{"statisticType":"count","onStatisticField":"XID","outStatisticFieldName":"n"}]', #count the crashes, and call that count n. XID is the crash ID, so counting XID is counting the crashes.
    #groupByFieldForStatistics and outStatistics work togeher to group the data by the fields specified in groupByFieldsForStatistics, and then apply the statistics specified in outStatistics to each group. In this case, we are grouping by ROADWAYID and INJSEVER, and counting the number of crashes (XID) for each group. 
    #Basically:group all 140,584 crashes into buckets where every crash in a bucket shares the same roadway and the same severity code. Then count how many crashes are in each bucket.
    "returnGeometry": "false",
    "f": "json",
}

response = requests.get(CRASH_URL, params=params)
data = response.json()

print(f"Rows returned: {len(data['features'])}")
print(data['features'][:3])