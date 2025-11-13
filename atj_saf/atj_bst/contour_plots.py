#from atj_saf.atj_bst.contour_data import saf_selectivity_etoh_price_contour



#saf_selectivity_etoh_price_contour


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


saf_selectivity_etoh_price_contour = np.array([[ 8.66,  9.81, 10.95, 12.09, 13.24, 14.38, 15.52, 16.67, 17.81,
        18.96, 20.1 , 21.24, 22.39, 23.53],
       [ 7.58,  8.56,  9.54, 10.51, 11.49, 12.47, 13.44, 14.42, 15.4 ,
        16.37, 17.35, 18.33, 19.3 , 20.28],
       [ 6.78,  7.63,  8.49,  9.34, 10.19, 11.04, 11.9 , 12.75, 13.6 ,
        14.46, 15.31, 16.16, 17.01, 17.87],
       [ 6.2 ,  6.95,  7.71,  8.47,  9.22,  9.98, 10.73, 11.49, 12.25,
        13.  , 13.76, 14.52, 15.27, 16.03],
       [ 5.69,  6.37,  7.05,  7.73,  8.41,  9.09,  9.77, 10.45, 11.13,
        11.81, 12.49, 13.17, 13.85, 14.53],
       [ 5.32,  5.93,  6.55,  7.17,  7.79,  8.4 ,  9.02,  9.64, 10.25,
        10.87, 11.49, 12.11, 12.72, 13.34],
       [ 4.97,  5.54,  6.1 ,  6.67,  7.23,  7.8 ,  8.36,  8.93,  9.49,
        10.06, 10.62, 11.19, 11.76, 12.32],
       [ 4.68,  5.21,  5.73,  6.25,  6.77,  7.29,  7.81,  8.33,  8.85,
         9.37,  9.9 , 10.42, 10.94, 11.46],
       [ 4.46,  4.94,  5.43,  5.91,  6.4 ,  6.88,  7.36,  7.85,  8.33,
         8.81,  9.3 ,  9.78, 10.26, 10.75],
       [ 4.25,  4.7 ,  5.15,  5.6 ,  6.05,  6.5 ,  6.95,  7.4 ,  7.85,
         8.3 ,  8.76,  9.21,  9.66, 10.11],
       [ 4.06,  4.48,  4.9 ,  5.32,  5.75,  6.17,  6.59,  7.01,  7.44,
         7.86,  8.28,  8.7 ,  9.13,  9.55],
       [ 3.91,  4.31,  4.7 ,  5.1 ,  5.5 ,  5.9 ,  6.29,  6.69,  7.09,
         7.49,  7.88,  8.28,  8.68,  9.08],
       [ 3.76,  4.14,  4.51,  4.89,  5.26,  5.64,  6.01,  6.39,  6.76,
         7.14,  7.51,  7.89,  8.26,  8.64],
       [ 3.65,  4.  ,  4.36,  4.71,  5.07,  5.42,  5.78,  6.13,  6.49,
         6.84,  7.2 ,  7.55,  7.91,  8.26]])




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


plt.rc('font',family='Arial')


#Swap X and Y axes: SAF capacity on x-axis, ethanol price on y-axis
#Y, X = np.meshgrid(ethanol_prices, saf_yield)

plt.figure(figsize=(8, 6))


from matplotlib.ticker import FuncFormatter

# Filled contour
contourf = plt.contourf(X_c, Y, saf_selectivity_etoh_price_contour, levels=80, cmap='coolwarm')

cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=24)
cbar.ax.tick_params(labelsize=24)
cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.1f}"))



# Contour lines + labels
levels_to_label = [5, 6, 7, 8]
contour_lines = plt.contour(X_c, Y, saf_selectivity_etoh_price_contour, levels=levels_to_label, 
                            colors='black', linewidths=1)
plt.clabel(contour_lines, fmt="%.0f", fontsize=24)



ax = plt.gca()
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"{int(x*100)}")
)



# Axis labels with increased font size
plt.xlabel('SAF selectivity (wt.%)', fontsize=24)
plt.ylabel('Ethanol Price ($/gal)', fontsize=24)
plt.xticks(fontsize=24)
plt.yticks(fontsize=24)


# now overlay the gray shading region
ax.contourf(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[4.6, 9.6],
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
        markersize=15,
        markerfacecolor='lightgray', # fill
        markeredgecolor='black',     # outline
        markeredgewidth=2.5,     
        linewidth = 2.5,
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

ax.contour(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[4.6],
    colors='#d6d8d8',
    linewidths=3,
    linestyles='--',
    zorder=4         # make sure it sits above the other contours
)

ax.contour(
    X_c, Y, saf_selectivity_etoh_price_contour,
    levels=[9.6],
    colors='#d6d8d8',
    linewidths=3,
    linestyles='--',
    zorder=4         # make sure it sits above the other contours
)



# Colorbar
#cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=24, labelpad=20)
cbar.ax.tick_params(labelsize=24)

# plt.savefig("capacity-etohprice contour-5.png", bbox_inches = 'tight', dpi=300)
plt.tight_layout()
plt.show()


