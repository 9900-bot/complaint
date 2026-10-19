# Build a Premium India Complaint Intelligence Platform

## Role

Act as a Senior Full-Stack Engineer, Machine Learning Engineer, Geospatial Engineer, and Principal Product Designer.

Build a fully functional, visually exceptional complaint reporting and analytics website for India.

The website must combine:

1. Public complaint submission.
2. Automatic semantic clustering using bi-encoder embeddings.
3. Cross-encoder-based merging of similar clusters.
4. A highly interactive, detailed map of India.
5. A comprehensive analytics dashboard.

**The application must be functional, not a mockup. Visual quality is a first-class requirement, not something to address only after implementation.**

---

# 1. Project Scope and Constraints

This is an initial local implementation.

### Requirements

- Expected concurrent users: 1–2.
- Run entirely on localhost.
- No login or authentication.
- No email verification.
- No Docker.
- No Redis.
- No Celery.
- No Kubernetes.
- No cloud infrastructure.
- No paid AI APIs.
- SQLite is the database.
- ML models run locally.
- Only text complaints are supported.

### Important architecture principle

Keep the implementation simple for current needs while preserving clear boundaries for future scalability.

Do not build enterprise infrastructure prematurely.

However, avoid tightly coupling database queries, ML execution, and business logic.

Later phases may replace:

| Current | Future |
|---|---|
| SQLite | PostgreSQL |
| NumPy vector similarity | pgvector / vector database |
| Shapely spatial queries | PostGIS |
| In-process job processor | Celery + Redis |
| Local backend | Hosted deployment |

The future replacements should not require rewriting the entire application.

Use interfaces and separate services where they meaningfully support this migration. Do not overengineer abstract interfaces for every component.

---

# 2. Technology Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui selectively for accessible primitives
- MapLibre GL JS
- Recharts, Visx, or carefully selected charting components
- Lucide icons where appropriate
- Motion for React only where animation improves the experience

Do not let the default appearance of shadcn/ui determine the visual design.

## Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- SQLite

## Machine Learning

- sentence-transformers
- PyTorch
- NumPy
- Scikit-learn where appropriate

Use locally runnable, openly available bi-encoder and cross-encoder models.

Select suitable lightweight models and document the choices.

Do not implement translation.

Prefer models that can process the original language of submissions where supported, but do not claim multilingual support without testing it.

## Geography

- MapLibre GL JS for frontend visualization
- GeoJSON geographic boundary datasets
- Shapely for spatial operations
- STRtree or equivalent spatial indexing

Use real India boundary datasets with source and version documentation.

---

# 3. Mandatory Design Skills and Visual Quality

**This project must look like a professionally designed, premium data-intelligence application.**

The design should be memorable, aesthetically cohesive, and unlike common AI-generated SaaS dashboards.

Use the principles from these design resources:

### Skill A — Anthropic Frontend Design

https://github.com/anthropics/skills/tree/main/skills/frontend-design

Apply:
- Strong, deliberate art direction.
- Distinctive typography and visual hierarchy.
- Non-generic spatial compositions.
- Purposeful use of negative space.
- Subject-specific visual identity.
- Restraint in decorative effects.
- Carefully orchestrated motion.
- Design planning before implementation.

### Skill B — Impeccable

https://github.com/pbakaus/impeccable

Apply:
- Visual critique and refinement.
- Typography and spacing discipline.
- Reduction of visual clutter.
- Accessible contrast.
- Consistent tokens and component styling.
- Responsive adaptation.
- Removal of generic AI-interface patterns.

### Skill C — Vercel Web Interface Guidelines

https://github.com/vercel-labs/web-interface-guidelines

Apply:
- Accessible interactions.
- Keyboard navigation.
- Correct loading and error states.
- Clear interaction feedback.
- Stable layouts.
- Responsive design.
- Proper mobile touch targets.
- Readable and accessible data visualizations.

If these skills are installed in the coding environment, use them directly.

Otherwise, follow their relevant published principles. Do not block implementation merely because an optional skill is unavailable.

