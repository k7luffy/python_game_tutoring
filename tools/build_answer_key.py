"""Regenerate answers/answer_key.html from the mission data.

Run from the repository root:
    .venv/bin/python tools/build_answer_key.py

The answer key is a static, self-contained teacher page.  Building it from
``mission_one`` keeps the teacher answers identical to the game.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game"))

from engine import constants as C  # noqa: E402
from missions import mission_one as M  # noqa: E402

esc = html.escape


def map_block(spec) -> str:
    return f'<pre class="map">{esc(spec.maze_ascii.strip())}</pre>'


def code_block(code: str, extra: str = "") -> str:
    cls = "code" + (f" {extra}" if extra else "")
    return f'<pre class="{cls}"><code>{esc(code.rstrip())}</code></pre>'


def level_section(spec, index: int) -> str:
    direct = f"{spec.direct_coins} coins"
    if spec.direct_coins <= 0:
        direct += " (fails)"
    bonus = ""
    if index == len(M.LEVELS) - 1:
        add = max(0, C.FINAL_BONUS_TARGET - spec.expected_coins)
        bonus = (
            '<p class="note">The base tops the checkpoint up to '
            f"<strong>{C.FINAL_BONUS_TARGET} coins</strong> before the boss "
            f"(level finish: {spec.expected_coins}, then +{add} bonus).</p>"
        )
    extra = ""
    if spec.number == 2:
        extra = (
            "    <h3>Optional chest detour</h3>\n"
            "    <p>The direct route above skips the chest. A short detour collects it: "
            "<strong>24 steps &rarr; 31 coins</strong>.</p>\n"
            f"    {code_block(M.L2_CHEST_DETOUR, 'optional')}\n"
        )
    return f"""  <section class="level" data-route="{spec.number}">
    <div class="level-head">
      <h2>Level {spec.number}: {esc(spec.name)}</h2>
      <span class="pill">Start: {spec.start_coins} coins</span>
    </div>
    <div class="stats">
      <span>Shortest route: <strong>{spec.shortest_steps} steps</strong></span>
      <span>Shortest result: <strong>{direct}</strong></span>
      <span>Reference route: <strong>{spec.expected_steps} steps &rarr; {spec.expected_coins} coins</strong></span>
    </div>
    <p class="objective">{esc(spec.objective)}</p>
    {map_block(spec)}
    {code_block(spec.reference_code)}
    {extra}{bonus}
  </section>
