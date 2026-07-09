# SuryaAutomobiles Docs

This package provides a hybrid documentation scaffold for the SuryaExtend concept using:

- Arc42-style architecture chapters for product and platform thinking
- Sphinx-friendly Markdown structure for publishing and navigation
- YAML requirement files for downstream automation and AI agents

## Intended use

A cloud agent can use this scaffold to draft an initial documentation set from the existing project context in the repository, especially the product summary in README.md and the deeper concept notes in surya_chakra.md.

## Suggested workflow

1. Review the source material in the repository.
2. Fill the portfolio and product templates with project-specific facts.
3. Capture requirements in the YAML files.
4. Add sketches and diagrams to the diagrams folder.
5. Build the docs with Sphinx and publish them.

## Source mapping

- Portfolio vision and roadmap: pull from the startup overview and business model sections.
- Charging stations: capture scope, requirements, architecture, interfaces, and verification.
- Retrofit kits and range extenders: document product variants and shared platform assumptions.
- Shared materials: collect regulations, safety, certification, suppliers, and decisions.
