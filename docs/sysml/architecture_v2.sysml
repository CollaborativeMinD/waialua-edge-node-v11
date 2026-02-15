package WaialuaPowerAwareSystem {
    doc "Waialua Edge Node v2.0 // Hardware-in-the-Loop (RPi 5)";

    import ScalarValues::*;

    // --- NEW ATTRIBUTES ---
    attribute def Volts;
    attribute def Amperes;
    attribute def Frequency; // For Sampling Rate

    item def PowerState {
        attribute voltage : Volts;
        attribute current_draw : Amperes;
    }

    // --- REVISED REQUIREMENTS ---
    requirement <REQ_03> PowerAwareness {
        doc "System shall monitor battery voltage and adjust operations to prevent unplanned shutdown.";
    }

    requirement <REQ_04> AdaptivePolling {
        doc "If voltage < 3.7V, polling frequency shall decrease by 80% (1Hz -> 0.2Hz).";
        subject part governor : PowerGovernor;
    }

    // --- UPDATED ARCHITECTURE ---
    part def RPi5Node {
        port pwr_in : PowerState;

        part power_bus : PowerSource {
            doc "Physical Li-ion + ADC Interface (I2C)";
            port out v_telemetry : PowerState;
        }

        part governor : PowerGovernor {
            doc "Logic: Implements PACE transition based on Voltage";
            port in v_sense : PowerState;
            port out sample_rate : Frequency;

            // State-based Logic (Finite State Machine)
            state power_states {
                state nominal;   // > 3.7V
                state degraded;  // 3.4V - 3.7V
                state safe_mode; // < 3.4V

                transition nominal to degraded
                    first v_sense.voltage < 3.7;

                transition degraded to safe_mode
                    first v_sense.voltage < 3.4;
            }
        }

        part telemetry_engine : TelemetrySystem {
            doc "Existing Logic from v1.0 (Imported)";
            port in rate_cmd : Frequency;
        }

        // --- CONTROL LOOP ---
        connect power_bus.v_telemetry to governor.v_sense;
        connect governor.sample_rate to telemetry_engine.rate_cmd;
    }
}
