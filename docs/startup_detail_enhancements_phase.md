# Startup Detail Enhancements Phase

## Vertical Definition

Vertical means the startup's main industry, business domain, or functional area. UI help text explains it with examples such as Manufacturing AI, Sales Automation, Supply Chain, HR Tech, Legal Tech, Energy Optimization, and Computer Vision.

The tooltip is shown next to Vertical labels in Startup Library filters, add/edit company forms, and the company detail profile section.

## Status And Last Contact Editing

Startup detail uses the existing organization update endpoint:

- `PUT /api/v1/organizations/{id}`
- Supports `lifecycle_status_id`
- Also accepts `status_code` for company lifecycle status lookup
- Supports `last_contact_date`

Audit logs are written for:

- `ORGANIZATION_STATUS_CHANGED`
- `ORGANIZATION_LAST_CONTACT_CHANGED`

## Follow-Up Assignment

Startup detail can create organization follow-ups with:

- `entity_type = ORGANIZATION`
- `entity_id = organization id`
- `title`
- `due_date`
- `assigned_to_user_id`
- `status = OPEN`

The active user picker is exposed at:

- `GET /api/v1/users/active`

Follow-up completion remains unchanged and continues to count toward leaderboard scoring when completed manually.

## Startup Deck Upload

Decks are stored in the new `organization_documents` table and attached to organizations.

Endpoints:

- `POST /api/v1/organizations/{id}/documents`
- `GET /api/v1/organizations/{id}/documents`
- `GET /api/v1/organizations/{id}/documents/{document_id}/download`
- `PATCH /api/v1/organizations/{id}/documents/{document_id}/archive`
- `PATCH /api/v1/organizations/{id}/documents/{document_id}/unarchive`

Allowed file types:

- PDF: `.pdf`, `application/pdf`
- PowerPoint deck: `.pptx`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`

Maximum file size:

- 50 MB

Storage:

- Local MVP path: `backend/uploads/organization_documents`
- Stored filenames are generated UUID filenames
- Original filename is preserved for display/download
- SHA-256 hash is calculated and stored

## Security Notes

- Original filenames are not used as storage paths.
- Only authenticated users can upload/list/download decks.
- Admins and the original uploader can archive/unarchive a deck.
- Path traversal is avoided by using generated filenames and a fixed upload directory.
- Audit logs are written for deck upload/archive/unarchive.
- No OCR, deck parsing, AI analysis, or external storage is implemented in this phase.

## Testing Steps

1. Open Startup Library.
2. Confirm the Vertical filter label has an info tooltip.
3. Open a startup detail page.
4. Edit status and last contact date in the Profile card.
5. Assign a follow-up to an active user and confirm it appears in the Follow-ups card.
6. Upload a PDF deck.
7. Upload a PPTX deck.
8. Try an unsupported file type and confirm it is rejected.
9. Download an uploaded deck.
10. Archive a deck as admin or uploader.
11. Check Audit Logs for status, last contact, follow-up assignment, and deck actions.

## Known Limitations

- Decks are stored on the local filesystem and must be backed up with the app uploads folder.
- Add Company does not upload a deck inline; users create the company, open detail, then upload the deck.
- There is no deck preview, OCR, AI summary, or semantic search yet.
