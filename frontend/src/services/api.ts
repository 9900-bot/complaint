import { useEffect, useState } from 'react'

export type Filters = {
  state_id?: string
  district_id?: string
  constituency_id?: string
  cluster_id?: string
  date_from?: string
  date_to?: string
}
export type Region = {
  id: string
  name: string
  region_type: string
  parent_region_id: string | null
  dataset_version: string
}
export type Category = {
  id: string | null
  label: string
  count: number
  share: number
  growth: number
  new: boolean
  representative_text?: string
}
export type Complaint = {
  id: string
  text: string
  created_at: string
  category_id: string | null
  category: string | null
  state: string
  district: string | null
  constituency: string | null
  is_demo: boolean
}
export type ComplaintPage = { items: Complaint[]; total: number; page: number; page_size: number }
export type Overview = {
  total: number
  total_all_dates: number
  active_clusters: number
  states: number
  top_category: string | null
  latest_submission: string | null
  demo_count: number
}
export type GeographicCount = { id: string; name: string; count: number; top_category?: string }
export type Timeline = { date: string; count: number; categories: Record<string, number> }
export type Resolution = {
  state: Region | null
  district: Region | null
  constituency: Region | null
  coverage_note: string
}
export type Config = {
  complaint_max_length: number
  geography_available: boolean
  boundary_vintage: string
  public_grid_degrees: number
}

export function query(values: Record<string, string | number | undefined>) {
  const p = new URLSearchParams()
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined && v !== '') p.set(k, String(v))
  })
  return p.toString()
}

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail =
      typeof body.detail === 'string'
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((d: { msg: string }) => d.msg).join(' ')
          : 'The local service is unavailable. Start the backend and try again.'
    throw new Error(detail)
  }
  return response.json()
}

export function useApi<T>(path: string | null, poll = false) {
  const [state, setState] = useState<{ data?: T; error?: string; loading: boolean }>({
    loading: true,
  })
  const [version, retry] = useState(0)
  useEffect(() => {
    if (!path) {
      setState({ loading: false })
      return
    }
    const controller = new AbortController()
    setState({ loading: true })
    const load = () =>
      api<T>(path, { signal: controller.signal })
        .then((data) => setState({ data, loading: false }))
        .catch((e) => {
          if (e.name !== 'AbortError') setState({ error: e.message, loading: false })
        })
    void load()
    const timer = poll ? setInterval(load, 15000) : undefined
    return () => {
      controller.abort()
      clearInterval(timer)
    }
  }, [path, version, poll])
  return { ...state, retry: () => retry((v) => v + 1) }
}

export const number = (value: number) => new Intl.NumberFormat('en-IN').format(value)
export const date = (value: string, short = false) =>
  new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    ...(short ? {} : { year: 'numeric' }),
    timeZone: 'Asia/Kolkata',
  }).format(new Date(value.endsWith('Z') || value.length === 10 ? value : value + 'Z'))
