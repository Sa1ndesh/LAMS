# National Land Acquisition & Management System (LAMS) - Database Architecture

## 1. Database Overview
LAMS uses PostgreSQL with the **PostGIS** extension to store relational project management data alongside spatial GIS representations (polygons, centroids, and boundaries) of land parcels and project zones across Indian states.

---

## 2. Entity Relationship Diagram (Conceptual)

```
[roles] <--- [users] ---> [audit_logs]
               |
               v
 [states] ---> [projects] <--- [districts]
                  |
        +---------+---------+------------------+-------------------+
        |                   |                  |                   |
        v                   v                  v                   v
  [land_parcels]      [compensation]   [affected_families]    [documents]
        |                                      |
        v                                      v
  [land_owners]                          [rehabilitation]
```

---

## 3. Detailed Table Schema Definitions

### 3.1 `roles`
Stores core security roles.
- `id` (INT, PK)
- `name` (VARCHAR(50), UNIQUE, NOT NULL) -- e.g. 'SUPER_ADMIN', 'CENTRAL_MINISTRY', 'STATE_AUTHORITY', 'DISTRICT_ADMIN', 'LAND_ACQUISITION_OFFICER', 'FIELD_OFFICER', 'PROJECT_IMPLEMENTING_AGENCY', 'VIEWER'
- `description` (TEXT)

### 3.2 `states`
Administrative state entities in India.
- `id` (INT, PK)
- `code` (VARCHAR(10), UNIQUE, NOT NULL) -- e.g. 'KA', 'MH', 'TN'
- `name` (VARCHAR(100), UNIQUE, NOT NULL)

### 3.3 `districts`
Administrative district entities within states.
- `id` (INT, PK)
- `state_id` (INT, FK -> states.id)
- `code` (VARCHAR(10), NOT NULL)
- `name` (VARCHAR(100), NOT NULL)

