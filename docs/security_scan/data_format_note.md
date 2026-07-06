# JSON / XML / Multipart Data Format Note

The Borusan AI Ecosystem CRM currently uses REST-style HTTP APIs with JSON request and response bodies.

## JSON

- JSON is the primary API data format.
- FastAPI exposes OpenAPI JSON at `/openapi.json`.
- An exported OpenAPI schema is available at `docs/security_scan/openapi.json`.
- This schema can be used for automated API scanning and Postman/import tooling.

## XML

- XML is not currently used by the application.
- There are no active XML endpoints.
- There are no XML schemas/XSD files in the current application.
- If Information Security requires XML samples, the correct answer is that the current system has no XML API surface.

## Multipart Form Data

`multipart/form-data` is used for file uploads:

- Excel workbook import: `.xlsx`, admin-only, 25 MB limit.
- Startup deck upload: `.pdf` / `.pptx`, authenticated users, 50 MB limit.
- Branding/logo upload: `.png` / `.jpg` / `.jpeg` / `.svg` / `.webp`, admin-only, 2 MB limit.

## File Downloads

File download endpoints exist for:

- Startup deck downloads.
- Branding/logo content.

Download endpoints require authentication and return file responses rather than JSON.
