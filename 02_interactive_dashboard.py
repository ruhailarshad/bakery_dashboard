from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html

# --------------------------------------------------------------------
# Data
# --------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "bakery_clean.csv"

df = pd.read_csv(DATA, parse_dates=["Date", "YearMonth"])

CITY_COORDS = {
    "London":  {"lat": 51.5074, "lon": -0.1278},
    "Paris":   {"lat": 48.8566, "lon":  2.3522},
    "Bonn":    {"lat": 50.7374, "lon":  7.0982},
    "Seville": {"lat": 37.3891, "lon": -5.9845},
    "Napoli":  {"lat": 40.8518, "lon": 14.2681},
}

CITY_PALETTE = {
    "London":  "#3b82f6",
    "Paris":   "#ef4444",
    "Bonn":    "#22c55e",
    "Seville": "#f97316",
    "Napoli":  "#a855f7",
}

ALL_CITIES   = sorted(df["City"].unique())
ALL_PRODUCTS = sorted(df["Confectionary"].unique())
YEAR_MIN, YEAR_MAX = int(df["Year"].min()), int(df["Year"].max())

# --------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------
BG          = "#f1f5f9"
CARD_BG     = "#ffffff"
HEADER_BG   = "#0f172a"
ACCENT      = "#3b82f6"
TEXT_DARK   = "#0f172a"
TEXT_MED    = "#475569"
TEXT_LIGHT  = "#94a3b8"
BORDER      = "#e2e8f0"
SHADOW      = "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04)"
SHADOW_LG   = "0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04)"
RADIUS      = "12px"
FONT        = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"

KPI_COLORS = {
    "Revenue": {"accent": "#3b82f6", "bg": "#eff6ff", "icon": "💰"},
    "Cost":    {"accent": "#ef4444", "bg": "#fef2f2", "icon": "📦"},
    "Profit":  {"accent": "#22c55e", "bg": "#f0fdf4", "icon": "📈"},
    "Margin":  {"accent": "#f97316", "bg": "#fff7ed", "icon": "🎯"},
}

CHART_LAYOUT = dict(
    template="plotly_white",
    font=dict(family=FONT, color=TEXT_DARK),
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    margin=dict(l=16, r=16, t=48, b=16),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(size=12),
    ),
    title=dict(font=dict(size=14, color=TEXT_DARK, family=FONT), x=0.01, xanchor="left"),
    xaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False,
               tickfont=dict(size=11, color=TEXT_MED)),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9", zeroline=False,
               tickfont=dict(size=11, color=TEXT_MED)),
)

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def card(children, style=None):
    base = {
        "background": CARD_BG,
        "borderRadius": RADIUS,
        "boxShadow": SHADOW,
        "border": f"1px solid {BORDER}",
        "overflow": "hidden",
    }
    if style:
        base.update(style)
    return html.Div(children, style=base)


def kpi_card(label, value, subtitle=""):
    cfg = KPI_COLORS.get(label, {"accent": ACCENT, "bg": "#eff6ff", "icon": "•"})
    return html.Div(
        style={
            "background": CARD_BG,
            "borderRadius": RADIUS,
            "boxShadow": SHADOW,
            "border": f"1px solid {BORDER}",
            "padding": "20px 22px",
            "position": "relative",
            "overflow": "hidden",
        },
        children=[
            html.Div(style={
                "position": "absolute", "top": 0, "left": 0,
                "width": "4px", "height": "100%",
                "background": cfg["accent"],
            }),
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "flex-start",
            }, children=[
                html.Div([
                    html.Div(label.upper(), style={
                        "fontSize": "10px", "fontWeight": 700,
                        "letterSpacing": "0.08em", "color": TEXT_LIGHT,
                        "marginBottom": "6px",
                    }),
                    html.Div(value, style={
                        "fontSize": "26px", "fontWeight": 800,
                        "color": TEXT_DARK, "lineHeight": 1.1,
                        "fontVariantNumeric": "tabular-nums",
                    }),
                    html.Div(subtitle, style={
                        "fontSize": "11px", "color": TEXT_MED, "marginTop": "4px",
                    }),
                ]),
                html.Div(cfg["icon"], style={
                    "fontSize": "28px",
                    "background": cfg["bg"],
                    "borderRadius": "10px",
                    "padding": "8px 10px",
                    "lineHeight": 1,
                }),
            ]),
        ],
    )


