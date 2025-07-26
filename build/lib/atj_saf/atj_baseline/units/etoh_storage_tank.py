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
        
        
    