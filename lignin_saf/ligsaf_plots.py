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
    "#476066",  # dark teal
    "#562C29",  # dark brown
    "#009E73",  # bluish green
    "#999999",  # grey
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


def _pie_chart(
    categories,
    values,
    title,
    save_path,
    dpi,
    fig_w_px,
    fig_h_px,
    fontsize,
    ncol,
    legend_bottom,
):
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

    fig.tight_layout(rect=[0, legend_bottom, 1, 1])

    if save_path is not None:
        fmt = save_path.rsplit(".", 1)[-1] if "." in save_path else "svg"
        fig.savefig(save_path, format=fmt, dpi=dpi, bbox_inches="tight")

    return fig, ax


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
    Pie chart of installed capital cost by process area.

    Parameters
    ----------
    categories : list[str]
        Area labels, one per wedge.
    values : list[float]
        Installed costs in USD, same order as categories.
    title : str
        Chart title.
    save_path : str or None
        Output path; extension sets format (.svg, .png, …). None skips saving.
    dpi : int
        Resolution for raster formats.
    fig_w_px, fig_h_px : int
        Figure size in pixels.
    fontsize : int
        Base font size for all text elements.

    Returns
    -------
    fig, ax
    """
    return _pie_chart(
        categories, values, title, save_path, dpi, fig_w_px, fig_h_px,
        fontsize, ncol=min(3, len(categories)), legend_bottom=0.14,
    )


def plot_operating_cost_breakdown(
    categories,
    values,
    title="Annual Operating Cost Breakdown",
    save_path="operating_cost_breakdown.svg",
    dpi=300,
    fig_w_px=1500,
    fig_h_px=1260,
    fontsize=13,
):
    """
    Pie chart of annual operating cost by cost item.

    Parameters
    ----------
    categories : list[str]
        Cost-item labels, one per wedge.
    values : list[float]
        Annual costs in USD/yr, same order as categories.
    title : str
        Chart title.
    save_path : str or None
        Output path; extension sets format (.svg, .png, …). None skips saving.
    dpi : int
        Resolution for raster formats.
    fig_w_px, fig_h_px : int
        Figure size in pixels.
    fontsize : int
        Base font size for all text elements.

    Returns
    -------
    fig, ax
    """
    return _pie_chart(
        categories, values, title, save_path, dpi, fig_w_px, fig_h_px,
        fontsize, ncol=min(4, len(categories)), legend_bottom=0.10,
    )
