# AI Tools Library Phase

## Purpose

AI Tools Library is now a working CRM library for cataloging internal and external AI tools, vendors, use cases, deployment models, pricing, and owner notes.

## Fields

Core fields:

- name
- vendor name
- website URL
- category
- primary use case
- description
- pricing model
- deployment type
- data sensitivity level
- status
- owner notes
- source
- created/updated metadata
- archive metadata

Controlled UI options include GenAI, Data & Analytics, Automation, Computer Vision, Sales & Marketing, HR & Learning, Legal & Compliance, Cybersecurity, Productivity, Industry-specific, and Other.

## Behavior

Users can:

- list AI tools
- search by name, vendor, website, use case, description, and notes
- filter by category, status, deployment type, and pricing model
- create AI tools
- edit AI tools

Admins can:

- include archived tools in the list
- archive and unarchive AI tools

Archived tools are hidden from normal lists by default.

## Champion Score And CRM Activity Points

Manual AI tool creation creates:

- `user_contributions` record with `AI_TOOL_CREATED`
- `champion_activities` record with category `ECOSYSTEM_LIBRARY` and activity type `AI_TOOL_ADDED`

This means manually added AI tools count as operational CRM Activity Points and as evidence for the official YZ Champion Score category **Ecosystem Library Contribution**.

Excel-imported records do not automatically create AI tool points or Champion Score evidence unless explicitly mapped in a future approved process.

## Audit Logging

Audit logs are written for:

- AI tool created
- AI tool updated
- AI tool archived
- AI tool unarchived

## Not Included Yet

- AI-powered tool evaluation
- tool recommendation or scoring engine
- procurement approval workflow
- automated vendor risk assessment
- external tool catalog integration

## Testing

Backend:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\backend
.\.venv\Scripts\python.exe -m compileall -q app alembic scripts tests
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Frontend:

```powershell
cd C:\Users\emirc\borusan-ai-studio-crm\frontend
npm run build
npm run lint
```

Manual:

- open `/ai-tools`
- add an AI tool
- confirm it appears in the list
- edit the tool
- archive/unarchive as admin
- confirm Leaderboard Ecosystem Library evidence increases for manual creation
