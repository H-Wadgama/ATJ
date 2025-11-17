import matplotlib.pyplot as plt
import numpy as np

def nice_pie(
    values,
    labels,
    title="",
    subtitle=None,
    colors=None,
    filename=None,
    figsize=(5, 5),
    dpi=500,
    font_family="Arial",
):
    """
    Makes a nice looking pie chart
  

    Parameters
    ----------
    values : list of numbers
        Size of each slice (e.g. costs).
    labels : list of str
        Labels for each slice (e.g. 'BT', 'WWT').
    title : str, optional
        Title above the pie (e.g. 'Capital Costs').
    subtitle : str, optional
        Line of text under the title (e.g. 'TIC: 120 MM$').
    colors : list of color hex codes, optional
        Custom colors; if None, a color-blind friendly palette is used.
    filename : str, optional
        If given (e.g. 'plot.png'), saves the figure to this file.
    figsize : tuple, optional
        Figure size in inches, default (5, 5).
    dpi : int, optional
        Resolution for saving, default 500.
    font_family : str, optional
        Matplotlib font family name, default 'Arial'.
    """

    ####### Basic checks #############
    if len(values) != len(labels):
        raise ValueError("values and labels must have the same length")

    if colors is not None and len(colors) != len(values):
        raise ValueError("colors must be None or the same length as values")

    # -------- 1. Default color palette (only change if you want new colors)
    if colors is None:
        # Color-blind–friendly Okabe–Ito palette
        colors = ['#0072B2', '#E69F00', '#56B4E9', '#CC79A7', '#009E73'][:len(values)]




    ######### Styling options - can be tweaked if needed ##############

    # Geometry / spacing
    R_PIE          = 1.0    # Pie radius
    R_MID          = 1.05   # Where connector leaves the pie (just outside)
    LABEL_X_FACTOR = 1.35   # Horizontal connector length
    LABEL_DY       = 0.03   # Vertical offset of label ABOVE the connector
    PCT_DY         = 0.01   # Vertical offset of % BELOW the connector
    LABEL_PAD      = 0.05   # separation between connector end and label
    PCT_PAD        = 0.05   # separation between connector end and percentage

    # Font sizes
    FS_LABEL   = 14         # Font size for section labels (e.g. 'BT')
    FS_PERCENT = 14         # Font size for percentages (e.g. '33.6%')
    FS_TITLE   = 16         # Font size for title and subtitle

    # Line styles
    EDGE_LW        = 1    # Slice border width
    CONNECTOR_LW   = EDGE_LW  # Connector line width (change if you want different)
    CONNECTOR_COLOR = "black" # Connector line color



    # ------------------------------------------------------------------- Don't touch the code below
    plt.rc('font', family=font_family)

    total = float(sum(values))
    percents = [100 * v / total for v in values]

    fig, ax = plt.subplots(figsize=figsize)

    # Draw pie slices
    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=150,
        radius=R_PIE,
        wedgeprops=dict(
            edgecolor="black",
            linewidth=EDGE_LW,
            joinstyle="miter"
        )
    )

    # Draw connectors + labels
    for name, pct, wedge in zip(labels, percents, wedges):
        theta = 0.5 * (wedge.theta1 + wedge.theta2)
        theta_rad = np.deg2rad(theta)

        # Edge of pie
        x_edge = R_PIE * np.cos(theta_rad)
        y_edge = R_PIE * np.sin(theta_rad)

        # Step beyond pie
        x_mid = R_MID * np.cos(theta_rad)
        y_mid = R_MID * np.sin(theta_rad)

        # End of connector (before padding)
        x_base = LABEL_X_FACTOR * np.sign(x_edge)
        y_base = y_mid

        # Apply horizontal padding depending on which side
        if x_base > 0:
            x_label = x_base + LABEL_PAD
            x_pct   = x_base + PCT_PAD
            ha = "left"
        else:
            x_label = x_base - LABEL_PAD
            x_pct   = x_base - PCT_PAD
            ha = "right"

        # Connector line
        ax.plot(
            [x_edge, x_mid, x_base],
            [y_edge, y_mid, y_base],
            color=CONNECTOR_COLOR,
            linewidth=CONNECTOR_LW,
        )

        # Label (bold)
        ax.text(
            x_label, y_base + LABEL_DY,
            name,
            ha=ha, va='bottom',
            fontsize=FS_LABEL,
            fontweight='bold'
        )

        # Percentage (normal)
        ax.text(
            x_pct, y_base - PCT_DY,
            f"{pct:.1f}%",
            ha=ha, va='top',
            fontsize=FS_PERCENT
        )

    ax.axis("equal")

    # Title + subtitle
    if title:
        plt.text(0, 1.9, title, ha="center", va="center",
                 fontsize=FS_TITLE, fontweight="bold")

    if subtitle:
        plt.text(0, 1.6, subtitle, ha="center", va="center",
                 fontsize=FS_TITLE)

    plt.tight_layout()

    if filename:
        plt.savefig(filename, dpi=dpi, bbox_inches="tight")
    plt.show()