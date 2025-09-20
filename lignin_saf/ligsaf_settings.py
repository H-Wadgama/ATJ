
# Process conditions from Bartling et al 2021 unless specified otherwise


# Feed
feed_parameters = {
    'flow' : 2000,                   # [dry metric tons per day], consistent with other TEA models 
    'moisture' : 0.2         # [%] 20% moisture
}


# RCF
rcf_conditions =  {
    'T' : 200 + 273.15,            # [K]
    'P' : 60e5,                    # [bar]
    'tau_s' : 2,                   # [hr] Solvolysis reaction residence time
    'tau_h' : 1,                   # [hr] Hydrogenolysis reaction residence time

}



meoh_h2o = 9                       # [ratio] Solvent : Water ratio
methanol_to_biomass = 9            # [L/kg] from https://doi.org/10.1016/j.copbio.2018.12.005
                                   # Surprisingly, Bartling et al assumes a 9L/kg for a flow through
                                   # configuration which is very less.


h2_consumption = 0.01241           # h2 consumption per kg dry biomass feed. Roughly 0.02958 kg H2 consumed per kg RCF oil, I just back calculated it in terms of dry biomass feed so I can use it as an input parameter

solvolysis_parameters = {
    'Cellulose_retention' : 0.9,    # [%] 90% cellulose retained in biomass pulp after RCF
     'Xylose_retention' : 0.93,     # [%] 93% xylose retained in biomass pulp after RCF
     'Extractives_retention' : 0,   # [%] extractives retention in biomass from 10.1039/d1gc01591e Table S1 (no extractives in post-solvolysis poplar).  # Also validated from SI Table S17 of Bartling et al where extractives total amount (kg) in RCF oil is similar to what is in the poplar feed            
     'Acetate_retention' : 0,       # [%] acetate retention in biomass from 10.1039/d1gc01591e Table S1 (no acetate in post-solvolysis poplar)
     'Arabinan_retention' : 0.4,    # [%] Bartling et al
     'Galactan_retention' : 0.5,    # [%] Bartling et al
     'Mannan_retention' : 0.5,      # [%] Bartling et al
     'Delignification' : 0.7,        # [%] 70% biomass delignified from Bartling et al
     'MeOH_CO' : 0.364/100,   # [wt%] methanol lost as CH4. From https://pubs.rsc.org/en/content/articlelanding/2015/cc/c5cc04025f Table 1 where 0.13 mol% of methanol lost as CH4 for Ru/C catalyst
                                    # reactor was batch and hydrogen was fed at 3 MPa within the reactor, also biomass was birchwood, so this might be different in my case
    'MeOH_CH4' :    0.128/100     # [wt%] methanol lost as CH4. From https://pubs.rsc.org/en/content/articlelanding/2015/cc/c5cc04025f Table 1 where 0.08 mol% of methanol lost as CH4 for Ru/C catalyst
                                    # reactor was batch and hydrogen was fed at 3 MPa within the reactor, also biomass was birchwood so this might be different in my case
}


RCF_catalyst = {
    'replacement' : 1,   # [/yr] catalyst replacement rate from Bartling et al
    'loading' : 0.1    # [kg/kg]  1:10 catalyst: dry biomass feed by wt
}



     
h2_biomass_ratio = 0.053958086     # Ratio of mass flow of h2 by the mass flow of dry biomass feed from Bartling et al, SI stream tables (Table S2)
                                   # Main text mentioned 10 L/min/dry kg biomass (STP) but i don't know what the dry kg biomass is normalized to (/day, /hr ?)

catalyst_loading = 0.1             # 1:10 catalyst: dry biomass feed by wt 

# RCF oil composition

rcf_oil_yield = {
    'Monomers' : 0.5,
    'Dimers' : 0.25,
    'Oligomers' : 0.25
}




##### Conversion factors ########
kg_per_ton = 907.1846 # kg per metric ton
moisture = 0.2

feedstock_price = 80 # USD/dry metric ton from Bartling et al
feedstock_price = feedstock_price/kg_per_ton/(1+moisture)

# Chemicals from cellulosic ethanol model
# Prices are in 2007 USD (from 2011 Humbird report), and are updated to 2016 USD here 
# Prices are from September since end of fiscal year
# Using Federal Reserve Economic Data (FRED) St. Louis Fed data (accessed 9/17/2025)

sulfuric_acid_price = 0.08972 *  (128.9/174.8)      # [USD/kg] Sulfuric acid price update from https://fred.stlouisfed.org/series/WPU0613020T1
ammonia_price = 0.4486 * (229.7/227.5)              # [USD/kg] Ammonia price update from https://fred.stlouisfed.org/series/WPU061
cellulase_price = 0.212 * (233.6/180.1)             # [USD/kg] Cellulase price update from https://fred.stlouisfed.org/series/WPU0679
CSL_price = 0.05682 * (221.3/226.7)                 # [USD/kg] Corn steep liquor price update from https://fred.stlouisfed.org/series/WPU065201. CSL is a nitrogen containing compound
DAP_price = 0.98692 * (221.3/226.7)                 # [USD/kg] DAP price update from https://fred.stlouisfed.org/series/WPU065201. DAP is a nitrogen containing compound
caustic_price = 0.07476 * (135.3/116.6)             # [USD/kg] Casutic price update from https://fred.stlouisfed.org/series/WPU06130302
denaturant_price = 0.756 * (152.0/225.6)            # [USD/kg] Denaturant update from https://fred.stlouisfed.org/series/WPU0571. Denaturant is gasoline
cooling_tower_chemicals_price = 3.0 * (155.6/165.0) # [USD/kg] Cooling tower chemcials update from https://fred.stlouisfed.org/series/PCU325998325998A. cooling tower chemicals are used for water treatment
FOD_lime_price = 0.19938 * (237.5/164.6)            # [USD/kg] FGD lime update from https://fred.stlouisfed.org/series/WPU06130213
boiler_chemicals_price = 4.99586 * (248.8/189.5)    # [USD/kg] Boiler chemicals update from https://fred.stlouisfed.org/series/WPU0613. Boiler chemicals are ash which is inorganic



prices = {
    'Feedstock' : feedstock_price,
    'Methanol' :  0.27455,               # [USD/kg] from Bartling et al
    'Hydrogen' : 1.606,                  # [USD/kg] from Bartling et al
    'NiC_catalyst' : 37.5,              # [USD/kg] from Bartling et al
    'H2SO4' : sulfuric_acid_price,
    'NH3' : ammonia_price,
    'Cellulase' : cellulase_price,
    'CSL' : CSL_price,
    'DAP' : DAP_price,
    'Caustic' : caustic_price,
    'Denaturant' : denaturant_price,
    'CT_chemicals' : cooling_tower_chemicals_price,
    'FOD_lime' : FOD_lime_price,
    'Boiler_chemicals' : boiler_chemicals_price
}