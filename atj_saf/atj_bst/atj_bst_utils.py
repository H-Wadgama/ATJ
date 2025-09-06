feed_parameters = {
    'phase' : 'l',
    'purity' : 0.995,                
    'temperature' : 293.15,          
    'pressure' : 101325,             
}


'''
feed_parameters are from [1], page 128. 
The process flow diagram - Stream 703
Temperature = 20 C
Pressure = 1 bar
Vapor fraction = 0 
Purity = 99.5 wt%


    [1] Humbird, D., Davis, R., Tao, L., Kinchin, C., Hsu, D., Aden, A., ... & Dudgeon, D. (2011). 
    Process design and economics for biochemical conversion of lignocellulosic biomass to ethanol: 
    dilute-acid pretreatment and enzymatic hydrolysis of corn stover (No. NREL/TP-5100-47764). 
    National Renewable Energy Lab.(NREL), Golden, CO (United States).

'''


# Below is data for the 3 catalytic upgrading reactor steps 

dehyd_data = {
    'temp' : 481+273.15,   
    'pressure' : 1.063e6, 
    'conv' : 0.995,       
    'whsv' : 0.3,
    'catalyst_lifetime' : 2 
}




olig_data = {
    'temp' : 393.15,         # [K] Corresponding to 120 C
    'pressure' : 3.5e6,      # [bar] 30 bar
    'conv'    : 0.993,       # [%] 99.3% conversion from Heveling paper
    'whsv'    : 1.5,         # [kg/hr/kg.cat] Weighted Hourly Space Velocity (feed flow rate divide by catalyst weight)
    'catalyst_lifetime' : 1  # [yr] 

}

prod_selectivity = {                         
                    'C4H8'  : 0.2,          
                    'C6H12' : 0.15,         
                    'C10H20': 0.62,          
                    'C18H36': 0.03,          
                    }           


hydgn_data = {
    'temp' : 623.15,    
    'pressure' : 3.5e6,   
    'conv' : 1.0, 
    'whsv' : 3,
    'catalyst_lifetime' : 3
}




# Below is price data for the chemicals and streams
# Plan would be to ideally convert it to JSON or YAML or some other proper file
price_data = {
    'ethanol' : 2.67, # USD/gal
    'hydrogen' : 4.45,  # USD/kg for ATR + CCS determined using H2A. Includes complete value chain costs (production. compression, delivery, and storage)
    'renewable_naphtha' : 0.71 , # USD/kg
    'renewable_diesel' : 1.888,         # USD/kg [2]
    'wastewater_treatment' : 1.85e-3,      # $/kg of standard WW from [1]
    'dehydration_catalyst' : 36.81,     # USD/kg 
    'oligomerization_catalyst' : 158.4, # USD/kg
    'hydrogenation_catalyst' : 59.12    # USD/kg
}
