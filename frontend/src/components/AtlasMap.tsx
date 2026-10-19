import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { Map as GLMap, GeoJSONSource } from 'maplibre-gl'
import type { FeatureCollection, Feature, Geometry, Position } from 'geojson'
import { Maximize2, Plus, Minus } from 'lucide-react'
import { useApi, query } from '../services/api'
import type { Complaint, Filters, GeographicCount } from '../services/api'
import { Feedback } from './Shared'

export type Mode = 'heatmap' | 'region' | 'individual'
export type Level = 'state' | 'district' | 'constituency'
const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] }
maplibregl.setWorkerUrl(workerUrl)
const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

function bounds(features: Feature[]): maplibregl.LngLatBoundsLike | undefined {
  const result = new maplibregl.LngLatBounds()
  function walk(coords: unknown) {
    if (Array.isArray(coords) && typeof coords[0] === 'number')
      result.extend(coords as [number, number])
    else if (Array.isArray(coords)) coords.forEach(walk)
  }
  features.forEach((f) => {
    if ('coordinates' in f.geometry) walk(f.geometry.coordinates)
  })
  return result.isEmpty() ? undefined : result
}

export function AtlasMap({
  filters = {},
  mode = 'region',
  level = 'state',
  onRegion,
  onComplaint,
  selectedId,
  picker,
  onPick,
  location,
}: {
  filters?: Filters
  mode?: Mode
  level?: Level
  onRegion?: (id: string, level: Level) => void
  onComplaint?: (c: Complaint) => void
  selectedId?: string
  picker?: boolean
  onPick?: (latitude: number, longitude: number) => void
  location?: [number, number]
}) {
  const container = useRef<HTMLDivElement>(null),
    map = useRef<GLMap | null>(null),
    marker = useRef<maplibregl.Marker | null>(null)
  const focusBounds = useRef<maplibregl.LngLatBoundsLike | undefined>(undefined)
  const callbacks = useRef({ onRegion, onComplaint, onPick, level, picker })
  callbacks.current = { onRegion, onComplaint, onPick, level, picker }
  const [ready, setReady] = useState(false),
    [mapError, setMapError] = useState<string>(),
    [hover, setHover] = useState('')
  const boundary = useApi<FeatureCollection>(
    `geography/boundaries?${query({ level: picker ? 'state' : level, state_id: picker ? undefined : filters.state_id })}`,
  )
  const counts = useApi<GeographicCount[]>(
    picker ? null : `map/regions?${query({ ...filters, level })}`,
    true,
  )
  const points = useApi<FeatureCollection>(
    picker ? null : `map/${mode === 'heatmap' ? 'heatmap' : 'complaints'}?${query(filters)}`,
    true,
  )

  useEffect(() => {
    if (!container.current) return
    let instance: GLMap
    try {
      instance = new maplibregl.Map({
        container: container.current,
        style: {
          version: 8,
          sources: {},
          layers: [
            { id: 'background', type: 'background', paint: { 'background-color': '#111f22' } },
          ],
        },
        center: [81, 22],
        zoom: 3.7,
        minZoom: picker ? 1.8 : 2,
        maxZoom: 13,
        attributionControl: false,
      })
      map.current = instance
      instance.addControl(
        new maplibregl.AttributionControl({
          compact: true,
          customAttribution:
            '<a href="https://projects.datameet.org/maps/" target="_blank" rel="noopener">DataMeet · Historical boundaries</a>',
        }),
        'bottom-right',
      )
      instance.on('load', () => {
        const lines: Feature[] = []
        for (let lat = 0; lat <= 40; lat += 5)
          lines.push({
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: [
                [60, lat],
                [105, lat],
              ],
            },
          })
        for (let lng = 60; lng <= 105; lng += 5)
          lines.push({
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: [
                [lng, 0],
                [lng, 40],
              ],
            },
          })
        instance.addSource('grid', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: lines },
        })
        instance.addLayer({
          id: 'grid-lines',
          type: 'line',
          source: 'grid',
          paint: { 'line-color': '#294044', 'line-width': 0.5, 'line-opacity': 0.45 },
        })
        instance.addSource('regions', { type: 'geojson', data: EMPTY })
        instance.addLayer({
          id: 'region-fill',
          type: 'fill',
          source: 'regions',
          paint: { 'fill-color': '#1b383b', 'fill-opacity': 0.88 },
        })
        instance.addLayer({
          id: 'region-line',
          type: 'line',
          source: 'regions',
          paint: { 'line-color': '#52736e', 'line-width': 0.7 },
        })
        instance.addLayer({
          id: 'selected-line',
          type: 'line',
          source: 'regions',
          filter: ['==', ['get', 'id'], ''],
          paint: { 'line-color': '#e6bc91', 'line-width': 2 },
        })
        instance.addSource('complaints', {
          type: 'geojson',
          data: EMPTY,
          cluster: true,
          clusterMaxZoom: 9,
          clusterRadius: 32,
          clusterProperties: { weight: ['+', ['coalesce', ['get', 'count'], 1]] },
        })
        instance.addLayer({
          id: 'heat',
          type: 'heatmap',
          source: 'complaints',
          paint: {
            'heatmap-weight': ['coalesce', ['get', 'weight'], ['get', 'count'], 1],
            'heatmap-intensity': 1.2,
            'heatmap-radius': 32,
            'heatmap-opacity': 0.85,
            'heatmap-color': [
              'interpolate',
              ['linear'],
              ['heatmap-density'],
              0,
              'rgba(40,106,99,0)',
              0.2,
              '#397a70',
              0.5,
              '#c2bd86',
              0.75,
              '#d5a263',
              1,
              '#e07848',
            ],
          },
        })
        instance.addLayer({
          id: 'clusters',
          type: 'circle',
          source: 'complaints',
          filter: ['has', 'point_count'],
          paint: {
            'circle-radius': ['step', ['get', 'point_count'], 14, 10, 19, 50, 25],
            'circle-color': '#ce9567',
            'circle-stroke-color': '#f4d8b6',
            'circle-stroke-width': 1.5,
          },
        })
        instance.addLayer({
          id: 'points',
          type: 'circle',
          source: 'complaints',
          filter: ['!', ['has', 'point_count']],
          paint: {
            'circle-radius': 5,
            'circle-color': '#d7a274',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#243b3c',
          },
        })
        instance.on('click', 'region-fill', (e) => {
          if (instance.queryRenderedFeatures(e.point, { layers: ['points', 'clusters'] }).length)
            return
          const id = e.features?.[0]?.properties?.id
          if (id && !callbacks.current.picker)
            callbacks.current.onRegion?.(String(id), callbacks.current.level)
        })
        instance.on('click', 'points', (e) => {
          const p = e.features?.[0]?.properties
          if (p) {
            callbacks.current.onComplaint?.({
              ...p,
              is_demo: p.is_demo === true || p.is_demo === 'true',
            } as Complaint)
          }
        })
        instance.on('click', 'clusters', async (e) => {
          const f = e.features?.[0]
          if (!f || f.geometry.type !== 'Point') return
          const source = instance.getSource('complaints') as GeoJSONSource
          const zoom = await source.getClusterExpansionZoom(Number(f.properties?.cluster_id))
          instance.easeTo({
            center: f.geometry.coordinates as [number, number],
            zoom,
            duration: reduced() ? 0 : 500,
          })
        })
        instance.on('click', (e) => {
          if (callbacks.current.picker) callbacks.current.onPick?.(e.lngLat.lat, e.lngLat.lng)
        })
        instance.on('mousemove', 'region-fill', (e) => {
          const p = e.features?.[0]?.properties
          setHover(p ? `${p.name} · ${p.count || 0} reports` : '')
          instance.getCanvas().style.cursor = 'pointer'
        })
        instance.on('mouseleave', 'region-fill', () => {
          setHover('')
          instance.getCanvas().style.cursor = ''
        })
        instance.fitBounds(
          [
            [67, 6],
            [98, 36],
          ],
          { padding: picker ? 12 : 30, duration: 0 },
        )
        setReady(true)
      })
      instance.on('error', (e) => {
        setMapError(
          e.error?.message?.includes('WebGL')
            ? 'The map needs WebGL. Use the region selectors to explore the same data.'
            : 'Map rendering failed. Reload the page or use the region selectors to explore the data.',
        )
      })
    } catch {
      setMapError(
        'Your browser cannot display this map. Use the region selectors to explore the data.',
      )
    }
    let previousWidth = container.current.clientWidth
    const observer = new ResizeObserver(() => {
      const width = container.current?.clientWidth || 0
      instance?.resize()
      if (
        width >= 180 &&
        (container.current?.clientHeight || 0) >= 180 &&
        Math.abs(width - previousWidth) > 8 &&
        focusBounds.current &&
        !callbacks.current.picker
      ) {
        instance?.fitBounds(focusBounds.current, { padding: 35, duration: 0, maxZoom: 12.5 })
      }
      previousWidth = width
    })
    observer.observe(container.current)
    return () => {
      observer.disconnect()
      marker.current?.remove()
      instance?.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    const instance = map.current
    if (!ready || !instance || !boundary.data) return
    const values = new Map(counts.data?.map((c) => [c.id, c.count]) || [])
    const features: Feature[] = boundary.data.features.map((f) => ({
      ...f,
      properties: { ...f.properties, count: values.get(f.properties?.id) || 0 },
    }))
    ;(instance.getSource('regions') as GeoJSONSource).setData({
      type: 'FeatureCollection',
      features,
    })
    const max = Math.max(1, ...values.values())
    instance.setPaintProperty(
      'region-fill',
      'fill-color',
      mode === 'region' && !picker
        ? [
            'case',
            ['==', ['get', 'count'], 0],
            '#1b3538',
            [
              'interpolate',
              ['linear'],
              ['/', ['get', 'count'], max],
              0,
              '#2e645b',
              0.5,
              '#71876a',
              1,
              '#c48c5a',
            ],
          ]
        : '#1b3538',
    )
    instance.setFilter('selected-line', ['==', ['get', 'id'], selectedId || ''])
  }, [ready, boundary.data, counts.data, mode, selectedId, picker])

  useEffect(() => {
    if (!ready || !map.current || !boundary.data || picker) return
    const selected = boundary.data.features.filter((f) => f.properties?.id === selectedId)
    const box = bounds(selected.length ? selected : boundary.data.features)
    focusBounds.current = box
    if (box)
      map.current.fitBounds(box, { padding: 45, duration: reduced() ? 0 : 650, maxZoom: 12.5 })
  }, [ready, boundary.data, selectedId, picker])

  useEffect(() => {
    if (!ready || !map.current) return
    ;(map.current.getSource('complaints') as GeoJSONSource).setData(points.data || EMPTY)
    map.current.setLayoutProperty(
      'heat',
      'visibility',
      mode === 'heatmap' && !picker ? 'visible' : 'none',
    )
    for (const id of ['clusters', 'points'])
      map.current.setLayoutProperty(
        id,
        'visibility',
        mode === 'individual' && !picker ? 'visible' : 'none',
      )
  }, [ready, points.data, mode, picker])

  useEffect(() => {
    const instance = map.current
    if (!ready || !instance || !location) return
    if (!marker.current) {
      marker.current = new maplibregl.Marker({ color: '#e3af7f', draggable: true })
        .setLngLat(location)
        .addTo(instance)
      marker.current.on('dragend', () => {
        const p = marker.current!.getLngLat()
        callbacks.current.onPick?.(p.lat, p.lng)
      })
    } else marker.current.setLngLat(location)
    instance.easeTo({ center: location, zoom: 7, duration: reduced() ? 0 : 500 })
  }, [ready, location])

  return (
    <div className={`map-shell ${picker ? 'picker-map' : ''}`}>
      <div
        ref={container}
        className="map-canvas"
        aria-label={picker ? 'Select your location on the map' : 'Interactive India complaint map'}
      />
      {!picker && (
        <>
          <div className="map-corner">
            <span className="map-cross">+</span>
            <span>
              INDIA
              <br />
              <small>Geographic intelligence</small>
            </span>
          </div>
          {level === 'state' && !filters.state_id && (
            <>
              <span className="ocean-label">
                ARABIAN
                <br />
                SEA
              </span>
              <span className="ocean-label bay">
                BAY OF
                <br />
                BENGAL
              </span>
            </>
          )}
        </>
      )}
      <div className="map-controls">
        <span className="north">N ↑</span>
        <button
          aria-label="Zoom in"
          onClick={() => map.current?.zoomIn({ duration: reduced() ? 0 : 250 })}
        >
          <Plus size={18} />
        </button>
        <button
          aria-label="Zoom out"
          onClick={() => map.current?.zoomOut({ duration: reduced() ? 0 : 250 })}
        >
          <Minus size={18} />
        </button>
        <button
          aria-label="Show all India"
          onClick={() =>
            map.current?.fitBounds(
              [
                [67, 6],
                [98, 36],
              ],
              { padding: 30, duration: reduced() ? 0 : 500 },
            )
          }
        >
          <Maximize2 size={16} />
        </button>
      </div>
      {!picker && (
        <div className="map-legend">
          <span>
            {mode === 'heatmap'
              ? 'Complaint density'
              : mode === 'region'
                ? 'Reports per region'
                : 'Approximate locations'}
          </span>
          {mode === 'region' && numberMax(counts.data) === '0' ? (
            <small>No reports in this view.</small>
          ) : mode !== 'individual' ? (
            <>
              <div className="legend-ramp" />
              <div className="legend-ends">
                <span>{mode === 'region' ? '1 report' : 'Lower'}</span>
                <span>{mode === 'region' ? numberMax(counts.data) : 'Higher'}</span>
              </div>
            </>
          ) : (
            <small>Grouped within a 0.05° grid</small>
          )}
          <small className="no-data-key">
            <i /> No reports
          </small>
        </div>
      )}
      {hover && !picker && (
        <div className="map-hover" role="status">
          {hover}
        </div>
      )}
      <div className="map-feedback">
        <Feedback
          error={mapError || boundary.error || counts.error || points.error}
          loading={boundary.loading}
          retry={() => {
            boundary.retry()
            counts.retry()
            points.retry()
          }}
        />
      </div>
    </div>
  )
}

function numberMax(data?: GeographicCount[]) {
  return new Intl.NumberFormat('en-IN').format(Math.max(0, ...(data?.map((d) => d.count) || [])))
}
