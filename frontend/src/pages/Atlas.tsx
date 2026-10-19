import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, ChevronRight, Layers, MapPin, Waves } from 'lucide-react'
import { AtlasMap } from '../components/AtlasMap'
import type { Mode, Level } from '../components/AtlasMap'
import {
  CategoryBars,
  ComplaintDetail,
  Feedback,
  FilterBar,
  Records,
  useFilters,
} from '../components/Shared'
import { useApi, query, number, date } from '../services/api'
import type { Overview, Category, Complaint, ComplaintPage, Region, Config } from '../services/api'

export default function Atlas() {
  const { filters, update, params } = useFilters()
  const mode = (
    ['heatmap', 'region', 'individual'].includes(params.get('mode') || '')
      ? params.get('mode')
      : 'region'
  ) as Mode
  const level = (
    ['state', 'district', 'constituency'].includes(params.get('level') || '')
      ? params.get('level')
      : filters.state_id
        ? 'district'
        : 'state'
  ) as Level
  const [selected, setSelected] = useState<Complaint | null>(null)
  const filterKey = query(filters)
  useEffect(() => setSelected(null), [filterKey])
  const overview = useApi<Overview>(`analytics/overview?${query(filters)}`, true)
  const categories = useApi<Category[]>(`analytics/categories?${query(filters)}`, true)
  const reports = useApi<ComplaintPage>(`complaints?${query({ ...filters, page_size: 3 })}`, true)
  const states = useApi<Region[]>('geography/states')
  const districts = useApi<Region[]>(
    filters.state_id ? `geography/districts?${query({ state_id: filters.state_id })}` : null,
  )
  const assemblies = useApi<Region[]>(
    filters.state_id ? `geography/constituencies?${query({ state_id: filters.state_id })}` : null,
  )
  const config = useApi<Config>('config')
  const state = states.data?.find((s) => s.id === filters.state_id)
  const district = districts.data?.find((s) => s.id === filters.district_id)
  const assembly = assemblies.data?.find((s) => s.id === filters.constituency_id)
  const viewName = assembly?.name || district?.name || state?.name || 'Across the country'
  const onRegion = (id: string, clicked: Level) => {
    setSelected(null)
    if (clicked === 'state')
      update({
        state_id: id,
        district_id: undefined,
        constituency_id: undefined,
        level: 'district',
      })
    else if (clicked === 'district')
      update({ district_id: id, constituency_id: undefined, level: 'constituency' })
    else update({ constituency_id: id })
  }
  return (
    <main id="main" className="atlas-page">
      <div className="page-intro">
        <div>
          <p className="eyebrow">A shared concern. A clearer perspective.</p>
          <h1>
            India, in perspective<span className="copper">.</span>
          </h1>
          <p className="intro-copy">
            Every report is a local story. Together, they reveal the bigger picture.
          </p>
        </div>
        <Link to="/raise" className="button primary">
          Raise a complaint <ArrowUpRight size={17} />
        </Link>
      </div>
      <FilterBar filters={filters} update={update} />
      <div className="atlas-toolbar">
        <div className="breadcrumb">
          <button
            onClick={() =>
              update({
                state_id: undefined,
                district_id: undefined,
                constituency_id: undefined,
                level: 'state',
              })
            }
          >
            India
          </button>
          {state && (
            <>
              <ChevronRight size={13} />
              <button
                onClick={() =>
                  update({ district_id: undefined, constituency_id: undefined, level: 'district' })
                }
              >
                {state.name}
              </button>
            </>
          )}
          {district && (
            <>
              <ChevronRight size={13} />
              <button onClick={() => update({ constituency_id: undefined, level: 'district' })}>
                {district.name}
              </button>
            </>
          )}
          {assembly && (
            <>
              <ChevronRight size={13} />
              <span>{assembly.name}</span>
            </>
          )}
        </div>
        <div className="map-options">
          <label>
            <span className="sr-only">Boundary layer</span>
            <select
              aria-label="Boundary layer"
              value={level}
              onChange={(e) => update({ level: e.target.value })}
            >
              <option value="state">State boundaries</option>
              <option value="district">District boundaries</option>
              <option value="constituency">Assembly boundaries</option>
            </select>
          </label>
          <div className="mode-switch" aria-label="Map display mode">
            {(
              [
                { id: 'heatmap', label: 'Heatmap', icon: Waves },
                { id: 'region', label: 'Regions', icon: Layers },
                { id: 'individual', label: 'Individual', icon: MapPin },
              ] as const
            ).map((m) => (
              <button
                aria-pressed={mode === m.id}
                key={m.id}
                onClick={() => {
                  setSelected(null)
                  update({ mode: m.id })
                }}
              >
                <m.icon size={14} />
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="atlas-layout">
        <AtlasMap
          filters={filters}
          mode={mode}
          level={level}
          selectedId={filters.constituency_id || filters.district_id || filters.state_id}
          onRegion={onRegion}
          onComplaint={setSelected}
        />
        <aside className="atlas-reading">
          <div className="reading-top">
            <span className="section-label">The current view</span>
            <span className="live-dot" title="Refreshes every 15 seconds" />
          </div>
          <h2>{viewName}</h2>
          <Feedback error={overview.error} loading={overview.loading} retry={overview.retry} />
          <div className="atlas-count">
            {number(overview.data?.total || 0)}
            <span>public complaints</span>
          </div>
          <div className="mini-metrics">
            <div>
              <strong>{number(overview.data?.active_clusters || 0)}</strong>
              <span>shared concerns</span>
            </div>
            <div>
              <strong>{number(overview.data?.states || 0)}</strong>
              <span>states represented</span>
            </div>
          </div>
          {selected ? (
            <ComplaintDetail complaint={selected} onClose={() => setSelected(null)} />
          ) : (
            <>
              <div className="aside-section">
                <div className="section-heading small">
                  <h3>What people are reporting</h3>
                  <span>{number(categories.data?.length || 0)}</span>
                </div>
                <Feedback error={categories.error} retry={categories.retry} />
                <CategoryBars
                  categories={categories.data || []}
                  selected={filters.cluster_id}
                  onSelect={(id) =>
                    update({ cluster_id: filters.cluster_id === id ? undefined : id })
                  }
                  limit={4}
                />
              </div>
              <div className="aside-section recent">
                <div className="section-heading small">
                  <h3>From the public record</h3>
                  <ArrowUpRight size={15} />
                </div>
                {reports.data?.items.map((c) => (
                  <button className="recent-report" key={c.id} onClick={() => setSelected(c)}>
                    <span>{c.text}</span>
                    <small>
                      {c.district || c.state} · {date(c.created_at, true)}
                    </small>
                  </button>
                ))}
                {!reports.data?.items.length && (
                  <p className="muted">No reports here yet. Your voice can be the first.</p>
                )}
              </div>
            </>
          )}
          <Link className="text-link atlas-analytics" to={`/analytics?${query(filters)}`}>
            Explore the full picture <ArrowUpRight size={15} />
          </Link>
        </aside>
      </div>
      <div className="atlas-notes">
        <span>
          <i className="small-square" />{' '}
          {overview.data?.demo_count
            ? `${number(overview.data.demo_count)} fictional demonstration reports in this view`
            : 'Local reports. Shared understanding.'}
        </span>
        <span>
          Locations are approximate · {config.data?.boundary_vintage || 'Historical boundaries'}
        </span>
      </div>
      {mode === 'individual' && <Records key={query(filters)} filters={filters} />}
      {config.data && !config.data.geography_available && (
        <div className="feedback error">
          Geographic data is not installed. Run the setup command in the repository README to enable
          the map and submissions.
        </div>
      )}
    </main>
  )
}
