export default function ProfilePanel({ road, scoreType, onClose }) {
  const pct = road[`score_${scoreType}_pct`]

  return (
    <div className="panel">
      <button className="close" onClick={onClose}>×</button>
      <h2>{road.STREET_NAME ?? 'Unnamed road segment'}</h2>

      {road.rankable ? (
        <p>
          {scoreType === 'freq' ? 'Crash frequency' : 'Crash cost'} percentile:{' '}
          {Math.round(pct)} / 100
        </p>
      ) : (
        <p>Not ranked: too short or missing data to score fairly.</p>
      )}

      <p>{road.total.toLocaleString()} crashes, {road.fatal} fatal (2014–2018)</p>
    </div>
  )
}