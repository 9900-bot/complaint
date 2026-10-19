import { NavLink, Route, Routes, Link } from 'react-router-dom'
import { ArrowUpRight, Globe2 } from 'lucide-react'
import Atlas from './pages/Atlas'
import Raise from './pages/Raise'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="masthead">
        <Link className="brand" to="/" aria-label="Civic Atlas home">
          <Globe2 size={30} strokeWidth={1.3} />
          <span>
            Civic Atlas<small>INDIA COMPLAINT INTELLIGENCE</small>
          </span>
        </Link>
        <nav aria-label="Main navigation">
          <NavLink to="/" end>
            Explore the atlas
          </NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
          <NavLink to="/raise" className="nav-raise">
            Raise a complaint <ArrowUpRight size={14} />
          </NavLink>
        </nav>
        <span className="edition">
          A LOCAL PERSPECTIVE
          <br />
          <strong>INDIA / 01</strong>
        </span>
      </header>
      <Routes>
        <Route path="/" element={<Atlas />} />
        <Route path="/raise" element={<Raise />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route
          path="*"
          element={
            <main id="main" className="confirmation">
              <h1>This place isn’t on the atlas.</h1>
              <Link className="button primary" to="/">
                Return to India <ArrowUpRight size={16} />
              </Link>
            </main>
          }
        />
      </Routes>
      <footer>
        <Link className="footer-brand" to="/">
          Civic Atlas<span>Local voices. Shared understanding.</span>
        </Link>
        <p>Built for a clearer picture of the places we call home.</p>
        <a href="https://projects.datameet.org/maps/" target="_blank" rel="noreferrer">
          Boundaries by DataMeet ↗<small>Historical geography · CC BY 2.5 India / 4.0</small>
        </a>
      </footer>
    </>
  )
}
