import { beforeEach, expect, test, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import Raise from '../pages/Raise'
import Atlas from '../pages/Atlas'
import { FilterBar, useFilters } from '../components/Shared'

vi.mock('../components/AtlasMap', () => ({
  AtlasMap: ({
    onPick,
    onRegion,
    level,
    mode,
  }: {
    onPick?: (lat: number, lng: number) => void
    onRegion?: (id: string, level: string) => void
    level?: string
    mode?: string
  }) => (
    <div>
      <span>Map mode: {mode}</span>
      <button type="button" onClick={() => onPick?.(12.9716, 77.5946)}>
        Choose test location
      </button>
      <button type="button" onClick={() => onRegion?.('state:1', level || 'state')}>
        Select map region
      </button>
    </div>
  ),
}))
const state = {
  id: 'state:1',
  name: 'Karnataka',
  region_type: 'state',
  parent_region_id: null,
  dataset_version: 'test',
}
let fail = false
let stress = false
const fetchMock = vi.fn(async (input: string, options?: RequestInit) => {
  const url = String(input)
  let data: unknown = []
  if (url.includes('/config')) data = { complaint_max_length: 3000, geography_available: true }
  else if (url.includes('/resolve')) data = { state, district: null, constituency: null }
  else if (url.includes('/states')) data = [state]
  else if (url.includes('/districts')) data = [{ id: 'd1', name: 'Bengaluru Urban' }]
  else if (url.includes('/constituencies')) data = [{ id: 'a1', name: 'Shivajinagar' }]
  else if (url.includes('/clusters') || url.includes('analytics/categories'))
    data = [{ id: 'c1', label: 'Broken Streetlights', count: 3, share: 100 }]
  else if (url.includes('/overview'))
    data = stress
      ? { total: 123456789, active_clusters: 75, states: 36 }
      : { total: 0, active_clusters: 0, states: 0 }
  else if (url.includes('/complaints'))
    data =
      options?.method === 'POST' ? { reference_id: 'test-reference-123' } : { items: [], total: 0 }
  return {
    ok: !fail,
    status: fail ? 503 : 200,
    json: async () => (fail ? { detail: 'Local service unavailable' } : data),
  } as Response
})
function URLState() {
  const location = useLocation()
  return <output aria-label="Current filters">{location.search}</output>
}
function FilterHarness() {
  const { filters, update } = useFilters()
  return (
    <>
      <FilterBar filters={filters} update={update} dates />
      <URLState />
    </>
  )
}
function wrapper(element: React.ReactNode) {
  return render(
    <MemoryRouter>
      {element}
      <URLState />
    </MemoryRouter>,
  )
}
beforeEach(() => {
  fail = false
  stress = false
  fetchMock.mockClear()
  vi.stubGlobal('fetch', fetchMock)
  window.scrollTo = vi.fn()
})

test('submission persists text and private input, then displays a reference without ML status', async () => {
  wrapper(<Raise />)
  fireEvent.change(screen.getByLabelText('Email address'), {
    target: { value: 'test@example.com' },
  })
  fireEvent.click(screen.getByText('Choose test location'))
  await screen.findByText(/Constituency unknown/)
  fireEvent.change(screen.getByLabelText('Your complaint'), {
    target: { value: 'The streetlights have stopped working on our residential road.' },
  })
  fireEvent.click(screen.getByRole('button', { name: /Submit complaint/ }))
  expect(await screen.findByText('test-reference-123')).toBeVisible()
  const request = fetchMock.mock.calls.find(([, options]) => options?.method === 'POST')!
  expect(JSON.parse(request[1]!.body as string)).toMatchObject({
    email: 'test@example.com',
    latitude: 12.9716,
    longitude: 77.5946,
  })
  expect(screen.queryByText(/processing|pending|cluster assignment/i)).not.toBeInTheDocument()
})

test('location denial offers manual adjustment', async () => {
  Object.defineProperty(navigator, 'geolocation', {
    configurable: true,
    value: { getCurrentPosition: (_: unknown, error: () => void) => error() },
  })
  wrapper(<Raise />)
  fireEvent.click(screen.getByRole('button', { name: /Get my location/ }))
  expect(await screen.findByText(/Location access was denied/)).toBeVisible()
  fireEvent.change(screen.getByLabelText('Latitude'), { target: { value: '12.9716' } })
  fireEvent.change(screen.getByLabelText('Longitude'), { target: { value: '77.5946' } })
  expect(await screen.findByText(/Constituency unknown/)).toBeVisible()
})

test('submission refuses an unresolved location', async () => {
  wrapper(<Raise />)
  fireEvent.submit(screen.getByRole('button', { name: /Submit complaint/ }).closest('form')!)
  expect(await screen.findByRole('alert')).toHaveTextContent('Choose a location')
  expect(fetchMock.mock.calls.some(([, o]) => o?.method === 'POST')).toBe(false)
})

test('three map modes and geographic drill-down update the URL', async () => {
  wrapper(<Atlas />)
  await screen.findByRole('option', { name: 'Karnataka' })
  fireEvent.click(screen.getByRole('button', { name: 'Heatmap' }))
  expect(screen.getByRole('button', { name: 'Heatmap' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByLabelText('Current filters')).toHaveTextContent('mode=heatmap')
  fireEvent.click(screen.getByRole('button', { name: 'Individual' }))
  expect(screen.getByText('Map mode: individual')).toBeVisible()
  fireEvent.click(screen.getByText('Select map region'))
  expect(screen.getByLabelText('Current filters')).toHaveTextContent('state_id=state%3A1')
  expect(screen.getByLabelText('Boundary layer')).toHaveValue('district')
})

test('geographic and category filters combine with dates and reset', async () => {
  render(
    <MemoryRouter>
      <FilterHarness />
    </MemoryRouter>,
  )
  await screen.findByRole('option', { name: 'Karnataka' })
  fireEvent.change(screen.getByLabelText('State / UT'), { target: { value: 'state:1' } })
  await screen.findByRole('option', { name: 'Bengaluru Urban' })
  fireEvent.change(screen.getByLabelText('District', { exact: true }), { target: { value: 'd1' } })
  fireEvent.change(screen.getByLabelText('Semantic category'), { target: { value: 'c1' } })
  fireEvent.change(screen.getByLabelText('From date'), { target: { value: '2026-10-01' } })
  expect(screen.getByLabelText('Current filters')).toHaveTextContent('district_id=d1')
  expect(screen.getByLabelText('Current filters')).toHaveTextContent('cluster_id=c1')
  expect(screen.getByLabelText('Current filters')).toHaveTextContent('date_from=2026-10-01')
  fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }))
  expect(screen.getByLabelText('Current filters')).toBeEmptyDOMElement()
  expect(screen.getByLabelText('Semantic category')).toHaveValue('')
})

test('empty data is readable and API errors offer retry', async () => {
  wrapper(<Atlas />)
  expect(await screen.findByText('No reports here yet. Your voice can be the first.')).toBeVisible()
  fail = true
  fireEvent.change(screen.getByLabelText('State / UT'), { target: { value: 'state:1' } })
  await waitFor(() =>
    expect(screen.getAllByText('Local service unavailable').length).toBeGreaterThan(0),
  )
  expect(screen.getAllByRole('button', { name: /Try again/ }).length).toBeGreaterThan(0)
})

test('large totals retain Indian numeric formatting and long complaint input has a real limit', async () => {
  stress = true
  const mounted = wrapper(<Atlas />)
  expect(await screen.findByText('12,34,56,789')).toBeVisible()
  mounted.unmount()
  wrapper(<Raise />)
  const prose = 'The public footbridge has damaged railings and loose planks. '
    .repeat(60)
    .slice(0, 3000)
  fireEvent.change(screen.getByLabelText('Your complaint'), { target: { value: prose } })
  expect(screen.getByLabelText('Your complaint')).toHaveAttribute('maxlength', '3000')
  expect(screen.getByLabelText('Your complaint')).toHaveValue(prose)
})
