import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_field_diagram(df, player):
    """
    Creates a cricket field diagram showing boundary distribution
    by phase for a selected batter.
    4s = green dots, 6s = red dots
    Distributed around field based on over phase
    """
    pdf = df[df['batter'] == player].copy()

    fours = pdf[pdf['runs_batter'] == 4].copy()
    sixes = pdf[pdf['runs_batter'] == 6].copy()

    def get_positions(deliveries, radius_base, spread):
        np.random.seed(42)
        n = len(deliveries)
        if n == 0:
            return [], []
        # Distribute by phase angle zones
        phase_angles = {
            'Powerplay': (0, 120),
            'Middle': (120, 240),
            'Death': (240, 360)
        }
        xs, ys = [], []
        for _, row in deliveries.iterrows():
            phase = row.get('phase', 'Middle')
            a_min, a_max = phase_angles.get(phase, (0, 360))
            angle = np.radians(np.random.uniform(a_min, a_max))
            radius = radius_base + np.random.uniform(-spread, spread)
            xs.append(radius * np.cos(angle))
            ys.append(radius * np.sin(angle))
        return xs, ys

    four_x, four_y = get_positions(fours, 0.65, 0.2)
    six_x, six_y = get_positions(sixes, 0.88, 0.08)

    fig = go.Figure()

    # ── Field circles ──
    theta = np.linspace(0, 2 * np.pi, 300)

    # Boundary
    fig.add_trace(go.Scatter(
        x=np.cos(theta), y=np.sin(theta),
        mode='lines', line=dict(color='#4ade80', width=2),
        showlegend=False, hoverinfo='skip'
    ))

    # 30-yard circle
    fig.add_trace(go.Scatter(
        x=0.65 * np.cos(theta), y=0.65 * np.sin(theta),
        mode='lines', line=dict(color='#4ade80', width=1, dash='dash'),
        showlegend=False, hoverinfo='skip'
    ))

    # Pitch rectangle
    fig.add_shape(type='rect',
        x0=-0.04, y0=-0.13, x1=0.04, y1=0.13,
        fillcolor='#d4a853', opacity=0.6,
        line=dict(color='#a07840', width=1)
    )

    # Crease lines
    for y in [-0.1, 0.1]:
        fig.add_shape(type='line',
            x0=-0.04, y0=y, x1=0.04, y1=y,
            line=dict(color='white', width=1)
        )

    # Phase zone labels
    phase_labels = [
        dict(x=0, y=0.5, text="Powerplay Zone", angle=0),
        dict(x=-0.5, y=-0.25, text="Middle Zone", angle=0),
        dict(x=0.5, y=-0.25, text="Death Zone", angle=0),
    ]
    for lbl in phase_labels:
        fig.add_annotation(
            x=lbl['x'], y=lbl['y'],
            text=lbl['text'],
            showarrow=False,
            font=dict(size=9, color='rgba(255,255,255,0.3)'),
        )

    # ── Boundaries ──
    if four_x:
        fig.add_trace(go.Scatter(
            x=four_x, y=four_y,
            mode='markers',
            marker=dict(color='#4ade80', size=9, opacity=0.8,
                        line=dict(color='white', width=0.5)),
            name=f'Fours ({len(fours)})',
            hovertemplate='Four<extra></extra>'
        ))

    if six_x:
        fig.add_trace(go.Scatter(
            x=six_x, y=six_y,
            mode='markers',
            marker=dict(color='#f87171', size=12, opacity=0.85,
                        symbol='star',
                        line=dict(color='white', width=0.5)),
            name=f'Sixes ({len(sixes)})',
            hovertemplate='Six<extra></extra>'
        ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1a3a1a',
        title=dict(
            text=f'{player} — Boundary Map',
            font=dict(size=16, color='white'),
            x=0.5
        ),
        xaxis=dict(range=[-1.15, 1.15], showgrid=False,
                   zeroline=False, showticklabels=False),
        yaxis=dict(range=[-1.15, 1.15], showgrid=False,
                   zeroline=False, showticklabels=False,
                   scaleanchor='x'),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(color='white', size=11),
            x=0.01, y=0.99
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=480,
        annotations=[
            dict(x=0, y=-1.12, text="N", showarrow=False,
                 font=dict(size=12, color='rgba(255,255,255,0.4)')),
        ]
    )

    return fig


def player_strength_weakness(df, player):
    """
    Returns strength/weakness radar chart and summary labels
    for a player's batting performance by phase.
    """
    pdf = df[df['batter'] == player].copy()
    if pdf.empty:
        return None, None

    phases = ['Powerplay', 'Middle', 'Death']
    phase_data = {}

    for phase in phases:
        p = pdf[pdf['phase'] == phase]
        if len(p) < 5:
            phase_data[phase] = {'sr': 0, 'runs': 0, 'balls': 0, 'dot_pct': 0}
            continue
        runs = p['runs_batter'].sum()
        balls = len(p)
        sr = round(runs / balls * 100, 1)
        dots = ((p['runs_batter'] == 0) & (p['extras_type'] == '')).sum()
        dot_pct = round(dots / balls * 100, 1)
        phase_data[phase] = {
            'sr': sr, 'runs': runs,
            'balls': balls, 'dot_pct': dot_pct
        }

    # Radar chart
    categories = ['Powerplay SR', 'Middle SR', 'Death SR',
                  'Powerplay Consistency', 'Middle Consistency', 'Death Consistency']

    # Normalize SR to 0-100 scale (200 SR = 100%)
    def norm_sr(sr): return min(sr / 2, 100)
    # Consistency = inverse of dot ball % (lower dots = more consistent)
    def norm_con(dot_pct): return max(100 - dot_pct, 0)

    values = [
        norm_sr(phase_data['Powerplay']['sr']),
        norm_sr(phase_data['Middle']['sr']),
        norm_sr(phase_data['Death']['sr']),
        norm_con(phase_data['Powerplay']['dot_pct']),
        norm_con(phase_data['Middle']['dot_pct']),
        norm_con(phase_data['Death']['dot_pct']),
    ]
    values += [values[0]]  # close the polygon
    categories += [categories[0]]

    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 212, 170, 0.2)',
        line=dict(color='#00d4aa', width=2),
        name=player
    ))
    radar_fig.update_layout(
        polar=dict(
            bgcolor='#1e2130',
            radialaxis=dict(
                visible=True, range=[0, 100],
                color='rgba(255,255,255,0.3)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            angularaxis=dict(
                color='white',
                gridcolor='rgba(255,255,255,0.1)'
            )
        ),
        paper_bgcolor='#0e1117',
        template='plotly_dark',
        title=dict(
            text=f'{player} — Strength & Weakness Radar',
            font=dict(size=15, color='white'), x=0.5
        ),
        showlegend=False,
        height=420,
        margin=dict(l=60, r=60, t=60, b=40)
    )

    # Determine strong/weak phases
    sr_scores = {p: phase_data[p]['sr'] for p in phases}
    valid = {p: v for p, v in sr_scores.items() if v > 0}

    if valid:
        strong_phase = max(valid, key=valid.get)
        weak_phase = min(valid, key=valid.get)
    else:
        strong_phase = weak_phase = 'N/A'

    summary = {
        'phase_data': phase_data,
        'strong_phase': strong_phase,
        'weak_phase': weak_phase,
        'strong_sr': phase_data[strong_phase]['sr'] if strong_phase != 'N/A' else 0,
        'weak_sr': phase_data[weak_phase]['sr'] if weak_phase != 'N/A' else 0,
    }

    return radar_fig, summary