import { STOPS, UNRANKED } from './colors'

export default function Legend({ scoreType }) {
  const gradient = `linear-gradient(to right, ${
    STOPS.map(([pct, color]) => `${color} ${pct}%`).join(', ')
  })`

  return (
    <div className="legend">
      <strong>{scoreType === 'freq' ? 'Crash frequency' : 'Crash cost'}</strong>
      <div className="bar" style={{ background: gradient }} />
      <div className="bar-labels">
        <span>Lower rate</span>
        <span>Higher rate</span>
      </div>
      <div className="unranked">
        <span className="swatch" style={{ background: UNRANKED }} /> Not ranked
      </div>
      <p>
        {scoreType === 'freq'
          ? 'Crashes per 100 million vehicle-miles, lightly weighted by severity, ranked by percentile among Orange County major roads.'
          : 'Severity-weighted crashes (a fatal crash counts ~540× a property-damage crash) per vehicle-mile traveled, ranked by percentile. Volatile on low-volume roads.'}
      </p>
    </div>
  )
}