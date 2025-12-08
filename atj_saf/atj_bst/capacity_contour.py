import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


saf_capacity_etoh_price_contour = np.array([[ 5.15,  5.59,  6.04,  6.48,  6.92,  7.37,  7.81,  8.26,  8.7 ,
         9.14,  9.59, 10.03, 10.47, 10.92, 11.36, 11.81, 12.25, 12.69,
        13.14, 13.58],
       [ 4.51,  4.95,  5.4 ,  5.84,  6.28,  6.73,  7.17,  7.62,  8.06,
         8.5 ,  8.95,  9.39,  9.83, 10.28, 10.72, 11.17, 11.61, 12.05,
        12.5 , 12.94],
       [ 4.19,  4.63,  5.08,  5.52,  5.96,  6.41,  6.85,  7.29,  7.74,
         8.18,  8.63,  9.07,  9.51,  9.96, 10.4 , 10.84, 11.29, 11.73,
        12.18, 12.62],
       [ 3.99,  4.43,  4.87,  5.32,  5.76,  6.21,  6.65,  7.09,  7.54,
         7.98,  8.42,  8.87,  9.31,  9.76, 10.2 , 10.64, 11.09, 11.53,
        11.97, 12.42],
       [ 3.85,  4.29,  4.74,  5.18,  5.62,  6.07,  6.51,  6.96,  7.4 ,
         7.84,  8.29,  8.73,  9.17,  9.62, 10.06, 10.51, 10.95, 11.39,
        11.84, 12.28],
       [ 3.75,  4.19,  4.64,  5.08,  5.52,  5.97,  6.41,  6.85,  7.3 ,
         7.74,  8.19,  8.63,  9.07,  9.52,  9.96, 10.4 , 10.85, 11.29,
        11.74, 12.18],
       [ 3.67,  4.11,  4.56,  5.  ,  5.45,  5.89,  6.33,  6.78,  7.22,
         7.66,  8.11,  8.55,  9.  ,  9.44,  9.88, 10.33, 10.77, 11.21,
        11.66, 12.1 ],
       [ 3.61,  4.05,  4.5 ,  4.94,  5.38,  5.83,  6.27,  6.72,  7.16,
         7.6 ,  8.05,  8.49,  8.93,  9.38,  9.82, 10.27, 10.71, 11.15,
        11.6 , 12.04],
       [ 3.56,  4.01,  4.45,  4.89,  5.34,  5.78,  6.23,  6.67,  7.11,
         7.56,  8.  ,  8.44,  8.89,  9.33,  9.78, 10.22, 10.66, 11.11,
        11.55, 11.99],
       [ 3.52,  3.96,  4.41,  4.85,  5.29,  5.74,  6.18,  6.63,  7.07,
         7.51,  7.96,  8.4 ,  8.84,  9.29,  9.73, 10.18, 10.62, 11.06,
        11.51, 11.95],
       [ 3.48,  3.93,  4.37,  4.81,  5.26,  5.7 ,  6.15,  6.59,  7.03,
         7.48,  7.92,  8.36,  8.81,  9.25,  9.7 , 10.14, 10.58, 11.03,
        11.47, 11.91],
       [ 3.45,  3.9 ,  4.34,  4.78,  5.23,  5.67,  6.11,  6.56,  7.  ,
         7.45,  7.89,  8.33,  8.78,  9.22,  9.66, 10.11, 10.55, 11.  ,
        11.44, 11.88],
       [ 3.42,  3.87,  4.31,  4.76,  5.2 ,  5.64,  6.09,  6.53,  6.97,
         7.42,  7.86,  8.31,  8.75,  9.19,  9.64, 10.08, 10.52, 10.97,
        11.41, 11.86],
       [ 3.4 ,  3.84,  4.29,  4.73,  5.17,  5.62,  6.06,  6.51,  6.95,
         7.39,  7.84,  8.28,  8.72,  9.17,  9.61, 10.06, 10.5 , 10.94,
        11.39, 11.83],
       [ 3.38,  3.82,  4.27,  4.71,  5.15,  5.6 ,  6.04,  6.48,  6.93,
         7.37,  7.82,  8.26,  8.7 ,  9.15,  9.59, 10.03, 10.48, 10.92,
        11.37, 11.81],
       [ 3.44,  3.89,  4.33,  4.77,  5.22,  5.66,  6.11,  6.55,  6.99,
         7.44,  7.88,  8.32,  8.77,  9.21,  9.66, 10.1 , 10.54, 10.99,
        11.43, 11.87],
       [ 3.42,  3.86,  4.31,  4.75,  5.2 ,  5.64,  6.08,  6.53,  6.97,
         7.41,  7.86,  8.3 ,  8.75,  9.19,  9.63, 10.08, 10.52, 10.96,
        11.41, 11.85],
       [ 3.4 ,  3.85,  4.29,  4.73,  5.18,  5.62,  6.07,  6.51,  6.95,
         7.4 ,  7.84,  8.28,  8.73,  9.17,  9.62, 10.06, 10.5 , 10.95,
        11.39, 11.83],
       [ 3.38,  3.83,  4.27,  4.72,  5.16,  5.6 ,  6.05,  6.49,  6.93,
         7.38,  7.82,  8.27,  8.71,  9.15,  9.6 , 10.04, 10.48, 10.93,
        11.37, 11.82],
       [ 3.37,  3.81,  4.25,  4.7 ,  5.14,  5.59,  6.03,  6.47,  6.92,
         7.36,  7.8 ,  8.25,  8.69,  9.14,  9.58, 10.02, 10.47, 10.91,
        11.35, 11.8 ]])


