package AerospaceTelemetryPipeline {
    doc "Zero-Defect Telemetry Validation & Transformation Pipeline // Waialua Node v1.0";

    import ScalarValues::*;

    // --- DOMAIN DEFINITIONS ---
    attribute def Celsius;
    attribute def DecibelMilliwatts;

    item def RawTelemetryPacket {
        attribute timestamp : String;
        attribute sensor_id : String;
        attribute raw_temp : Real;
        attribute signal_dbm : Real;
    }

    item def ValidatedTelemetry {
        attribute temperature : Celsius;
        attribute signal_strength : DecibelMilliwatts;
    }

    item def AggregatedMetrics {
        attribute mean_signal : DecibelMilliwatts;
        attribute window_size : Integer = 5;
    }

    // --- REQUIREMENTS (V-Model Left Side) ---
    requirement <REQ_01> ThermalLimit {
        doc "System must flag any component temperature exceeding 85°C as critical failure.";
        subject part validator : TelemetryValidator;
    }

    requirement <REQ_02> RollingAverage {
        doc "Signal strength must be smoothed over a 5-step rolling window to reduce noise.";
    }

    // --- PARTS & ARCHITECTURE ---
    part def TelemetrySystem {
        port in raw_stream : RawTelemetryPacket;
        port out hmi_display : AggregatedMetrics;
        port out error_log : String;

        part receiver : DataIngress { doc "DuckDB Direct Query"; }

        part validator : TelemetryValidator {
            doc "Pydantic v2 Validator";
            port in unverified : RawTelemetryPacket;
            port out verified : ValidatedTelemetry;
            port out rejection : String;

            constraint check_thermal {
                doc "Enforces <REQ_01>";
                unverified.raw_temp <= 85.0;
            }
        }

        part processor : SignalTransformer {
            doc "Polars Lazy API (Rolling Mean)";
            port in valid_data : ValidatedTelemetry;
            port out metrics : AggregatedMetrics;
        }

        part dashboard : MarimoInterface {
            doc "Marimo Reactive UI";
            port in metrics_in : AggregatedMetrics;
            port out visual_table;
        }

        // --- CONNECTIONS ---
        connect raw_stream to receiver.packet_in;
        connect receiver.data_out to validator.unverified;
        connect validator.verified to processor.valid_data;
        connect processor.metrics to dashboard.metrics_in;
        connect dashboard.visual_table to hmi_display;
        connect validator.rejection to error_log;
    }
}
