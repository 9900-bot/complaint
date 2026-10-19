# Civic Atlas — a modern civic atlas

## Concept
India's real administrative geometry becomes the organizing surface for shared public concerns. This is an instrument for reading place: an editorial atlas with a quiet intelligence workstation attached. No marketing hero, invented metrics, national emblems or decorative illustrations.

## Tokens and type
Ink #111C1E; warm ivory #F3F0E9; off-white #FAF8F3; viridian #286A63; copper #C8814F; slate #8D9E9A. Light text on ink must meet AA contrast. Copper is an accent and map intensity endpoint, not small text on white. Strong viridian for links on ivory. Map boundary lines are muted green; nonzero regions use a sequential green-to-copper ramp and empty regions remain distinct. Radius 2–6px for controls; no rounded panel stacks. Spacing base 4px, main gutters 40px desktop / 20px mobile. Thin separators express hierarchy.

Newsreader for major editorial headings (40–64px) and emphasized metrics; IBM Plex Sans for body (14–16px), controls (13–14px), table data and captions (12px minimum). Local font packages avoid runtime web dependencies. Numeric values use tabular numerals. Long place names wrap; complaint prose is never forced into tiny type.

## Three compositions / focal points
1. Atlas: compact masthead with a cartographic wordmark; editorial title and concise geographic context; integrated filter row; a large dark MapLibre surface taking most of the viewport. A narrow ivory reading panel sits alongside, with selected region totals, category distribution and recent reports. Map mode switch, restrained legend, scale and accessible region selectors. On mobile the reading panel follows a 480px map instead of obscuring it. Focal point is always real India geometry.
2. Raise complaint: large welcoming heading and concise privacy explanation; three numbered sections separated by rules. Email, location with compact map and manual coordinates, then comfortable complaint prose. A quiet side column explains approximate public display and geographic coverage. Confirmation replaces form, shows a reference and navigation. Focal point is the text field and submit action.
3. Analytics: title with data timestamp; synchronized filters; typographic metric strip, no tiles. A wide trend chart shares a row with category distribution; geographic rankings and category exploration have distinct visual weights. Paginated complaint table below. Focal point is trend and category evidence, not decoration.

## Interaction and accessibility
Exactly three routes. Visible focus, skip link, labeled native controls, 44px mobile targets. Native selects provide keyboard alternatives to map clicks. Search narrows generated categories. Query parameters preserve filters. Data requests show loading, errors with retry, and truthful empty states. Geolocation denied offers manual map/coordinate adjustment. Submitted content is rendered as React text, never HTML. Motion is limited to map transitions and control feedback, with reduced-motion respected. Hover labels never carry the only access to information.

## Prebuild critique
Avoid equal chart cards and overboxed metrics. Keep the map as hero even with an empty database. Zero counts are honest; demo is explicitly fictional. Regional boundaries provide visual substance without fake points. Controls must not hide the northeast or island territories. Dashboard charts use zero baselines and readable date labels. Generated category labels may change, so identity always uses a stable cluster ID.

## Design references
Applied the installed frontend-design skill (derived from Anthropic). Reviewed [Impeccable](https://github.com/pbakaus/impeccable) for critique, spacing and anti-patterns and [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines) for keyboard, forms, feedback and responsive behavior. Their optional tooling is not a runtime dependency.

## Postbuild critique and verification
Completed a deliberate browser critique at 390/768/1440/1920. Retained the map as the focal surface and the dashboard's unequal chart/reading proportions. Fixed collapsed mobile search, overly close map framing after resizing, small reading-panel type, misleading empty legends, camera resets on refresh and oversized chart animation duration. Added actual geographic names in breadcrumbs, independent selector updates and accessible individual records. Ocean labels now appear only on the national overview, where they are geographically meaningful. The form retains its numbered editorial rhythm on mobile; the reading aside follows the main form. See VERIFICATION.md and local screenshots for the executed checks and limits.
