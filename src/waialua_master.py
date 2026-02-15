# ==============================================================================
# WAIALUA EDGE NODE | V11 GOLD MASTER REV_A | FINAL PRODUCTION KERNEL
# ==============================================================================
# NOTE:
# - This kernel is designed for Jupyter/Colab execution using ipywidgets.
# - For headless deployments, replace the widget rendering with a log-only runner.
# - For physical RPi 5 integration, map the power reader to smbus2 (I2C ADC).
# ==============================================================================

from __future__ import annotations

import datetime
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

# --- 1. CORE DEPENDENCIES ---
try:
    import polars as pl
    import ipywidgets as widgets
    from IPython.display import display, clear_output
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "CRITICAL FAILURE: Missing production libraries (Polars/IPyWidgets). "
        "Install via: pip install -r requirements.txt"
    ) from exc


# --- 2. PACE CONFIGURATION ---
@dataclass(frozen=True)
class SystemConfig:
    """Mission constants for the PACE control loop."""

    MAX_TEMP: float = 85.0
    V_NOMINAL: float = 3.7
    V_SAFE: float = 3.4
    DECAY: float = 0.012
    WINDOW: int = 5


C = SystemConfig()


class State(Enum):
    """PACE system state with associated UI color and label."""

    NOMINAL = ("#00FF00", "LIME")
    DEGRADED = ("#FFD700", "AMBER")
    EMERGENCY = ("#FF0000", "RED")


# --- 3. PRODUCTION ORCHESTRATOR ---
class Orchestrator:
    """Generates telemetry ticks, applies REQ_01 and REQ_04, and buffers results."""

    def __init__(self) -> None:
        self.v: float = 4.2
        self.state: State = State.NOMINAL
        self.logs: List[str] = []
        self.polling_interval: float = 1.0  # REQ_04 INITIAL

        self.buf = pl.DataFrame(
            schema={
                "tick": pl.Int64,
                "time": pl.Datetime,
                "temp": pl.Float64,
                "signal": pl.Float64,
                "voltage": pl.Float64,
                "state": pl.Utf8,
            }
        )

    def tick(self, i: int) -> Dict[str, Any]:
        """Run one mission tick."""
        now = datetime.datetime.now()

        # Simple voltage decay (simulation)
        self.v -= C.DECAY
        v_cur = round(max(self.v, 2.9), 3)

        # --- POWER GOVERNOR: ADAPTIVE POLLING (REQ_04) ---
        if v_cur > C.V_NOMINAL:
            self.state = State.NOMINAL
            self.polling_interval = 1.0  # 1Hz High-Resolution
        elif C.V_SAFE < v_cur <= C.V_NOMINAL:
            self.state = State.DEGRADED
            self.polling_interval = 5.0  # 0.2Hz Power Conservation
        else:
            self.state = State.EMERGENCY

        # Simulated sensor values
        raw_t = round(45.0 + random.uniform(-2, 3), 2)
        if random.random() < 0.15:
            raw_t = 98.5  # Simulated Thermal Fault (REQ_01 test vector)
        raw_s = round(-50.0 + random.gauss(0, 5), 2)

        # --- THERMAL GUARDRAIL (REQ_01) ---
        is_rej = raw_t > C.MAX_TEMP

        res: Dict[str, Any] = {
            "tick": i,
            "time": now,
            "voltage": v_cur,
            "temp": raw_t if not is_rej else None,
            "signal": raw_s if not is_rej else None,
            "state": self.state,
            "excursion": is_rej,
        }

        # Buffer only if not in emergency
        if self.state != State.EMERGENCY:
            row = pl.DataFrame(
                {
                    "tick": [i],
                    "time": [now],
                    "temp": [res["temp"]],
                    "signal": [res["signal"]],
                    "voltage": [v_cur],
                    "state": [self.state.name],
                },
                schema=self.buf.schema,
            )
            self.buf = pl.concat([self.buf, row])

            ts = now.strftime("%H:%M:%S")
            self.logs.insert(
                0,
                f"[{ts}] TICK_{i:03d} | {'REJECT' if is_rej else 'OK'} | "
                f"{v_cur}V | {raw_t if not is_rej else '!!!'}C",
            )

        return res


