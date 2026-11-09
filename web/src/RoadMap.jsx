import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

maplibregl.setWorkerUrl(workerUrl)

const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
const ORLANDO = [-81.38, 28.54]   // [longitude, latitude]
const START_ZOOM = 10

export default function RoadMap() {
  const containerRef = useRef(null)   // the <div> the map draws into
  const mapRef = useRef(null)         // the Mapibre map object

  useEffect(() => {

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP,
      center: ORLANDO,
      zoom: START_ZOOM
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  return <div ref={containerRef} className="map" />
}