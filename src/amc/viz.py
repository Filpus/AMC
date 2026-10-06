"""Styl i paleta wykresów (matplotlib).

Kolor zawsze oznacza ten sam blok polityczny; kolejność barw zwalidowana pod kątem daltonizmu dla sąsiadujących par.
Natężenie (heatmapy) — jedna barwa od jasnej do ciemnej (SEQ).
"""
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from . import paths
from .speakers import BLOKI, INNE

INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
ACCENT = "#2a78d6"
ACCENT_LIGHT = "#cde2fb"
SECOND = "#eb6834"  # druga seria, gdy kolory nie oznaczają bloków (np. plenarne vs komisje)

BLOK_KOLOR = {
    "PiS": "#2a78d6", "KO": "#eb6834", "Kukiz'15": "#1baf7a", "Polska 2050": "#eda100",
    "Lewica": "#e87ba4", "PSL": "#008300", "Konfederacja": "#4a3aa7", INNE: "#b5b3ac",
}
assert list(BLOK_KOLOR) == BLOKI
ROLE_KOLOR = {"poseł": ACCENT, "rząd": "#86b6ef", "inni": "#c3c2b7"}
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])


def setup():
    """Ustawia styl wykresów dla całej sesji."""
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "savefig.bbox": "tight",
        "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 22,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "legend.frameon": False, "lines.linewidth": 2,
    })


def save(fig, name):
    """Zapisuje wykres do figures/<name>.png."""
    paths.FIGURES.mkdir(exist_ok=True)
    fig.savefig(paths.FIGURES / f"{name}.png")


def subtitle(ax, text):
    """Podtytuł nad osiami, pod tytułem (tytuł ma titlepad=22)."""
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction", xytext=(0, 2), textcoords="offset points",
                fontsize=9, color=INK2, va="bottom")


def term_lines(ax, label=True):
    """Pionowe linie na początku IX i X kadencji (oś x w datach)."""
    for t, d in paths.TERM_START.items():
        if t == min(paths.TERM_START):
            continue
        ax.axvline(d, color=AXIS, lw=1, ls=":")
        if label:
            ax.text(d, 1.0, f" {t}. kadencja", transform=ax.get_xaxis_transform(), fontsize=8, color=MUTED, va="top")
