# Welcome to the Ethanol to Jet model for BioSTEAM
This document is meant to guide new users if they want to generate results from the manuscript
Everything here is done in the etj_bst_system.ipynb file - .ipynb notebook files are much more intuitive to use! 


# Generating SAF selectivity contour 

In the `etj_bst_system.ipynb` file, run the following code at the end.

```bash

# your original breakdown and the ratio for a:b
biofuel_composition = {'C4H8': 0.20, 'C6H12': 0.15, 'C10H20': 0.62, 'C18H36': 0.03}
ratio_sum = biofuel_composition['C4H8'] + biofuel_composition['C6H12']
a_frac = biofuel_composition['C4H8'] / ratio_sum
b_frac = biofuel_composition['C6H12'] / ratio_sum

# fixed d
d = biofuel_composition['C18H36']

# prepare list to hold your 20 breakdowns
breakdowns = []

# c goes 0, 0.05, 0.10, ..., 0.95  (20 values)
for c in np.arange(0.3, 1, 0.05):
    ab_total = 1.0 - d - c           # this is a + b
    a = round(ab_total * a_frac, 4)
    b = round(ab_total * b_frac, 4)
    breakdowns.append({'C4H8': a, 'C6H12': b, 'C10H20': round(c, 2), 'C18H36': d})

# inspect
for bd in breakdowns:
    print(bd, 'sum:', round(sum(bd.values()), 4))

```


This will yield the breakdown of the selectivity values, and can be used as confirmation:


```
>>> {'C4H8': 0.3829, 'C6H12': 0.2871, 'C10H20': 0.3, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.3543, 'C6H12': 0.2657, 'C10H20': 0.35, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.3257, 'C6H12': 0.2443, 'C10H20': 0.4, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.2971, 'C6H12': 0.2229, 'C10H20': 0.45, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.2686, 'C6H12': 0.2014, 'C10H20': 0.5, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.24, 'C6H12': 0.18, 'C10H20': 0.55, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.2114, 'C6H12': 0.1586, 'C10H20': 0.6, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.1829, 'C6H12': 0.1371, 'C10H20': 0.65, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.1543, 'C6H12': 0.1157, 'C10H20': 0.7, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.1257, 'C6H12': 0.0943, 'C10H20': 0.75, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.0971, 'C6H12': 0.0729, 'C10H20': 0.8, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.0686, 'C6H12': 0.0514, 'C10H20': 0.85, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.04, 'C6H12': 0.03, 'C10H20': 0.9, 'C18H36': 0.03} sum: 1.0
>>> {'C4H8': 0.0114, 'C6H12': 0.0086, 'C10H20': 0.95, 'C18H36': 0.03} sum: 1.0

```

Next, run the following code:


```bash

ethanol_prices = np.linspace(1.1, 4.6, 14)  # $/kg
saf_yield = breakdowns  # gal/year
msp_matrix = np.zeros((len(saf_yield), len(ethanol_prices)))

for i, saf_yields in enumerate(saf_yield):

    prod_selectivity = saf_yields
    oligomerization_rxn = bst.ParallelReaction([
    bst.Reaction('2Ethylene,g -> Butene,g', reactant='Ethylene', X=olig_data['conv']*prod_selectivity['C4H8'], basis='wt', phases='lg', correct_atomic_balance=True),
    bst.Reaction('1.5Ethylene,g -> Hex-1-ene,g', reactant='Ethylene', X=olig_data['conv']*prod_selectivity['C6H12'], basis='wt', phases='lg', correct_atomic_balance=True),
    bst.Reaction('5Ethylene,g -> Dec-1-ene,l', reactant='Ethylene', X=olig_data['conv']*prod_selectivity['C10H20'], basis='wt', phases='lg', correct_atomic_balance=True),
    bst.Reaction('9Ethylene,g -> Octadec-1-ene,l', reactant='Ethylene', X=olig_data['conv']*prod_selectivity['C18H36'], basis='wt', phases='lg', correct_atomic_balance=True)
    ])
    olig_1.reaction = oligomerization_rxn

    # Update SAF product flowrate (mass or volumetric as needed)
    #saf_stream.F_mass = saf_required * 0.00378541 * saf_stream.rho  # gal → kg

    # Calculate required ethanol flowrate
    #my_sys.ins[0].imass['Ethanol'] = calculate_ethanol_flow(saf_required)
    
    for j, ethanol_price in enumerate(ethanol_prices):
        etoh_in.price = ethanol_price_converter(ethanol_price)
        
        # Run the model
        atj_sys.empty_outlet_streams()
        atj_sys.empty_recycles()
        atj_sys.reset_cache()
        atj_sys.simulate()       
        # Solve MSP
        msp = round((final_tea.solve_price(saf_stream)*saf_stream.rho)/264.172,2)
        #msp_kg = tea.solve_price(saf_stream)
        msp_matrix[i, j] = msp

```


This will take some time (< 5 mins) and generate MSP values for SAF for each combination of selectivity and ethanol price.

Next, the following code generates the actual plot. 


```bash
Y, X = np.meshgrid(ethanol_prices, saf_yield)
# suppose X is your original object array
ny, nx = X.shape

# method 1: list comprehension → numeric float array
X_c = np.array([[X[i,j]['C10H20']
                  for j in range(nx)]
                 for i in range(ny)], dtype=float)

# method 2: vectorize (a bit shorter)
get_c = np.vectorize(lambda d: d['C10H20'], otypes=[float])
X_c = get_c(X)

# now X_c is shape (ny,nx), dtype float64
print(X_c.shape, X_c.dtype)   # e.g. (50, 40) float64



import matplotlib.pyplot as plt
plt.rc('font',family='Arial')
import matplotlib.ticker as ticker




#Swap X and Y axes: SAF capacity on x-axis, ethanol price on y-axis
#Y, X = np.meshgrid(ethanol_prices, saf_yield)

plt.figure(figsize=(3.13066929134, 2.177598425))


from matplotlib.ticker import FuncFormatter

# Filled contour
contourf = plt.contourf(X_c, Y, msp_matrix, levels=80, cmap='coolwarm')

cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=10)
cbar.ax.tick_params(labelsize=10)
cbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.1f}"))



# Contour lines + labels
levels_to_label = [5, 6, 10]
contour_lines = plt.contour(X_c, Y, msp_matrix, levels=levels_to_label, 
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
    X_c, Y, msp_matrix,
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
    X_c, Y, msp_matrix,
    levels=[4.5],
    colors='#d6d8d8',
    linewidths=1,
    linestyles='--',
    zorder=4         # make sure it sits above the other contours
)

ax.contour(
    X_c, Y, msp_matrix,
    levels=[9.6],
    colors='#d6d8d8',
    linewidths=1,
    linestyles='--',
)

# Gevo line
# 3) Dashed boundary at MSP = 9.6
plt.contour(
    X_c, Y, msp_matrix,
    levels=[7.75],
    colors="#A6A611",
    linewidths=1)



# Colorbar
#cbar = plt.colorbar(contourf)
cbar.set_label('Minimum Jet Selling Price [$/gal]', fontsize=10, labelpad=20)
cbar.ax.tick_params(labelsize=10)

plt.savefig("selectiivty contour.svg", bbox_inches = 'tight', dpi=300)
plt.tight_layout()
plt.show()

```

This shall yield the contour plot!


