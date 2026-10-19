import { useSearchParams, Link } from 'react-router-dom'
import {
  ArrowUpRight,
  RotateCcw,
  RefreshCw,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useApi, query, number, date } from '../services/api'
import type { Filters, Region, Category, ComplaintPage, Complaint } from '../services/api'

export function useFilters() {
  const [params, setParams] = useSearchParams()
  const latestParams = useRef(params)
  useEffect(() => {
    latestParams.current = params
  }, [params])
  const filters: Filters = Object.fromEntries(
    [...params].filter(([k]) =>
      ['state_id', 'district_id', 'constituency_id', 'cluster_id', 'date_from', 'date_to'].includes(
        k,
      ),
    ),
  )
  const update = (changes: Record<string, string | undefined>) => {
    const next = new URLSearchParams(latestParams.current)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    latestParams.current = next
    setParams(next)
  }
  return { filters, update, params }
}

export function Feedback({
  error,
  loading,
  retry,
}: {
  error?: string
  loading?: boolean
  retry?: () => void
}) {
  if (error)
    return (
      <div className="feedback error" role="alert">
        <AlertCircle size={17} />
        <span>{error}</span>
        {retry && (
          <button className="text-button" onClick={retry}>
            Try again <RefreshCw size={14} />
          </button>
        )}
      </div>
    )
  if (loading)
    return (
      <div className="feedback" role="status">
        <span className="loading-dot" />
        Reading the atlas…
      </div>
    )
  return null
}

export function FilterBar({
  filters,
  update,
  dates = false,
}: {
  filters: Filters
  update: (changes: Record<string, string | undefined>) => void
  dates?: boolean
}) {
  const [search, setSearch] = useState('')
  const states = useApi<Region[]>('geography/states')
  const districts = useApi<Region[]>(
    filters.state_id ? `geography/districts?${query({ state_id: filters.state_id })}` : null,
  )
  const assemblies = useApi<Region[]>(
    filters.state_id ? `geography/constituencies?${query({ state_id: filters.state_id })}` : null,
  )
  const categories = useApi<Category[]>('clusters', true)
  const select = (
    label: string,
    value: string | undefined,
    items: Region[] | undefined,
    onChange: (v: string) => void,
    empty: string,
    disabled = false,
  ) => (
    <label className="filter-field">
      <span>{label}</span>
      <select
        aria-label={label}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{empty}</option>
        {items?.map((i) => (
          <option key={i.id} value={i.id}>
            {i.name}
          </option>
        ))}
      </select>
    </label>
  )
  return (
    <>
      <div className={`filters ${dates ? 'with-dates' : ''}`}>
        {select(
          'State / UT',
          filters.state_id,
          states.data,
          (v) =>
            update({
              state_id: v,
              district_id: undefined,
              constituency_id: undefined,
              level: undefined,
            }),
          'All of India',
        )}
        {select(
          'District',
          filters.district_id,
          districts.data,
          (v) => update({ district_id: v, level: v ? 'district' : undefined }),
          'All districts',
          !filters.state_id,
        )}
        {select(
          'Assembly constituency',
          filters.constituency_id,
          assemblies.data,
          (v) => update({ constituency_id: v, level: v ? 'constituency' : undefined }),
          'All constituencies',
          !filters.state_id,
        )}
        <label className="filter-field category-filter">
          <span>Semantic category</span>
          <select
            aria-label="Semantic category"
            value={filters.cluster_id || ''}
            onChange={(e) => update({ cluster_id: e.target.value })}
          >
            <option value="">All categories</option>
            {categories.data
              ?.filter(
                (c) =>
                  c.label.toLowerCase().includes(search.toLowerCase()) ||
                  c.id === filters.cluster_id,
              )
              .map((c) => (
                <option key={c.id} value={c.id!}>
                  {c.label} ({number(c.count)})
                </option>
              ))}
          </select>
        </label>
        <label className="category-search">
          <span className="sr-only">Search categories</span>
          <input
            aria-label="Search categories"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Find a category…"
            type="search"
          />
        </label>
        {dates && (
          <>
            <label className="filter-field">
              <span>From</span>
              <input
                aria-label="From date"
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => update({ date_from: e.target.value })}
              />
            </label>
            <label className="filter-field">
              <span>To</span>
              <input
                aria-label="To date"
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => update({ date_to: e.target.value })}
              />
            </label>
          </>
        )}
        <button
          className="reset"
          aria-label="Reset filters"
          title="Reset filters"
          onClick={() => {
            setSearch('')
            update({
              state_id: undefined,
              district_id: undefined,
              constituency_id: undefined,
              cluster_id: undefined,
              date_from: undefined,
              date_to: undefined,
              level: undefined,
            })
          }}
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <Feedback
        error={states.error || categories.error || districts.error || assemblies.error}
        retry={() => {
          states.retry()
          categories.retry()
          districts.retry()
          assemblies.retry()
        }}
      />
    </>
  )
}

