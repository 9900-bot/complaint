import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, LocateFixed, Check, ShieldCheck, MapPin } from 'lucide-react'
import { AtlasMap } from '../components/AtlasMap'
import { api, useApi, query } from '../services/api'
import type { Resolution, Config } from '../services/api'

export default function Raise() {
  const [email, setEmail] = useState(''),
    [text, setText] = useState(''),
    [latitude, setLatitude] = useState(''),
    [longitude, setLongitude] = useState('')
  const [locating, setLocating] = useState(false),
    [locationMessage, setLocationMessage] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [reference, setReference] = useState('')
  const config = useApi<Config>('config')
  const max = config.data?.complaint_max_length || 3000
  const validCoordinates =
    latitude !== '' &&
    longitude !== '' &&
    Number.isFinite(Number(latitude)) &&
    Number.isFinite(Number(longitude)) &&
    Math.abs(Number(latitude)) <= 90 &&
    Math.abs(Number(longitude)) <= 180
  const [resolved, setResolved] = useState<Resolution | null>(null)
  const [resolving, setResolving] = useState(false)
  const position = useMemo<[number, number] | undefined>(
    () => (validCoordinates ? [Number(longitude), Number(latitude)] : undefined),
    [validCoordinates, longitude, latitude],
  )
  useEffect(() => {
    setResolved(null)
    if (!validCoordinates) return
    const controller = new AbortController()
    setResolving(true)
    const timer = setTimeout(() => {
      api<Resolution>(`geography/resolve?${query({ latitude, longitude })}`, {
        signal: controller.signal,
      })
        .then(setResolved)
        .catch((e) => {
          if (e.name !== 'AbortError') setLocationMessage(e.message)
        })
        .finally(() => {
          if (!controller.signal.aborted) setResolving(false)
        })
    }, 300)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [validCoordinates, latitude, longitude])
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!reference && (email || text)) {
        event.preventDefault()
        event.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [email, text, reference])
  const pick = (lat: number, lng: number) => {
    setLatitude(lat.toFixed(6))
    setLongitude(lng.toFixed(6))
    setLocationMessage('Pin selected. Drag it or tap the map to adjust.')
  }
  const locate = () => {
    setLocationMessage('')
    if (!navigator.geolocation) {
      setLocationMessage(
        'Location is unavailable in this browser. Select a place on the map or enter coordinates.',
      )
      return
    }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (p) => {
        pick(p.coords.latitude, p.coords.longitude)
        setLocating(false)
      },
      () => {
        setLocating(false)
        setLocationMessage(
          'Location access was denied or unavailable. Tap the map or enter coordinates below.',
        )
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (!validCoordinates || !resolved?.state) {
      setError('Choose a location inside the supported Indian boundary coverage.')
      document.getElementById('latitude')?.focus()
      return
    }
    setBusy(true)
    try {
      const result = await api<{ reference_id: string }>('complaints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          text,
          latitude: Number(latitude),
          longitude: Number(longitude),
        }),
      })
      setReference(result.reference_id)
      window.scrollTo({ top: 0, behavior: 'instant' })
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  if (reference)
    return (
      <main id="main" className="confirmation">
        <span className="confirmation-mark">
          <Check size={34} />
        </span>
        <p className="eyebrow">Your voice is part of the picture</p>
        <h1>
          Recorded. And counted<span className="copper">.</span>
        </h1>
        <p>Your complaint has been saved. Thank you for making a shared concern visible.</p>
        <div className="reference">
          <span className="section-label">Your reference</span>
          <strong>{reference}</strong>
          <small>Keep this reference for your records.</small>
        </div>
        <div className="confirmation-actions">
          <Link className="button primary" to="/">
            Back to the atlas <ArrowUpRight size={17} />
          </Link>
          <button
            className="button secondary"
            onClick={() => {
              setReference('')
              setText('')
            }}
          >
            Raise another complaint
          </button>
        </div>
      </main>
    )
  return (
    <main id="main" className="raise-page">
      <div className="page-intro">
        <div>
          <p className="eyebrow">Make a local concern visible</p>
          <h1>
            Your place. Your voice<span className="copper">.</span>
          </h1>
          <p className="intro-copy">
            Tell us what needs attention. No account, no complicated process.
          </p>
        </div>
        <span className="quiet-label">A few minutes is all it takes.</span>
      </div>
      <div className="form-layout">
        <form onSubmit={submit}>
          <section className="form-section">
            <div className="form-heading">
              <span>01</span>
              <div>
                <h2>A way to identify your report.</h2>
                <p>Your email stays private. No verification required.</p>
              </div>
            </div>
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              autoComplete="email"
              type="email"
              maxLength={254}
              spellCheck={false}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com…"
            />
          </section>
          <section className="form-section">
            <div className="form-heading">
              <span>02</span>
              <div>
                <h2>Where is this happening?</h2>
                <p>Choose the place your complaint is about.</p>
              </div>
            </div>
            <button
              type="button"
              className="button location-button"
              onClick={locate}
              disabled={locating}
            >
              <LocateFixed size={17} />
              {locating ? 'Finding your location…' : 'Get my location'}
            </button>
            <span className="location-hint">or tap the map to place a pin</span>
            <div className="location-status" aria-live="polite">
              {locationMessage}
            </div>
            <AtlasMap picker onPick={pick} location={position} />
            <div className="coordinate-fields">
              <label htmlFor="latitude">
                Latitude
                <input
                  id="latitude"
                  name="latitude"
                  type="number"
                  inputMode="decimal"
                  step="any"
                  min="-90"
                  max="90"
                  required
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="e.g. 12.97…"
                />
              </label>
              <label htmlFor="longitude">
                Longitude
                <input
                  id="longitude"
                  name="longitude"
                  type="number"
                  inputMode="decimal"
                  step="any"
                  min="-180"
                  max="180"
                  required
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="e.g. 77.59…"
                />
              </label>
            </div>
            <div className="resolved-area" aria-live="polite">
              <MapPin size={16} />
              <span>
                {resolving
                  ? 'Checking the selected area…'
                  : resolved?.state
                    ? [
                        resolved.constituency?.name || 'Constituency unknown',
                        resolved.district?.name,
                        resolved.state.name,
                      ]
                        .filter(Boolean)
                        .join(' · ')
                    : validCoordinates
                      ? 'Outside supported coverage. Adjust your location.'
                      : 'Select a location to identify the area.'}
              </span>
            </div>
          </section>
          <section className="form-section">
            <div className="form-heading">
              <span>03</span>
              <div>
                <h2>Tell us what needs attention.</h2>
                <p>
                  Describe the issue in your own words. Related concerns are grouped automatically.
                </p>
              </div>
            </div>
            <label htmlFor="complaint">Your complaint</label>
            <textarea
              id="complaint"
              name="complaint"
              minLength={10}
              maxLength={max}
              rows={7}
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
              placeholder="What is happening, and how is it affecting your area?…"
            />
            <div className="textarea-note">
              <span>Please keep personal contact details out of your complaint.</span>
              <span>
                {text.length} / {max}
              </span>
            </div>
          </section>
          {error && (
            <div className="feedback error" role="alert">
              {error}
            </div>
          )}
          <div className="submit-row">
            <p>Your complaint text and approximate area will be public.</p>
            <button className="button primary" type="submit" disabled={busy}>
              {busy ? 'Recording your complaint…' : 'Submit complaint'}
              <ArrowUpRight size={17} />
            </button>
          </div>
        </form>
        <aside className="form-aside">
          <ShieldCheck size={25} />
          <h3>
            A public concern.
            <br />A private email.
          </h3>
          <p>
            Only your complaint and approximate area appear on the atlas. Your email and precise
            location stay private.
          </p>
          <div className="aside-note">
            <span className="section-label">A note on geography</span>
            <p>
              The atlas uses historical Indian boundaries. Some constituency names or boundaries may
              have changed. A report can still be recorded when its constituency is unknown.
            </p>
          </div>
          <div className="aside-note">
            <span className="section-label">Shared understanding</span>
            <p>
              Reports help reveal patterns across places. This platform records concerns; it does
              not track their resolution.
            </p>
          </div>
        </aside>
      </div>
    </main>
  )
}
