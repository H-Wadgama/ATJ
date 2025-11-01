"""

Ethanol-to-Jet biorefinery for Sustainable Aviation Fuel production 
The Pennsylvania State University
Chemical Engineering Department
S2D2 Lab (Dr. Rui Shi)
@author: Hafi Wadgama

This file contains:
-   Bioethanol feed parameters
-   Catalytic upgrading reaction conditions and ethylene to olefins selectivity
-   Price data for all streams in the model

Some parameters that don't fall into the above category but can also be readily changed by the user are also provided here. 

Detailed information about the literature values is provided in Appendix SX from doi....

"""


# Bioethanol feed parameters
feed_parameters = {
    'phase' : 'l',
    'purity' : 0.995,                
    'temperature' : 293.15,          
    'pressure' : 101325,             
}


# Catalytic upgrading reaction conditions and ethylene to olefins selectivity

# Dehydration reaction parameters
dehyd_data = {
    'temp' : 481+273.15,    # [K] Operating temperature   
    'pressure' : 1.063e6,   # [Pa] Operating pressure    
    'conv' : 0.995,         # [%] Conversion      
    'whsv' : 0.3,           # [kg/hr/kgcat] Weighted Hourly Space Velocity (feed flow rate divide by catalyst weight)
    'catalyst_lifetime' : 2 # [yr] Catalyst lifetime
}



# Oligomerization reaction parameters
olig_data = {
    'temp' : 393.15,         # [K] Corresponding to 120 C
    'pressure' : 3.5e6,      # [Pa] 30 bar
    'conv'    : 0.993,       # [%] 99.3% conversion from Heveling paper
    'whsv'    : 1.5,         # [kg/hr/kgcat] Weighted Hourly Space Velocity (feed flow rate divide by catalyst weight)
    'catalyst_lifetime' : 1  # [yr] 

}

# Ethylene to oligomer selectivity
prod_selectivity = {                         
                    'C4H8'  : 0.2,           
                    'C6H12' : 0.15,         
                    'C10H20': 0.62,          
                    'C18H36': 0.03,          
                    }           

# Hydrogenation reaction parameters
hydgn_data = {
    'temp' : 623.15,    
    'pressure' : 3.5e6,   
    'conv' : 1.0, 
    'whsv' : 3,
    'catalyst_lifetime' : 3
}

h2_recovery = 0.85 # mol % recovery of hydrogen from PSA splitter following hydrogenation.


##### Conversion factors #######
gal_to_m3 = 1/264.172
mj_per_btu = 0.00105506

# Ethanol price conversion (From USD/gal to USD/kg)
ethanol_price = 2.67      # [USD/gal]
ethanol_rho = 789.45      # [kg/m3] Density of liquid ethanol at 20 C and 1 atm
ethanol_price = ethanol_price*(1/gal_to_m3)*(1/ethanol_rho)

# Natural gas price conversion
natural_gas_price = 3       # [$/MMBTU]
natural_gas_price = natural_gas_price/1e6/mj_per_btu   
natural_gas_HHV = 55        # [MJ/kg] https://group.met.com/en/media/energy-insight/calorific-value-of-natural-gas/
nautral_gas_price = natural_gas_price*natural_gas_HHV

# Price data for all streams in the model
price_data = {
    'ethanol' : ethanol_price,          # [USD/kg]
    'NG' : natural_gas_price,           # [USD/kg]
    'hydrogen' : 4.45,                  # [USD/kg] for ATR + CCS determined using H2A. Includes complete value chain costs (production. compression, delivery, and storage)
    'renewable_naphtha' : 0.71,         # [USD/kg] 
    'renewable_diesel' : 1.888,         # [USD/kg] [2]
    'wastewater_treatment' : 1.85e-3,   # [USD/kg] of standard WW from [1]
    'dehydration_catalyst' : 36.81,     # [USD/kg] 
    'oligomerization_catalyst' : 158.4, # [USD/kg]
    'hydrogenation_catalyst' : 59.12    # [USD/kg]
}
