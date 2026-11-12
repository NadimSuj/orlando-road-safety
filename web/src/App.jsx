import { useState } from 'react'
import RoadMap from './RoadMap'

export default function App() {
  const [scoreType, setScoreType] = useState('freq')   // start on frequency

  return (
    <>
      <div className="toggle">
        <button
          className={scoreType === 'freq' ? 'active' : ''}
          onClick={() => setScoreType('freq')}
        >
          Crash frequency
        </button>
        <button
          className={scoreType === 'cost' ? 'active' : ''}
          onClick={() => setScoreType('cost')}
        >
          Crash cost
        </button>
      </div>
      <RoadMap scoreType={scoreType} />
    </>
  )
}