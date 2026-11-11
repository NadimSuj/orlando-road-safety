import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
maplibregl.setWorkerUrl(workerUrl)

const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
const ORLANDO = [-81.38, 28.54]
const START_ZOOM = 10

const COLOR_EXPR = [
  'case',
  ['get', 'rankable'],
  [
    'interpolate', ['linear'],
    ['get', 'score_freq_pct'],
    0,   '#0d9488',
    40,  '#eab308',
    75,  '#ea580c',
    100, '#991b1b',
  ],
  '#94a3b8',
]

export default function RoadMap() {
  const containerRef = useRef(null)
  const mapRef = useRef(null)

  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP,
      center: ORLANDO,
      zoom: START_ZOOM,
    })
    mapRef.current = map

    map.on('load', () => {
      const firstLabelId = map.getStyle().layers.find(l => l.type === 'symbol').id

      map.addSource('roads', {
        type: 'geojson',
        data: '/orlando_roads.geojson',
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
            'line-color': COLOR_EXPR,
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
    })

    return () => { map.remove(); mapRef.current = null }
  }, [])

  return <div ref={containerRef} className="map" />
}