def section_label(text):
    return html.Div(text, style={
        "fontSize": "11px", "fontWeight": 700, "letterSpacing": "0.06em",
        "color": TEXT_LIGHT, "textTransform": "uppercase",
        "marginBottom": "10px",
    })


def filter_label(text):
    return html.Div(text, style={
        "fontSize": "12px", "fontWeight": 600,
        "color": TEXT_MED, "marginBottom": "6px",
    })


def filter_df(cities, prods, years):
    cities = cities or []
    prods  = prods  or []
    if not cities or not prods:
        return df.iloc[0:0]
    y0, y1 = years
    mask = (df["City"].isin(cities)
            & df["Confectionary"].isin(prods)
            & df["Year"].between(y0, y1))
    return df.loc[mask].copy()


# --------------------------------------------------------------------
# App
# --------------------------------------------------------------------
app = Dash(__name__, title="European Bakery Dashboard",
           meta_tags=[{"name": "viewport",
                       "content": "width=device-width, initial-scale=1"}])

app.index_string = """
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: """ + FONT + """; background: """ + BG + """; }
  .Select-control, .Select-menu-outer { border-radius: 8px !important; }
  .Select-control { border-color: """ + BORDER + """ !important; }
  .Select-control:hover { border-color: """ + ACCENT + """ !important; }
  .rc-slider-track { background-color: """ + ACCENT + """ !important; }
  .rc-slider-handle { border-color: """ + ACCENT + """ !important; }
  .rc-slider-dot-active { border-color: """ + ACCENT + """ !important; }
  .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
    border-color: """ + BORDER + """ !important;
  }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
"""

