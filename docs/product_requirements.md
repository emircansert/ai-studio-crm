# Product Requirements

## Purpose

Borusan AI Studio needs a web-based CRM to replace the current Ecosystem Library workbook. The CRM should manage AI startups, vendors, PoC opportunities, ecosystem events, network contacts, AI tools, meeting notes, company fit, statuses, and follow-up actions in one searchable system.

The first implementation will run locally. The architecture must remain suitable for later deployment to Borusan internal infrastructure, including Azure and Microsoft Entra ID SSO.

## Workbook Analysis Summary

Source file: `C:\Users\emirc\Downloads\Ekosistem_Library_V2.xlsx`

Sheets found:

| Sheet | Rows analyzed | Main meaning | Notes |
| --- | ---: | --- | --- |
| PoC | 7 actual opportunity rows, plus tail status values | Opportunity / PoC tracking | Header row is row 1. Rows 17-21 contain loose status/list values, not opportunity records. Date values are mixed Excel dates and strings like `31/07/2025`. |
| Events | 82 event records | Ecosystem event library | Many date values are blank or partial text such as `Aug 4-6`, `Nov`, `Her ay`, `yil sonu gibi`. |
| Startup Library | 342 company records | Startup/vendor library | Main source for company records, contacts, solution/use-case text, source, and Borusan company relevance flags. |
| Network | 71 institution records | VC, accelerator, CVC, platform, and ecosystem contacts | Many relationship values are Turkish and need normalization. |
| AI Tools | Header only | Future AI tool library | No data records yet. |
| Lists | 10 category values, 7 status values, and notes | Seed controlled vocabularies | Useful as a starting point, not complete enough to drive the whole CRM. |

Important Startup Library observations:

- `Status` has many variants. Top values include `Bilgi` (223), `Gorusuldu` (57), `Komite olarak gorusuldu` (13), `Calisiliyor` (8), `Demo Asamasinda` (6), plus smaller English and Turkish variants.
- `Category` is mostly blank: 339 blanks out of 342 records. The CRM should derive category primarily from `Vertical`, `Solution / Use-case`, and future tags, not trust the Excel category column.
- Top verticals include Predictive Maintenance, Image Processing, Customer Experience, Decarbonisation, Forecasting/Recommendation Software, Health & Safety, Wind Energy, Autonomous Robots, EV Charging, Energy Storage, Digital Twin, HR Technology, Sustainability, IoT, AI Provider, Robotics.
- Geography values are inconsistent: examples include `TR`, `ABD`, `USA`, `US`, `UK`, `Ingilizce country names`, and combinations like `TR / ABD`.
- Contact data is mixed. 124 email-like values were found, with 114 unique emails. Some contact fields contain phone numbers, person names only, placeholders, or action notes.
- Duplicate candidates exist. Name duplicates include Artiwise, Jetlink, OneNewOne. Domain duplicates include `alternacx.com` and `onenewone.com`.
- Borusan fit is currently represented as seven company flag columns: Boru, Borcelik, Supsan, Oto, CAT, Enerji, Liman. These should become relationship records, not columns.

Important Events observations:

- AI relevance values: High (23), Medium (22), Low (12), unknown/question mark (3), blank (22).
- Value creation option values: High (23), Medium (19), Low (12), unknown/question mark (4), blank (24).
- Event categories are multi-value text fields with Turkish and English terms mixed together.
- Participant roles include Strategy, Ventures, CDO, Champion, C-Level, Finance, and combinations. These should be normalized as tags or role assignments.

Important Network observations:

- Type values include VC, Accelerator, CVC, Fund, Community, Platform, Program, and blanks.
- Relationship values include Acquaintance, Close Relationship, No Close Relationship, Information, Borusan Ventures Investor, Borusan Group Investor, and ad-hoc person names.
- Contact Person often contains an email, but sometimes contains a person name, dash, or blank.

## Product Scope

### In Scope for the CRM Product

- Dashboard with counts, pipeline summary, recent activity, upcoming follow-ups, and import warnings.
- Company / Startup Library with search, filters, tags, fit by Borusan company, status, geography, source, and solution area.
- Company detail page with profile, contacts, notes, opportunities, fit records, related events, related network institutions, audit history, and raw import references.
- PoC / Opportunity pipeline with stages, owner, target Borusan company, value hypothesis, dates, status, next action, and decision notes.
- Events library with relevance scoring, value potential, location, date range, category tags, attendance notes, and related follow-ups.
- Network library for VCs, CVCs, accelerators, communities, programs, platforms, and other ecosystem institutions.
- AI tools library for tools used or evaluated by AI Studio.
- Meeting notes and follow-up actions.
- Admin and User roles.
- Admin panel for users, vocabularies, import batches, audit logs, and branding.
- Admin-managed Borusan AI Studio logo upload/change.
- Robust Excel import pipeline with preview and confirmation.
- Audit logs for security and accountability.

### Out of Scope for the First Stage

- Full UI workflows.
- Production authentication integration.
- AI-assisted tagging, summarization, duplicate detection, or natural language search.
- Direct write of Excel rows into CRM tables.
- Corporate deployment automation.

## Roles

### Admin

- Manage users and roles.
- Upload/change the Borusan AI Studio logo.
- Configure controlled vocabularies.
- Upload Excel workbooks.
- Review import preview and validation warnings.
- Confirm or reject import commits.
- View audit logs.

### User

- Search and filter records.
- View company, event, network, opportunity, and tool details.
- Create and update notes, meetings, and follow-up actions if permitted.
- Export filtered views if later enabled by policy.

## Core Workflows

### Find relevant startups

Example: "startups that provide GenAI solutions and are relevant for Borcelik"

Expected CRM behavior:

1. Search index matches `GenAI`, `Generative AI`, `AI Provider`, solution text, verticals, tags, and notes.
2. Filter by Borusan company fit = Borcelik.
3. Filter by organization type = Startup or Vendor.
4. Optional status filters exclude rejected or failed records.
5. Results show company name, solution summary, status, geography, source, fit strength, and next action.

The result set must not include Borusan internal companies or network institutions unless the user is explicitly in those libraries. This separation is enforced by `organization_type` filters in each product area.

### Import workbook

1. Admin uploads workbook.
2. System detects sheets.
3. System applies sheet and column mapping configs.
4. Raw rows are saved to import staging.
5. Values are cleaned and normalized.
6. Contacts, emails, domains, dates, statuses, tags, and Borusan company fits are extracted.
7. Duplicate candidates and validation warnings are shown.
8. Admin reviews preview.
9. Only after explicit confirmation are normalized CRM records committed.

### Manage company detail

Users should see a clean profile, not spreadsheet columns. A company detail page should include:

- Organization identity, website, normalized domain, geography, and type.
- Solution/use-case summary.
- Categories, verticals, and tags.
- Status and lifecycle stage.
- Borusan company fit records.
- Contacts and extracted emails/phones.
- Opportunities and PoCs.
- Notes, meetings, follow-ups.
- Import source and raw values where useful for traceability.

## Non-Functional Requirements

- English application UI and database naming.
- Modular backend and frontend.
- Microsoft SQL Server relational model.
- Robust search and filtering from the beginning.
- Secure local authentication with JWT for MVP.
- Role-based access control with ADMIN and USER.
- Migration-ready for Azure and Microsoft Entra ID SSO.
- Audit logs for changes, imports, logins, and admin actions.
- No dirty data written directly to normalized tables.
- Import warnings must be visible and actionable.
- Local Microsoft SQL Server development.
