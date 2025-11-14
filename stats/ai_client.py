from django.conf import settings
from openai import OpenAI

def generate_team_report(team, players):
    # Safe fallback if no key (works offline)
    if not settings.OPENAI_API_KEY:
        return _fallback_report(team, players)

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        lines = []
        for p in players:
            lines.append(
                f"{p.name} ({p.position}) - {p.points_per_game:.1f} PTS, "
                f"{p.rebounds_per_game:.1f} REB, {p.assists_per_game:.1f} AST; "
                f"rating {p.rating:.1f}"
            )
        roster = "\n".join(lines) if lines else "No players."

        prompt = f"""
Analyze basketball team "{team.name}" using these player stats:

{roster}

Write 3–5 sentences about: main scorers, rebounders, playmaking, and a quick style/strengths note. Be concise.
"""
        resp = client.responses.create(model="gpt-5", input=prompt)
        return resp.output[0].content[0].text.strip() or _fallback_report(team, players)
    except Exception:
        return _fallback_report(team, players)

def _avg(seq):
    seq = [x for x in seq if x is not None]
    return sum(seq) / len(seq) if seq else 0.0

def _fallback_report(team, players):
    if not players:
        return f"No player statistics available yet for {team.name}."

    active = [p for p in players if p.minutes_per_game > 0 or p.points_per_game > 0]
    if not active:
        active = list(players)

    top_pts = max(active, key=lambda p: p.points_per_game)
    top_reb = max(active, key=lambda p: p.rebounds_per_game)
    top_ast = max(active, key=lambda p: p.assists_per_game)

    avg_pts = _avg([p.points_per_game for p in active])
    avg_reb = _avg([p.rebounds_per_game for p in active])
    avg_ast = _avg([p.assists_per_game for p in active])

    return (
        f"{team.name} lean on {top_pts.name} for scoring ({top_pts.points_per_game:.1f} ppg), "
        f"{top_reb.name} on the boards ({top_reb.rebounds_per_game:.1f} rpg), and "
        f"{top_ast.name} for playmaking ({top_ast.assists_per_game:.1f} apg). "
        f"Across their active rotation they average roughly {avg_pts:.1f} points, "
        f"{avg_reb:.1f} rebounds, and {avg_ast:.1f} assists per game."
    )
