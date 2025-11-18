import numpy as np
import pandas as pd


costs = np.array([[ 2.624e-01,  3.960e-02,  5.871e-01,  4.997e-01,  9.868e-02,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 6.686e-02,  0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 5.350e-01,  4.378e-02,  0.000e+00, -3.322e-01,  0.000e+00,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 1.920e-02,  1.182e-04,  0.000e+00, -2.997e-02,  3.843e-03,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 1.782e-01,  1.782e-01,  1.782e-01,  1.782e-01,  1.782e-01,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 4.997e-01,  0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,
         0.000e+00,  0.000e+00,  0.000e+00],
       [ 0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,
         0.000e+00,  0.000e+00,  6.412e+00],
       [ 0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,  0.000e+00,
        -1.011e+00, -1.557e-01,  0.000e+00]])

# Legend categories (costs)
legend_categories = [
    'Installed costs', 
    'Catalyst replacement', 
    'Utilities excl. electricity', 
    'Process electricity', 
    'Fixed costs', 
    'Hydrogen', 
    'Ethanol', 
    'Co-product'
]

# Bar categories (processes)
bar_categories = [
    'Catalytic upgrading', 
    'Product fractionation', 
    'Storage', 
    'Boiler Turbogenerator',
    'Wastewater Treatment',
    'Renewable naphtha', 
    'Renewable diesel', 
    'Bioethanol'
]

cost_breakdown_df = pd.DataFrame(costs.T, columns=legend_categories, index=bar_categories)


import numpy as np
import matplotlib.pyplot as plt
plt.rc('font', family='Arial')

fig, ax = plt.subplots(figsize=(4.370079, 2.438897638))

custom_colors = [
    '#332288',  # Installed costs
    "#8C7201",  # Catalyst replacement
    "#41B09D",  # Utilities excl. electricity
    "#546E30",  # Process electricity
    '#DDCC77',  # Fixed costs
    '#CC6677',  # Hydrogen
    '#AA4499',  # Ethanol
    '#882255',  # Co-product
]

# two separate “bottoms”
bottom_pos = np.zeros(len(bar_categories))  # for >= 0
bottom_neg = np.zeros(len(bar_categories))  # for < 0

for i, (cost, label) in enumerate(zip(costs, legend_categories)):
    cost = np.asarray(cost)

    pos = np.where(cost > 0, cost, 0)
    neg = np.where(cost < 0, cost, 0)

    # positive part
    ax.barh(
        bar_categories, pos, left=bottom_pos,
        color=custom_colors[i], edgecolor='black', linewidth=1, height=0.6,
        label=label  # legend
    )
    bottom_pos += pos

    # negative part
    ax.barh(
        bar_categories, neg, left=bottom_neg,
        color=custom_colors[i], edgecolor='black', linewidth=1, height=0.6
    )
    bottom_neg += neg
    

font_size = 11

# Add labels and legend
ax.set_xlabel('Contribution to MJSP ($/gal)', fontsize = font_size)
ax.set_ylabel('Process section', fontsize = font_size)
#ax.legend(title="Cost Category", bbox_to_anchor=(1.05, 1), loc='upper left')


ax.tick_params(axis='both', which='major', labelsize=font_size, width=1, length=10)
# set the axis line width in pixels
for axis in 'left', 'bottom', 'top', 'right':
  ax.spines[axis].set_linewidth(1)

# Add a vertical line at x=0
ax.axvline(0, color='black', linewidth=1)

# Set the x positions for the vertical lines (for example, every 0.2 units from -1 to 1)
xlines = np.arange(-3, 8, 0.5)  # adjust range and step as needed

for x in xlines:
    ax.axvline(x, color='#bdbdbd', linestyle='--', linewidth=0.5, zorder=0)


# Define the range for x-axis ticks
min_tick = np.floor(bottom_neg.min())     # negative extent
max_tick = np.ceil(bottom_pos.max())      # positive extent
step = 1.0



# Add some padding if desired
ax.set_xlim(min_tick - 0.5, max_tick + 0.5)
# Create ticks at -1.0, 0.0, 1.0, ...
xticks = np.arange(min_tick, max_tick + step, step)
ax.set_xticks(xticks)
ax.set_xticklabels([f"{x:.1f}" for x in xticks], fontsize=font_size)
ax.set_xlim(-2.5, 7.5)


# Totals per bar
net_totals = costs.sum(axis=0)                         # net contribution
pos_totals = np.clip(costs, 0, None).sum(axis=0)       # sum of >= 0 parts
neg_totals = np.clip(costs, None, 0).sum(axis=0)       # sum of < 0 parts (negative)

for i, (category, net, pos, neg) in enumerate(
        zip(bar_categories, net_totals, pos_totals, neg_totals)):
    
    if net >= 0:
        # place label just to the right of the rightmost positive stack
        xpos = pos + 0.04
        ha = 'left'
    else:
        # place label just to the left of the leftmost negative stack
        xpos = neg - 0.15
        ha = 'right'
    
    ax.text(
        xpos, i,
        f"{net:.2f}$",
        va='center',
        ha=ha,
        fontsize=10,
        #fontweight='bold'
    )   # Size of $ numbers


mjsp = np.sum(costs)

ax.text(
    3.2, 1.8,  # x, y position; adjust as needed
    f"MJSP = ${mjsp:.2f}/gal",
    fontsize=font_size,
    color='black',
    bbox=dict(
        facecolor='white',
        edgecolor='black',
        linewidth=1,         # Thicker box border
        boxstyle='square,pad=0.2'  # Sharp edges
    )
)


#plt.tight_layout() 
#plt.savefig('cost_breakdown.svg', bbox_inches = 'tight')
plt.show()