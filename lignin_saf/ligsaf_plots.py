import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_OI_COLORS = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    # extended palette for >6 areas
    "#009E73",  # bluish green
    "#999999",  # grey
    "#F781BF",  # pink
    "#A65628",  # brown
]


def _setup_fonts():
    font_pref = ["Arial", "Liberation Sans", "DejaVu Sans"]
    available = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
    chosen = next((f for f in font_pref if f in available), "DejaVu Sans")
    plt.rcParams.update({
        "font.family": chosen,
        "mathtext.fontset": "custom",
        "mathtext.rm": chosen,
        "mathtext.it": chosen,
        "mathtext.bf": chosen,
        "svg.fonttype": "none",
    })
    return chosen


def plot_installed_cost_breakdown(
    categories,
    values,
    title="Installed Cost Breakdown",
    save_path="installed_cost_breakdown.svg",
    dpi=300,
    fig_w_px=1500,
    fig_h_px=1260,
    fontsize=13,
):
    """
    Generate a pie chart of installed cost by process area.

    Parameters
    ----------
    categories : list[str]
        Area labels, one per wedge.
    values : list[float]
        Installed costs in USD, same order as categories.
    title : str
        Chart title.
    save_path : str or None
        Output file path. Extension determines format (.svg, .png, …).
        Pass None to skip saving.
    dpi : int
        Resolution for raster formats.
    fig_w_px, fig_h_px : int
        Figure dimensions in pixels (used with dpi to set figure size in inches).
    fontsize : int
        Base font size for title, percentages, total label, and legend.

    Returns
    -------
    fig, ax
    """
    _setup_fonts()

    n = len(categories)
    if n > len(_OI_COLORS):
        raise ValueError(
            f"Only {len(_OI_COLORS)} colors defined; add more to _OI_COLORS in ligsaf_plots.py"
        )
    colors = _OI_COLORS[:n]

    total = sum(values)
    fracs = [v / total for v in values]

    fig, ax = plt.subplots(figsize=(fig_w_px / dpi, fig_h_px / dpi))

    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(linewidth=0.8, edgecolor="white"),
    )

    # percentage labels with leader lines
    label_data = []
    for i, (wedge, frac) in enumerate(zip(wedges, fracs)):
        pct = frac * 100
        theta = np.deg2rad((wedge.theta1 + wedge.theta2) / 2)
        if pct >= 20:
            r_out = 1.14
        elif pct >= 10:
            r_out = 1.21
        elif pct >= 5:
            r_out = 1.29
        else:
            r_out = 1.38
        label_data.append(dict(theta=theta, pct=pct, r_out=r_out, r_in=0.78, idx=i))

    small_indices = [d["idx"] for d in label_data if d["pct"] < 5]
    for j, idx in enumerate(small_indices):
        label_data[idx]["r_out"] = 1.36 if j % 2 == 0 else 1.46

    for d in label_data:
        theta, r_in, r_out, pct = d["theta"], d["r_in"], d["r_out"], d["pct"]
        ax.annotate(
            f"{pct:.1f}%",
            xy=(r_in * np.cos(theta), r_in * np.sin(theta)),
            xytext=(r_out * np.cos(theta), r_out * np.sin(theta)),
            fontsize=fontsize,
            ha="center",
            va="center",
            arrowprops=dict(arrowstyle="-", color="#666666", lw=0.6, shrinkA=0, shrinkB=2),
        )

    ax.set_title(title, fontsize=fontsize, fontweight="bold", pad=6)
    ax.text(
        0, -1.72,
        f"Total: {total / 1e6:.1f} MM $",
        ha="center", va="top", fontsize=fontsize,
        color="#222222", fontweight="bold",
    )
    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.95, 1.50)

    # legend — use 3 columns, wrapping to a 4th if needed
    ncol = min(3, n)
    handles = [
        mpatches.Patch(facecolor=c, edgecolor="white", linewidth=0.8, label=lbl)
        for c, lbl in zip(colors, categories)
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=ncol,
        fontsize=fontsize,
        frameon=False,
        columnspacing=1.2,
        handlelength=2.6,
        handleheight=0.85,
        handletextpad=0.6,
        bbox_to_anchor=(0.5, 0.0),
    )

    fig.tight_layout(rect=[0, 0.14, 1, 1])

    if save_path is not None:
        fmt = save_path.rsplit(".", 1)[-1] if "." in save_path else "svg"
        fig.savefig(save_path, format=fmt, dpi=dpi, bbox_inches="tight")

    return fig, ax