ethanol_prices = np.linspace(1.1, 4.6, 20)   # $/kg
saf_required_vals = np.linspace(9, 100, 20)  # MM gal/year (your x-axis)

# Swap X and Y axes: SAF capacity on x-axis, ethanol price on y-axis
Y, X = np.meshgrid(ethanol_prices, saf_required_vals)
from matplotlib.ticker import FuncFormatter

plt.rc('font',family='Arial')

plt.figure(figsize=(3.13066929134, 2.177598425))

# Filled contour
contourf = plt.contourf(X, Y, saf_capacity_etoh_price_contour, levels=50, cmap='coolwarm')

# Contour lines + labels
levels_to_label = [5, 6, 10]

contour_lines = plt.contour(X, Y, saf_capacity_etoh_price_contour, levels=levels_to_label, colors='black', linewidths=1)
plt.clabel(contour_lines, fmt="%.0f", fontsize=10)

# Axis labels with increased font size
plt.xlabel('SAF production scale (MM gal/year)', fontsize=10)
plt.ylabel('Ethanol Price ($/gal)', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)


# y axes formatting
N_y_labels = 5
plt.yticks(np.linspace(Y.min(), Y.max(), N_y_labels), fontsize=10) # Changes number of labels
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}')) # Makes sure labels are only 1 decimal place


# X-axis tick formatting
plt.xticks([25, 50, 75, 100], fontsize=10)
plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0f}'))

# Colorbar
cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=10)

from matplotlib.ticker import FuncFormatter
cbar.formatter = FuncFormatter(lambda x, pos: f'{x:.1f}')
cbar.update_ticks()

# Shaded gray region for SAF Liftoff report
plt.contourf(
    X, Y, saf_capacity_etoh_price_contour,
    levels=[4.5, 9.6],           # Only shade this band
    colors=['lightgray'],
    alpha=0.5
)




# 2) Dashed boundary at MSP = 4.6
plt.contour(
    X, Y, saf_capacity_etoh_price_contour,
    levels=[4.5],
    colors='#6c6e6e',   # slightly darker gray if you want
    linewidths=1,
    linestyles='--',
    zorder=4
)

# 3) Dashed boundary at MSP = 9.6
plt.contour(
    X, Y, saf_capacity_etoh_price_contour,
    levels=[9.6],
    colors='#6c6e6e',
    linewidths=1,
    linestyles='--',
    zorder=4
)


# Gevo line
# 3) Dashed boundary at MSP = 9.6
plt.contour(
    X, Y, saf_capacity_etoh_price_contour,
    levels=[7.75],
    colors="#A6A611",
    linewidths=1,
    zorder=4
)



baseline_x = 9
baseline_y = 2.67

# 2. Plot a marker there
plt.plot(baseline_x, baseline_y,
        marker='o',
        markersize=5,
        markerfacecolor='lightgray', # fill
        markeredgecolor='black',     # outline
        markeredgewidth=1,     
        linewidth = 1,
        label='Baseline point')


plt.savefig("capacity contour.svg", dpi=300)
plt.tight_layout()
plt.show()
        