# --- 4. SYMMETRICAL TUI ENGINE ---
class TUIRenderer:
    """Renders a high-contrast HUD as HTML."""

    @staticmethod
    def render(data: Dict[str, Any], buf: pl.DataFrame, interval: float) -> str:
        color, label = data["state"].value

        # Gauge maps 3.0V..4.2V into 0..20 segments
        v_pos = int(((data["voltage"] - 3.0) / 1.2) * 20)
        v_pos = max(0, min(20, v_pos))
        v_gauge = f"[{'=' * v_pos}▶{'.' * (19 - v_pos)}]"

        ts_now = data["time"].strftime("%H:%M:%S")

        # Data availability: percentage of non-null temps
        avail = round((1 - (buf["temp"].null_count() / max(1, len(buf)))) * 100, 1)

        temp_display = data["temp"] if data["temp"] is not None else "FAIL"
        signal_display = data["signal"] if data["signal"] is not None else "---"

        return f"""<div style="font-family:'Courier New', monospace; background:#000; color:#0FF; padding:20px; border:2px solid #333; width:600px; border-radius:10px;">
  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #333; padding-bottom:10px; margin-bottom:15px;">
    <span style="font-weight:bold;">📡 WAIALUA_V11_MASTER</span>
    <span style="color:#FFF; font-weight:bold;">CLOCK: {ts_now}</span>
    <span style="color:{color}; font-weight:bold;">[{label}]</span>
  </div>

  <div style="margin-bottom:20px;">
    <div style="color:#555; font-size:10px;">VOLTAGE_SWEEP_ANALYSIS (POLLING_RATE: {1/interval:.1f}Hz)</div>
    <div style="font-size:16px; letter-spacing:2px;">{v_gauge} {data['voltage']}V</div>
  </div>

  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; border-top:1px solid #333; padding-top:15px;">
    <div style="border:1px solid #222; padding:10px; text-align:center;">
      <div style="color:#555; font-size:10px;">THERMAL_SNS</div>
      <div style="color:{'#F00' if data['excursion'] else '#0F0'}; font-size:20px;">{temp_display}°C</div>
    </div>
    <div style="border:1px solid #222; padding:10px; text-align:center;">
      <div style="color:#555; font-size:10px;">SIGNAL_RAW</div>
      <div style="color:#fdcb6e; font-size:20px;">{signal_display}</div>
    </div>
    <div style="border:1px solid #222; padding:10px; text-align:center;">
      <div style="color:#555; font-size:10px;">MISSION_TICK</div>
      <div style="color:#FFF; font-size:20px;">{data['tick']:03d}</div>
    </div>
    <div style="border:1px solid #222; padding:10px; text-align:center;">
      <div style="color:#555; font-size:10px;">DATA_AVAIL</div>
      <div style="color:#0FF; font-size:20px;">{avail}%</div>
    </div>
  </div>
</div>
"""


def main() -> None:
    """Interactive run loop (Jupyter/Colab)."""
    orc = Orchestrator()
    hud_view = widgets.Output()
    log_view = widgets.Output()

    display(widgets.VBox([hud_view, log_view]))

    for i in range(1, 101):
        data = orc.tick(i)

        with hud_view:
            clear_output(wait=True)
            display(widgets.HTML(TUIRenderer.render(data, orc.buf, orc.polling_interval)))

        with log_view:
            clear_output(wait=True)
            l_html = f"""<div style='background:#000; color:#555; font-family:monospace; padding:15px; border:2px solid #333; width:600px; font-size:11px; margin-top:10px; border-radius:5px;'>
  <div style="color:#444; border-bottom:1px solid #222; margin-bottom:5px;">// MISSION_EVENT_LOG</div>
  {'<br>'.join(orc.logs[:5])}
</div>
"""
            display(widgets.HTML(l_html))

        if data["state"] == State.EMERGENCY:
            print("SAFE MODE: MISSION TERMINATED.")
            break

        # ROAD 1: DYNAMIC HEARTBEAT (REQ_04 ALIGNMENT)
        time.sleep(orc.polling_interval)


if __name__ == "__main__":
    main()
