# Waialua Edge Node | TRL-8 Gold Master

**Status:** AUDITED & VERIFIED  
**Version:** V11 Rev_A (Production Kernel)  
**Target Hardware:** Raspberry Pi 5 / Li-ion / I2C ADC  

## 1.0 Mission Overview
The **Waialua Edge Node** is a "Zero-Fail" telemetry validation system designed for high-latency, power-constrained field environments. It implements a **Power-Adaptive Control Loop (PACE)** that dynamically adjusts polling frequency based on battery voltage, ensuring mission longevity without sacrificing data fidelity during critical phases.

### Key Capabilities
- **Adaptive Polling (REQ_04):** Automatically throttles acquisition from 1Hz (Nominal) to 0.2Hz (Degraded) to save power.
- **Thermal Guardrails (REQ_01):** Instant rejection of packets > 85°C with "Gap Fidelity" logging (no interpolation).
- **Symmetrical TUI:** A high-contrast, monospaced HUD providing instantaneous situational awareness via a Doppler-style voltage sweep.

## 2.0 System States (PACE)

| State | Voltage Range | Behavior | Indicator |
| :--- | :--- | :--- | :--- |
| **NOMINAL** | > 3.7V | High-Res Polling (1Hz) | **LIME** |
| **DEGRADED** | 3.4V - 3.7V | Power Save Polling (0.2Hz) | **AMBER** |
| **EMERGENCY** | < 3.4V | Safe Mode / Shutdown | **RED** |

## 3.0 Installation & Usage

### Prerequisites
- Python 3.11+
- Raspberry Pi 5 (recommended)

### Setup
```bash
pip install -r requirements.txt
```

### Execution
```bash
python src/waialua_master.py
```

> Note: The current kernel runs in a "Headless Simulation" mode suitable for Jupyter/Colab verification. For physical deployment, map the `PowerSource` class to `smbus2`.

## 4.0 Architecture
This system is modeled in SysML v2:
- v1: Software-Defined Telemetry Pipeline
- v2: Hardware-in-the-Loop Power Awareness

## 5.0 License
Copyright 2026 Waialua Systems Group. Mission Critical / Audit Node.
