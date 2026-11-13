import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { STOPS, UNRANKED } from './colors'
maplibregl.setWorkerUrl(workerUrl)

const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
const ORLANDO = [-81.38, 28.54]
const START_ZOOM = 10
const BOUNDS = [
  [-81.85, 28.25],   // southwest corner
  [-80.75, 28.90],   // northeast corner
]

function colorExpr(field) {
  return [
    'case',
    ['get', 'rankable'],
    ['interpolate', ['linear'], ['get', field], ...STOPS.flat()],
    UNRANKED,
  ]
}

export default function RoadMap({ scoreType, onSelect }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const [loaded, setLoaded] = useState(false)

  // Effect 1: create the map once and add the roads layer
  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP,
      center: ORLANDO,
      zoom: START_ZOOM,
      maxBounds: BOUNDS,
    })
    mapRef.current = map

    map.on('load', () => {
      const firstLabelId = map.getStyle().layers.find(l => l.type === 'symbol').id

      map.addSource('roads', {
        type: 'geojson',
        data: '/orlando_roads.geojson',
        tolerance: 0,
        data: `${import.meta.env.BASE_URL}orlando_roads.geojson`,
      })

      map.addLayer(
        {
          id: 'roads-line',
          type: 'line',
          source: 'roads',
          layout: {
            'line-cap': 'round',
            'line-join': 'round',
          },
          paint: {
            'line-color': colorExpr('score_freq_pct'),
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              10, 3,   // width at city view
              14, 5,   // width at neighborhood view
              17, 7,   // width at street view
            ],
          },
        },
        firstLabelId,
      )

      map.on('click', 'roads-line', (e) => {
        onSelect(e.features[0].properties)
      })

      // show a pointer cursor over roads, so users know they can click
      map.on('mouseenter', 'roads-line', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'roads-line', () => { map.getCanvas().style.cursor = '' })

      setLoaded(true)
    })

    return () => { map.remove(); mapRef.current = null }
  }, [])

  // Effect 2: recolor the roads whenever the score type changes
  useEffect(() => {
    if (!loaded) return
    const field = `score_${scoreType}_pct`
    mapRef.current.setPaintProperty('roads-line', 'line-color', colorExpr(field))
  }, [scoreType, loaded])

  return <div ref={containerRef} className="map" />
}