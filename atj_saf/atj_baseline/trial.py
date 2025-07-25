import qsdsan as qs
import biosteam as bst
import thermosteam as tmo
tmo.Stream.display_units.N = 20 
from qsdsan.sanunits import _heat_exchanging 
import pandas as pd

chemicals = qs.Chemicals(
    ['Water', 
    'Ethanol', 
    'Ethylene',
    'Butene',
    'Hex-1-ene',
    'Oct-1-ene',
    'Dec-1-ene',
    'Dodec-1-ene',
    'Tetradec-1-ene',
    'Hexadec-1-ene',
    'Octadec-1-ene',
    'Icos-1-ene',
    'Ethane',
    'Butane',
    'Hexane',
    'Octane',
    'Decane',
    'Dodecane',
    'Tetradecane',
    'Hexadecane',
    'Octadecane',
    'Eicosane',
    'Hydrogen'], cache = True)


qs.set_thermo(chemicals)

conversion_factors = {
    'gal_to_m3' : 1/264.17       # 1 m3 = 264.17 gals
}

operating_parameters = {
    'operating_factor' : 0.9,    # % of time the plant operates annually
    'hours_per_annum' : 365*24,  # 8760 total hours 
}

fuel_properties = {
    'max_fuel_yield' : 0.56,  # kg Fuel/kg Ethanol -  From Wang et al https://docs.nrel.gov/docs/fy16osti/66291.pdf
    'percentage_yield' : 0.8,        # 80% theoretical yield
    'saf_density' : 776,             # kg/m3 at 15 C according to ASTM D7566 (https://www.spglobal.com/content/dam/spglobal/ci/en/documents/platts/en/our-methodology/methodology-specifications/biofuels/supporting-materials/faq-platts-saf-renewable-diesel.pdf)
    'rn_density' : 725              # kg/m3 
}

feed_parameters = {
    'phase' : 'l',
    'purity' : 0.995,                 # 95 wt% aqueous feed
    'temperature' : 293.15,          # 20 C
    'pressure' : 101325,             # 1 bar
}


price_data = {
    'ethanol' : 2.67, # USD/gal
    'hydrogen' : 3.7,  # USD/kg for ATR + CCS determined using H2A. Includes complete value chain costs (production. compression, delivery, and storage)
    'renewable_naphtha' : 0.71 , # USD/kg
    'renewable_diesel' : 1.888,         # USD/kg [2]
    'wastewater_treatment' : 1.85e-3,      # $/kg of standard WW from [1]
    'dehydration_catalyst' : 36.81,     # USD/kg 
    'oligomerization_catalyst' : 158.4, # USD/kg
    'hydrogenation_catalyst' : 59.12    # USD/kg
}

dehydration_parameters = {
    'dehyd_temp' : 481+273.15,   
    'dehyd_pressure' : 1.063e6, 
    'dehyd_conv' : 0.995,       
    'dehyd_WHSV' : 0.3,
    'catalyst_lifetime' : 2 
}

#split_ratio = 0.5 # split ratio of dehydration reactor effluent

oligomerization_parameters = {
    'olig_temp' : 393.15,     # in K corresponding to 120 C
    'olig_pressure' : 3.5e6,    # 30 bar
    'olig_conv'    : 0.993,       # 99.3% conversion from Heveling paper
    'olig_WHSV'    : 1.5,    # Weighted Hourly Space Velocity
    'catalyst_lifetime' : 1

}

biofuel_composition = {              # More info in the OligomerizationReactor class doc.
                    'C4H8'  : 0.2,          # 0.2
                    'C6H12' : 0.15,          # 0.15
                    'C10H20': 0.62,          # 0.62
                    'C18H36': 0.03,          # 0.03
                    }


hydrogenation_parameters = {
    'hydgn_temp' : 623.15,    # in K corresponding to 250 c
    'hydgn_pressure' : 3.5e6,   # 3More info in HydrogenationReactor class documentation
    'hydgn_conv' : 1.0, 
    'hydgn_WHSV' : 3,
    'catalyst_lifetime' : 3
}

hydgn_conv = 1

comp_driver_efficiency = 1
excess_hydrogen_ratio = 2 

