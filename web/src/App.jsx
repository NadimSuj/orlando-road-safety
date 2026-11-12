import { useState } from 'react'
import RoadMap from './RoadMap'
import ProfilePanel from './ProfilePanel'

export default function App() {
  const [scoreType, setScoreType] = useState('freq')   // start on frequency
  const [selected, setSelected] = useState(null)       // no road selected yet

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
      <RoadMap scoreType={scoreType} onSelect={setSelected} />
      {selected && (
        <ProfilePanel
          road={selected}
          scoreType={scoreType}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  )
}