## 3.1 Required Art Direction

Use the design concept:

**"A Modern Civic Atlas — Editorial Cartography Meets Premium Data Intelligence."**

Visual references should draw from:
- Editorial data journalism.
- Premium geographic atlases.
- Institutional data visualization.
- Refined architectural and information design.
- Sophisticated financial and intelligence dashboards.

The experience should communicate precision, credibility, and clarity.

It must not feel like a government form built in 2012 or a generic 2025 AI dashboard.

## 3.2 Color System

Start with this palette, then refine it if justified.

- Deep Ink: `#111C1E`
- Warm Ivory: `#F3F0E9`
- Viridian: `#286A63`
- Burnished Copper: `#C8814F`
- Muted Slate: `#8D9E9A`
- Off-White: `#FAF8F3`

Use these as a considered design system, not six equally prominent colors.

Suggested direction:

- Dark, atmospheric map surfaces.
- Warm neutral reading surfaces.
- Restrained copper accents.
- Muted geographic boundaries.
- Precise, easily distinguishable heatmap colors.

Use CSS custom properties for design tokens.

Avoid cliché tricolor branding or decorative national symbols.

## 3.3 Typography

Use an intentional type pairing.

Suggested:
- Newsreader for editorial headings and major display text.
- IBM Plex Sans for controls, data, charts, and body text.

Choose another pairing only if it better supports the design.

Create a consistent typography scale.

Pay attention to:
- Tracking
- Weight
- Baseline alignment
- Numerical formatting
- Readability
- Text wrapping
- Responsive type scaling

Data-heavy interfaces should use tabular numerals where appropriate.

## 3.4 Forbidden Visual Patterns

Do not use:

- Purple-to-blue gradients.
- Generic glowing backgrounds.
- Floating glassmorphism everywhere.
- Large rounded cards for every piece of information.
- Cards nested inside more cards.
- Decorative icon tiles above headings.
- Random gradient blobs.
- Unnecessary floating particles.
- Generic AI-generated hero illustrations.
- Emoji icons.
- Excessive drop shadows.
- Uniform three-column SaaS feature grids.
- Repeated section entrance animations.
- Arbitrary illustrations unrelated to complaints or geography.
- Excessive badges and decorative labels.

A card should exist because it creates a meaningful information boundary, not because the content needs a container.

Prefer typography, spacing, alignment, fine dividers, and visual hierarchy over boxing everything.

## 3.5 Motion and Interactions

Implement subtle, high-quality interactions:

- Smooth map zoom and geographic transitions.
- Refined filter transitions.
- Responsive hover feedback on geographic regions.
- Smooth panel expansion.
- Animated chart updates when filters change.
- Clear submission confirmation.
- Subtle button press feedback.

Use motion primarily to explain state changes.

Avoid exaggerated bounces, endless ambient animations, or effects that degrade performance.

Respect reduced-motion preferences.

## 3.6 Design Process

Before frontend implementation:

1. Define the visual concept and design tokens.
2. Sketch the layout of each page.
3. Determine typography, spacing, and information hierarchy.
4. Identify the primary focal element on each page.
5. Critique the proposed design for generic patterns.
6. Refine the design.
7. Build and review the actual interfaces.

Create a concise `DESIGN.md` documenting these decisions.

After implementation, inspect the rendered interface at desktop and mobile sizes using available browser or screenshot tools.

Fix visual problems before declaring the frontend complete.

If Impeccable is available, use its critique, audit, and polish workflows.

---

# 4. Frontend: Exactly Three Main Pages

The application has:

1. Landing Page / India Map
2. Raise Complaint
3. Analytics Dashboard

Use a shared, refined navigation system.

No login or account pages.

---

# 5. Page One — India Complaint Atlas

This is the flagship page.

It should immediately communicate the purpose and scale of the application.

## 5.1 Layout

The interactive India map must dominate the first viewport.

Suggested layout:

- Minimal, elegant navigation.
- Strong editorial heading.
- Large interactive map as the centerpiece.
- Compact, integrated geographic controls.
- A carefully designed information panel for selected regions.
- Minimal supplementary statistics.
- An accessible call to action for raising complaints.

Do not build a conventional marketing hero followed by a stack of feature cards.

The actual map is the hero.

## 5.2 Geographic Detail

Support geographic exploration of India.

Required layers:

- India overview.
- State / Union Territory boundaries.
- District boundaries.
- Assembly Constituency boundaries.
- Individual approximate complaint locations.

Provide constituency-level exploration.

Do not assume that every constituency is strictly nested within one district. Model district and constituency boundaries as independent geographic layers within the relevant state.

Use stable geographic identifiers.

## 5.3 Map Interaction

Users must be able to:

- Zoom and pan.
- Select a state.
- Focus on a district.
- View Assembly Constituencies.
- Select a constituency.
- Return to previous geographic levels.
- Filter by semantic category.
- Inspect complaint counts.
- View individual complaints.

Use smooth geographic transitions.

Selected regions should be clearly highlighted.

Avoid unnecessary overlays that obscure the map.

## 5.4 Map Modes

Provide three modes.

### Mode A: Heatmap

Show the geographic concentration of complaints.

Requirements:
- Aggregated complaint locations.
- Clear density color scale.
- Responsive to zoom.
- Respect selected geographic and category filters.
- Do not invent data for empty regions.

### Mode B: Region View

Color geographic regions according to complaint counts.

At different zoom levels, display meaningful state, district, or constituency aggregations.

Provide a legend and hover details.

### Mode C: Individual View

Show approximate complaint points.

Selecting one should display:
- Complaint text.
- Automatically generated semantic category.
- Submission date.
- Approximate area.

Never expose private email addresses or exact coordinates.

Use clustering of visible map markers where appropriate to avoid clutter.

## 5.5 Geographic Data

Find an appropriate, reliable geographic dataset.

Important:
- Verify the dataset source.
- Check permitted usage and attribution.
- Validate geographic boundary coverage.
- Document data vintage and limitations.
- Do not create fake constituency polygons.
- Do not silently substitute Parliamentary Constituencies for Assembly Constituencies.

Prepare an import script that reads the selected data and builds the necessary SQLite region metadata and local spatial indexes.

Store geographic boundary data as local assets where appropriate.

Use Shapely for point-in-polygon resolution.

Optimize boundary files for frontend use through simplification or tiled data when appropriate.

Do not require paid map APIs.

An internet-served development basemap is acceptable if its usage policy permits the expected usage. Document if internet access is required for basemap tiles.

## 5.6 Interactive Category Filtering

Categories are generated automatically by the semantic clustering pipeline.

Provide:
- All categories.
- Searchable category selection.
- Complaint count for each category.
- Individual category filtering.
- Clear filter reset.

Selecting a category should update the map and related statistics.

Geographic filtering and semantic categories must be independent.

---

# 6. Page Two — Raise Complaint

Create a beautifully designed, minimal complaint-submission experience.

This page should feel simple and welcoming, not like a complicated administrative form.

## Layout

Use a restrained editorial form layout with three clearly separated sections.

### A. Email

- Required.
- Basic email-format validation.
- No verification.
- No OTP.
- No accounts.

### B. Location

Provide a prominent "Get My Location" action.

Use browser geolocation after requesting permission.

Show the selected location on a compact interactive map.

Allow manual adjustment if geolocation is denied or incorrect.

Capture precise coordinates privately for geographic resolution.

Use backend spatial logic to determine:
- State.
- District.
- Assembly Constituency.

Reject locations outside the supported Indian geographic coverage with a clear explanation.

If constituency data is missing for an otherwise valid Indian location, allow submission with an unknown constituency.

### C. Complaint Text

Provide a comfortable, large text input.

- Text only.
- Required.
- Configurable length limit.
- No predefined category selection.
- No media uploads.

### Submission Experience

On submission:

