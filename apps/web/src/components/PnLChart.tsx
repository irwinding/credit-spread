import { useEffect, useState } from "react";
import Plot from "react-plotly.js";

import type { SnapshotPoint } from "../api/types";
import { readCssVarRgb } from "../lib/theme";

interface Props {
  points: SnapshotPoint[];
  underlying: string;
}

function readPalette() {
  return {
    panel: readCssVarRgb("--c-panel"),
    fg: readCssVarRgb("--c-fg"),
    muted: readCssVarRgb("--c-muted"),
    accent: readCssVarRgb("--c-accent"),
    grid: readCssVarRgb("--c-grid"),
    border: readCssVarRgb("--c-border"),
  };
}

export function PnLChart({ points, underlying }: Props) {
  const [palette, setPalette] = useState(readPalette);

  useEffect(() => {
    const obs = new MutationObserver(() => setPalette(readPalette()));
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => obs.disconnect();
  }, []);

  const x = points.map((p) => p.ts);
  const pnl = points.map((p) => Number(p.pnl_unrealised));
  const px = points.map((p) => Number(p.underlying_price));

  return (
    <Plot
      data={[
        {
          x,
          y: pnl,
          type: "scatter",
          mode: "lines",
          name: "PnL",
          line: { color: palette.accent, width: 2 },
          yaxis: "y",
          hovertemplate: "PnL: $%{y:.2f}<extra></extra>",
        },
        {
          x,
          y: px,
          type: "scatter",
          mode: "lines",
          name: `${underlying} price`,
          line: { color: palette.muted, width: 1.5, dash: "dot" },
          yaxis: "y2",
          hovertemplate: `${underlying}: $%{y:.2f}<extra></extra>`,
        },
      ]}
      layout={{
        autosize: true,
        height: 420,
        margin: { l: 60, r: 60, t: 24, b: 40 },
        paper_bgcolor: palette.panel,
        plot_bgcolor: palette.panel,
        font: { color: palette.fg, family: "Inter, sans-serif" },
        xaxis: { gridcolor: palette.grid, showgrid: true, zeroline: false },
        yaxis: {
          title: { text: "PnL ($)" },
          gridcolor: palette.grid,
          zerolinecolor: palette.border,
        },
        yaxis2: {
          title: { text: `${underlying} ($)` },
          overlaying: "y",
          side: "right",
          gridcolor: "transparent",
          zeroline: false,
        },
        legend: { orientation: "h", y: -0.18 },
        hovermode: "x unified",
      }}
      config={{ displaylogo: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
