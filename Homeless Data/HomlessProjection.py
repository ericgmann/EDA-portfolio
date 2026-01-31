# --- Import libraries ---
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Read and clean data ---
data = pd.read_csv("HomlessData.csv")
data.columns = data.columns.str.strip()

# Clean numeric data
for col in ['Total Population']:
    data[col] = (
        data[col]
        .astype(str)
        .str.replace('"', '')
        .str.replace(',', '')
        .astype(float)
    )

# --- Compute homeless rate ---

data = data.sort_values(by='Year')

# ==================================================
# 1️⃣ Table Figure
# ==================================================
table_fig = go.Figure(
    data=[
        go.Table(
            header=dict(
                values=list(data.columns),
                fill_color='rgb(48, 84, 150)',
                font=dict(color='white', size=14),
                align='center'
            ),
            cells=dict(
                values=[data[col] for col in data.columns],
                fill_color='rgb(240, 240, 255)',
                align='center',
                font=dict(size=12)
            )
        )
    ]
)
table_fig.update_layout(
    title=dict(text="U.S. Homelessness Data (2010–2025)", x=0.5, font=dict(size=22))
)

# ==================================================
# 2️⃣ Line Plot: Year vs Homeless Population
# ==================================================
fig_population = px.line(
    data,
    x='Year',
    y='Homeless Population',
    title='U.S. Homeless Population Over Time',
    markers=True,
    line_shape='spline',
    color_discrete_sequence=['#0077b6']
)
fig_population.update_layout(title_x=0.5, template='plotly_white')

# ==================================================
# 3️⃣ Line Plot: Year vs Homeless Rate (%)
# ==================================================
fig_rate = px.line(
    data,
    x='Year',
    y='Percent (%)',
    title='U.S. Homeless Rate (% of Total Population)',
    markers=True,
    line_shape='spline',
    color_discrete_sequence=['#e63946']
)
fig_rate.update_layout(title_x=0.5, template='plotly_white')

# ==================================================
# 🔮 Projected Homeless Population (2026–2030) — Polynomial Curve Fit
# ==================================================

# Fit a 2nd-degree polynomial to capture curve trends
coeffs = np.polyfit(data['Year'], data['Homeless Population'], deg=2)
poly = np.poly1d(coeffs)

# Generate smooth curve up to 2030
year_range = np.arange(data['Year'].min(), 2031)
fitted_values = poly(year_range)

# Identify last known year for separation
last_year = data['Year'].max()
future_mask = year_range > last_year

# Create projection plot
fig_projection = go.Figure()

# Actual data
fig_projection.add_trace(go.Scatter(
    x=data['Year'],
    y=data['Homeless Population'],
    mode='lines+markers',
    name='Actual Data',
    line=dict(color='#2a9d8f', width=3)
))

# Historical trend (fitted curve)
fig_projection.add_trace(go.Scatter(
    x=year_range[~future_mask],
    y=fitted_values[~future_mask],
    mode='lines',
    name='Trend Fit',
    line=dict(color='#264653', width=2, dash='dot')
))

# Future projection (2026–2030)
fig_projection.add_trace(go.Scatter(
    x=year_range[future_mask],
    y=fitted_values[future_mask],
    mode='lines+markers',
    name='Projected (2026–2030)',
    line=dict(color='#f4a261', width=3, dash='dash')
))

fig_projection.update_layout(
    title="Projected U.S. Homeless Population (2026–2030, Polynomial Trend)",
    xaxis_title="Year",
    yaxis_title="Homeless Population",
    template='plotly_white',
    title_x=0.5,
    legend=dict(bgcolor='rgba(255,255,255,0.8)')
)



# ==================================================
# 5️⃣ Build HTML Report
# ==================================================
html_header = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>U.S. Homelessness Data Report</title>
<style>
    body {
        font-family: 'Segoe UI', Roboto, sans-serif;
        margin: 0;
        background-color: #f9fafc;
        color: #222;
    }
    header {
        background: linear-gradient(90deg, #023e8a, #0077b6);
        color: white;
        text-align: center;
        padding: 50px 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    header h1 {
        margin: 0;
        font-size: 2.5em;
    }
    header p {
        font-size: 1.2em;
        margin-top: 10px;
    }
    section {
        max-width: 1100px;
        margin: 40px auto;
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    h2 {
        border-left: 6px solid #0077b6;
        padding-left: 10px;
        color: #0077b6;
        font-size: 1.6em;
    }
</style>
</head>
<body>
<header>
    <h1>📊 U.S. Homelessness Analysis (2010–2030)</h1>
    <p>Trends, Rates, and Future Projections</p>
</header>
<section>
    <h2>1. Original Data Table</h2>
"""

html_middle = """
</section>
<section>
    <h2>2. Homeless Population Over Time</h2>
"""

html_middle2 = """
</section>
<section>
    <h2>3. Homeless Rate (% of Total Population)</h2>
"""

html_middle3 = """
</section>
<section>
    <h2>4. Projected Homeless Population (2026–2030)</h2>
"""

html_footer = """
</section>
<footer style="text-align:center; padding:20px; color:#555; font-size:0.9em;">
    <p>Generated using Python, Pandas, NumPy, and Plotly</p>
</footer>
</body>
</html>
"""

# ==================================================
# 6️⃣ Write everything to an HTML file
# ==================================================
with open("Homeless_Report.html", "w", encoding="utf-8") as f:
    f.write(html_header)
    f.write(table_fig.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write(html_middle)
    f.write(fig_population.to_html(full_html=False, include_plotlyjs=False))
    f.write(html_middle2)
    f.write(fig_rate.to_html(full_html=False, include_plotlyjs=False))
    f.write(html_middle3)
    f.write(fig_projection.to_html(full_html=False, include_plotlyjs=False))
    f.write(html_footer)

print("report generated: Homeless_Report.html — open it in your browser!")
