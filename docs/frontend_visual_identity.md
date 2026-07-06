# Frontend Visual Identity

## Direction

The CRM now uses a Borusan AI Studio inspired visual direction: premium internal product, clean enterprise workspace, and restrained AI-studio energy.

The palette uses light working surfaces with controlled purple, magenta, orange, and red gradient accents. The sidebar carries the strongest brand energy, while tables, forms, and detail cards stay readable for repeated daily use.

## Applied UI patterns

- Dark premium sidebar with white Borusan AI Studio brand placeholder.
- Light workspace background with subtle gradient accents.
- Gradient primary buttons and softer secondary controls.
- Enriched dashboard hero and metric cards.
- CRM toolbar for search and filters.
- Detail page layout with profile, Borusan fit, contacts, notes, opportunities, and metadata.
- Import Center step indicator for Upload, Preview, Candidates, Review, and Commit.
- Polished branding manager wired to backend upload.

## Usability principles

- Keep data-dense CRM areas readable.
- Use color for hierarchy, state, and brand accents rather than decoration.
- Make row scanning faster than Excel by exposing status, fit, source, counts, and summaries.
- Keep manual actions close to the record where the user makes the decision.

## Current logo behavior

Until a real Borusan AI Studio logo is uploaded by an admin, the app shows an `AI` placeholder mark. The Admin Branding page supports uploading PNG, JPG, SVG, or WebP files up to 2 MB. The backend stores the active logo locally under `backend/uploads/branding` and exposes it through an authenticated content endpoint.

## Known limitations

- The uploaded logo is wired in the Admin Branding page preview; global shell consumption can be added in the next frontend pass.
- No custom illustration or AI-generated imagery is used in the MVP workspace to keep the product focused and corporate.
- Mobile behavior is responsive but optimized primarily for desktop CRM use.