1. Validate inputs.
2. Save the complaint.
3. Schedule semantic processing.
4. Return a generated reference ID.
5. Display a refined confirmation state.

Do not block the HTTP response while the complete ML pipeline runs.

No query status page is needed.

No resolution tracking.

The frontend should never expose internal ML processing metadata as a user-facing complaint status system.

---

# 7. Page Three — Analytics Dashboard

The dashboard should feel like a premium intelligence workstation.

It must not resemble a collection of generic Recharts cards.

## 7.1 Dashboard Layout

Use purposeful information density.

Suggested hierarchy:

1. High-level metrics integrated into a compact overview.
2. A primary complaint-trend visualization.
3. Category distribution analysis.
4. Geographic concentration analysis.
5. Cluster exploration.
6. Detailed complaint records.

Avoid giving every chart identical dimensions and visual weight.

Some information should be full-width, some should be compact, and some should be displayed through tables or editorial-style panels.

## 7.2 Overview Metrics

Show:
- Total complaints.
- Number of active semantic clusters.
- Complaints in selected date range.
- States with complaints.
- Most common category.
- Latest submission activity.

Use clear typography and restrained numeric formatting.

## 7.3 Category Analytics

Display:
- Largest complaint categories.
- Percentage distribution.
- Complaints per category.
- Category growth.
- Newly emerging categories.
- Category trends over time.

Allow selecting a category to inspect:
- Representative complaint.
- Individual complaints.
- Geographic distribution.
- Timeline.
- Total complaint count.

## 7.4 Geographic Analytics

Provide:
- Complaints by state.
- Complaints by district.
- Complaints by Assembly Constituency.
- Top complaint categories within selected regions.
- Geographic distribution for a selected category.

## 7.5 Time-Based Analytics

Display:
- Daily complaints.
- Weekly complaints.
- Changes over the selected period.
- Category activity over time.

Use readable axes, appropriate time formatting, meaningful chart scales, and contextual legends.

## 7.6 Filters

Support:
- Date range.
- State.
- District.
- Constituency.
- Semantic category.

Filters must combine correctly and be reflected consistently across analytics.

## 7.7 Visual Standards

Use:
- Refined data typography.
- Thin, subtle separators.
- Consistent spacing.
- Excellent chart labeling.
- Accessible color palettes.
- Sophisticated, restrained interaction feedback.
- Clear empty states.
- Responsive layouts.

Never sacrifice accurate data interpretation merely to make charts visually dramatic.

---

# 8. Core Machine Learning Architecture

This is the most important backend requirement.

There are TWO semantic stages:

1. Bi-encoder clustering.
2. Cross-encoder cluster merging.

Keep the responsibilities separate.

## 8.1 Bi-Encoder — Initial Assignment

For every complaint:

1. Take the original text.
2. Apply minimal technical normalization.
3. Generate an embedding.
4. Load existing active cluster representations.
5. Compute cosine similarity.
6. Find the SINGLE closest cluster globally.
7. Compare its similarity with the membership threshold.
8. Assign the complaint or create a new cluster.

Use NumPy for exact cosine similarity.

For the current scale, loading active cluster vectors into memory and performing vectorized similarity calculations is sufficient.

Do not introduce a vector database.

For cluster assignment, return the exact global nearest cluster rather than using an approximate top-N shortlist.

### Threshold

Use a configurable initial assignment threshold.

The threshold must be evaluated on example pairs.

If the best similarity is at or above the configured threshold:
- Assign the complaint to that cluster.

Otherwise:
- Create a new cluster.

Make behavior at the threshold boundary explicit and test it.

### Cluster Representation

Each cluster maintains:
- ID.
- Label.
- Representative complaint text.
- Centroid vector.
- Number of complaints.
- Creation timestamp.
- Last updated timestamp.
- Active/inactive state.

Store embeddings in SQLite as consistently serialized float32 vectors, with dimension and model-version metadata.

Keep serialization behind a vector-store interface.

Maintain normalized vectors for cosine similarity.

