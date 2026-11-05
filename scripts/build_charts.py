"""Build profile charts (SVG, light and dark) from the GitHub GraphQL API.

Run locally:  GITHUB_TOKEN=... python scripts/build_charts.py
In CI the workflow .github/workflows/charts.yml runs it daily.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from html import escape
from pathlib import Path

import httpx

LOGIN = os.environ.get("PROFILE_LOGIN", "EGRNEGR")
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "charts"
README = ROOT / "README.md"

# Repositories that are not shown on the charts: the profile itself and projects kept off the profile.
EXCLUDED_REPOS = {"EGRNEGR", "Ans_Hide"}
TOP_LANGUAGES = 6
MONTHS_RU = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
MONTHS_RU_FULL = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories: 25) {
        repository { nameWithOwner isPrivate isFork }
        contributions { totalCount }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      nodes {
        name
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class Theme:
    name: str
    accent: str
    highlight: str
    ink: str
    ink_muted: str
    grid: str


# Colors follow the logo (magenta to orange) and are validated against GitHub surfaces
# #ffffff and #0d1117: lightness band, contrast >= 3:1, CVD separation.
THEMES = (
    Theme("light", accent="#d6127f", highlight="#e8590c", ink="#1f2328", ink_muted="#59636e", grid="#d1d9e0"),
    Theme("dark", accent="#f2338f", highlight="#e85a0c", ink="#f0f6fc", ink_muted="#9198a1", grid="#3d444d"),
)


@dataclass(frozen=True)
class Stats:
    total_contributions: int
    total_commits: int
    total_prs: int
    active_days: int
    months: list[tuple[dt.date, int]]
    repos: list[tuple[str, int]]
    languages: list[tuple[str, float]]


async def fetch(token: str) -> dict:
    headers = {"Authorization": f"bearer {token}", "User-Agent": f"{LOGIN}-profile-charts"}
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for attempt in range(3):
            try:
                resp = await client.post(
                    "https://api.github.com/graphql",
                    json={"query": QUERY, "variables": {"login": LOGIN}},
                )
                resp.raise_for_status()
                payload = resp.json()
                if "errors" in payload:
                    raise RuntimeError(payload["errors"])
                return payload["data"]["user"]
            except (httpx.TransportError, httpx.HTTPStatusError):
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def month_start(day: dt.date, shift: int = 0) -> dt.date:
    index = day.year * 12 + day.month - 1 + shift
    return dt.date(index // 12, index % 12 + 1, 1)


def repo_label(name_with_owner: str) -> str:
    """Own repositories are shown by name, team repositories keep the owner."""
    owner, _, name = name_with_owner.partition("/")
    return name if owner == LOGIN else name_with_owner


def collect(user: dict, today: dt.date) -> Stats:
    cc = user["contributionsCollection"]
    days = [
        (dt.date.fromisoformat(d["date"]), d["contributionCount"])
        for week in cc["contributionCalendar"]["weeks"]
        for d in week["contributionDays"]
    ]
    per_month: Counter[dt.date] = Counter()
    for day, count in days:
        per_month[month_start(day)] += count
    months = [(month_start(today, -i), 0) for i in range(11, -1, -1)]
    months = [(m, per_month[m]) for m, _ in months]

    repos = sorted(
        (
            (repo_label(item["repository"]["nameWithOwner"]), item["contributions"]["totalCount"])
            for item in cc["commitContributionsByRepository"]
            if not item["repository"]["isPrivate"]
            and not item["repository"]["isFork"]
            and repo_label(item["repository"]["nameWithOwner"]) not in EXCLUDED_REPOS
        ),
        key=lambda pair: (-pair[1], pair[0].lower()),
    )

    lang_bytes: Counter[str] = Counter()
    for repo in user["repositories"]["nodes"]:
        if repo["name"] in EXCLUDED_REPOS:
            continue
        for edge in repo["languages"]["edges"]:
            lang_bytes[edge["node"]["name"]] += edge["size"]
    total_bytes = sum(lang_bytes.values()) or 1
    ranked = lang_bytes.most_common()
    languages = [(name, size / total_bytes * 100) for name, size in ranked[:TOP_LANGUAGES]]
    rest = sum(size for _, size in ranked[TOP_LANGUAGES:])
    if rest:
        languages.append(("Другие", rest / total_bytes * 100))

    return Stats(
        total_contributions=cc["contributionCalendar"]["totalContributions"],
        total_commits=cc["totalCommitContributions"],
        total_prs=cc["totalPullRequestContributions"],
        active_days=sum(1 for _, count in days if count > 0),
        months=months,
        repos=repos,
        languages=languages,
    )


def plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def nice_step(max_value: float, target_ticks: int = 4) -> int:
    raw = max(max_value, 1) / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 5, 10):
        if raw <= factor * magnitude:
            return max(1, int(factor * magnitude))
    return int(10 * magnitude)


def text_width(text: str, size: float) -> float:
    return len(text) * size * 0.58


def svg_doc(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-labelledby="t d" font-family="{FONT}">',
            f'<title id="t">{escape(title)}</title>',
            f'<desc id="d">{escape(desc)}</desc>',
            *body,
            "</svg>",
            "",
        ]
    )


def header(theme: Theme, title: str, subtitle: str) -> list[str]:
    return [
        f'<text x="0" y="22" font-size="17" font-weight="600" fill="{theme.ink}">{escape(title)}</text>',
        f'<text x="0" y="44" font-size="13" fill="{theme.ink_muted}">{escape(subtitle)}</text>',
    ]


def column_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Column with a rounded top and a square base."""
    r = min(r, w / 2, h)
    return (
        f"M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z"
    )


