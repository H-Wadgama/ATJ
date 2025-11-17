# Code that provides a legend for the breakdown
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
plt.rc('font',family='Arial')
# Define categories and corresponding colors from original vertical legend
categories_styled = [
    'Installed costs', 
    'Catalyst replacement', 
    'Utilities excl. electricity', 
    'Process electricity', 
    'Fixed costs', 
    'Hydrogen', 
    'Ethanol', 
    'Co-product'
]

colors_styled = [
    '#332288',  # Installed costs
    "#8C7201",  # Catalyst replacement
    "#41B09D",  # Utilities excl. electricity
    "#546E30",  # Process electricity
    '#DDCC77',  # Fixed costs
    '#CC6677',  # Hydrogen
    '#AA4499',  # Ethanol
    '#882255',  # Co-product
]

patches = [mpatches.Patch(facecolor=color, label=label, edgecolor='black', linewidth=1.2) 
           for color, label in zip(colors_styled, categories_styled)]

fig, ax = plt.subplots(figsize=(10, 2))

# Create legend
legend = ax.legend(
    handles=patches,
    loc='center',
    ncol=4,
    frameon=False,        # No frame around the entire legend
    fontsize=16,
    handlelength=2,
    handletextpad=0.3,
    borderpad=10.8,
    columnspacing=0.8,
    labelspacing=0.3
)

# Ensure no text boxes
for text in legend.get_texts():
    text.set_bbox(None)

ax.axis('off')
plt.tight_layout()
# plt.savefig("legend_breakdown.svg")
plt.show()