Update the centroid whenever membership changes.

The centroid should represent all current member embeddings, not merely the latest complaint.

### Critical Rule

Geographic location must NEVER be part of the semantic embedding or grouping decision.

Two identical complaints from two different states should be eligible for the same cluster.

Two unrelated complaints from the same street should not automatically group together.

---

# 9. Cross-Encoder — Cluster Merging Only

The cross-encoder's responsibility is to compare existing clusters.

It must NOT replace the bi-encoder's initial assignment stage.

## Process

1. Obtain active clusters.
2. Compute similarity between cluster centroids.
3. Discover close cluster pairs.
4. Select promising candidate pairs.
5. Compare their representative complaint texts using the cross-encoder.
6. Calculate the cross-encoder score.
7. If the score is greater than 0.92, merge the clusters.
8. Otherwise leave them separate.

**Merge threshold: 0.92 by default, configurable.**

The 0.92 value is specific to the cross-encoder merge stage, not the initial bi-encoder cluster-assignment threshold.

Cross-encoder model outputs may be raw logits or model-specific relevance scores.

Choose an explicit transformation or scoring convention that supports the configured threshold, and document its limitations.

Do not describe a transformed score as a calibrated probability unless it has actually been calibrated.

## Important Behavior

Bi-encoder cosine similarity identifies candidate cluster pairs.

Cross-encoder scoring decides whether they should merge.

Do not use the cross-encoder to compare every complaint against all existing complaints.

Avoid exhaustive pairwise cross-encoder inference.

A small shortlist is allowed for MERGE CANDIDATE DISCOVERY, even though initial complaint assignment uses the single exact nearest cluster.

Use multiple representative complaints for ambiguous merge candidates when needed to reduce false merges.

## Merge Correctness

When merging:

- Keep one canonical cluster ID.
- Reassign member complaints.
- Recalculate centroid.
- Recalculate complaint count.
- Update representative text.
- Update category label if appropriate.
- Record merge history.
- Mark the merged-away cluster inactive.
- Prevent duplicate memberships.
- Ensure transaction safety.
- Ensure retries do not duplicate merges.

Do not blindly merge all clusters connected by one high-scoring pair without considering the risk of semantic drift.

If a newly merged cluster becomes close to additional clusters, reevaluate candidate merges using the updated representation.

Use bounded merge iterations to avoid infinite loops.

---

# 10. Automatically Generated Category Labels

Do not use a predefined list of government complaint categories.

The categories must be derived from cluster content.

Examples:
- Streetlight Failures
- Pothole Complaints
- Water Shortages
- Garbage Collection Issues
- Bus Service Delays

These are examples, not fixed labels.

Use deterministic or lightweight methods such as:
- Keyphrase extraction.
- TF-IDF.
- Representative complaint selection.
- Frequency-based phrase extraction.

No generative LLM is required.

Category naming must be a separate service.

A cluster ID, not its generated label, must be used as its identity.

Labels may be updated when clusters grow or merge.

---

# 11. SQLite Database Design

Use SQLAlchemy ORM and Alembic migrations.

Define at minimum:

## complaints

- id
- email
- original_text
- latitude
- longitude
- state_id
- district_id
- constituency_id
- cluster_id
- embedding
- embedding_model_version
- internal_processing_state
- created_at

The internal processing state exists for background-job reliability, not for public complaint tracking.

## clusters

- id
- label
- representative_text
- centroid_embedding
- embedding_model_version
- complaint_count
- active
- created_at
- updated_at

## cluster_merges

- id
- source_cluster_id
- target_cluster_id
- merge_score
- model_version
- merged_at

## geographic_regions

- id
- stable_code
- name
- region_type
- parent_region_id where applicable
- geometry reference
- dataset_version

Districts and Assembly Constituencies should be modeled so they can overlap without assuming strict parent-child containment between those two layers.

Add useful constraints and indexes.

Enable SQLite foreign-key enforcement.

Use WAL mode and configure a reasonable busy timeout.

Use short-lived database sessions.

