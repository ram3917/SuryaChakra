# 02. Requirements

## Functional requirements

- CS-F1: Support vehicle detection and accept SuryaExtend telemetry at operator console.
- CS-F2: Provide clear operator UI to indicate reserve battery presence and handling instructions.
- CS-F3: Ensure safe physical accommodation and charging handshake for vehicles with dual-battery systems.

## Non-functional requirements

- Reliability: Operator site must handle expected daily vehicle throughput with <1% failure for communications.
- Safety: Conform to local electrical safety and vehicle handling standards.
- Maintainability: Clear checklists for operator technicians.

## Acceptance criteria

- Operator can identify SuryaExtend vehicles and follow safe swap/park flow in >95% of pilot transactions.

## Open questions

- Exact telemetry format and minimal data set to exchange.
- Whether swap stations should provide any managed charging to reserve batteries.