app.layout = html.Div(
    style={"fontFamily": FONT, "background": BG, "minHeight": "100vh"},
    children=[

        # ---- Header -------------------------------------------------------
        html.Div(
            style={
                "background": HEADER_BG,
                "padding": "0 32px",
                "height": "64px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "position": "sticky",
                "top": 0,
                "zIndex": 1000,
                "boxShadow": "0 1px 3px rgba(0,0,0,0.3)",
            },
            children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px"}, children=[
                    html.Div("🥐", style={"fontSize": "26px"}),
                    html.Div([
                        html.Div("European Bakery Intelligence", style={
                            "color": "#ffffff", "fontSize": "16px",
                            "fontWeight": 700, "letterSpacing": "-0.02em",
                        }),
                        html.Div("Sales & Profitability · 2000–2005", style={
                            "color": "#94a3b8", "fontSize": "11px",
                            "marginTop": "1px",
                        }),
                    ]),
                ]),
            ],
        ),

        # ---- Body ---------------------------------------------------------
        html.Div(style={"padding": "24px 32px", "maxWidth": "1400px", "margin": "0 auto"}, children=[

            # ---- Filters --------------------------------------------------
            card(
                style={"padding": "20px 24px", "marginBottom": "20px"},
                children=[
                    section_label("Filters"),
                    html.Div(
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "1fr 1fr 1.5fr",
                            "gap": "20px",
                            "alignItems": "end",
                        },
                        children=[
                            html.Div([
                                filter_label("City"),
                                dcc.Dropdown(
                                    id="f-city",
                                    options=[{"label": c, "value": c} for c in ALL_CITIES],
                                    value=ALL_CITIES,
                                    multi=True,
                                    clearable=False,
                                    style={"fontSize": "13px"},
                                ),
                            ]),
                            html.Div([
                                filter_label("Confectionary"),
                                dcc.Dropdown(
                                    id="f-prod",
                                    options=[{"label": p, "value": p} for p in ALL_PRODUCTS],
                                    value=ALL_PRODUCTS,
                                    multi=True,
                                    clearable=False,
                                    style={"fontSize": "13px"},
                                ),
                            ]),
                            html.Div([
                                filter_label(f"Year range  ·  {YEAR_MIN} – {YEAR_MAX}"),
                                dcc.RangeSlider(
                                    id="f-year",
                                    min=YEAR_MIN, max=YEAR_MAX, step=1,
                                    value=[YEAR_MIN, YEAR_MAX],
                                    marks={y: {"label": str(y),
                                               "style": {"fontSize": "11px",
                                                          "color": TEXT_MED}}
                                           for y in range(YEAR_MIN, YEAR_MAX + 1)},
                                    tooltip={"placement": "bottom",
                                             "always_visible": False},
                                ),
                            ]),
                        ],
                    ),
                ],
            ),

            # ---- KPI row --------------------------------------------------
            html.Div(
                id="kpi-row",
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "16px",
                    "marginBottom": "20px",
                },
            ),

            # ---- Map + Trend ----------------------------------------------
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "5fr 7fr",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
                children=[
                    card(children=[dcc.Graph(id="map-fig",
                                             config={"displayModeBar": False})]),
                    card(children=[dcc.Graph(id="trend-fig",
                                             config={"displayModeBar": False})]),
                ],
            ),

            # ---- Heatmap + Product bar ------------------------------------
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "7fr 5fr",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
                children=[
                    card(children=[dcc.Graph(id="heat-fig",
                                             config={"displayModeBar": False})]),
                    card(children=[dcc.Graph(id="prod-fig",
                                             config={"displayModeBar": False})]),
                ],
            ),

            # ---- Profit by city + Profit per unit ------------------------
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "5fr 7fr",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
                children=[
                    card(children=[dcc.Graph(id="city-bar-fig",
                                             config={"displayModeBar": False})]),
                    card(children=[dcc.Graph(id="ppu-fig",
                                             config={"displayModeBar": False})]),
                ],
            ),

            # ---- Annual trend + YoY growth -------------------------------
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "7fr 5fr",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
                children=[
                    card(children=[dcc.Graph(id="annual-fig",
                                             config={"displayModeBar": False})]),
                    card(children=[dcc.Graph(id="yoy-fig",
                                             config={"displayModeBar": False})]),
                ],
            ),

            # ---- Product mix + Margin distribution -----------------------
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "7fr 5fr",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
                children=[
                    card(children=[dcc.Graph(id="mix-fig",
                                             config={"displayModeBar": False})]),
                    card(children=[dcc.Graph(id="box-fig",
                                             config={"displayModeBar": False})]),
                ],
            ),

            # ---- Seasonality heatmap (full width) ------------------------
            card(
                style={"marginBottom": "16px"},
                children=[dcc.Graph(id="season-fig",
                                    config={"displayModeBar": False})],
            ),

            # ---- Volume vs profit scatter (full width) -------------------
            card(
                style={"marginBottom": "16px"},
                children=[dcc.Graph(id="scatter-fig",
                                    config={"displayModeBar": False})],
            ),

            # ---- Table ----------------------------------------------------
            card(
                style={"padding": "20px 24px", "marginBottom": "24px"},
                children=[
                    html.Div(style={
                        "display": "flex", "justifyContent": "space-between",
                        "alignItems": "center", "marginBottom": "14px",
                    }, children=[
                        html.Div([
                            html.Div("Top Transactions", style={
                                "fontSize": "14px", "fontWeight": 700,
                                "color": TEXT_DARK,
                            }),
                            html.Div("Highest-profit transactions in current selection",
                                     style={"fontSize": "11px", "color": TEXT_LIGHT,
                                            "marginTop": "2px"}),
                        ]),
                        html.Div(id="tx-count", style={
                            "fontSize": "11px", "color": TEXT_MED,
                            "background": "#f1f5f9", "padding": "4px 10px",
                            "borderRadius": "20px", "fontWeight": 600,
                        }),
                    ]),
                    dash_table.DataTable(
                        id="tx-table",
                        page_size=10,
                        style_table={"overflowX": "auto", "borderRadius": "8px",
                                     "border": f"1px solid {BORDER}"},
                        style_cell={
                            "padding": "10px 14px",
                            "fontFamily": FONT,
                            "fontSize": "12px",
                            "color": TEXT_DARK,
                            "border": f"1px solid {BORDER}",
                            "whiteSpace": "normal",
                        },
                        style_header={
                            "backgroundColor": "#f8fafc",
                            "color": TEXT_MED,
                            "fontWeight": 700,
                            "fontSize": "11px",
                            "letterSpacing": "0.04em",
                            "textTransform": "uppercase",
                            "border": f"1px solid {BORDER}",
                            "padding": "10px 14px",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"},
                             "backgroundColor": "#fafafa"},
                            {"if": {"column_id": "Profit"},
                             "color": "#16a34a", "fontWeight": 700},
                        ],
                    ),
                ],
            ),

        ]),
    ],
)