Do not share SQLAlchemy sessions between threads.

---

# 12. Local Background Processing

Celery and Redis are explicitly out of scope.

Use a lightweight in-process background worker.

Suitable implementation:
- A single worker thread or equivalent simple task executor.
- Database-backed pending-work state.
- A single serialized semantic clustering processor.
- Controlled task retries.
- Error logging.

Requirements:

1. Complaint submission persists to SQLite first.
2. The API returns without waiting for ML inference.
3. The local worker performs embedding and clustering.
4. Cluster merge processing happens after assignment.
5. Failed processing can be retried.
6. Unfinished work is recoverable after restarting the application.

Use one application-server worker in this phase to avoid multiple independent in-process processors competing for the same clustering work.

Store the pending state durably in SQLite.

Avoid relying exclusively on an in-memory queue that loses all pending work on restart.

Ensure ML models load once per application process rather than once per complaint.

For initial implementation, process semantic updates sequentially to avoid concurrent cluster assignment races.

Do not add:
- Celery
- Redis
- RabbitMQ
- Kafka
- Distributed schedulers

Keep worker orchestration independent from clustering logic so a persistent external job queue can replace it later.

---

# 13. Geographic Processing

Use a local geographic service.

Its responsibilities:

- Load geographic boundary data.
- Build spatial indexes.
- Resolve coordinates to states.
- Resolve coordinates to districts.
- Resolve coordinates to Assembly Constituencies.
- Return appropriate polygons to the frontend.
- Aggregate complaint counts geographically.

Use Shapely and efficient spatial prefiltering.

Do not perform expensive nationwide geometry scans for every request if an indexed approach is available.

Preserve clear coordinate conventions.

Use a geographic coordinate reference system consistently and transform data when necessary.

Do not use string matching to determine constituency membership.

When a location matches multiple boundaries due to overlaps or inconsistent datasets, use deterministic documented rules and record ambiguous results rather than silently choosing an arbitrary constituency.

---

# 14. Public APIs

Implement clean REST endpoints.

## Complaints

POST /api/complaints

GET /api/complaints

## Clusters

GET /api/clusters

GET /api/clusters/{id}

GET /api/clusters/{id}/complaints

## Geography

GET /api/geography/states

GET /api/geography/districts

GET /api/geography/constituencies

GET /api/geography/resolve

GET /api/geography/boundaries

## Maps

GET /api/map/heatmap

GET /api/map/regions

GET /api/map/complaints

## Analytics

GET /api/analytics/overview

GET /api/analytics/categories

GET /api/analytics/geography

GET /api/analytics/timeline

GET /api/analytics/trends

Support appropriate:
- Filters.
- Pagination.
- Date ranges.
- Sorting.
- Geographic constraints.
- Map bounding boxes.

Do not expose private database fields accidentally by serializing ORM models directly.

Use explicit public response schemas.

---

# 15. Privacy and Technical Protection

The application is public.

However:
- Never expose submitted email addresses publicly.
- Never expose exact submitted GPS coordinates.
- Show approximate or spatially aggregated public map positions.
- Prevent HTML/script injection.
- Validate submitted input.
- Add basic local rate limiting.
- Do not log unnecessary personal data.
- Store secrets or configurable private settings outside source code.
- Design all public endpoints to handle untrusted input.

Use stable spatial aggregation for public maps so repeated requests do not reveal private coordinates through changing random offsets.

Technical input validation and rate limiting are allowed.

Content moderation is out of scope.

---

# 16. Data Processing Workflow

Implement:

```text
Complaint Submission
        |
        v
FastAPI Validation
        |
        v
SQLite Persistence
        |
        v
Return Success Response
        |
        v
Local Background Worker
        |
        v
Bi-Encoder Embedding
        |
        v
Exact Cosine Similarity Search
        |
        v
Find Closest Cluster
        |
        +-- Above Membership Threshold
        |       |
        |       v
        |   Assign Existing Cluster
        |
        +-- Below Membership Threshold
                |
                v
            Create New Cluster
                |
                v
Update Cluster Representation
                |
                v
Discover Nearby Cluster Pairs
                |
                v
Cross-Encoder Comparison
                |
                v
        Score > 0.92?
          /         \
        Yes          No
         |            |
         v            v
    Merge Clusters   Preserve Clusters
         |
         v
Update Memberships & Aggregates
         |
         v
Public Map and Analytics APIs
         |
         v
React Frontend
```

