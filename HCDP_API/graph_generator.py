import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_climatogram_file(df, output_path=None, title="Monthly Climate Averages", auto_open=True):
    """
    Creates an interactive Climatogram (Temperature + Rainfall) from a DataFrame
    and saves it to an HTML file.
    Args:
        df: DataFrame with columns ['Month', 'Temp_C', 'Rainfall_mm']
        output_path: Absolute path to save the HTML. If None, saves to script directory.
        title: Title of the chart.
        auto_open: If True, opens the browser automatically.
    Returns:
        Absolute path to the generated HTML file.
    """
    # Use script directory if no path provided
    if output_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "climate_chart.html")

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add Rainfall (Bars) on Secondary Y-Axis
    fig.add_trace(
        go.Bar(
            x=df['Month'], 
            y=df['Rainfall_mm'], 
            name="Rainfall (mm)",
            marker_color='rgba(135, 206, 235, 0.7)',
            hovertemplate='%{x}: %{y}mm<extra></extra>'
        ),
        secondary_y=True,
    )

    # Add Temperature (Line) on Primary Y-Axis
    fig.add_trace(
        go.Scatter(
            x=df['Month'], 
            y=df['Temp_C'], 
            name="Avg Temperature (°C)",
            mode='lines+markers',
            line=dict(color='firebrick', width=3),
            hovertemplate='%{x}: %{y}°C<extra></extra>'
        ),
        secondary_y=False,
    )

    # Configure Layout
    fig.update_layout(
        title={
            'text': title,
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20)
        },
        xaxis_title="Month",
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.5)'),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='white',
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        title_text="Temperature (°C)", 
        secondary_y=False, 
        color="firebrick",
        gridcolor='rgba(0, 0, 0, 0.1)',
        showgrid=True,
        zeroline=False
    )
    fig.update_yaxes(
        title_text="Rainfall (mm)", 
        secondary_y=True, 
        color="steelblue",
        showgrid=False,
        zeroline=False
    )

    # Save and optionally show
    fig.write_html(output_path)
    if auto_open:
        fig.show()
    
    return os.path.abspath(output_path)

if __name__ == "__main__":
    # Mock Data for Hilo, HI
    data = {
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'Temp_C': [22.1, 22.0, 22.3, 22.8, 23.6, 24.4, 25.0, 25.4, 25.3, 24.8, 23.8, 22.8],
        'Rainfall_mm': [245, 238, 342, 290, 201, 185, 240, 285, 248, 252, 365, 305]
    }
    df = pd.DataFrame(data)

    print("[*] Generating interactive Plotly Climatogram...")
    path = create_climatogram_file(df, title="Interactive Climatogram: Hilo, Hawaii", auto_open=False)
    print(f"[+] Chart saved and viewable at: {path}")
