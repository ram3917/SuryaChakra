# 05. Interfaces

## Internal interfaces

- BMS ↔ MPPT: status and charging control signals.
- BMS ↔ Transfer relay: pre-charge and transfer enable.

## External interfaces

- Vehicle main drive battery system (mechanical and electrical handshake).
- Operator consoles at swap stations (identification, handling guidance).
- Supplier test equipment for QC flows.

## Interface contracts

- Minimal telemetry packet: timestamp, reserve SOC, panel yield (Wh), transfer events, error codes.
- Safety handshake: pre-charge success required before closing main relay.
