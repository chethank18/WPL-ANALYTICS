import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.analysis import (
    load_data, top_batters, top_bowlers, team_win_summary,
    run_rate_by_over, phase_batting, phase_bowling, toss_impact, venue_stats
)
from utils.player import player_batting_profile, player_bowling_profile
from utils.field_viz import create_field_diagram, player_strength_weakness

st.set_page_config(page_title="WPL Analytics", page_icon="🏏", layout="wide", initial_sidebar_state="expanded")

# ── GLOBAL CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080c14;
}

/* Main background */
.stApp {
    background: radial-gradient(ellipse at top, #1a0d0d 0%, #080c14 50%, #080c14 100%);
}

/* Hide streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid rgba(248, 113, 113, 0.1);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(248, 113, 113, 0.15);
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: rgba(255,255,255,0.5) !important;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 16px;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #991b1b, #b91c1c) !important;
    color: white !important;
    box-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a0d0d, #111827);
    border: 1px solid rgba(248, 113, 113, 0.2);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 0 20px rgba(248, 113, 113, 0.05);
}
[data-testid="metric-container"] label {
    color: rgba(255,255,255,0.5) !important;
    font-size: 12px !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f87171 !important;
    font-size: 28px !important;
    font-weight: 800 !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #1a0d0d;
    border: 1px solid rgba(248, 113, 113, 0.3);
    border-radius: 8px;
    color: white;
}

/* Dataframe */
.stDataFrame {
    border: 1px solid rgba(248, 113, 113, 0.15);
    border-radius: 10px;
}

/* Divider */
hr {
    border-color: rgba(248, 113, 113, 0.1) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: #991b1b; border-radius: 3px; }

/* MOBILE FIX: previously "header {visibility: hidden;}" was hiding
   Streamlit's whole header bar, which on narrow/mobile viewports also
   houses the sidebar's collapse/expand toggle button -- so on phones
   there was no way to open the sidebar at all, making the Season/Team
   filters that lived inside it completely inaccessible. We no longer
   hide the header element itself (see below); instead we just hide the
   specific decorative bits we don't want, and force the sidebar toggle
   to always stay visible and on top as a second safety net. The MAIN
   fix is that Season/Team are now also rendered directly on the page
   below, so they work even if the sidebar toggle is ever flaky on some
   browser/OS combination. */
button[kind="header"],
section[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    opacity: 1 !important;
    display: flex !important;
    z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a0d0d 0%, #111827 100%);
    border: 1px solid rgba(248,113,113,0.2);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
">
    <div style="
        position: absolute; top: -60px; right: -60px;
        width: 250px; height: 250px;
        background: radial-gradient(circle, rgba(248,113,113,0.15) 0%, transparent 70%);
        pointer-events: none;
    "></div>
    <div style="
        position: absolute; bottom: -40px; left: 200px;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(248,113,113,0.08) 0%, transparent 70%);
        pointer-events: none;
    "></div>
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:8px;">
        <div style="font-size:40px;">🏏</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif; font-size:32px; font-weight:800; color:white; letter-spacing:-0.5px;">
                WPL <span style="color:#f87171;">Analytics</span>
            </div>
            <div style="color:rgba(255,255,255,0.4); font-size:14px; letter-spacing:2px; text-transform:uppercase;">
                Women's Premier League · Ball-by-Ball Intelligence
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── DATA ──
@st.cache_data
def get_data():
    return load_data()

df = get_data()

# ── FILTERS (now also on the main page, not just the sidebar) ──
# MOBILE FIX: these used to live ONLY inside `with st.sidebar:`. On phones,
# Streamlit's sidebar starts collapsed behind a toggle that can be easy to
# miss (or, in this app's case, was getting hidden by a CSS rule that also
# caught the toggle button). Putting the filters here too means mobile
# users always have a working way to change them, with no dependency on
# the sidebar opening correctly.
styled_filter_row = st.columns(2)
with styled_filter_row[0]:
    seasons = ['All'] + sorted(df['season'].unique().tolist())
    selected_season = st.selectbox("📅 Season", seasons, key="main_season_select")
with styled_filter_row[1]:
    teams = ['All'] + sorted(df['batting_team'].unique().tolist())
    selected_team = st.selectbox("🏟️ Team", teams, key="main_team_select")

# ── SIDEBAR (desktop convenience — mirrors the main-page filters above) ──
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 16px 0 24px;">
        <div style="font-size:28px;">🏏</div>
        <div style="color:#f87171; font-weight:700; font-size:16px; letter-spacing:1px;">WPL ANALYTICS</div>
        <div style="color:rgba(255,255,255,0.3); font-size:11px;">FILTERS</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Filters are also available at the top of the page.")
    st.markdown(f"**Season:** {selected_season}")
    st.markdown(f"**Team:** {selected_team}")
    st.markdown("---")
    st.markdown(f"""
    <div style="color:rgba(255,255,255,0.3); font-size:11px; text-align:center; padding-top:8px;">
        {df['match_id'].nunique()} matches · {len(df):,} deliveries<br>
        Source: Cricsheet.org
    </div>
    """, unsafe_allow_html=True)

# ── APPLY FILTERS ──
filtered = df.copy()
if selected_season != 'All':
    filtered = filtered[filtered['season'] == selected_season]
if selected_team != 'All':
    filtered = filtered[
        (filtered['batting_team'] == selected_team) |
        (filtered['bowling_team'] == selected_team)
    ]

# Directional filters - batting stats only for selected team's batters,
# bowling stats only for selected team's bowlers. These are the ones that
# should be used for any "Top Batters" / "Top Bowlers" style view, since
# `filtered` still contains the OPPONENT's players for every match the
# selected team played.
batting_filtered = filtered[filtered['batting_team'] == selected_team] if selected_team != 'All' else filtered
bowling_filtered = filtered[filtered['bowling_team'] == selected_team] if selected_team != 'All' else filtered

# ── TOP METRICS ──
c1, c2, c3, c4 = st.columns(4)
c1.metric("🏟️ Matches", filtered['match_id'].nunique())
c2.metric("🎯 Deliveries", f"{len(filtered):,}")
c3.metric("🏏 Runs Scored", f"{filtered['runs_total'].sum():,}")
c4.metric("🎳 Wickets", int(filtered['is_wicket'].sum()))

st.markdown("<div style='margin:24px 0 8px;'></div>", unsafe_allow_html=True)

# ── TABS ──
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏏 Batting", "🎳 Bowling", "🏆 Teams",
    "👤 Player Profile", "🎯 Field & Strengths",
    "📊 Phase Analysis", "📈 Match Trends"
])

