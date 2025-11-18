#from atj_saf.atj_bst.contour_data import saf_selectivity_etoh_price_contour



#saf_selectivity_etoh_price_contour


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


saf_selectivity_etoh_price_contour = np.array([[ 5.53,  6.89,  8.25,  9.6 , 10.96, 12.32, 13.67, 15.03, 16.39,
        17.75, 19.1 , 20.46, 21.82, 23.17],
       [ 4.92,  6.08,  7.24,  8.4 ,  9.56, 10.72, 11.88, 13.04, 14.2 ,
        15.36, 16.52, 17.67, 18.83, 19.99],
       [ 4.47,  5.48,  6.49,  7.51,  8.52,  9.53, 10.54, 11.55, 12.56,
        13.58, 14.59, 15.6 , 16.61, 17.62],
       [ 4.12,  5.02,  5.92,  6.82,  7.71,  8.61,  9.51, 10.41, 11.3 ,
        12.2 , 13.1 , 14.  , 14.89, 15.79],
       [ 3.84,  4.65,  5.46,  6.26,  7.07,  7.88,  8.68,  9.49, 10.3 ,
        11.1 , 11.91, 12.72, 13.52, 14.33],
       [ 3.62,  4.35,  5.08,  5.82,  6.55,  7.28,  8.01,  8.74,  9.48,
        10.21, 10.94, 11.67, 12.41, 13.14],
       [ 3.43,  4.1 ,  4.77,  5.44,  6.11,  6.78,  7.45,  8.12,  8.79,
         9.46, 10.13, 10.8 , 11.47, 12.14],
       [ 3.27,  3.89,  4.51,  5.13,  5.74,  6.36,  6.98,  7.6 ,  8.22,
         8.84,  9.45, 10.07, 10.69, 11.31],
       [ 3.13,  3.71,  4.28,  4.85,  5.43,  6.  ,  6.58,  7.15,  7.72,
         8.3 ,  8.87,  9.44, 10.02, 10.59],
       [ 3.01,  3.55,  4.08,  4.62,  5.16,  5.69,  6.23,  6.76,  7.3 ,
         7.83,  8.37,  8.9 ,  9.44,  9.97],
       [ 2.91,  3.41,  3.92,  4.42,  4.92,  5.42,  5.92,  6.42,  6.92,
         7.43,  7.93,  8.43,  8.93,  9.43],
       [ 2.82,  3.29,  3.77,  4.24,  4.71,  5.18,  5.65,  6.12,  6.59,
         7.07,  7.54,  8.01,  8.48,  8.95],
       [ 2.74,  3.19,  3.63,  4.08,  4.52,  4.97,  5.41,  5.86,  6.3 ,
         6.75,  7.19,  7.64,  8.09,  8.53],
       [ 2.67,  3.09,  3.51,  3.93,  4.36,  4.78,  5.2 ,  5.62,  6.04,
         6.46,  6.89,  7.31,  7.73,  8.15]])



biofuel_composition = {'C4H8': 0.20, 'C6H12': 0.15, 'C10H20': 0.62, 'C18H36': 0.03}
ratio_sum = biofuel_composition['C4H8'] + biofuel_composition['C6H12']
a_frac = biofuel_composition['C4H8'] / ratio_sum
b_frac = biofuel_composition['C6H12'] / ratio_sum

# fixed d (RD composition)
d = biofuel_composition['C18H36']

breakdowns = []

for c in np.arange(0.3, 1, 0.05):
    ab_total = 1.0 - d - c           # this is a + b
    a = round(ab_total * a_frac, 4)
    b = round(ab_total * b_frac, 4)
    breakdowns.append({'C4H8': a, 'C6H12': b, 'C10H20': round(c, 2), 'C18H36': d})

# inspect
#for bd in breakdowns:
#    print(bd, 'sum:', round(sum(bd.values()), 4))


ethanol_prices = np.linspace(1.25, 4.2, 14)  # $/kg
saf_yield = breakdowns  # gal/year

Y, X = np.meshgrid(ethanol_prices, saf_yield)

import numpy as np

# suppose X is your original object array
ny, nx = X.shape

# method 1: list comprehension → numeric float array
X_c = np.array([[X[i,j]['C10H20']
                  for j in range(nx)]
                 for i in range(ny)], dtype=float)

# method 2: vectorize (a bit shorter)
get_c = np.vectorize(lambda d: d['C10H20'], otypes=[float])
X_c = get_c(X)


import matplotlib.pyplot as plt
plt.rc('font',family='Arial')
import matplotlib.ticker as ticker




#Swap X and Y axes: SAF capacity on x-axis, ethanol price on y-axis
#Y, X = np.meshgrid(ethanol_prices, saf_yield)

plt.figure(figsize=(3.13066929134, 2.177598425))


from matplotlib.ticker import FuncFormatter

# Filled contour
contourf = plt.contourf(X_c, Y, saf_selectivity_etoh_price_contour, levels=80, cmap='coolwarm')

cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=10)
cbar.ax.tick_params(labelsize=10)
cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.1f}"))



# Contour lines + labels
levels_to_label = [5, 6, 10]
contour_lines = plt.contour(X_c, Y, saf_selectivity_etoh_price_contour, levels=levels_to_label, 
                            colors='black', linewidths=1)
plt.clabel(contour_lines, fmt="%.0f", fontsize=10)





ax = plt.gca()

# X-axis: show percentage without decimal points, with many ticks
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"{int(x*100)}")
)

# Choose one of the three options below:
ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))   # every 2%  ← recommended, clean
# ax.xaxis.set_major_locator(ticker.MultipleLocator(0.01)) # every 1%  ← denser
# ax.xaxis.set_major_locator(ticker.MultipleLocator(0.005))# every 0.5% ← very dense





# Axis labels with increased font size
plt.xlabel('SAF selectivity (wt.%)', fontsize=10)
plt.ylabel('Ethanol Price ($/gal)', fontsize=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)


# now overlay the gray shading region
ax.contourf(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[4.5, 9.6],
    colors=['lightgray'],
    alpha=0.5,
    extend='neither',
    antialiased=True
)




baseline_x = 0.62
baseline_y = 2.8

# 2. Plot a marker there
ax.plot(baseline_x, baseline_y,
        marker='o',
        markersize=5,
        markerfacecolor='lightgray', # fill
        markeredgecolor='black',     # outline
        markeredgewidth=1,     
        linewidth = 1,
        label='Baseline point')

'''
c7 = ax.contour(
    X_c, Y, msp_matrix,
    levels=[7.5],
    colors='#ffdf82',
    linewidths=3,
    linestyles='-',
    zorder=4         # make sure it sits above the other contours
)

'''


# y axes formatting
N_y_labels = 5
plt.yticks(np.linspace(Y.min(), Y.max(), N_y_labels), fontsize=10) # Changes number of labels
plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}')) # Makes sure labels are only 1 decimal place


ax.contour(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[4.5],
    colors='#d6d8d8',
    linewidths=1,
    linestyles='--',
    zorder=4         # make sure it sits above the other contours
)

ax.contour(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[9.6],
    colors='#d6d8d8',
    linewidths=1,
    linestyles='--',
)

# Gevo line
# 3) Dashed boundary at MSP = 9.6
plt.contour(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[7.75],
    colors="#A6A611",
    linewidths=1)



# Colorbar
#cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=10, labelpad=20)
cbar.ax.tick_params(labelsize=10)

# plt.savefig("selectiivty contour.svg", bbox_inches = 'tight', dpi=300)
plt.tight_layout()
plt.show()

