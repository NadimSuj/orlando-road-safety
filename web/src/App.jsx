import { useState } from 'react'
import RoadMap from './RoadMap'
import ProfilePanel from './ProfilePanel'
import Legend from './Legend'
import IntroModal from './IntroModal'

export default function App() {
  const [scoreType, setScoreType] = useState('freq')   // start on frequency
  const [selected, setSelected] = useState(null)       // no road selected yet
  const [showIntro, setShowIntro] = useState(true)     // show intro on load

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
        <button onClick={() => setShowIntro(true)}>About</button>
      </div>

      <RoadMap scoreType={scoreType} onSelect={setSelected} />
      <Legend scoreType={scoreType} />

      {selected && (
        <ProfilePanel
          road={selected}
          scoreType={scoreType}
          onClose={() => setSelected(null)}
        />
      )}

      {showIntro && <IntroModal onClose={() => setShowIntro(false)} />}
    </>
  )
}