import pandas as pd
import plotly.graph_objs as go

# Load the telemetry data for both drivers
car1_data = pd.read_csv('car1_actions_plotly.csv')
car2_data = pd.read_csv('car2_actions_plotly.csv')

# Normalize time to start from zero for both drivers
car1_data['Normalized Time'] = car1_data['Time'] - car1_data['Time'].iloc[0]
car2_data['Normalized Time'] = car2_data['Time'] - car2_data['Time'].iloc[0]

# Interpolate time over distance for alignment
car1_interp = pd.Series(car1_data['Normalized Time'].values, index=car1_data['Distance']).reindex(car2_data['Distance'], method="nearest")
car2_interp = pd.Series(car2_data['Normalized Time'].values, index=car2_data['Distance'])

# Calculating the time delta (car2 - car1)
lap_delta = car2_interp - car1_interp

# Create the plot
fig = go.Figure()

# Adding the Lap Delta line
fig.add_trace(go.Scatter(
    x=car2_data['Distance'],
    y=lap_delta,
    mode='lines',
    name='Lap Delta (Car 2 - Car 1)',
    line=dict(width=2)
))

# Add a zero reference line
fig.add_trace(go.Scatter(
    x=car2_data['Distance'],
    y=[0] * len(car2_data['Distance']),
    mode='lines',
    name='Zero Reference',
    line=dict(color='gray', dash='dash')
))

# Customize the layout
fig.update_layout(
    title="Lap Delta Plot: Time Difference between Car 1 and Car 2",
    xaxis_title="Distance (meters)",
    yaxis_title="Time Delta (seconds)",
    legend=dict(x=0.05, y=0.95),
    template="plotly_dark"
)

# Show the plot
fig.show()
