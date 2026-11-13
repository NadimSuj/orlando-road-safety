const ROAD_TYPES = {
  1: 'Interstate',
  2: 'Freeway / expressway',
  3: 'Principal arterial',
  4: 'Minor arterial',
  5: 'Major collector',
  6: 'Minor collector',
  7: 'Local road',
}

const YEARS = 5

// round and add commas: 12131.7 → "12,132"
const fmt = (x) => Math.round(x).toLocaleString()

function Stat({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  )
}

export default function ProfilePanel({ road, scoreType, onClose }) {
  const pct = road[`score_${scoreType}_pct`]
  const score = road[`score_${scoreType}`]
  const modeName = scoreType === 'freq' ? 'Crash frequency' : 'Crash cost'

  return (
    <div className="panel">
      <button className="close" onClick={onClose}>×</button>
      <h2>{road.STREET_NAME ?? 'Unnamed road segment'}</h2>

      {road.rankable ? (
        <p className="headline">
          {modeName} percentile: <strong>{Math.round(pct)} / 100</strong>
          <br />
          Score: {fmt(score)} weighted crashes per 100M vehicle-miles
        </p>
      ) : (
        <p className="headline">Not ranked: too short or missing data to score fairly.</p>
      )}

      <h3>The road</h3>
      <dl>
        <Stat label="Type" value={ROAD_TYPES[road.FLARIS_FUNCTIONAL_CLASS_CD] ?? 'Unknown'} />
        <Stat label="Length" value={`${road.length_mi.toFixed(1)} mi`} />
        <Stat label="Daily traffic (2021)" value={`${fmt(road.aadt)} vehicles`} />
        <Stat label="Lanes (average)" value={road.lanes} />
        <Stat label="Speed limit" value={`up to ${road.speed_max} mph`} />
      </dl>

      <h3>Crashes, 2014–2018</h3>
      <dl>
        <Stat label="Total" value={`${fmt(road.total)} (about ${fmt(road.total / YEARS)}/year)`} />
        <Stat label="Fatal" value={fmt(road.fatal)} />
        <Stat label="Serious injury" value={fmt(road.serious)} />
        <Stat label="Minor injury" value={fmt(road.other)} />
        <Stat label="Property damage only" value={fmt(road.pdo)} />
      </dl>
    </div>
  )
}