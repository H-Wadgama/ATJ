import qsdsan as qs, biosteam as bst

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
        
        
class HydrogenStorageTank(qs.SanUnit):
    '''
    Hydrogen storage tank based off the method by [1]

    Method assumes compressd H2 gas storage at 20 MPa
    Cost of tank calculated was ($600/lb)*(500 lb tank) = $300,000 per tank
    Cost of tank is then subsequently scaled up using an exponent of 0.75 from [1]
    
    _N_ins = 1 (just one hydrogen feed)
    _N_outs = 1
    storage_period = defaults to 7 days of storage
    tank_exp = scale up factor for storage tank based off [1]

    [1] Amos, W. A. (1999). Costs of storing and transporting hydrogen (No. NREL/TP-570-25106; ON: DE00006574). National Renewable Energy Lab.(NREL), Golden, CO (United States).

    '''
    _N_ins = 1
    _N_outs = 1

    _units = {
        'Storage Days': 'days',
        'Total Capacity': 'kg'}



        
    def __init__(self, ID = '',     ins = None, outs = (), thermo = None, init_with = 'SanStream',
                 storage_period = 7, tank_exp = 0.75):
        qs.SanUnit.__init__(self, ID, ins, outs, thermo, init_with)
        self.storage_period = storage_period
        self.tank_exp = tank_exp
        
            
    def _design(self):
        D = self.design_results
        h2_flow = self.ins[0].F_mass 
        capacity = h2_flow * self.storage_period * 24 
        D['Total Capacity'] = capacity

    def _cost(self):
        D = self.design_results
        purchase_costs = self.baseline_purchase_costs
        total_cost = (600*500) * (D['Total Capacity'] /(500/2.2))**self.tank_exp 
        total_cost_cepci_update = total_cost * (bst.CE/381.1)
        total_cost_remove_lang_factor = (total_cost_cepci_update/5.04)
        #D['Total Cost'] = total_cost_cepci_update
        purchase_costs['Total Cost'] = total_cost_remove_lang_factor
        


class HydrocarbonProductTank(qs.SanUnit):
    '''
    Hydrocarbon storage tank from [1].
    Study assumed same storage vessels for gasoline and diesel. Costing based off Aspen Capital Cost Estimator tool
    Gasoline similar to renewable naphtha and diesel similar to SAF, so we assume 1 type of storage 
    for hydrocarbon products.
    Cost is given as original equipment cost in 2013 dollars, for a 500,000 gal storage tank at 15 psi, and 250 F
    Material of construction is carbon steel. 
    Scaling exponent is 0.7. Study also accounts for one spare tank
    

    [2] Dutta, A., Sahir, A. H., Tan, E., Humbird, D., Snowden-Swan, L. J., Meyer, P. A., ... & Lukas, J. 
    (2015). Process design and economics for the conversion of lignocellulosic biomass to hydrocarbon fuels:
    Thermochemical research pathways with in situ and ex situ upgrading of fast pyrolysis vapors 
    (No. PNNL-23823). Pacific Northwest National Lab.(PNNL), Richland, WA (United States).


    '''
    _N_ins = 1
    _N_outs = 1

    _units = {
        'Storage Days': 'days',
        'Total Capacity': 'gals'}

    
    def __init__(self, ID = '',     ins = None, outs = (), thermo = None, init_with = 'SanStream',
                 storage_period = 14,
                tank_exp = 0.7):
        qs.SanUnit.__init__(self, ID, ins, outs, thermo, init_with)
        self.storage_period = storage_period
        self.tank_exp = tank_exp
        
            
    def _design(self):
        D = self.design_results
        hydrocarbon_flow = self.ins[0].F_vol
        capacity = hydrocarbon_flow  * 264.172* self.storage_period *24
        D['Total Capacity'] = capacity

    def _cost(self):
        D = self.design_results
        purchase_costs = self.baseline_purchase_costs
        total_cost = 885400*(bst.CE/567.3)*(D['Total Capacity']/500000)**self.tank_exp

        purchase_costs['Total Cost'] = total_cost
        
        
    
        
    
    