export default function IntroModal({ onClose }) {
  return (
    <div className="intro-overlay">
      <div className="intro-card">
        <h1>Orlando Road Safety Map</h1>

        <p>
          This map shows how often crashes happen on 191 major roads in Orange
          County, Florida, using FDOT crash records from 2014–2018. About
          100,000 crashes are matched to the roads shown here.
        </p>

        <h3>Why we use rates</h3>
        <p>
          Busy roads have more crashes simply because more people drive on
          them. Each road is scored per 100 million vehicle-miles, so a road
          is compared by its risk per trip instead of its traffic.
        </p>

        <h3>The goal</h3>
        <p>
          To help anyone trying to learn about urban design see how a road's design (its speed,
          width and type) relates to safety, and to ask why some streets are
          more dangerous than others.
        </p>

        <h3>How to use it</h3>
        <ul>
          <li>Colors run from teal (lower rate) to dark red (higher rate).</li>
          <li>Switch between <strong>crash frequency</strong> and{' '}
            <strong>crash cost</strong>, which weights severe crashes more.</li>
          <li>Click any road to see its traffic, speed limit and crash breakdown.</li>
        </ul>

        <p className="intro-note">
            A high rate shows where crashes concentrate, not exactly why. Crashes are
            from 2014–2018 and traffic counts from 2021; the background map shows
            today's streets, so roads redesigned since 2018 may look different from
            when their crashes happened.
        </p>

        <button className="intro-button" onClick={onClose}>
          Explore the map
        </button>
      </div>
    </div>
  )
}