import numpy as np

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

# Example arrays for each cost (fill in your real values)
installed_costs        = installed_costs_per_gal
catalyst_replacement   = cat_replacement_per_gal
utilities_excl_elec    = utility_per_gal
process_electricity    = electricity_per_gal
fixed_costs            = fixed_cost_per_gal
hydrogen               = h2_cost_per_gal
ethanol                = etoh_cost_per_gal
co_product             = co_product_per_gal

# Stack all cost arrays into a single 2D array
costs = np.vstack([
    installed_costs, 
    catalyst_replacement, 
    utilities_excl_elec, 
    process_electricity, 
    fixed_costs, 
    hydrogen, 
    ethanol, 
    co_product
])