# Web Development Skills Profile
# Used by S4 (match_request) to improve verdict accuracy for web dev projects.
# Injected into the match_request prompt as context.

## What counts as a tweak (small, usually in scope for revisions)
- Changing text content on an existing page
- Updating a colour, font size, or button style
- Fixing a broken link or image
- Swapping an image on an existing page
- Minor copy edits (under ~50 words changed)

## What counts as substantial (new work, usually out of scope)
- Adding a new page not listed in the SOW
- Implementing a new feature (search, filtering, login, e-commerce)
- CMS integration if not specified in the SOW
- Database design or backend changes beyond static content
- Adding a new language / translation layer
- Responsive redesign if the SOW only covered desktop
- SEO audit and implementation (separate service)
- Performance optimisation beyond basic image compression

## Items usually out of scope for a standard web project
- E-commerce / payment processing (unless explicitly listed)
- Custom admin dashboards
- API integrations with third-party services
- Membership or subscription systems
- Progressive Web App (PWA) features
- Multi-language support
- Accessibility audit (WCAG compliance beyond basics)
- Ongoing maintenance after launch

## Revision guidance
- "Revision round" typically means one consolidated set of changes from the client.
- Multiple back-and-forth cycles within one topic count as multiple revision rounds.
- A "revision" that requires redesigning a section is "substantial", not a tweak.

## Gold-set cases for testing
# CASE 1: in_scope tweak
# Client: "Can you change the hero text to say 'Welcome to our bakery'?"
# SOW has: "Home page with hero section"
# Expected: in_scope, tweak

# CASE 2: out_of_scope new feature
# Client: "Can you add an online ordering system?"
# SOW has: "5 pages: Home, Menu, About, Gallery, Contact. No e-commerce."
# Expected: out_of_scope (exclusion or not listed)

# CASE 3: gray_area
# Client: "Can you make it look more modern?"
# SOW has: "minor revisions included"
# Expected: gray_area (vague revision clause + vague request)
