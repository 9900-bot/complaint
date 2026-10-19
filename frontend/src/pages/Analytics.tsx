import { useState } from 'react'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import { CategoryBars, Feedback, FilterBar, Records, useFilters } from '../components/Shared'
import { useApi, query, number, date } from '../services/api'
import type { Overview, Category, GeographicCount, Timeline, Filters } from '../services/api'
import type { Level } from '../components/AtlasMap'

export default function Analytics() {
  const { filters, update } = useFilters()
  const [interval, setInterval] = useState('day'),
    [geography, setGeography] = useState<Level>('state')
  const overview = useApi<Overview>(`analytics/overview?${query(filters)}`, true)
  const timeline = useApi<Timeline[]>(`analytics/timeline?${query({ ...filters, interval })}`, true)
  const categories = useApi<Category[]>(`analytics/categories?${query(filters)}`, true)
  const regions = useApi<GeographicCount[]>(
    `analytics/geography?${query({ ...filters, level: geography })}`,
    true,
  )
  const trends = useApi<{
    current: number
    previous: number
    change: number
    emerging: Category[]
  }>(`analytics/trends?${query(filters)}`, true)
  const selected = categories.data?.find((c) => c.id === filters.cluster_id)
  const max = Math.max(1, ...(regions.data?.map((r) => r.count) || []))
  return (
    <main id="main" className="analytics-page">
      <div className="page-intro">
        <div>
          <p className="eyebrow">Patterns behind the public record</p>
          <h1>
            The bigger picture<span className="copper">.</span>
          </h1>
          <p className="intro-copy">Follow shared concerns across places and over time.</p>
        </div>
        <div className="data-stamp">
          <span className="live-dot" />
          Local intelligence
          <span>
            Latest report{' '}
            {overview.data?.latest_submission ? date(overview.data.latest_submission) : '—'}
          </span>
        </div>
      </div>
      <FilterBar filters={filters} update={update} dates />
      <Feedback error={overview.error} loading={overview.loading} retry={overview.retry} />
      <section className="metric-strip" aria-label="Complaint overview">
        <div>
          <span>Total complaints</span>
          <strong>{number(overview.data?.total_all_dates || 0)}</strong>
          <small>across matching regions & categories</small>
        </div>
        <div>
          <span>In selected period</span>
          <strong>{number(overview.data?.total || 0)}</strong>
          <small>all dates unless filtered</small>
        </div>
        <div>
          <span>Shared concerns</span>
          <strong>{number(overview.data?.active_clusters || 0)}</strong>
          <small>active semantic categories</small>
        </div>
        <div>
          <span>States represented</span>
          <strong>{number(overview.data?.states || 0)}</strong>
          <small>with matching complaints</small>
        </div>
        <div className="leading-category">
          <span>Most reported concern</span>
          <strong>{overview.data?.top_category || 'No reports yet'}</strong>
          <small>
            {overview.data?.demo_count
              ? `${number(overview.data.demo_count)} fictional demo reports included`
              : 'Derived from the public record'}
          </small>
        </div>
      </section>
      <div className="analysis-primary">
        <section className="trend-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">Activity over time</span>
              <h2>How the conversation is changing.</h2>
            </div>
            <div className="small-switch">
              {['day', 'week'].map((i) => (
                <button aria-pressed={interval === i} key={i} onClick={() => setInterval(i)}>
                  {i === 'day' ? 'Daily' : 'Weekly'}
                </button>
              ))}
            </div>
          </div>
          <Feedback error={timeline.error} retry={timeline.retry} />
          <div
            className="chart"
            role="img"
            aria-label={`${interval === 'day' ? 'Daily' : 'Weekly'} complaints: ${(timeline.data || []).map((t) => `${t.date}: ${t.count}`).join(', ')}`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={timeline.data || []}
                margin={{ top: 20, right: 12, bottom: 4, left: -20 }}
              >
                <CartesianGrid stroke="#deded2" vertical={false} strokeDasharray="2 5" />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  minTickGap={45}
                  tick={{ fill: '#64716b', fontSize: 11 }}
                  tickFormatter={(v) => date(v, true)}
                />
                <YAxis
                  allowDecimals={false}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64716b', fontSize: 11 }}
                  domain={[0, 'auto']}
                />
                <Tooltip
                  labelFormatter={(v) => date(String(v))}
                  contentStyle={{
                    background: '#faf8f3',
                    border: '1px solid #c9d0c4',
                    borderRadius: 3,
                    fontSize: 13,
                  }}
                />
                <Area
                  type="linear"
                  dataKey="count"
                  name="Complaints"
                  stroke="#286a63"
                  strokeWidth={2}
                  fill="#286a63"
                  fillOpacity={0.1}
                  animationDuration={240}
                  isAnimationActive={!window.matchMedia('(prefers-reduced-motion: reduce)').matches}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-caption">
            <span>
              <i />
              Submitted complaints
            </span>
            <span>
              {trends.data?.change === undefined
                ? ''
                : `${trends.data.change >= 0 ? '+' : ''}${trends.data.change} reports vs. previous equal period (30 days by default)`}
            </span>
          </div>
          <Feedback error={trends.error} retry={trends.retry} />
        </section>
        <section className="distribution-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">The shape of concern</span>
              <h2>Shared issues.</h2>
            </div>
            <span>{number(categories.data?.length || 0)} categories</span>
          </div>
          <Feedback error={categories.error} retry={categories.retry} />
          <CategoryBars
            categories={categories.data || []}
            onSelect={(id) => update({ cluster_id: filters.cluster_id === id ? undefined : id })}
            selected={filters.cluster_id}
            limit={5}
          />
        </section>
      </div>
      <div className="analysis-secondary">
        <section className="geography-panel">
          <div className="section-heading">
            <div>
              <span className="section-label">Geographic concentration</span>
              <h2>Where voices gather.</h2>
            </div>
            <label>
              <span className="sr-only">Geographic ranking level</span>
              <select
                aria-label="Geographic ranking level"
                value={geography}
                onChange={(e) => setGeography(e.target.value as Level)}
              >
                <option value="state">By state</option>
                <option value="district">By district</option>
                <option value="constituency">By constituency</option>
              </select>
            </label>
          </div>
          <Feedback error={regions.error} retry={regions.retry} />
          {!regions.data?.length && (
            <div className="empty">
              <p>No geographic activity in this view.</p>
              <span>Regional comparisons appear with your first reports.</span>
            </div>
          )}
          <div className="region-rankings">
            {regions.data?.slice(0, 7).map((r, i) => (
              <button
                key={r.id}
                className="region-rank"
                onClick={() =>
                  update(
                    geography === 'state'
                      ? { state_id: r.id, district_id: undefined, constituency_id: undefined }
                      : { [`${geography}_id`]: r.id },
                  )
                }
              >
                <span className="rank">{String(i + 1).padStart(2, '0')}</span>
                <span className="region-name">
                  {r.name}
                  <small>{r.top_category || 'Uncategorised'}</small>
                </span>
                <div className="region-bar">
                  <span style={{ width: `${(r.count / max) * 100}%` }} />
                </div>
                <strong>{number(r.count)}</strong>
                <ArrowUpRight size={14} />
              </button>
            ))}
          </div>
        </section>
        <section className="category-exploration">
          <span className="section-label">Read between the reports</span>
          <h2>{selected?.label || 'One concern. Many places.'}</h2>
          {selected ? (
            <>
              <p className="representative">“{selected.representative_text}”</p>
              <div className="explore-stats">
                <div>
                  <strong>{number(selected.count)}</strong>
                  <span>related reports</span>
                </div>
                <div>
                  <strong>{number(overview.data?.states || 0)}</strong>
                  <span>states</span>
                </div>
              </div>
              <p className="growth">
                {selected.growth >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}{' '}
                {selected.growth >= 0 ? '+' : ''}
                {selected.growth} reports in the second half of the period
              </p>
              <button className="text-link" onClick={() => update({ cluster_id: undefined })}>
                Show all concerns <ArrowUpRight size={15} />
              </button>
            </>
          ) : (
            <>
              <p>
                Similar complaints are connected by meaning, wherever they happen. Select a category
                to explore its representative voice, geography and timeline.
              </p>
              <div className="emerging">
                <span className="section-label">New in the period</span>
                {trends.data?.emerging.slice(0, 3).map((c) => (
                  <button key={c.id} onClick={() => update({ cluster_id: c.id! })}>
                    {c.label}
                    <ArrowUpRight size={14} />
                  </button>
                ))}
                {!trends.data?.emerging.length && (
                  <p>New concerns will appear here as the public record grows.</p>
                )}
              </div>
            </>
          )}
        </section>
      </div>
      <Records key={query(filters)} filters={filters} />
    </main>
  )
}