"""


def build() -> str:
    rows = "".join(
        f"<tr><td>{s.number}</td><td>{esc(s.name)}</td><td>{s.start_coins}</td>"
        f"<td>{s.shortest_steps}</td><td>{s.direct_coins}</td>"
        f"<td>{s.expected_steps}</td><td>{s.expected_coins}</td></tr>"
        for s in M.LEVELS
    )
    levels = "".join(level_section(spec, i) for i, spec in enumerate(M.LEVELS))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Teacher Answer Key - Python Maze Adventure</title>
<style>
  :root {{
    --ink: #17203a;
    --muted: #5a6684;
    --line: #cfd6ea;
    --gold: #a8730a;
    --paper: #fbf8ef;
    --panel: #ffffff;
    --danger: #9b2335;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  }}
  header.warning {{
    position: sticky;
    top: 0;
    z-index: 5;
    background: var(--danger);
    color: #fff;
    text-align: center;
    padding: 12px 18px;
    font-weight: 800;
    letter-spacing: .14em;
    text-transform: uppercase;
  }}
  main {{ max-width: 1060px; margin: 0 auto; padding: 36px 24px 80px; }}
  h1 {{ font-size: 2rem; line-height: 1.15; margin: 0 0 8px; }}
  h2 {{ font-size: 1.35rem; margin: 0; }}
  h3 {{ font-size: 1.05rem; margin: 26px 0 8px; color: var(--gold); }}
  .lede {{ color: var(--muted); margin: 0 0 24px; }}
  section {{
    background: var(--panel);
    border: 2px solid var(--line);
    border-radius: 14px;
    padding: 22px 24px;
    margin: 22px 0;
    break-inside: avoid;
  }}
  section.level {{ border-left: 8px solid var(--gold); }}
  .level-head {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; }}
  .pill {{
    background: #fff4d6;
    border: 1px solid #e2c26b;
    border-radius: 999px;
    padding: 4px 12px;
    font-weight: 700;
    color: #6d4a00;
    white-space: nowrap;
  }}
  .stats {{ display: flex; flex-wrap: wrap; gap: 8px 22px; margin: 12px 0 4px; color: var(--muted); }}
  .objective {{ margin: 8px 0 16px; }}
  .note {{ background: #fff8e6; border-left: 5px solid var(--gold); padding: 10px 14px; margin: 14px 0 0; }}
  pre {{
    overflow-x: auto;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 12px 0 0;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    font-size: 14px;
    line-height: 1.5;
  }}
  pre.code {{ background: #17203a; color: #e8eeff; }}
  pre.code.optional {{ background: #26305a; }}
  pre.map {{ background: #f1f3f9; color: #3a4666; border: 1px solid var(--line); line-height: 1.25; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: .92rem; }}
  th, td {{ border: 1px solid var(--line); padding: 7px 9px; text-align: left; }}
  th {{ background: #eef1f8; }}
  tbody tr:nth-child(even) {{ background: #f7f8fc; }}
  .rule {{ color: var(--muted); font-size: .95rem; }}
  @media print {{
    body {{ background: #fff; }}
    header.warning {{ position: static; }}
    section {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<header class="warning">Teacher answer key &mdash; do not project</header>
<main>
  <h1>Python Maze Adventure: The Coin Mission</h1>
  <p class="lede">Teacher-only reference for the Create mission, the four maze levels and the boss.
  Students start from an empty editor; share hints, not this page.</p>

  <section class="overview" data-answer="overview">
    <h2>Level economy at a glance</h2>
    <p class="rule">Each move costs 1 coin. Gold coin +10, treasure chest +20.
    A level passes when the base is reached with at least 0 coins. The final base tops the player up
    to <strong>{C.FINAL_BONUS_TARGET} coins</strong> for the boss, and the boss practice run starts
    with the same {C.PRACTICE_COINS}. Every boss move also costs 1 coin.</p>
    <table>
      <thead><tr><th>#</th><th>Level</th><th>Start</th><th>Shortest</th><th>Shortest result</th>
      <th>Reference steps</th><th>Reference result</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </section>

  <section data-answer="create">
    <h2>Create Your Explorer</h2>
    <p class="objective">Ask the player for a name with <code>input()</code>, store it in
       <code>player_name</code>, then print a welcome that includes the name.</p>
    {code_block(M.CREATE_SOLUTION)}
    <p class="note">Sample run: the player types Nova &rarr; <code>player_name = "Nova"</code>
       and the console shows the welcome. <code>weapon_power</code> is fixed at 5 by the game.</p>
  </section>
{levels}
  <section data-answer="boss">
    <h2>Boss: Super Attack</h2>
    <p class="objective">The boss starts at the top-left start tile with {C.FINAL_BONUS_TARGET} coins
       (checkpoint top-up) or {C.PRACTICE_COINS} coins in a practice run. Students walk to the cyan
       attack pad two tiles above the boss, then write a function that checks
       <code>coins &gt;= {C.SUPER_ATTACK_COST}</code> and fires only inside the <code>if</code> branch.
       The boss tile itself is blocked, every move costs 1 coin, and the shortest walk to the pad is
       <strong>{M.BOSS_SPEC.shortest_steps} steps</strong> - arriving with exactly
       {M.BOSS_SPEC.expected_coins} coins.</p>
    <h3>Reference walk</h3>
    {map_block(M.BOSS_SPEC)}
    {code_block(M.BOSS_ROUTE_CODE)}
    <h3>Full program</h3>
    {code_block(M.BOSS_SOLUTION)}
    <p class="note">The route above is the reference walk; the second block is the full program.
       The game refuses <code>fire_super_attack()</code> unless the robot stands on the pad and the call
       sits inside an <code>if coins &gt;= {C.SUPER_ATTACK_COST}:</code> check. If the function is never
       called, the fire line is missing, or the guard is absent, the boss survives and the game shows a
       hint on the notice card.</p>
  </section>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    out = ROOT / "answers" / "answer_key.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
