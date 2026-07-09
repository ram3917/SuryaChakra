# 03. Architecture

## Architectural overview

Core components:
- Rooftop solar panel (150–180W semi-flexible)
- MPPT charger
- 1 kWh LFP reserve battery pack
- Dual-battery BMS with SOC monitoring and transfer logic
- Manual/controlled transfer relay and pre-charge circuitry
- Minimal telemetry hardware for recording yield and events

## Key principles

- Modularity: retrofit kit should be modular and serviceable.
- Safety-first design: pre-charge, isolation, and thermal protection.
- Serviceability: field-replaceable modules and simple diagnostic LED/serial output.

## Deployment view

Vehicles carry the reserve module; operator stations interact only at a higher level (identification, swap instructions). Diagrams should show the energy flow and control points.
