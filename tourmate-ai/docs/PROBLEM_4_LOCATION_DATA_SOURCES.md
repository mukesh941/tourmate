# PROBLEM 4 — LOCATION DATA SOURCES

## 1. Initial State of the Database
- **Orphan Records**: Over 6,200 locations (mainly Cities) had no hierarchical relation to a state, district, or union territory.
- **States & UTs**: The system had 36 records assigned as "State" (including duplicate state entries, misclassified entities, and old names like 'Orissa' instead of 'Odisha').
- **Districts**: There were no explicitly classified `District` records in the system. All child entities were either labeled as cities, POIs, or missing relationships entirely.
- **Duplicates**: Over 300 locations had duplicate names, and 45 coordinate pairs were exact duplicates. Many cities were represented by two records: one actual with coordinates and one placeholder with `(20.0, 77.0)`.

## 2. Approach Taken
### Phase 1: Full Database Audit
- Audited the exact state of the `locations` table, categorizing them by valid/invalid parents, duplicate coords, and orphaned entities.

### Phase 2: Valid India Hierarchy
- Cleansed the state records so exactly 28 states and 8 union territories exist.
- Standardized names (e.g., `Pondicherry` -> `Puducherry`, `Orissa` -> `Odisha`).
- Modified the hierarchy logic to ensure all valid state locations have `parent_id = NULL`.

### Phase 3 & 4: Expansion & Data Cleanup
- Leveraged `indian_districts.json` and `indian_cities.json` from the backend `data` directory to structurally populate the database.
- Inserted over 722 missing district-level locations.
- Attempted to map orphaned cities to states and districts based on name-matching.
- Successfully linked over 106 orphaned cities. We opted not to blindly delete the remaining 6,100+ unlinked cities since they hold valid coordinate data that might still be used by downstream tasks or represent legitimate remote locations.
- Ensured no fabrication of data.

### Phase 5: Duplicate Resolution
- Modified the existing duplicate-cleaning scripts to detect duplicates based on `name` and `parent_id`.
- Consolidated over 100 duplicate pairs into single canonical entities, migrating their related `POI`, `Trip`, `Accommodation`, and `TransportOption` dependencies before gracefully deleting the duplicate records.

### Phase 6: Aliases System
- Added an `aliases` column of type `JSONB` to the schema and generated an Alembic migration.
- Populated common aliases for major states and cities (e.g., `Bengaluru` -> `Bangalore`, `Mumbai` -> `Bombay`, `Chennai` -> `Madras`).

## 3. Current Dataset Sources
The current geographical locations map derives from:
1. **Initial `world_cities.json` import**: Providing the baseline ~7,000 cities with valid longitude and latitude data (many of which are currently unmapped orphaned entities).
2. **`indian_districts.json`**: Providing accurate district hierarchy (600+ new districts properly attached to States/UTs).
3. **`indian_cities.json`**: Providing a structured layout for the top 1200+ major cities and their respective state mapping.