# --------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------
@app.callback(
    Output("kpi-row",      "children"),
    Output("map-fig",      "figure"),
    Output("trend-fig",    "figure"),
    Output("heat-fig",     "figure"),
    Output("prod-fig",     "figure"),
    Output("city-bar-fig", "figure"),
    Output("ppu-fig",      "figure"),
    Output("annual-fig",   "figure"),
    Output("yoy-fig",      "figure"),
    Output("mix-fig",      "figure"),
    Output("box-fig",      "figure"),
    Output("season-fig",   "figure"),
    Output("scatter-fig",  "figure"),
    Output("tx-table",     "data"),
    Output("tx-table",     "columns"),
    Output("tx-count",     "children"),
    Input("f-city",  "value"),
    Input("f-prod",  "value"),
    Input("f-year",  "value"),
)
def update_dashboard(cities, prods, years):
    sub = filter_df(cities, prods, years)

    empty_fig = go.Figure()
    empty_fig.update_layout(
        **CHART_LAYOUT,
        annotations=[dict(
            text="No data — adjust filters",
            showarrow=False, xref="paper", yref="paper",
            x=0.5, y=0.5, font=dict(size=14, color=TEXT_LIGHT),
        )],
    )

    if sub.empty:
        kpis = [kpi_card("Revenue", "—"), kpi_card("Cost", "—"),
                kpi_card("Profit", "—"), kpi_card("Margin", "—")]
        return (kpis, empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_fig,
                [], [], "0 rows")

    revenue = sub["Revenue"].sum()
    cost    = sub["Cost"].sum()
    profit  = sub["Profit"].sum()
    margin  = profit / revenue * 100

    kpis = [
        kpi_card("Revenue", f"£{revenue/1e6:,.2f}m", "Total top-line"),
        kpi_card("Cost",    f"£{cost/1e6:,.2f}m",    "Direct cost of goods"),
        kpi_card("Profit",  f"£{profit/1e6:,.2f}m",  "Revenue minus cost"),
        kpi_card("Margin",  f"{margin:.1f}%",         "Profit / revenue"),
    ]

    # ---- Map -----------------------------------------------------------
    geo = (sub.groupby("City")
              .agg(Profit=("Profit", "sum"),
                   Revenue=("Revenue", "sum"),
                   Margin=("Profit_Margin", "mean"))
              .reset_index())
    geo["lat"] = geo["City"].map(lambda c: CITY_COORDS[c]["lat"])
    geo["lon"] = geo["City"].map(lambda c: CITY_COORDS[c]["lon"])

    map_fig = px.scatter_geo(
        geo, lat="lat", lon="lon",
        size="Profit", color="City",
        color_discrete_map=CITY_PALETTE,
        hover_name="City",
        hover_data={
            "Revenue": ":,.0f",
            "Profit": ":,.0f",
            "Margin": ":.1%",
            "lat": False, "lon": False,
        },
        size_max=55,
        title="Profit by store location",
    )
    map_fig.update_geos(
        scope="europe", projection_type="natural earth",
        showcountries=True, countrycolor="#cbd5e1",
        showland=True, landcolor="#f8fafc",
        showocean=True, oceancolor="#e0f2fe",
        showcoastlines=True, coastlinecolor="#94a3b8",
        lataxis_range=[34, 60], lonaxis_range=[-12, 22],
    )
    map_layout = {**CHART_LAYOUT,
                  "legend": dict(orientation="h", y=-0.05, x=0.5,
                                 xanchor="center", font=dict(size=11))}
    map_fig.update_layout(**map_layout)

    # ---- Trend ---------------------------------------------------------
    trend = (sub.groupby(["YearMonth", "City"])["Profit"]
                .sum().reset_index())
    trend_fig = px.line(
        trend, x="YearMonth", y="Profit", color="City",
        color_discrete_map=CITY_PALETTE,
        title="Monthly profit trajectory",
        markers=False,
    )
    trend_fig.update_traces(line=dict(width=2.2))
    trend_fig.update_layout(
        **CHART_LAYOUT,
        yaxis_title="Profit (£)",
        xaxis_title="",
        legend_title="",
    )

    # ---- Heat-map ------------------------------------------------------
    heat = (sub.assign(M=sub["Profit_Margin"] * 100)
               .pivot_table(index="City", columns="Confectionary",
                            values="M", aggfunc="mean"))
    heat_fig = px.imshow(
        heat, text_auto=".1f",
        color_continuous_scale=[[0, "#fef2f2"], [0.4, "#fef9c3"], [1, "#dcfce7"]],
        aspect="auto",
        labels=dict(color="Margin %"),
        title="Profit margin (%) — city × product",
    )
    heat_layout = {**CHART_LAYOUT,
                   "coloraxis_showscale": True,
                   "coloraxis_colorbar": dict(
                       thickness=12, len=0.8, title="",
                       tickfont=dict(size=10, color=TEXT_MED)),
                   "xaxis": dict(tickfont=dict(size=11, color=TEXT_MED),
                                 tickangle=-20),
                   "yaxis": dict(tickfont=dict(size=11, color=TEXT_MED))}
    heat_fig.update_layout(**heat_layout)
    heat_fig.update_traces(
        textfont=dict(size=11, color=TEXT_DARK),
    )

    # ---- Product bar ---------------------------------------------------
    prod_tot = (sub.groupby("Confectionary")["Profit"]
                   .sum().sort_values(ascending=True)
                   .reset_index())
    prod_fig = px.bar(
        prod_tot, y="Confectionary", x="Profit",
        orientation="h",
        title="Profit by confectionary",
        color="Profit",
        color_continuous_scale=["#dbeafe", "#2563eb"],
        text=prod_tot["Profit"].apply(lambda v: f"£{v/1e3:,.0f}k"),
    )
    prod_fig.update_traces(
        textposition="outside",
        textfont=dict(size=11, color=TEXT_MED),
        marker_line_width=0,
    )
    prod_layout = {**CHART_LAYOUT,
                   "coloraxis_showscale": False,
                   "xaxis_title": "Profit (£)",
                   "yaxis_title": "",
                   "xaxis": dict(showgrid=True, gridcolor="#f1f5f9",
                                 zeroline=False,
                                 tickfont=dict(size=11, color=TEXT_MED)),
                   "yaxis": dict(showgrid=False,
                                 tickfont=dict(size=11, color=TEXT_MED))}
    prod_fig.update_layout(**prod_layout)

    # ---- Profit by city (horizontal bar) -------------------------------
    city_tot = (sub.groupby("City")["Profit"].sum()
                   .sort_values(ascending=True).reset_index())
    city_bar_fig = px.bar(
        city_tot, y="City", x="Profit",
        orientation="h",
        title="Cumulative profit by city",
        color="City", color_discrete_map=CITY_PALETTE,
        text=city_tot["Profit"].apply(lambda v: f"£{v/1e3:,.0f}k"),
    )
    city_bar_fig.update_traces(
        textposition="outside",
        textfont=dict(size=11, color=TEXT_MED),
        marker_line_width=0,
        showlegend=False,
    )
    city_bar_fig.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Profit (£)", yaxis_title="",
    )

    # ---- Profit per unit by city ---------------------------------------
    ppu = (sub.groupby("City")
              .apply(lambda g: g["Profit"].sum() / g["Units_Sold"].sum())
              .sort_values(ascending=True)
              .rename("PPU").reset_index())
    ppu_fig = px.bar(
        ppu, y="City", x="PPU",
        orientation="h",
        title="Average profit per unit sold (£)",
        color="City", color_discrete_map=CITY_PALETTE,
        text=ppu["PPU"].apply(lambda v: f"£{v:,.2f}"),
    )
    ppu_fig.update_traces(
        textposition="outside",
        textfont=dict(size=11, color=TEXT_MED),
        marker_line_width=0,
        showlegend=False,
    )
    ppu_fig.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Profit per unit (£)", yaxis_title="",
    )

    # ---- Annual profit trend by city -----------------------------------
    annual = (sub.groupby(["Year", "City"])["Profit"].sum().reset_index())
    annual_fig = px.line(
        annual, x="Year", y="Profit", color="City",
        color_discrete_map=CITY_PALETTE,
        markers=True,
        title="Annual profit trajectory by city",
    )
    annual_fig.update_traces(line=dict(width=2.4))
    annual_fig.update_layout(
        **CHART_LAYOUT,
        yaxis_title="Profit (£)", xaxis_title="",
        legend_title="",
    )

    # ---- Year-on-year growth (%) ---------------------------------------
    yoy = (sub.groupby(["Year", "City"])["Profit"].sum()
              .unstack("City").sort_index())
    yoy_pct = yoy.pct_change() * 100
    yoy_long = (yoy_pct.reset_index()
                       .melt(id_vars="Year", var_name="City",
                             value_name="Growth")
                       .dropna())
    yoy_fig = px.bar(
        yoy_long, x="Year", y="Growth", color="City",
        barmode="group",
        color_discrete_map=CITY_PALETTE,
        title="Year-on-year profit growth (%)",
    )
    yoy_fig.add_hline(y=0, line_width=1, line_color=TEXT_MED)
    yoy_fig.update_layout(
        **CHART_LAYOUT,
        yaxis_title="YoY growth (%)", xaxis_title="",
        legend_title="",
    )

    # ---- Product mix (100% stacked bar) --------------------------------
    mix = (sub.groupby(["City", "Confectionary"])["Profit"].sum()
              .unstack("Confectionary").fillna(0))
    mix_pct = mix.div(mix.sum(axis=1), axis=0) * 100
    mix_long = (mix_pct.reset_index()
                       .melt(id_vars="City", var_name="Confectionary",
                             value_name="Share"))
    mix_fig = px.bar(
        mix_long, x="City", y="Share", color="Confectionary",
        title="Product mix — share of city profit (%)",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    mix_fig.update_layout(
        **CHART_LAYOUT,
        barmode="stack",
        yaxis_title="Share of profit (%)", xaxis_title="",
        legend_title="",
    )

    # ---- Margin distribution boxplot -----------------------------------
    box_fig = px.box(
        sub.assign(MarginPct=sub["Profit_Margin"] * 100),
        x="City", y="MarginPct", color="City",
        color_discrete_map=CITY_PALETTE,
        points=False,
        title="Margin per transaction by city (%)",
    )
    box_fig.update_layout(
        **CHART_LAYOUT,
        yaxis_title="Profit margin (%)", xaxis_title="",
        showlegend=False,
    )

    # ---- Seasonality heatmap (year x month) ----------------------------
    season = (sub.groupby(["Year", "Month"])["Profit"].sum()
                 .unstack("Month") / 1e3)
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    season = season.reindex(columns=range(1, 13))
    season.columns = month_labels
    season_fig = px.imshow(
        season, text_auto=".0f",
        color_continuous_scale="YlGnBu",
        aspect="auto",
        labels=dict(color="Profit (£k)"),
        title="Seasonality — monthly profit (£k) by year",
    )
    season_layout = {**CHART_LAYOUT,
                     "coloraxis_colorbar": dict(
                         thickness=12, len=0.8, title="",
                         tickfont=dict(size=10, color=TEXT_MED)),
                     "xaxis": dict(tickfont=dict(size=11, color=TEXT_MED)),
                     "yaxis": dict(tickfont=dict(size=11, color=TEXT_MED))}
    season_fig.update_layout(**season_layout)

    # ---- Volume vs profit scatter --------------------------------------
    scatter_fig = px.scatter(
        sub, x="Units_Sold", y="Profit",
        color="City", symbol="Confectionary",
        color_discrete_map=CITY_PALETTE,
        opacity=0.75,
        title="Units sold vs. profit per transaction",
    )
    scatter_fig.update_traces(marker=dict(size=8, line=dict(width=0)))
    scatter_fig.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Units sold per transaction",
        yaxis_title="Profit per transaction (£)",
        legend_title="",
    )

    # ---- Table ---------------------------------------------------------
    top = (sub.nlargest(10, "Profit")
              [["Date", "City", "Confectionary", "Units_Sold",
                "Revenue", "Cost", "Profit"]]
              .assign(
                  Date=lambda d: d["Date"].dt.strftime("%d %b %Y"),
                  Revenue=lambda d: d["Revenue"].apply(lambda v: f"£{v:,.0f}"),
                  Cost=lambda d: d["Cost"].apply(lambda v: f"£{v:,.0f}"),
                  Profit=lambda d: d["Profit"].apply(lambda v: f"£{v:,.0f}"),
              ))
    cols = [{"name": c.replace("_", " "), "id": c} for c in top.columns]
    count = f"{len(sub):,} transactions"

    return (kpis, map_fig, trend_fig, heat_fig, prod_fig,
            city_bar_fig, ppu_fig, annual_fig, yoy_fig,
            mix_fig, box_fig, season_fig, scatter_fig,
            top.to_dict("records"), cols, count)


# --------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