The database must remain the source of truth.

Analytics should reflect committed changes.

Avoid double-counting complaints during cluster merges.

Allow unprocessed complaints to appear in applicable overall statistics, while clearly handling cases where a semantic category has not yet been assigned.

---

# 17. Testing

Create meaningful automated tests.

## ML Tests

- Correct embedding dimensions.
- Exact cosine nearest-cluster selection.
- Threshold boundary behavior.
- Creation of new clusters.
- Assignment to existing clusters.
- Cross-encoder merge decision.
- Rejection of unrelated merge candidates.
- Cluster centroid updates.
- Membership consistency.
- Merge idempotency.
- Stable canonical cluster IDs.
- Different geographic locations with the same semantic issue.

Use mocked embeddings and cross-encoder scores for deterministic tests.

Also provide a smaller integration test using the actual models.

## Backend Tests

- Complaint submission.
- Email validation.
- Coordinate validation.
- SQLite persistence.
- Geographic resolution.
- Filtering and pagination.
- Analytics correctness.
- Restart recovery of pending work.
- Protection of private email and coordinate fields.

## Frontend Tests

- Complaint submission form.
- Location permission denial.
- Map modes.
- Geographic drill-down.
- Semantic category filters.
- Dashboard filters.
- Empty and error states.

## Visual QA

Inspect:
- 1440px desktop.
- 1920px desktop.
- Tablet layout.
- 390px mobile layout.

Test with:
- Empty data.
- Sparse data.
- Many categories.
- Very long complaint text.
- Large numeric values.
- Long state and constituency names.

Use screenshot comparison or browser-based inspection where available.

---

# 18. Demo Dataset

Build an optional sample-data generator.

Create realistic, explicitly fictional demonstration complaints.

Include examples across multiple Indian locations.

Cover:
- Same issue, different phrasing.
- Same issue, different location.
- Different issue, same location.
- Near-duplicate complaints.
- Semantically ambiguous complaints.
- Several categories in one constituency.
- One category distributed across several states.

Run these submissions through the actual ML pipeline.

Do not manually assign category IDs to bypass clustering.

Demo data must be clearly identifiable and removable.

The application must also operate correctly with an empty database.

---

# 19. Repository Structure

Use a straightforward monorepo.

```text
complaint-platform/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── map/
│   │   │   ├── complaints/
│   │   │   └── analytics/
│   │   ├── services/
│   │   ├── styles/
│   │   └── App.tsx
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ml/
│   │   ├── geography/
│   │   ├── database/
│   │   ├── workers/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   └── geography/
│
├── scripts/
├── DESIGN.md
├── README.md
└── .gitignore
```

Avoid unnecessary folder proliferation or excessive abstractions.

Do not create Docker files.

Keep generated model caches, SQLite databases, and private configuration out of version control.

---

# 20. Implementation Tasks

Implement sequentially.

### Task 1 — Project Foundation

- Create frontend and backend.
- Set up SQLite.
- Create migrations.
- Configure local run commands.
- Define the backend service boundaries.

### Task 2 — Visual Design System

- Read available design skills.
- Establish art direction.
- Define color tokens and typography.
- Design page compositions.
- Create shared components.
- Document decisions in DESIGN.md.

### Task 3 — Geographic Data

- Identify suitable India boundary data.
- Validate and import it.
- Build spatial resolution services.
- Implement geographic APIs.

### Task 4 — Complaint Submission

- Build the frontend form.
- Implement geolocation.
- Persist complaints in SQLite.
- Implement the local background worker.

### Task 5 — Machine Learning