'''

[2] https://afdc.energy.gov/fuels/prices.html. Value from January 2023 -> 5.57 USD/gal converted to USD/kg.
RD density here was 773 kg/m3 and has been reported to have a density of 765 - 800 kg/m3 according to https://www.phillips66.co.uk/renewable-diesel/ so I'm good
'''
def calculate_ethanol_flow(req_saf = None):
    '''
        Calculate the hourly ethanol mass flow rate required to produce the given SAF output.

        Parameters:
        - req_saf (float, optional): Required SAF production in million gallons per year (MM gal/yr)
                                     If None, defaults to 9 MM Gal/yr for conventional atj baseline case

        Returns:
    - float: Ethanol feedstock flow rate (kg/hr)

    '''

    if req_saf is None:
        req_saf = 9 # MM gal/yr default value


    saf_mass_flow = req_saf*(1e6)*conversion_factors['gal_to_m3']*fuel_properties['saf_density'] # convert MMgal/yr to kg/yr
    etoh_flow = saf_mass_flow/(fuel_properties['max_fuel_yield']*fuel_properties['percentage_yield']*operating_parameters['operating_factor']*operating_parameters['hours_per_annum'])
    # feed_parameters['ethanol_flow'] = etoh_flow

    return etoh_flow

def ethanol_price_converter(price):
    '''
    Function to convert the price of ethanol from USD/gal to USD/kg as BioSTEAM takes in values in USD/kg
    '''
    updated_price = (price*264.172)/789  # 789 is the density of ethanol that is at 20 C from Aspen Plus, a value taken from 2011 Humbird report
    return updated_price

saf_required = 9

class EthanolStorageTank(qs.SanUnit):
    '''
    Hydrocarbon storage tank from [1] 
    Similar storage for gasoine and jet fuel

    The costing is based off 2 tanks, 750,000 gallons each, and 7 days of storage
    The costing year in the original analysis was 2009. Costing is based off vendor 'Mueller'
    Also assumes one spare
    Material of construction is ASTM A285 Grade C carbon steel.

    [1] Humbird, D., Davis, R., Tao, L., Kinchin, C., Hsu, D., Aden, A., ... & Dudgeon, D. (2011). 
    Process design and economics for biochemical conversion of lignocellulosic biomass to ethanol: 
    dilute-acid pretreatment and enzymatic hydrolysis of corn stover (No. NREL/TP-5100-47764). 
    National Renewable Energy Lab.(NREL), Golden, CO (United States).

    '''
    _N_ins = 1
    _N_outs = 1

    _units = {
        'Storage Days': 'days',
        'Total Capacity': 'gals'}



    def __init__(self, ID = '',     ins = None, outs = (), thermo = None, init_with = 'SanStream',
                 storage_period = 7,
                tank_exp = 0.7):
        qs.SanUnit.__init__(self, ID, ins, outs, thermo, init_with)
        self.storage_period = storage_period
        self.tank_exp = tank_exp
        
            
    def _design(self):
        D = self.design_results
        ethanol_flow = self.ins[0].F_vol
        capacity = ethanol_flow  * 264.172* self.storage_period *24
        D['Total Capacity'] = capacity

    def _cost(self):
        D = self.design_results
        purchase_costs = self.baseline_purchase_costs
        total_cost = 1340000*(bst.CE/521.9)*(D['Total Capacity']/750000)**self.tank_exp
        purchase_costs['Total Cost'] = total_cost
        
        
etoh_in = qs.SanStream(
    'etoh_in',
    Ethanol = calculate_ethanol_flow(saf_required),
    Water =  calculate_ethanol_flow(saf_required)*((1-feed_parameters['purity'])/(feed_parameters['purity'])),
    units = 'kg/hr',
    T = feed_parameters['temperature'],
    P = feed_parameters['pressure'],
    phase = feed_parameters['phase'],
    price = ethanol_price_converter(price_data['ethanol'])) # 2.7/gal    

etoh_storage = EthanolStorageTank(ins = etoh_in)
etoh_storage.simulate()


import biosteam as bst, qsdsan as qs


class Pump(bst.units.Pump): 

    @property
    def add_OPEX(self):
        if not hasattr(self, "_add_OPEX"):
            self._add_OPEX = 0.0  # Default OPEX if missing

        return {'Additional OPEX': self._add_OPEX} if isinstance(self._add_OPEX, (float, int)) \
            else self._add_OPEX


    @property
    def uptime_ratio(self):
        if not hasattr(self, "_uptime_ratio"):
            self._uptime_ratio = 0.9  # Default OPEX if missing
        return self._uptime_ratio
    

    # Should be a pump and not a compressor, need to fix this
pump_1 = Pump('PUMP1', ins = etoh_storage.outs[0], P = 1373000)    # Pressure from the patent
pump_1.simulate()


#pump_1.outs[0].show()
furnace_0 = _heat_exchanging.HXutility('FURNACE_0', ins = pump_1.outs[0], T = 500, rigorous = True)
furnace_0.simulate()

furnace_0.outs[0].show()