DARK_TEMPLATE = dict(
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(13,31,13,0.4)',
    font=dict(family='Inter', color='white'),
    margin=dict(l=20, r=20, t=40, b=20)
)

def styled_header(text):
    st.markdown(f"""
    <div style="
        font-family:'Space Grotesk',sans-serif;
        font-size:20px; font-weight:700; color:white;
        border-left: 3px solid #f87171;
        padding-left: 12px; margin: 20px 0 12px;
    ">{text}</div>
    """, unsafe_allow_html=True)

# ── TAB 1: BATTING ──
with tab1:
    styled_header("Top Run Scorers")
    bat_df = top_batters(batting_filtered)
    fig = px.bar(bat_df, x='batter', y='runs',
                 color='strike_rate', color_continuous_scale='Plasma',
                 hover_data=['balls', 'strike_rate', 'average'])
    fig.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30,
                      coloraxis_colorbar=dict(title='SR'))
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        styled_header("Strike Rate")
        fig2 = px.bar(bat_df.sort_values('strike_rate', ascending=False),
                      x='batter', y='strike_rate',
                      color='strike_rate', color_continuous_scale='Viridis')
        fig2.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30, showlegend=False)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        styled_header("Batting Average")
        fig3 = px.bar(bat_df.sort_values('average', ascending=False),
                      x='batter', y='average',
                      color='average', color_continuous_scale='Plasma')
        fig3.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30, showlegend=False)
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)

    styled_header("Full Stats Table")
    st.dataframe(bat_df.reset_index(drop=True), use_container_width=True)

