# Copywriting Skills Profile
# Used by S4 (match_request) to improve verdict accuracy for writing/content projects.
# Injected into the match_request prompt as context.

## What counts as a tweak (small, usually in scope for revisions)
- Changing a few words or a sentence in existing content
- Fixing grammar or spelling errors
- Adjusting the tone of a paragraph
- Minor headline changes
- Small formatting adjustments within a delivered piece

## What counts as substantial (new work, usually out of scope)
- Writing a new piece (article, post, page) not listed in the SOW
- Increasing word count significantly (e.g. doubling the length of a piece)
- Adding new sections to delivered content
- Completely rewriting a piece from scratch after approval
- Adding research, interviews, or expert quotes if not in scope
- Translating content to another language
- Adding SEO keyword research (separate service)
- Ghostwriting in a significantly different voice than agreed

## Items usually out of scope for a standard copywriting project
- Social media posts (unless listed)
- Email sequences beyond what's listed
- Ad copy or PPC copy (separate service)
- Video scripts if only written content was agreed
- Infographic text
- Press releases (separate deliverable)
- Ongoing content calendar management

## Revision guidance
- "One round of revisions" = one set of consolidated client feedback applied once.
- Asking for a complete tone change after delivery typically counts as a new brief.
- Factual corrections (e.g. wrong company name) are usually not a revision round.
- Adding entirely new sections after delivery is new work, not a revision.

## Gold-set cases for testing
# CASE 1: in_scope revision (tweak)
# Client: "Can you change 'innovative solutions' to 'practical tools' throughout?"
# SOW has: "3 blog posts, 2 rounds of revisions"
# Expected: in_scope, tweak, consumes_revision=true

# CASE 2: out_of_scope new deliverable
# Client: "Can you also write 3 email newsletters?"
# SOW has: "5 blog posts (800-1000 words each). No email copy."
# Expected: out_of_scope

# CASE 3: gray_area vague revision
# Client: "The tone doesn't feel right. Can you make it more engaging?"
# SOW has: "minor revisions included"
# Expected: gray_area (vague revision clause + subjective request)