def bar_path(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Horizontal bar with a rounded end and a square base."""
    r = min(r, h / 2, w)
    return (
        f"M{x:.1f},{y:.1f} H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"V{y + h - r:.1f} Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z"
    )


def activity_chart(stats: Stats, theme: Theme) -> str:
    width, height = 840, 300
    left, right, top, bottom = 36, 8, 76, 262
    plot_h = bottom - top
    values = [v for _, v in stats.months]
    peak = max(values)
    step = nice_step(peak)
    y_max = max(step, math.ceil(peak / step) * step)
    slot = (width - left - right) / len(values)
    bar_w = min(24, slot * 0.5)
    peak_index = max(range(len(values)), key=lambda i: (values[i], i))
    # With few active months every column gets a value label, otherwise only the peak and the last one.
    sparse = sum(1 for v in values if v) <= 6

    first, last = stats.months[0][0], stats.months[-1][0]
    subtitle = (
        f"{stats.total_contributions} {plural(stats.total_contributions, 'вклад', 'вклада', 'вкладов')} "
        f"(коммиты, PR, новые репозитории) за {stats.active_days} "
        f"{plural(stats.active_days, 'активный день', 'активных дня', 'активных дней')}"
    )
    body = header(theme, "Активность по месяцам", subtitle)

    for tick in range(0, y_max + 1, step):
        y = bottom - tick / y_max * plot_h
        body.append(f'<line x1="{left}" x2="{width - right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{theme.grid}" stroke-width="1"/>')
        body.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" font-size="11" text-anchor="end" fill="{theme.ink_muted}">{tick}</text>'
        )

    for i, (month, value) in enumerate(stats.months):
        cx = left + slot * i + slot / 2
        label = MONTHS_RU[month.month - 1]
        if month.month == 1 or i == 0:
            label = f"{label} {month.year % 100:02d}"
        body.append(
            f'<text x="{cx:.1f}" y="{bottom + 20}" font-size="11" text-anchor="middle" fill="{theme.ink_muted}">{label}</text>'
        )
        if value == 0:
            continue
        h = value / y_max * plot_h
        color = theme.highlight if i == peak_index else theme.accent
        body.append(
            f'<path d="{column_path(cx - bar_w / 2, bottom - h, bar_w, h)}" fill="{color}">'
            f"<title>{MONTHS_RU_FULL[month.month - 1]} {month.year}: {value}</title></path>"
        )
        if sparse or i in (peak_index, len(values) - 1):
            body.append(
                f'<text x="{cx:.1f}" y="{bottom - h - 6:.1f}" font-size="12" font-weight="600" '
                f'text-anchor="middle" fill="{theme.ink}">{value}</text>'
            )

    desc = "; ".join(f"{MONTHS_RU_FULL[m.month - 1]} {m.year}: {v}" for m, v in stats.months)
    title = f"Активность на GitHub по месяцам, {MONTHS_RU_FULL[first.month - 1]} {first.year} - {MONTHS_RU_FULL[last.month - 1]} {last.year}"
    return svg_doc(width, height, title, desc, body)


def bar_chart(
    rows: list[tuple[str, float]],
    theme: Theme,
    title: str,
    subtitle: str,
    fmt,
    min_rows: int = 0,
) -> str:
    width = 410
    row_h, bar_h, top = 30, 16, 72
    height = top + row_h * max(len(rows), min_rows, 1) + 8
    label_w = max((text_width(name, 13) for name, _ in rows), default=60) + 12
    value_w = max((text_width(fmt(v), 12) for _, v in rows), default=20) + 8
    plot_w = width - label_w - value_w
    max_value = max((v for _, v in rows), default=1) or 1

    body = header(theme, title, subtitle)
    body.append(f'<line x1="{label_w:.1f}" x2="{label_w:.1f}" y1="{top - 4}" y2="{height - 8}" stroke="{theme.grid}" stroke-width="1"/>')
    for i, (name, value) in enumerate(rows):
        y = top + row_h * i + (row_h - bar_h) / 2
        w = max(value / max_value * plot_w, 2)
        color = theme.highlight if i == 0 else theme.accent
        body.append(
            f'<text x="{label_w - 10:.1f}" y="{y + bar_h - 3:.1f}" font-size="13" text-anchor="end" '
            f'fill="{theme.ink}">{escape(name)}</text>'
        )
        body.append(f'<path d="{bar_path(label_w, y, w, bar_h)}" fill="{color}"><title>{escape(name)}: {fmt(value)}</title></path>')
        body.append(
            f'<text x="{label_w + w + 6:.1f}" y="{y + bar_h - 3:.1f}" font-size="12" font-weight="600" '
            f'fill="{theme.ink}">{fmt(value)}</text>'
        )
    desc = "; ".join(f"{name}: {fmt(value)}" for name, value in rows)
    return svg_doc(width, height, title, desc, body)


def format_share(value: float) -> str:
    return f"{value:.1f} %".replace(".", ",") if value < 10 else f"{value:.0f} %"


def stats_table(stats: Stats) -> str:
    lines = [
        "<!-- stats:start -->",
        "<details>",
        "<summary>Те же данные таблицей</summary>",
        "",
        "| Показатель | Значение |",
        "|---|---:|",
        f"| Вклады за год | {stats.total_contributions} |",
        f"| Коммиты за год | {stats.total_commits} |",
        f"| Pull Request за год | {stats.total_prs} |",
        f"| Активные дни | {stats.active_days} |",
        "",
        "| Месяц | Вклады |",
        "|---|---:|",
        *(f"| {MONTHS_RU_FULL[m.month - 1]} {m.year} | {v} |" for m, v in stats.months),
        "",
        "| Репозиторий | Коммиты |",
        "|---|---:|",
        *(f"| {name} | {count} |" for name, count in stats.repos),
        "",
        "| Язык | Доля кода |",
        "|---|---:|",
        *(f"| {name} | {format_share(share)} |" for name, share in stats.languages),
        "",
        "</details>",
        "<!-- stats:end -->",
    ]
    return "\n".join(lines)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


async def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("Set GITHUB_TOKEN or GH_TOKEN")
    today = dt.datetime.now(dt.UTC).date()
    stats = collect(await fetch(token), today)

    # Both bar charts share one height so they line up side by side in the README.
    rows = max(len(stats.repos), len(stats.languages))
    for theme in THEMES:
        write(OUT_DIR / f"activity-{theme.name}.svg", activity_chart(stats, theme))
        write(
            OUT_DIR / f"repos-{theme.name}.svg",
            bar_chart(stats.repos, theme, "Коммиты по проектам", "за последние 12 месяцев", str, rows),
        )
        write(
            OUT_DIR / f"languages-{theme.name}.svg",
            bar_chart(stats.languages, theme, "Языки в коде", "доля объёма кода в публичных проектах", format_share, rows),
        )

    readme = README.read_text(encoding="utf-8")
    pattern = re.compile(r"<!-- stats:start -->.*?<!-- stats:end -->", re.S)
    if pattern.search(readme):
        write(README, pattern.sub(lambda _: stats_table(stats), readme))
    print(f"charts: {stats.total_contributions} contributions, {len(stats.repos)} repos, {len(stats.languages)} languages")


if __name__ == "__main__":
    asyncio.run(main())
