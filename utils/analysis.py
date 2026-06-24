import pandas as pd

# Canonical name mapping — add any other known aliases/renames here.
TEAM_NAME_MAP = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "RCB": "Royal Challengers Bengaluru",
    "Royal Challengers Bangalore Women": "Royal Challengers Bengaluru",
    "Delhi Capitals Women": "Delhi Capitals",
    "Mumbai Indians Women": "Mumbai Indians",
    "UP Warriorz": "UP Warriorz",
    "Gujarat Giants Women": "Gujarat Giants",
}


def _normalize_team(series: pd.Series) -> pd.Series:
    """Trim whitespace and collapse known aliases to one canonical team name."""
    cleaned = series.astype(str).str.strip()
    return cleaned.replace(TEAM_NAME_MAP)


def load_data():
    df = pd.read_csv("data/wpl_combined.csv")
    df['date'] = pd.to_datetime(df['date'])
    df['is_wicket'] = df['wicket_type'].notna() & (df['wicket_type'] != '')
    df['is_dot'] = (df['runs_total'] == 0) & (df['extras_type'] == '')
    df['phase'] = df['over'].apply(lambda x: 'Powerplay' if x < 6 else ('Middle' if x < 15 else 'Death'))

    # Normalize all team-name columns so renamed/aliased teams (e.g. RCB)
    # don't show up twice under different spellings.
    for col in ['batting_team', 'bowling_team', 'winner', 'toss_winner']:
        if col in df.columns:
            df[col] = _normalize_team(df[col])

    return df


def top_batters(df, n=10):
    bat = df.groupby('batter').agg(
        runs=('runs_batter', 'sum'),
        balls=('runs_batter', 'count'),
        dismissals=('player_dismissed', lambda x: (x != '').sum())
    ).reset_index()
    bat['strike_rate'] = (bat['runs'] / bat['balls'] * 100).round(1)
    bat['average'] = (bat['runs'] / bat['dismissals'].replace(0, 1)).round(1)
    return bat.sort_values('runs', ascending=False).head(n)


def top_bowlers(df, n=10):
    # exclude wides and no balls from bowler balls
    legal = df[df['extras_type'].isin(['', 'legbyes', 'byes'])]
    bowl = legal.groupby('bowler').agg(
        balls=('runs_total', 'count'),
        runs=('runs_total', 'sum'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    bowl['overs'] = (bowl['balls'] // 6) + (bowl['balls'] % 6) / 10
    bowl['economy'] = (bowl['runs'] / (bowl['balls'] / 6)).round(2)
    bowl['average'] = (bowl['runs'] / bowl['wickets'].replace(0, 1)).round(1)
    threshold = 12 if len(bowl) <= 15 else 30
    result = bowl[bowl['balls'] >= threshold].sort_values('wickets', ascending=False).head(n)
    if result.empty:
        result = bowl.sort_values('wickets', ascending=False).head(n)
    return result


def team_win_summary(df):
    # Build one row per (match_id, team) for every team that appeared in that
    # match (as either the batting or bowling side), then compare to the
    # match winner. Team names are already normalized in load_data(), so
    # there's no risk of e.g. "RCB" and "Royal Challengers Bengaluru"
    # being counted as separate teams here.
    all_teams = df[['match_id', 'batting_team']].drop_duplicates()
    all_teams2 = df[['match_id', 'bowling_team']].rename(columns={'bowling_team': 'batting_team'}).drop_duplicates()
    all_teams_combined = pd.concat([all_teams, all_teams2]).drop_duplicates()
    all_teams_combined.columns = ['match_id', 'team']

    winner_map = df.drop_duplicates('match_id')[['match_id', 'winner']].set_index('match_id')['winner']
    all_teams_combined['winner'] = all_teams_combined['match_id'].map(winner_map)

    summary = all_teams_combined.groupby('team').apply(
        lambda x: pd.Series({
            'matches': len(x),
            'wins': (x['team'] == x['winner']).sum()
        })
    ).reset_index()
    summary['losses'] = summary['matches'] - summary['wins']
    summary['win_pct'] = (summary['wins'] / summary['matches'] * 100).round(1)
    return summary.sort_values('wins', ascending=False)


def run_rate_by_over(df, team=None):
    filtered = df.copy()
    if team:
        filtered = filtered[filtered['batting_team'] == team]
    rr = filtered.groupby('over').agg(
        runs=('runs_total', 'sum'),
        balls=('runs_total', 'count')
    ).reset_index()
    rr['run_rate'] = (rr['runs'] / rr['balls'] * 6).round(2)
    rr['over_label'] = rr['over'] + 1
    return rr


def phase_batting(df):
    phase = df.groupby(['batter', 'phase']).agg(
        runs=('runs_batter', 'sum'),
        balls=('runs_batter', 'count')
    ).reset_index()
    phase['strike_rate'] = (phase['runs'] / phase['balls'] * 100).round(1)
    return phase


def phase_bowling(df):
    legal = df[df['extras_type'].isin(['', 'legbyes', 'byes'])]
    phase = legal.groupby(['bowler', 'phase']).agg(
        runs=('runs_total', 'sum'),
        balls=('runs_total', 'count'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    phase['economy'] = (phase['runs'] / (phase['balls'] / 6)).round(2)
    return phase


def toss_impact(df):
    matches = df.drop_duplicates('match_id')[['match_id', 'toss_winner', 'toss_decision', 'winner']]
    matches['toss_won_match'] = matches['toss_winner'] == matches['winner']
    summary = matches.groupby('toss_decision')['toss_won_match'].agg(['sum', 'count']).reset_index()
    summary.columns = ['toss_decision', 'wins', 'total']
    summary['win_pct'] = (summary['wins'] / summary['total'] * 100).round(1)
    return summary


def venue_stats(df):
    matches = df.drop_duplicates('match_id')[['match_id', 'venue', 'winner']]
    venue = df.groupby('venue').agg(
        matches=('match_id', 'nunique'),
        avg_runs=('runs_total', 'sum')
    ).reset_index()
    return venue.sort_values('matches', ascending=False)