### 3.4 `users`
System user accounts.
- `id` (UUID, PK)
- `email` (VARCHAR(255), UNIQUE, NOT NULL)
- `hashed_password` (VARCHAR(255), NOT NULL)
- `full_name` (VARCHAR(150), NOT NULL)
- `role` (VARCHAR(50), FK -> roles.name, NOT NULL)
- `state_id` (INT, FK -> states.id, NULLABLE)
- `district_id` (INT, FK -> districts.id, NULLABLE)
- `department` (VARCHAR(150))
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())
- `updated_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.5 `projects`
Core infrastructure land acquisition projects.
- `id` (UUID, PK)
- `project_code` (VARCHAR(50), UNIQUE, NOT NULL) -- e.g. 'LAMS-KA-2026-001'
- `name` (VARCHAR(255), NOT NULL)
- `project_type` (VARCHAR(100), NOT NULL) -- e.g. Highway, Railway, Industrial Corridor, Dam/Water, Airport, Power Grid
- `ministry` (VARCHAR(150), NOT NULL) -- e.g. Ministry of Road Transport and Highways
- `implementing_agency` (VARCHAR(150), NOT NULL) -- e.g. NHAI, DMRC, Railways
- `state_id` (INT, FK -> states.id, NOT NULL)
- `district_id` (INT, FK -> districts.id, NOT NULL)
- `village` (VARCHAR(150), NOT NULL)
- `land_proposed_hectares` (NUMERIC(12, 2), NOT NULL)
- `land_acquired_hectares` (NUMERIC(12, 2), DEFAULT 0.00)
- `budget_inr` (NUMERIC(15, 2), NOT NULL)
- `current_stage` (VARCHAR(50), NOT NULL) -- 'Proposal', 'Verification', 'Survey', 'Notification', 'Award', 'Compensation', 'Possession', 'Rehabilitation & Resettlement', 'Completed'
- `start_date` (DATE, NOT NULL)
- `target_completion_date` (DATE, NOT NULL)
- `status` (VARCHAR(50), DEFAULT 'ON_TRACK') -- 'ON_TRACK', 'DELAYED', 'CRITICAL', 'COMPLETED'
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())
- `updated_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.6 `land_parcels`
Individual survey numbers and boundary polygons.
- `id` (UUID, PK)
- `parcel_code` (VARCHAR(50), UNIQUE, NOT NULL)
- `project_id` (UUID, FK -> projects.id, NOT NULL)
- `survey_number` (VARCHAR(100), NOT NULL)
- `state_id` (INT, FK -> states.id, NOT NULL)
- `district_id` (INT, FK -> districts.id, NOT NULL)
- `taluk` (VARCHAR(100), NOT NULL)
- `village` (VARCHAR(100), NOT NULL)
- `area_hectares` (NUMERIC(10, 4), NOT NULL)
- `land_type` (VARCHAR(50), NOT NULL) -- 'Agricultural', 'Commercial', 'Residential', 'Forest', 'Government'
- `acquisition_status` (VARCHAR(50), NOT NULL) -- 'Proposed', 'Verified', 'Surveyed', 'Notified', 'Awarded', 'Acquired'
- `compensation_status` (VARCHAR(50), NOT NULL) -- 'Pending', 'Assessed', 'Approved', 'Disbursed'
- `possession_status` (VARCHAR(50), NOT NULL) -- 'Not Taken', 'Demarcated', 'Taken'
- `latitude` (NUMERIC(10, 8), NOT NULL)
- `longitude` (NUMERIC(11, 8), NOT NULL)
- `geometry` (GEOMETRY(Polygon, 4326), NULLABLE) -- PostGIS spatial geometry
- `geojson` (JSONB, NULLABLE) -- GeoJSON representation
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())
- `updated_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.7 `land_owners`
Recorded landowners associated with land parcels.
- `id` (UUID, PK)
- `parcel_id` (UUID, FK -> land_parcels.id, NOT NULL)
- `owner_name` (VARCHAR(150), NOT NULL)
- `contact_number` (VARCHAR(20))
- `ownership_share_percentage` (NUMERIC(5, 2), DEFAULT 100.00)
- `category` (VARCHAR(50)) -- General, OBC, SC, ST
- `bank_account_masked` (VARCHAR(50)) -- e.g. 'XXXX-XXXX-4920'
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.8 `compensation_records`
Financial assessment and disbursement tracking.
- `id` (UUID, PK)
- `parcel_id` (UUID, FK -> land_parcels.id, NOT NULL)
- `project_id` (UUID, FK -> projects.id, NOT NULL)
- `assessed_amount_inr` (NUMERIC(15, 2), NOT NULL)
- `approved_amount_inr` (NUMERIC(15, 2), NOT NULL)
- `disbursed_amount_inr` (NUMERIC(15, 2), DEFAULT 0.00)
- `pending_amount_inr` (NUMERIC(15, 2), NOT NULL)
- `payment_status` (VARCHAR(50), NOT NULL) -- 'Assessed', 'Approved', 'Partially Disbursed', 'Disbursed', 'Pending'
- `payment_date` (TIMESTAMPTZ, NULLABLE)
- `remarks` (TEXT)
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())
- `updated_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.9 `affected_families`
Rehabilitation and Resettlement (R&R) census.
- `id` (UUID, PK)
- `family_ref_id` (VARCHAR(50), UNIQUE, NOT NULL)
- `project_id` (UUID, FK -> projects.id, NOT NULL)
- `village` (VARCHAR(100), NOT NULL)
- `head_of_family` (VARCHAR(150), NOT NULL)
- `family_members_count` (INT, DEFAULT 1)
- `category` (VARCHAR(50)) -- General, OBC, SC, ST
- `is_displaced` (BOOLEAN, DEFAULT FALSE)
- `rr_status` (VARCHAR(50), NOT NULL) -- 'Identified', 'Eligible', 'Assistance Disbursed', 'Resettled', 'Completed'
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.10 `rehabilitation_packages`
Specific R&R entitlements allocated to families.
- `id` (UUID, PK)
- `family_id` (UUID, FK -> affected_families.id, NOT NULL)
- `housing_assistance` (BOOLEAN, DEFAULT FALSE)
- `employment_assistance` (BOOLEAN, DEFAULT FALSE)
- `cash_grant_inr` (NUMERIC(15, 2), DEFAULT 0.00)
- `resettlement_site` (VARCHAR(200))
- `status` (VARCHAR(50), DEFAULT 'PENDING') -- 'PENDING', 'IN_PROGRESS', 'COMPLETED'
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.11 `documents`
Uploaded project and parcel evidence files.
- `id` (UUID, PK)
- `project_id` (UUID, FK -> projects.id, NOT NULL)
- `parcel_id` (UUID, FK -> land_parcels.id, NULLABLE)
- `doc_type` (VARCHAR(100), NOT NULL) -- 'Project Proposal', 'Land Records', 'Survey Documents', 'Notifications', 'Award Documents', 'Compensation Documents', 'R&R Documents'
- `title` (VARCHAR(255), NOT NULL)
- `file_path` (VARCHAR(500), NOT NULL)
- `file_size_bytes` (BIGINT, NOT NULL)
- `file_type` (VARCHAR(50), NOT NULL)
- `uploaded_by_id` (UUID, FK -> users.id, NOT NULL)
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.12 `notifications`
System alerts and stage update notifications.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id, NULLABLE)
- `project_id` (UUID, FK -> projects.id, NULLABLE)
- `title` (VARCHAR(200), NOT NULL)
- `message` (TEXT, NOT NULL)
- `event_type` (VARCHAR(100), NOT NULL) -- 'PROJECT_APPROVAL', 'STAGE_CHANGE', 'COMPENSATION_PENDING', 'TIMELINE_DELAY', 'R_AND_R_PENDING'
- `is_read` (BOOLEAN, DEFAULT FALSE)
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

### 3.13 `audit_logs`
Immutable compliance and security logs.
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id, NULLABLE)
- `user_email` (VARCHAR(255))
- `action` (VARCHAR(100), NOT NULL)
- `entity_type` (VARCHAR(100), NOT NULL)
- `entity_id` (VARCHAR(100), NOT NULL)
- `details` (JSONB)
- `ip_address` (VARCHAR(45))
- `created_at` (TIMESTAMPTZ, DEFAULT NOW())

