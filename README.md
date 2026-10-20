# Orlando Road Safety Map

An analysis of how road design relates to crash outcomes on Orange County, Florida's arterial and highway network. It combines five years of Florida DOT crash records with FDOT's roadway inventory to score each major road by crashes per vehicle-mile traveled, and it is the data foundation for an interactive map aimed at students learning urban design.

**Status:** data pipeline complete. Interactive map in progress.

## Key numbers

| | |
|---|---|
| Crashes analyzed (Orange County, 2014–2018, known severity) | 140,584 |
| Roadways mapped (interstates, expressways, arterials) | 220 |
| Roadways with a reliable, rankable score | 191 |
| Share of all crashes occurring on these 220 roadways | 73% (102,251) |
| Mapped roadways with zero crashes | 21 |

A small number of high-capacity roads carry nearly three-quarters of the county's crashes.

## Data sources

All data comes from the Florida Department of Transportation (FDOT), queried through its public ArcGIS REST services.

| Dataset | Service | Used for |
|---|---|---|
| Crash records | `Crashes_All/FeatureServer/0` | Crash counts and severity per roadway |
| FLARIS Roadway Segments | `sso/ssogis_flaris/FeatureServer/100850` | Road geometry, length, traffic volume (AADT), lanes, speed limit, median type |

FLARIS (Florida All Roadways, Intersections and Streets) is FDOT's statewide road inventory, maintained by its State Safety Office.

**Study window: 2014–2018.** The per-year crash layers in `sso/ssogis` turned out to cover only a subset of crashes (state highways). `Crashes_All` is the complete dataset, but it ends in 2019, and 2019 is only partially populated. 2014–2018 is the most recent five-year window with complete data.

## Pipeline

Run the scripts in this order. Each fetch script caches its results in `data/`, so later steps never hit the API.

| Step | Script | What it does | Output |
|---|---|---|---|
| 1 | `pipeline/fetch_crashes.py` | Pages through all Orange County crashes for 2014–2018 (1,000 per request) | `data/crashes_raw.json` |
| 2 | `pipeline/fetch_segments.py` | Pages through FLARIS road segments for the selected road classes, with geometry (5,000 per request) | `data/segments_raw.geojson` |
| 3 | `pipeline/check_coverage.py` | Measures, for each roadway, how much of its length falls in road classes the filter excluded | `data/coverage.csv` |
| 4 | `pipeline/build_dataset.py` | Aggregates segments into roadways, joins crash counts, computes safety scores, applies rankability rules | `data/orlando_roads.geojson` |
| 5 | `pipeline/check_vintage.py` | Validation: compares FLARIS traffic, lanes, and speed against values recorded at the time of each crash | `data/vintage_check.csv` |

`pipeline/inspect_roads.py` is an ad-hoc diagnostic that breaks a few roadways down by road side.

## Methodology

### Crash severity

Each crash carries an injury severity code (`INJSEVER`). Codes are grouped into four buckets:

| Bucket | Codes | Meaning |
|---|---|---|
| Fatal | 5 | Death within 30 days |
| Serious injury | 4 | Incapacitating injury |
| Other injury | 2, 3 | Possible or non-incapacitating injury |
| Property damage only | 1 | No injury |

Two codes are excluded:

- **Code 0 (3,410 crashes):** severity was not recorded. A crash of unknown severity can't be weighted.
- **Code 6 (33 crashes):** a death not caused by the traffic event, such as a medical emergency. Road design did not cause it.

### Safety scores

Each roadway gets two scores, because "dangerous" depends on what you choose to measure.

| Scheme | Fatal | Serious | Other injury | Property only | Answers |
|---|---|---|---|---|---|
| Frequency-weighted | 10 | 5 | 2 | 1 | Which roads produce crashes persistently? |
| Cost-weighted (EPDO) | 540 | 55 | 12 | 1 | Where does the most human harm occur? |

The cost-weighted scale follows FHWA crash-cost studies, in which a fatal crash costs roughly 540 times a property-damage crash. It is volatile: a single fatal crash on a quiet road can dominate its score.

Both are normalized by exposure, as crashes per 100 million vehicle-miles traveled:

```
W     = weighted crash total (crash counts × weights)
VMT   = AADT × 365 × years × length_mi
score = W × 100,000,000 / VMT
```

Normalizing means a road isn't penalized simply for being long or busy. What remains reflects the road itself.

### Divided roads

FLARIS records a `ROADSIDE` code for every segment:

- **L / R:** the two carriageways of a divided road, each stored as its own line
- **C:** an undivided road, stored as one centerline
- **O:** not documented; it behaves like a single line, so it is treated like C

The two sides of a divided road need different handling depending on the attribute:

| Attribute | Rule | Reason |
|---|---|---|
| Length | `C + max(L, R)` | L and R trace the same pavement, so count it once |
| AADT | Length-weighted blend of the C stretch and the divided stretch (L + R) | Each direction carries different vehicles, so L + R is the divided stretch's total; blending by length makes `AADT × length` equal the road's true daily VMT |
| Lanes | Same length-weighted blend | Describes the road's typical cross-section |

**Verification:**

- I-4 summed to 49.3 miles across all segments. The length rule gives 24.6 miles, which matches its actual length through the county.
- On Colonial Dr, a directional segment reported 16,500 AADT and a nearby undivided segment reported 33,000, confirming that L and R values are per-direction.

