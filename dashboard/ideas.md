# VeriDoc Nexus Research Dashboard — Design Brainstorm

## Approach 1
**Theme Name:** Evidence Atelier

**Very Brief Intro:** A warm editorial research studio that treats every answer as a composed piece of evidence. Cream paper, ink-black typography, oxidized copper accents, and visible provenance make the product feel considered rather than generic.

**Probability:** 0.06

## Approach 2
**Theme Name:** Signal Control Room

**Very Brief Intro:** A restrained dark operational interface with high-contrast data panels and electric accents, designed to communicate live system intelligence and agent activity. Technical and cinematic, but still serious enough for legal research.

**Probability:** 0.03

## Approach 3
**Theme Name:** Civic Index

**Very Brief Intro:** A clean institutional system inspired by public archives, government gazettes, and library catalogues. Blue-grey paper, archival red markers, and structured typographic labels emphasize trust, completeness, and public-source authority.

**Probability:** 0.08

## Selected Direction: Evidence Atelier

### Design Movement
Contemporary editorial modernism with references to Swiss information design, independent publishing, and archival research rooms. The interface should feel like a high-end evidence desk: precise, quiet, tactile, and confident.

### Core Principles
1. **Evidence before spectacle:** Every major visual decision should reinforce source traceability, confidence, or research momentum.
2. **Editorial hierarchy:** Use strong typographic contrast and asymmetric composition to make complex research states legible at a glance.
3. **Tactile precision:** Paper-like surfaces, hairline rules, ink blocks, and copper markers create depth without ornamental noise.
4. **Calm intelligence:** Motion is purposeful and brief, showing progress, state transitions, and confidence rather than decoration.

### Color Philosophy
The base is an aged-paper ivory that softens the density of legal research without becoming nostalgic. Ink-black provides authority and readable contrast. Oxidized copper is the ownable signature color: it marks provenance, active reasoning, and verified connections. Muted sage indicates a healthy evidence state; restrained vermilion marks uncertainty or missing source coverage. The palette avoids glossy gradients and avoids the overused blue-purple SaaS default.

### Layout Paradigm
Use a persistent left research rail and an offset two-column workbench. The question composer occupies the visual center-left, while evidence and agent traces enter as a right-side inspection surface. Dashboard metrics sit as a horizontal instrument strip rather than a centered card grid. Large margins and staggered vertical anchors create an editorial page rhythm.

### Signature Elements
- Copper **evidence pins**: small numbered markers that connect claims in the answer to source passages.
- A **provenance ruler**: a thin horizontal line with document, page, and confidence ticks.
- **Paper tabs** and dossier labels: compact uppercase labels for domain, corpus, job state, and source type.

### Interaction Philosophy
Interactions should feel like handling a research instrument. Uploading opens a dossier drawer, question submission turns the composer into an active case file, and evidence pins expand into focused source excerpts. Hover states reveal context; clicks reveal depth. No interaction should feel like a toy or a marketing flourish.

### Animation
Use 160–220ms ease-out transitions for tabs, chips, and evidence expansion. New research runs enter with a subtle 40ms stagger between status rows. The agent trace uses a quiet pulse on the active node and a copper line that resolves as each stage completes. Avoid continuous decorative motion. Respect `prefers-reduced-motion` by disabling staged entrances and pulses.

### Typography System
Use **DM Serif Display** for the primary display wordmark and major research question heading, paired with **IBM Plex Sans** for interface text and metadata. Use IBM Plex Mono for hashes, page references, latency, and job IDs. Headlines should be compact and editorial; labels should be uppercase with generous tracking; body text should remain 15–16px with a 1.55 line height.

### Brand Essence
**VeriDoc Nexus is an evidence-grounded research workbench for analysts and legal researchers who need to move from a question to a defensible, cited answer without losing the chain of proof.**

Personality: **Exacting, composed, forensic.**

### Brand Voice
Headlines are direct and intelligent. CTAs describe the research action, not generic onboarding. Microcopy explains what the system knows, what it is checking, and where uncertainty remains.

Example lines:
- “Ask the corpus. Keep the proof.”
- “Every claim earns its page.”

### Wordmark & Logo
The mark is a compact **V-shaped evidence bracket**: two offset copper strokes form a V while a small black square sits at the intersection, symbolizing a claim anchored to a source. The wordmark uses DM Serif Display with a custom-spaced “NEXUS” treatment; never render the logo as plain default text.

### Signature Brand Color
**Oxidized Copper — `#B96845`**. It is warm, archival, and ownable, appearing only on active evidence, verified provenance, and primary research actions.

## Implementation Reminder
All dashboard files should reinforce Evidence Atelier. Before choosing a component, ask: **Does this choice make the evidence chain clearer, or does it dilute the research-desk character?**

## Product Scope for This Dashboard
The dashboard presents a large-corpus legal research system covering Central Acts, Rules, amendments, and curated Supreme Court/eSCR judgments. It should make the following visible: upload-to-index jobs, corpus health, agent stages, connected legal entities, answer confidence, page-level citations, and the distinction between supported evidence and unresolved gaps.

## Style Decisions
- Keep the dashboard light, editorial, and asymmetric rather than a generic centered SaaS grid.
- Use copper only for provenance and active research actions.
- Make the evidence chain visible in the primary interaction, not hidden behind a secondary page.
- Treat loading and processing states as research instrumentation, not generic spinners.
- Present the four current PDFs as a starter corpus only; the interface must communicate a scalable legal knowledge base.
