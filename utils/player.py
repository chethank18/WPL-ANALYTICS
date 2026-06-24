import pandas as pd

def player_batting_profile(df, player):
    pdf = df[df['batter'] == player].copy()
    if pdf.empty:
        return None, None, None, None

    # Overall stats
    total_runs = pdf['runs_batter'].sum()
    balls_faced = len(pdf)
    dismissals = (pdf['player_dismissed'] == player).sum()
    average = round(total_runs / dismissals, 1) if dismissals > 0 else total_runs
    strike_rate = round(total_runs / balls_faced * 100, 1)
    fours = (pdf['runs_batter'] == 4).sum()
    sixes = (pdf['runs_batter'] == 6).sum()
    dot_balls = ((pdf['runs_batter'] == 0) & (pdf['extras_type'] == '')).sum()
    dot_pct = round(dot_balls / balls_faced * 100, 1)

    overall = {
        'Total Runs': total_runs,
        'Balls Faced': balls_faced,
        'Average': average,
        'Strike Rate': strike_rate,
        'Fours': int(fours),
        'Sixes': int(sixes),
        'Dot Ball %': dot_pct,
        'Dismissals': int(dismissals)
    }

    # Runs by phase
    phase_stats = pdf.groupby('phase').agg(
        runs=('runs_batter', 'sum'),
        balls=('runs_batter', 'count')
    ).reset_index()
    phase_stats['strike_rate'] = (phase_stats['runs'] / phase_stats['balls'] * 100).round(1)

    # Runs by season
    season_stats = pdf.groupby('season').agg(
        runs=('runs_batter', 'sum'),
        balls=('runs_batter', 'count')
    ).reset_index()
    season_stats['strike_rate'] = (season_stats['runs'] / season_stats['balls'] * 100).round(1)

    # Dismissal types
    dismissal_data = df[df['player_dismissed'] == player]['wicket_type'].value_counts().reset_index()
    dismissal_data.columns = ['type', 'count']

    return overall, phase_stats, season_stats, dismissal_data

def player_bowling_profile(df, player):
    pdf = df[df['bowler'] == player].copy()
    legal = pdf[pdf['extras_type'].isin(['', 'legbyes', 'byes'])]
    if legal.empty:
        return None, None, None

    total_runs = legal['runs_total'].sum()
    total_balls = len(legal)
    total_wickets = legal['is_wicket'].sum()
    economy = round(total_runs / (total_balls / 6), 2)
    average = round(total_runs / total_wickets, 1) if total_wickets > 0 else '-'
    dot_balls = (legal['runs_total'] == 0).sum()
    dot_pct = round(dot_balls / total_balls * 100, 1)

    overall = {
        'Wickets': int(total_wickets),
        'Runs Conceded': int(total_runs),
        'Balls Bowled': total_balls,
        'Economy': economy,
        'Average': average,
        'Dot Ball %': dot_pct,
    }

    # Phase bowling
    phase_stats = legal.groupby('phase').agg(
        runs=('runs_total', 'sum'),
        balls=('runs_total', 'count'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    phase_stats['economy'] = (phase_stats['runs'] / (phase_stats['balls'] / 6)).round(2)

    # Season bowling
    season_stats = legal.groupby('season').agg(
        runs=('runs_total', 'sum'),
        balls=('runs_total', 'count'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    season_stats['economy'] = (season_stats['runs'] / (season_stats['balls'] / 6)).round(2)

    return overall, phase_stats, season_stats
