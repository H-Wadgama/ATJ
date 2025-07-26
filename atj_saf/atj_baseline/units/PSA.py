# PSA

import biosteam as bst, qsdsan as qs
from atj_saf.atj_baseline.data.other_parameters import *

class PressureSwingAdsorption(qs.sanunits.Splitter, bst.Unit):


    # 85% recovery also consider


        
    def _cost(self):
        D = self.design_results
        super()._cost()
        purchase_costs = self.baseline_purchase_costs
        operating_days = 0.9*24 
        h2_flow = self.outs[0].F_mass * operating_days
        total_cost = 52*(800.8/603.1) * h2_flow * (1/5.04)
        add_OPEX = 0.00162*self.outs[0].F_mass
        self._add_OPEX = {'Additional OPEX': add_OPEX}  

        purchase_costs['Total Cost'] = total_cost