# ── TAB 2: BOWLING ──
with tab2:
    styled_header("Top Wicket Takers")
    bowl_df = top_bowlers(bowling_filtered)
    fig = px.bar(bowl_df, x='bowler', y='wickets',
                 color='economy', color_continuous_scale='Plasma',
                 hover_data=['balls', 'runs', 'economy', 'average'])
    fig.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        styled_header("Economy Rate")
        fig2 = px.bar(bowl_df.sort_values('economy'),
                      x='bowler', y='economy',
                      color='economy', color_continuous_scale='Viridis')
        fig2.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30)
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        styled_header("Bowling Average")
        fig3 = px.bar(bowl_df.sort_values('average'),
                      x='bowler', y='average',
                      color='average', color_continuous_scale='Cividis')
        fig3.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30)
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)

    styled_header("Full Stats Table")
    st.dataframe(bowl_df.reset_index(drop=True), use_container_width=True)

# ── TAB 3: TEAMS ──
with tab3:
    styled_header("Team Win / Loss Summary")
    team_df = team_win_summary(filtered)
    fig = px.bar(team_df, x='team', y=['wins', 'losses'], barmode='group',
                 color_discrete_map={'wins': '#f87171', 'losses': '#f87171'})
    fig.update_layout(**DARK_TEMPLATE)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        styled_header("Win Percentage")
        fig2 = px.pie(team_df, names='team', values='win_pct',
                      color_discrete_sequence=['#f87171','#22d3ee','#a78bfa','#fb923c','#f472b6'])
        fig2.update_layout(**DARK_TEMPLATE)
        fig2.update_traces(textfont_color='white')
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        styled_header("Toss Impact on Wins")
        toss_df = toss_impact(filtered)
        fig3 = px.bar(toss_df, x='toss_decision', y='win_pct',
                      color='toss_decision',
                      color_discrete_sequence=['#f87171', '#22d3ee'])
        fig3.update_layout(**DARK_TEMPLATE)
        st.plotly_chart(fig3, use_container_width=True)

    styled_header("Team Stats")
    st.dataframe(team_df.reset_index(drop=True), use_container_width=True)

