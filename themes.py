"""Built-in color themes.

Pick one in content/profile.yaml with `theme: "<name>"`, and override any single
value under `colors:`. Every theme defines the same set of tokens, which
templates/base.html injects as CSS variables and static/style.css consumes.
"""

from __future__ import annotations

import sys

DEFAULT_THEME = "oxblood"

# Token order matters only for readability. `scheme` is the CSS color-scheme
# hint so form controls and scrollbars follow dark themes.
THEMES: dict[str, dict[str, str]] = {
    # Warm ivory greys with a deep red accent. The original design.
    "oxblood": {
        "bg": "#FFFFFF", "ink": "#1C1A17", "body": "#4A443A", "muted": "#6B6252",
        "rule": "#E6E2D8", "tint": "#F8F5EE", "tint_border": "#E0D9C8",
        "button_border": "#CFC6B3", "placeholder": "#EEE9DE",
        "accent": "#7A2E2E", "on_accent": "#FFFFFF", "scheme": "light",
    },
    # Cool greys with a deep teal accent. Calm, modern.
    "teal": {
        "bg": "#FFFFFF", "ink": "#14201F", "body": "#3F4F4D", "muted": "#5F716E",
        "rule": "#DCE4E2", "tint": "#EEF4F2", "tint_border": "#D3DEDB",
        "button_border": "#C2CFCC", "placeholder": "#E6EEEC",
        "accent": "#1F5F5B", "on_accent": "#FFFFFF", "scheme": "light",
    },
    # Blue-leaning greys with an indigo accent. Engineering feel.
    "indigo": {
        "bg": "#FFFFFF", "ink": "#171A2B", "body": "#454A63", "muted": "#646A85",
        "rule": "#E0E2EC", "tint": "#EEF0F7", "tint_border": "#D8DCEA",
        "button_border": "#C6CBDD", "placeholder": "#E7E9F2",
        "accent": "#2F3E8F", "on_accent": "#FFFFFF", "scheme": "light",
    },
    # Paper-toned background with a dark amber accent. Most analog.
    "ochre": {
        "bg": "#FBF8F1", "ink": "#221E17", "body": "#4F4636", "muted": "#6F6450",
        "rule": "#E7DFCF", "tint": "#F1EADB", "tint_border": "#E0D5BE",
        "button_border": "#CFC2A5", "placeholder": "#EAE2D0",
        "accent": "#8A5A14", "on_accent": "#FFFFFF", "scheme": "light",
    },
    # Near-monochrome cool greys; links are a dark slate blue.
    "slate": {
        "bg": "#FFFFFF", "ink": "#16191D", "body": "#444A52", "muted": "#66707C",
        "rule": "#E1E5EA", "tint": "#F1F3F5", "tint_border": "#D9DEE4",
        "button_border": "#C5CCD4", "placeholder": "#E8ECEF",
        "accent": "#3B4A5C", "on_accent": "#FFFFFF", "scheme": "light",
    },
    # Dark ground with warm text and an amber accent.
    "dark": {
        "bg": "#15171B", "ink": "#ECEAE4", "body": "#C3C0B8", "muted": "#8F8B82",
        "rule": "#2A2E35", "tint": "#1F2229", "tint_border": "#2F343C",
        "button_border": "#3A404A", "placeholder": "#23272E",
        "accent": "#D9A15B", "on_accent": "#15171B", "scheme": "dark",
    },
}


def resolve_palette(profile: dict, theme_override: str | None = None) -> dict[str, str]:
    """Return the final token map: theme defaults, then `colors:` overrides.

    `theme_override` (from the CLI) wins over profile.yaml. The legacy top-level
    `accent:` key in profile.yaml is still honored as an override.
    """
    name = (theme_override or profile.get("theme") or DEFAULT_THEME).strip().lower()
    if name not in THEMES:
        print(
            f"warning: unknown theme '{name}', using '{DEFAULT_THEME}'. "
            f"Available: {', '.join(THEMES)}",
            file=sys.stderr,
        )
        name = DEFAULT_THEME

    palette = dict(THEMES[name])
    palette["name"] = name

    overrides = dict(profile.get("colors") or {})
    if profile.get("accent"):
        overrides.setdefault("accent", profile["accent"])
    for key, value in overrides.items():
        token = str(key).replace("-", "_")
        if token in THEMES[name] and value:
            palette[token] = str(value)
        elif token not in THEMES[name]:
            print(f"warning: unknown color token '{key}' in profile.yaml colors:", file=sys.stderr)
    return palette