export function CategoryBars({
  categories,
  onSelect,
  selected,
  limit = 6,
}: {
  categories: Category[]
  onSelect?: (id: string) => void
  selected?: string
  limit?: number
}) {
  if (!categories.length)
    return (
      <div className="empty">
        <p>A clearer picture starts with a report.</p>
        <span>Categories appear as complaints are grouped by their meaning.</span>
      </div>
    )
  return (
    <div className="category-bars">
      {categories.slice(0, limit).map((c, i) => (
        <button
          className={`category-row ${selected === c.id ? 'selected' : ''}`}
          key={c.id || 'uncategorised'}
          disabled={!onSelect || !c.id}
          onClick={() => onSelect?.(c.id!)}
        >
          <div className="category-meta">
            <span>
              <span className="rank">{String(i + 1).padStart(2, '0')}</span>
              {c.label}
            </span>
            <strong>{number(c.count)}</strong>
          </div>
          <div className="bar-track">
            <span style={{ width: `${c.share}%` }} />
          </div>
          <div className="category-foot">
            <span>{c.share.toFixed(1)}% of reports</span>
            {onSelect && c.id && <ArrowUpRight size={13} />}
          </div>
        </button>
      ))}
    </div>
  )
}

export function ComplaintDetail({
  complaint,
  onClose,
}: {
  complaint: Complaint
  onClose: () => void
}) {
  return (
    <section className="complaint-detail" aria-label="Selected complaint">
      <div className="section-label">
        Approximate area{' '}
        <button className="text-button" onClick={onClose}>
          Close ×
        </button>
      </div>
      <p className="detail-area">
        {complaint.constituency || complaint.district || complaint.state}
      </p>
      <p className="complaint-prose">{complaint.text}</p>
      <div className="record-meta">
        {complaint.category || 'Uncategorised'} · {date(complaint.created_at)}
      </div>
      {complaint.is_demo && <p className="demo-label">Fictional demonstration complaint</p>}
    </section>
  )
}

export function Records({ filters }: { filters: Filters }) {
  const [page, setPage] = useState(1)
  const key = query(filters)
  // The parent keys this component by the filter combination to reset pagination.
  return <RecordPage key={key} filters={filters} page={page} setPage={setPage} />
}

function RecordPage({
  filters,
  page,
  setPage,
}: {
  filters: Filters
  page: number
  setPage: (n: number) => void
}) {
  const records = useApi<ComplaintPage>(
    `complaints?${query({ ...filters, page, page_size: 8 })}`,
    true,
  )
  const [expanded, setExpanded] = useState<string | null>(null)
  return (
    <section className="records">
      <div className="section-heading">
        <div>
          <span className="section-label">The public record</span>
          <h2>Individual voices.</h2>
        </div>
        <span>{number(records.data?.total || 0)} reports</span>
      </div>
      <Feedback {...records} />
      {records.data && !records.data.total && (
        <div className="empty">
          <p>No reports match this view.</p>
          <span>Try a wider date range or another region.</span>
        </div>
      )}
      {!!records.data?.total && (
        <>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Complaint</th>
                  <th>Category</th>
                  <th>Approximate area</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {records.data.items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <button
                        className={`record-text ${expanded === c.id ? 'expanded' : ''}`}
                        onClick={() => setExpanded(expanded === c.id ? null : c.id)}
                        aria-expanded={expanded === c.id}
                      >
                        {c.text}
                      </button>
                      {c.is_demo && <span className="demo-label">Fictional demo</span>}
                    </td>
                    <td>{c.category || 'Uncategorised'}</td>
                    <td>
                      {c.constituency || c.district || c.state}
                      <small>{c.state}</small>
                    </td>
                    <td>{date(c.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>
              Page {page} of {Math.max(1, Math.ceil(records.data.total / 8))}
            </span>
            <div>
              <button
                aria-label="Previous page"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft size={17} />
              </button>
              <button
                aria-label="Next page"
                disabled={page * 8 >= records.data.total}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight size={17} />
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  )
}

export function EmptyCTA() {
  return (
    <Link className="button primary" to="/raise">
      Raise a complaint <ArrowUpRight size={17} />
    </Link>
  )
}
