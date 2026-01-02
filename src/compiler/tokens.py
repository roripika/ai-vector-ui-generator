"""Design token registry powering the SVG compiler."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GradientStop:
    offset: float
    color: str
    opacity: float = 1.0


@dataclass(frozen=True)
class LinearGradientDef:
    angle: float
    stops: List[GradientStop]
    spread_method: str = "pad"


@dataclass(frozen=True)
class GlowDef:
    color: str
    opacity: float
    std_deviation: float
    margin: float = 24.0


DEFAULT_LINEAR_GRADIENTS: Dict[str, LinearGradientDef] = {
    "ui.primaryGradient": LinearGradientDef(
        angle=12.0,
        stops=[
            GradientStop(offset=0.0, color="#8AF3FF"),
            GradientStop(offset=1.0, color="#8576FF"),
        ],
    ),
    "ui.highlightGradient": LinearGradientDef(
        angle=90.0,
        stops=[
            GradientStop(offset=0.0, color="#FFFFFF", opacity=0.65),
            GradientStop(offset=1.0, color="#FFFFFF", opacity=0.05),
        ],
    ),
}

DEFAULT_COLORS: Dict[str, str] = {
    "ui.strokeLight": "#6FD3FF",
    "ui.accent": "#FFC17A",
    "ui.surface": "#1B1D2F",
    "ui.textPrimary": "#F5F7FF",
    "ui.textSecondary": "#B8C3E0",
}

DEFAULT_GLOWS: Dict[str, GlowDef] = {
    "ui.softGlow": GlowDef(color="#6EDAFF", opacity=0.7, std_deviation=9.0, margin=32.0),
    "ui.focusGlow": GlowDef(color="#81FFD8", opacity=0.55, std_deviation=11.0, margin=28.0),
}

DEFAULT_FONTS: Dict[str, str] = {
    "ui.font.primary": "Helvetica Neue",
    "ui.font.title": "Helvetica Neue",
}


class TokenRegistry:
    """In-memory lookup table for gradient/color/effect tokens."""

    def __init__(
        self,
        gradients: Optional[Dict[str, LinearGradientDef]] = None,
        colors: Optional[Dict[str, str]] = None,
        glows: Optional[Dict[str, GlowDef]] = None,
        fonts: Optional[Dict[str, str]] = None,
    ) -> None:
        self._gradients = {**DEFAULT_LINEAR_GRADIENTS, **(gradients or {})}
        self._colors = {**DEFAULT_COLORS, **(colors or {})}
        self._glows = {**DEFAULT_GLOWS, **(glows or {})}
        self._fonts = {**DEFAULT_FONTS, **(fonts or {})}

    def get_linear_gradient(self, token: Optional[str]) -> Optional[LinearGradientDef]:
        if not token:
            return None
        return self._gradients.get(token)

    def get_color(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        return self._colors.get(token)

    def get_glow(self, token: Optional[str]) -> Optional[GlowDef]:
        if not token:
            return None
        return self._glows.get(token)

    def get_font(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        return self._fonts.get(token)


__all__ = [
    "GradientStop",
    "LinearGradientDef",
    "GlowDef",
    "TokenRegistry",
]
