# Interface Control Document (ICD) | Waialua V11

**Document ID:** WAI-ICD-011  
**Date:** 2026-02-14  
**Classification:** TRL-8 Audit Artifact  

## 1.0 Hardware Interfaces (HIL)

| Interface ID | Component | Protocol | Input | Output | Frequency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IF-HW-01** | PowerReader | I2C / ADC | Analog V (Li-ion) | Float (Volts) | Dynamic (1Hz/0.2Hz) |
| **IF-HW-02** | RPi 5 GPIO | Internal | Temp Sensor | Float (Celsius) | Dynamic |

## 2.0 Software Interfaces (PACE Logic)

| Interface ID | Function | Source | Destination | Data Type | Constraint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **IF-SW-01** | `Orchestrator.tick` | System Clock | Data Buffer | `Dict[str, Any]` | Schema-Hardened |
| **IF-SW-02** | `PowerGovernor` | Voltage State | Polling Loop | `float` (Interval) | 1.0s or 5.0s |
| **IF-SW-03** | `DataIngress` | Raw Sensor | Validator | `float` | None |

## 3.0 Human-Machine Interface (TUI)

| Interface ID | Element | Type | Content | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **IF-HMI-01** | Doppler Gauge | Visual | `[===▶....]` | Voltage mapping (3.0-4.2V) |
| **IF-HMI-02** | Status Beacon | Text | `NOMINAL` / `EMERGENCY` | Color-Coded (Lime/Red) |
| **IF-HMI-03** | Data Availability | Metric | `Float %` | Null-Count / Total Ticks |

## 4.0 Persistence Interfaces

| Interface ID | File Type | Trigger | Content |
| :--- | :--- | :--- | :--- |
| **IF-STORE-01** | Parquet | End-of-Mission | Full Telemetry Buffer |
| **IF-STORE-02** | Event Log | Real-time | State Transitions & Rejections |