# ── TAB 4: PLAYER PROFILE ──
with tab4:
    if selected_team != 'All':
        team_players = sorted(filtered[filtered['batting_team'] == selected_team]['batter'].unique().tolist())
        # Also include bowlers from that team who may not bat
        team_bowlers = sorted(filtered[filtered['bowling_team'] == selected_team]['bowler'].unique().tolist())
        all_players = sorted(set(team_players + team_bowlers))
    else:
        all_players = sorted(df['batter'].unique().tolist())
    # Shared player selection across tabs.
    #
    # Why earlier attempts failed: Streamlit reruns the ENTIRE script on
    # every interaction, and both tabs' code runs every time regardless of
    # which tab is visible. Checking "is my own key already valid?" is not
    # enough to decide whether to reseed — by the time you switch tabs,
    # THIS tab's own key is usually still valid (it's just stale), so that
    # check never re-fires once a value has been set. What actually needs
    # checking is whether the SHARED value was changed by the OTHER tab
    # since the last time this tab ran — tracked via `_profile_player_seen`.
    _shared = st.session_state.get('shared_selected_player')
    if (
        _shared in all_players
        and _shared != st.session_state.get('_profile_player_seen')
    ):
        # The shared value changed (set by Tab 5) — adopt it here.
        st.session_state['profile_player'] = _shared
    elif st.session_state.get('profile_player') not in all_players:
        # No usable shared value and current value invalid for this filter.
        st.session_state['profile_player'] = (
            _shared if _shared in all_players else all_players[0]
        )

    def _sync_from_profile_player():
        st.session_state['shared_selected_player'] = st.session_state['profile_player']

    selected_player = st.selectbox(
        "Select Player", all_players, key='profile_player', on_change=_sync_from_profile_player
    )
    st.session_state['shared_selected_player'] = selected_player
    st.session_state['_profile_player_seen'] = selected_player
    overall, phase_stats, season_stats, dismissal_data = player_batting_profile(batting_filtered, selected_player)

    if overall:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,#1a0d0d,#111827);
            border:1px solid rgba(248,113,113,0.25);
            border-radius:12px; padding:20px 24px; margin:12px 0;
        ">
            <div style="font-size:22px;font-weight:800;color:white;">{selected_player}</div>
            <div style="color:#f87171;font-size:12px;letter-spacing:2px;">BATTING PROFILE</div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(4)
        keys = list(overall.keys())
        for i, col in enumerate(cols):
            if i < len(keys): col.metric(keys[i], overall[keys[i]])
            if i + 4 < len(keys): col.metric(keys[i+4], overall[keys[i+4]])

        col1, col2 = st.columns(2)
        with col1:
            styled_header("Runs by Phase")
            if phase_stats is not None and not phase_stats.empty:
                fig = px.bar(phase_stats, x='phase', y='runs',
                             color='strike_rate', color_continuous_scale='Plasma',
                             hover_data=['balls', 'strike_rate'])
                fig.update_layout(**DARK_TEMPLATE)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            styled_header("Dismissal Types")
            if dismissal_data is not None and not dismissal_data.empty:
                fig2 = px.pie(dismissal_data, names='type', values='count',
                              color_discrete_sequence=['#f87171','#f87171','#22d3ee','#a78bfa','#fb923c'])
                fig2.update_layout(**DARK_TEMPLATE)
                st.plotly_chart(fig2, use_container_width=True)

        if season_stats is not None and not season_stats.empty:
            styled_header("Season Performance")
            fig3 = px.line(season_stats, x='season', y='runs', markers=True,
                           hover_data=['balls', 'strike_rate'],
                           color_discrete_sequence=['#f87171'])
            fig3.update_layout(**DARK_TEMPLATE)
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    b_overall, b_phase, b_season = player_bowling_profile(bowling_filtered, selected_player)
    if b_overall:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,#1f0d0d,#1a1111);
            border:1px solid rgba(248,113,113,0.25);
            border-radius:12px; padding:20px 24px; margin:12px 0;
        ">
            <div style="font-size:22px;font-weight:800;color:white;">{selected_player}</div>
            <div style="color:#f87171;font-size:12px;letter-spacing:2px;">BOWLING PROFILE</div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        keys = list(b_overall.keys())
        for i, col in enumerate(cols):
            if i < len(keys): col.metric(keys[i], b_overall[keys[i]])
            if i + 3 < len(keys): col.metric(keys[i+3], b_overall[keys[i+3]])

        if b_phase is not None and not b_phase.empty:
            styled_header("Economy by Phase")
            fig = px.bar(b_phase, x='phase', y='economy',
                         color='wickets', color_continuous_scale='Plasma',
                         hover_data=['balls', 'runs', 'wickets'])
            fig.update_layout(**DARK_TEMPLATE)
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 5: FIELD & STRENGTHS ──
with tab5:
    if selected_team != 'All':
        all_players_2 = sorted(filtered[filtered['batting_team'] == selected_team]['batter'].unique().tolist())
    else:
        all_players_2 = sorted(df['batter'].unique().tolist())
    _shared_2 = st.session_state.get('shared_selected_player')
    if (
        _shared_2 in all_players_2
        and _shared_2 != st.session_state.get('_field_player_seen')
    ):
        st.session_state['field_player'] = _shared_2
    elif st.session_state.get('field_player') not in all_players_2:
        st.session_state['field_player'] = (
            _shared_2 if _shared_2 in all_players_2 else all_players_2[0]
        )

    def _sync_from_field_player():
        st.session_state['shared_selected_player'] = st.session_state['field_player']

    selected_player_2 = st.selectbox(
        "Select Player", all_players_2, key='field_player', on_change=_sync_from_field_player
    )
    st.session_state['shared_selected_player'] = selected_player_2
    st.session_state['_field_player_seen'] = selected_player_2

    col1, col2 = st.columns(2)
    with col1:
        styled_header("Boundary Map")
        field_fig = create_field_diagram(batting_filtered, selected_player_2)
        field_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#3a1a1a')
        st.plotly_chart(field_fig, use_container_width=True)
        st.caption("🟢 Fours  ⭐ Sixes | Top=Powerplay · Left=Middle · Right=Death")
    with col2:
        styled_header("Strength & Weakness Radar")
        radar_fig, summary = player_strength_weakness(batting_filtered, selected_player_2)
        if radar_fig:
            radar_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(radar_fig, use_container_width=True)
        else:
            st.info("Not enough data.")

    if summary:
        st.markdown("<div style='margin:20px 0 8px;'></div>", unsafe_allow_html=True)
        styled_header("Phase Verdict")
        c1, c2, c3 = st.columns(3)
        phases = ['Powerplay', 'Middle', 'Death']
        for col, phase in zip([c1, c2, c3], phases):
            pd_data = summary['phase_data'][phase]
            sr = pd_data['sr']
            dot = pd_data['dot_pct']
            balls = pd_data['balls']
            if balls < 5:
                verdict, color, bg = "⚪ No Data", "#555", "#1a1a2e"
            elif sr >= 130 and dot < 35:
                verdict, color, bg = "💪 Strong", "#f87171", "#2a0d0d"
            elif sr < 100 or dot > 50:
                verdict, color, bg = "⚠️ Weak", "#f87171", "#2a0d0d"
            else:
                verdict, color, bg = "➡️ Average", "#facc15", "#2a2a0d"

            col.markdown(f"""
            <div style='background:{bg};border-radius:12px;padding:20px;text-align:center;
                        border:1px solid {color};margin-bottom:8px;'>
                <div style='font-size:13px;font-weight:700;color:{color};letter-spacing:2px;
                            text-transform:uppercase;'>{phase}</div>
                <div style='color:white;font-size:20px;margin:8px 0;font-weight:700;'>{verdict}</div>
                <div style='color:rgba(255,255,255,0.45);font-size:12px;'>
                    SR: {sr} &nbsp;·&nbsp; Dot%: {dot}
                </div>
            </div>
            """, unsafe_allow_html=True)

        strong = summary['strong_phase']
        weak = summary['weak_phase']
        st.markdown(f"""
        <div style='display:flex;gap:16px;margin-top:16px;'>
            <div style='flex:1;background:#2a0d0d;border:1px solid #f87171;border-radius:12px;
                        padding:20px;text-align:center;'>
                <div style='color:#f87171;font-size:11px;font-weight:700;letter-spacing:2px;'>BEST PHASE</div>
                <div style='color:white;font-size:28px;font-weight:900;margin:6px 0;'>{strong}</div>
                <div style='color:rgba(255,255,255,0.45);font-size:13px;'>SR: {summary['strong_sr']}</div>
            </div>
            <div style='flex:1;background:#2a0d0d;border:1px solid #f87171;border-radius:12px;
                        padding:20px;text-align:center;'>
                <div style='color:#f87171;font-size:11px;font-weight:700;letter-spacing:2px;'>WEAK PHASE</div>
                <div style='color:white;font-size:28px;font-weight:900;margin:6px 0;'>{weak}</div>
                <div style='color:rgba(255,255,255,0.45);font-size:13px;'>SR: {summary['weak_sr']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 6: PHASE ANALYSIS ──
with tab6:
    styled_header("Run Rate by Over")
    rr_team = st.selectbox("Team", ['All'] + sorted(df['batting_team'].unique().tolist()))
    rr_df = run_rate_by_over(batting_filtered, None if rr_team == 'All' else rr_team)
    fig = px.line(rr_df, x='over_label', y='run_rate', markers=True,
                  color_discrete_sequence=['#f87171'])
    fig.add_vrect(x0=0.5, x1=6.5, fillcolor="#f87171", opacity=0.05, annotation_text="Powerplay", annotation_font_color="#f87171")
    fig.add_vrect(x0=6.5, x1=15.5, fillcolor="#facc15", opacity=0.03, annotation_text="Middle", annotation_font_color="#facc15")
    fig.add_vrect(x0=15.5, x1=20.5, fillcolor="#f87171", opacity=0.05, annotation_text="Death", annotation_font_color="#f87171")
    fig.update_layout(**DARK_TEMPLATE)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        styled_header("Batters by Phase")
        phase_bat = phase_batting(batting_filtered)
        sel_phase = st.selectbox("Phase", ['Powerplay', 'Middle', 'Death'])
        top_p = phase_bat[(phase_bat['phase'] == sel_phase) & (phase_bat['balls'] >= 20)]
        top_p = top_p.sort_values('strike_rate', ascending=False).head(8)
        fig2 = px.bar(top_p, x='batter', y='strike_rate',
                      color='runs', color_continuous_scale='Plasma',
                      hover_data=['runs', 'balls'])
        fig2.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        styled_header("Bowlers by Phase")
        phase_bowl = phase_bowling(bowling_filtered)
        sel_phase_b = st.selectbox("Phase ", ['Powerplay', 'Middle', 'Death'])
        top_b = phase_bowl[(phase_bowl['phase'] == sel_phase_b) & (phase_bowl['balls'] >= 12)]
        top_b = top_b.sort_values('economy').head(8)
        fig3 = px.bar(top_b, x='bowler', y='economy',
                      color='wickets', color_continuous_scale='Plasma',
                      hover_data=['runs', 'balls', 'wickets'])
        fig3.update_layout(**DARK_TEMPLATE, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

# ── TAB 7: MATCH TRENDS ──
with tab7:
    styled_header("Runs per Match Over Time")
    match_runs = filtered.groupby(['date', 'match_id'])['runs_total'].sum().reset_index()
    match_runs = match_runs.groupby('date')['runs_total'].mean().reset_index()
    match_runs.columns = ['date', 'avg_runs']
    fig = px.area(match_runs, x='date', y='avg_runs',
                  color_discrete_sequence=['#f87171'])
    fig.update_traces(fill='tozeroy', fillcolor='rgba(96,165,250,0.15)')
    fig.update_layout(**DARK_TEMPLATE)
    st.plotly_chart(fig, use_container_width=True)

    styled_header("Wickets per Match Over Time")
    match_wkts = filtered.groupby(['date', 'match_id'])['is_wicket'].sum().reset_index()
    match_wkts = match_wkts.groupby('date')['is_wicket'].mean().reset_index()
    match_wkts.columns = ['date', 'avg_wickets']
    fig2 = px.area(match_wkts, x='date', y='avg_wickets',
                   color_discrete_sequence=['#f87171'])
    fig2.update_traces(fill='tozeroy', fillcolor='rgba(96,165,250,0.15)')
    fig2.update_layout(**DARK_TEMPLATE)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("""
<div style="text-align:center;color:rgba(255,255,255,0.2);font-size:12px;
            padding:24px 0;letter-spacing:1px;">
    DATA SOURCE: CRICSHEET.ORG &nbsp;·&nbsp; BUILT WITH STREAMLIT & PLOTLY
</div>
""", unsafe_allow_html=True)