- Load the bi-encoder.
- Create embeddings.
- Implement exact nearest-cluster assignment.
- Create and update clusters.
- Implement cross-encoder merge candidate discovery.
- Implement transactional cluster merging.
- Implement category label generation.

### Task 6 — India Map

- Build the premium map interface.
- Add state and constituency layers.
- Add geographic navigation.
- Implement heatmap mode.
- Implement individual complaint view.
- Connect semantic category filters.

### Task 7 — Analytics

- Implement analytics endpoints.
- Build custom-styled visualizations.
- Add synchronized filters.
- Add category exploration.

### Task 8 — Quality and Testing

- Write automated tests.
- Run integration tests.
- Create demo data.
- Test geographic and semantic correctness.
- Review all responsive breakpoints.

### Task 9 — Visual Critique and Polish

Perform an explicit design review.

Look for:
- Generic AI-style components.
- Weak typography.
- Poor spacing.
- Excessive cards.
- Unnecessary decoration.
- Awkward responsive layouts.
- Unclear interaction states.
- Map controls that obstruct the map.
- Charts with weak hierarchy.

Improve identified issues and verify the changes.

**Do not consider the frontend complete until it has received a deliberate visual refinement pass.**

---

# 21. Explicitly Out of Scope

Do not implement:

- User authentication.
- Login.
- User accounts.
- Email verification.
- Complaint status tracking.
- Complaint resolution.
- Department assignment.
- Admin dashboard.
- Content moderation.
- Translation.
- Image or media uploads.
- SMS.
- WhatsApp.
- Notifications.
- Docker.
- Redis.
- Celery.
- Kubernetes.
- Cloud infrastructure.
- Paid external LLM APIs.

Do not add features beyond the requested product scope.

---

# 22. Acceptance Criteria

The project is complete when:

1. Frontend and backend run on localhost.
2. SQLite is the only application database.
3. The website has exactly three main pages.
4. The frontend is visually polished, distinctive, and responsive.
5. Complaint submissions work without authentication.
6. Geographic location is captured and resolved.
7. Complaints are persisted.
8. Local bi-encoder embeddings are generated.
9. Initial assignment uses exact nearest-cluster similarity.
10. New clusters are created when required.
11. The cross-encoder merges eligible related clusters.
12. Merge history and memberships remain consistent.
13. Categories are generated automatically.
14. The India map uses real geographic data.
15. Constituency-level exploration works wherever valid boundaries are available.
16. Heatmap, region, and individual modes work.
17. Dashboard analytics reflect SQLite data.
18. Geographic and category filters work independently.
19. No public endpoint exposes emails or exact GPS coordinates.
20. Automated tests pass.
21. The app runs without Docker, Redis, or Celery.
22. The design has undergone a visual critique and refinement pass.

---

# 23. Final Execution Instructions

You are expected to IMPLEMENT this application, not simply produce a requirements document.

Start by understanding the repository.

If the repository is empty, create the project.

Work through the implementation tasks in order.

Before frontend development, establish the design direction.

Before ML implementation, establish the selected models and their scoring conventions.

Prioritize:
1. Correct system behavior.
2. Correct semantic clustering.
3. Accurate geographic mapping.
4. Exceptional visual presentation.
5. Clean, maintainable code.
6. Smooth localhost operation.

Do not overengineer infrastructure for hypothetical traffic.

Do not compromise architecture by tightly coupling every service to SQLite.

Make reasonable implementation choices without requesting approval for trivial decisions.

After implementation:
- Run the tests.
- Fix identifiable failures.
- Inspect the actual frontend.
- Refine the design.
- Verify the core end-to-end flow.

Finally, report:
- What was implemented.
- Which ML models were selected.
- Which geographic datasets were used.
- Any geographic data limitations.
- How to run frontend and backend locally.
- How to seed demo data.
- Test results.
- Known limitations.
- Future scaling considerations.

The final result should be a functional, premium-quality civic complaint intelligence application, not a generic dashboard template.