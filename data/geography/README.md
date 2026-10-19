# Geographic source and attribution

DataMeet Community Maps, pinned commit `b3fbbde595310b397a55d718e0958ce249a4fa1f`, retrieved 19 October 2026. Source: <https://github.com/datameet/maps>. WGS84 / EPSG:4326, `[longitude, latitude]`.

| Layer | Source path | Vintage / limitations |
| --- | --- | --- |
| State / UT | States/Admin2 | 36 states/UTs, including Telangana and Ladakh; not an official legal boundary source. |
| District | Districts/Census_2011/2011_Dist | Census 2011 districts; newer districts are not represented. |
| Assembly constituency | assembly-constituencies/India_AC | ECI polling-station scrape; several states use pre-delimitation boundaries. Assembly polygons, never Parliamentary polygons. |

The [Assembly dataset documentation](https://projects.datameet.org/maps/assembly-constituencies/) reports older delimitations in Jammu and Kashmir, Jharkhand, Assam, Manipur, Nagaland and Arunachal Pradesh; positional shifts; incorrect/missing names; Telangana included under Andhra Pradesh in Assembly attributes. The state layer has Telangana and Ladakh; independent spatial parenting links the older layers to it without trusting their names. UTs without legislatures have no Assembly polygons. This is an exploratory historical atlas, not an authoritative electoral or legal map. Source geometry determines supported submission coverage; unsupported points receive an explicit error. A valid state with no matching Assembly is accepted with constituency unknown.

Layer-specific license in district/Assembly READMEs and project pages: [CC BY 2.5 India](https://creativecommons.org/licenses/by/2.5/in/). Repository default: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: **India state, district and Assembly boundaries provided by DataMeet Community Maps Project.** Derived files repair invalid polygons and simplify only display geometry. Full geometry remains available for private Shapely resolution. No national boundary is synthesized.

Run `scripts/prepare_geography.py` after migration. Downloads are local and ignored by Git; pinned source and SHA256 hashes are saved in generated `manifest.json`, with counts, geometry repairs and unmatched regions. Region IDs use source identifiers, scoped by layer/state; source record numbers are a documented fallback pinned to this version. Districts and Assemblies independently reference the state with the largest polygon intersection. Runtime membership is resolved by indexed point-in-polygon tests, never name matching. Overlaps choose smallest area then stable ID and record all matches privately in the complaint.

No external basemap or tile service is required. MapLibre draws the locally served polygons against an ink canvas. Internet is needed only for initial boundary/model/package downloads.