An earlier rule ("use the undivided value if one exists, otherwise L + R") was replaced after validation showed it failed on mixed roads. On S Kirkman Rd, it applied a 600-foot undivided stub's traffic (27,500) to the whole 7-mile road, which actually carries about 46,400. See **Validation**.

### Road filter

FLARIS assigns each segment a **functional class**, its role in the road network. Only the major classes are kept:

| Kept | Excluded |
|---|---|
| 1.0 Interstates | 3.1 Ramps |
| 2.0 Freeways and expressways | 5–6 Collectors |
| 3.0 Principal arterials | 7.x Local streets |
| 4.0 Minor arterials | 8.x Intersection internals |

This keeps the analysis on arterials and highways, and reduces 99,136 Orange County segments to 28,639, which aggregate into 220 roadways. Ramps are excluded because they are short connectors between roads, with different design questions (merging, curvature) than the corridors this project studies.

### Rankability

A roadway is ranked only if it meets all three rules:

1. **It has a street name.** Unnamed records are typically interchange fragments.
2. **It is at least 0.1 miles long.** Very short records produce unstable rates.
3. **At most 20% of its length falls in excluded classes.** Crashes are grouped by roadway ID across the whole roadway, so if most of a roadway was filtered out, its crash count and its length would describe different stretches of road.

| Step | Roadways remaining |
|---|---|
| All roadways | 220 |
| Has a street name | 201 |
| At least 0.1 miles | 195 |
| Excluded share ≤ 20% | **191** |

Non-rankable roads remain in the output with `rankable = false`, so the map can show them as "insufficient data" rather than hiding them.

## Validation

### Coverage check

Before the rankability rules, the top of the rankings was dominated by unnamed slivers with scores in the tens of thousands. Investigation showed these roadways were almost entirely ramp: roadway `75002026` is 0.4 miles long, 97% of it ramp, and all 40 of its crashes were being divided by the 0.012 miles that survived the filter. Across all 220 roadways, 28 have some excluded length. Most are fragments; of the 10 that are named and at least 0.1 miles long, 4 exceed the 20% threshold and are excluded, and the rest are long corridors where only a few percent of length is excluded.

### Traffic and design vintage check

FLARIS describes roads as they are today (all AADT values are from 2021), while the crashes are from 2014–2018. Every crash record also carries the road's traffic, lanes, and speed limit at the time of the crash, which provides an independent check.

- Crash-era traffic is available for 52 roads (state roads only). The median ratio of 2021 FLARIS AADT to crash-era AADT is **0.94**: the two agree to within about 6%.
- This check caught the divided-road aggregation bug described above. Before the fix, Silver Star Rd's traffic was understated by about 40%, which made it the #1 road on both rankings. After the fix it ranks #4 (frequency) and #5 (cost).
- 14 roads remain flagged for differences in traffic, lanes, or speed. Most are explained by **crash-weighting**: crashes cluster on a road's busiest stretches, so crash-era values describe those stretches rather than the road as a whole. A few (such as S Apopka Vineland Rd and Leevista Blvd) may reflect roads widened after 2018.

## Preliminary results

**Top 5, frequency-weighted:** N Orange Ave, Curry Ford Rd, Rio Grande Ave S, Silver Star Rd, Alafaya Trl N.

**Top 5, cost-weighted:** E Rollins St, International Dr S, Rio Grande Ave S, Curry Ford Rd, Silver Star Rd.

The lists differ, which is the point of computing both. N Orange Ave tops the frequency list with 410 crashes and no fatalities. E Rollins St tops the cost list with only 12 crashes, one of them fatal, which illustrates how volatile the cost-weighted score is on low-volume roads.

## Known limitations

- **Data vintage.** Crashes are from 2014–2018, the most recent complete window available from the public `Crashes_All` service. Traffic volumes are from 2021, and road geometry and design attributes reflect current conditions. Roads rebuilt after 2018 are paired with designs they didn't have during the crash window.
- **Small samples.** Roads with few crashes have unreliable rates. A single fatal crash can move a low-volume road to the top of the cost-weighted ranking.
- **Ramp crashes on long corridors.** Because crashes are grouped by roadway ID, a few long corridors include some crashes from their ramps, inflating their scores by up to about 7% (for example, W Maitland Blvd and Lee Rd).
- **Local streets are not mapped.** 27% of crashes (38,333) occurred on roads outside the selected classes.
- **Cross-county records.** 69 crashes recorded in Orange County carry roadway IDs from other counties and are dropped by the join.
- **Undocumented code.** The meaning of `ROADSIDE = O` isn't documented; it is treated as a single-line representation based on its behavior.

## Running it

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install requests pandas geopandas

python pipeline/fetch_crashes.py
python pipeline/fetch_segments.py
python pipeline/check_coverage.py
python pipeline/build_dataset.py
python pipeline/check_vintage.py
```

The cached files in `data/` are committed, so steps 1–3 can be skipped to rebuild from the saved data.

## Tech

Python 3.12, requests, pandas, GeoPandas. ArcGIS REST API.

## Data notice

Crash and roadway data are provided by the FDOT State Safety Office. This project is an independent educational analysis and is not affiliated with or endorsed by FDOT. FDOT notes that its safety data is compiled for identifying and planning safety improvements and is subject to 23 U.S.C. §409.
