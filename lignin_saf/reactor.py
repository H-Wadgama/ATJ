
import biosteam as bst, math, typing, numpy as np

from math import ceil
from typing import Optional
from biosteam.units.design_tools import (
    PressureVessel, size_batch
)
 
'''
__all__ = (
    'SolvolysisReactor', 'Solvolysis', 'RCF-1'
)
'''
class SolvolysisReactor(bst.Unit, bst.units.design_tools.PressureVessel):



    auxiliary_unit_names = (
        'pump_1', 'heat_exchanger_1'
    )

    _N_ins = 2
    _N_outs = 2
    
    _units = {**PressureVessel._units,
              'Pressure drop': 'bar',
              'Batch time': 'hr',
              'Loading time': 'hr',
              'Residence time': 'hr',
              'Total volume': 'm3',
              'Reactor volume': 'm3'}
    


    # Default operating temperature [K]
    T_default: float = 463.15  # 190 C from  https://doi.org/10.1016/j.joule.2017.10.004

    #: Default operating pressure [Pa]
    P_default:  float = 6e6 # 60 MPa from https://doi.org/10.1016/j.joule.2017.10.004
    
    #: Default residence time [hr]
    tau_default: float = 3

    #: Default fraction of working volume over total volume.
    V_wf_default: float = 0.8


    #: Default length to diameter ratio.
    length_to_diameter_default: float = 3
    
    #: Default cleaning and unloading time (hr).
    tau_0_default: float  = 1 # from https://doi.org/10.1039/D1EE01642C
    
    # Default superficial velocity of solvent (ft/s)
    superficial_velocity_default: float = 0.3 # Just assumed 

    # Default methanol decomposition (%)
    methanol_decomposition_default: float = 0.005 # from https://doi.org/10.1039/D1EE01642C

    # Default poplar bed void fraction 
    epsilon_default: float = 0.5


    def _init(
            self,
            T: Optional[float] = None, 
            P: Optional[float] = None,
            tau: Optional[float] = None,
            V_wf: Optional[float] = None,
            length_to_diameter: Optional[float] = None, 
            vessel_material: Optional[str] = None,
            vessel_type: Optional[str] = None,
            tau_0: Optional[float] = None,  
            superficial_velocity: Optional[float] = None,
            methanol_decomposition: Optional[float] = None,
            epsilon: Optional[float] = None,
            N_beds = 4, *,
            reaction
            ):
        
        
        self.T = self.T_default if T is None else T
        self.P = self.P_default if P is None else P
        self.tau = self.tau_default if tau is None else tau
        self.V_wf = self.V_wf_default if V_wf is None else V_wf
        self.length_to_diameter = self.length_to_diameter_default if length_to_diameter is None else length_to_diameter
        self.vessel_material = 'Stainless steel 316' if vessel_material is None else vessel_material
        self.vessel_type = 'Vertical' if vessel_type is None else vessel_type
        self.tau_0 = self.tau_0_default if tau_0 is None else tau_0
        self.superficial_velocity = self.superficial_velocity_default if superficial_velocity is None else superficial_velocity
        self.methanol_decomposition = self.methanol_decomposition_default if methanol_decomposition is None else methanol_decomposition
        self.epsilon = self.epsilon_default if epsilon is None else epsilon
        
        if N_beds != 4:
            raise ValueError('only 4 biomass beds are valid')
        self.reaction = reaction
        self.N_beds = N_beds
        pump_1 = self.auxiliary('pump_1', bst.Pump, ins = self.ins[1])
        heat_exchanger_1 = self.auxiliary('heat_exchanger_1', bst.HXutility, ins = pump_1.outs[0])


    def _size_bed(self):
        biomass, solvent = self.ins
        #used_biomass, used_solvent = self.outs
        #used_solvent.copy_like(solvent)
        #used_solvent.P = self.P
        #used_solvent.T = self.T

        biomass_rho = 150  # [kg/m3] density of poplar of particle size 0.4 x 0.4 cm from Table 2-2 of https://digital.lib.washington.edu/server/api/core/bitstreams/ac598b6f-f82a-423a-a8c9-2cd4ecd9aac1/content
        total_mass_flow = biomass.F_mass + solvent.F_mass
        solvent_mass_frac = solvent.F_mass/total_mass_flow
        biomass_mass_frac = biomass.F_mass/total_mass_flow
        mixture_avg_density = biomass_rho * biomass_mass_frac + solvent.rho * solvent_mass_frac 

        total_tau = self.tau + self.tau_0 

        total_volume = (total_mass_flow*total_tau)/mixture_avg_density

        volume_per_reactor = total_volume/self.N_beds

        actual_per_reactor_volume = volume_per_reactor/0.5  # frac_working volume

        Q = solvent.F_vol * (3.28**3) # ft3/hr
        u = self.superficial_velocity * 3600   # ft/hr
        self.area = area = Q / u
        self.diameter = diameter = 4 * (area/np.pi) ** 0.5

        self.length = bed_length = actual_per_reactor_volume/area


        #self.length = total_length = total_biomass_volume/area # Length calculated based off L/D
        #if self.N_beds == 4:  # always true
        #
        #     bed_length = total_length/4
        return diameter, bed_length, actual_per_reactor_volume
        
        




        
        
        
        biomass = self.ins[0]
        biomass_massflow = biomass.F_mass # kg/hr
        total_biomass_weight = biomass_massflow * (self.tau+self.tau_0)
        total_biomass_volume = (total_biomass_weight/self.rho) * 1.5 # 50% overdesign to accomodate solvent flow 

        solvent = self.ins[1]
        

    def _run(self):
        biomass, solvent = self.ins
        used_biomass, used_solvent = self.outs
        used_solvent.copy_like(solvent) 
        used_solvent.imass['Methanol'] = used_solvent.imass['Methanol']*(1-self.methanol_decomposition) # 0.5% methanol lost due to decomposition
        used_biomass.copy_like(biomass)
        used_solvent.P = self.P
        used_solvent.T = self.T

        self.reaction(used_biomass)
        

        solubilized_lignin = used_biomass.imass['SolubleLignin'] 
        used_solvent.imass['SolubleLignin'] += solubilized_lignin # Soluble lignin part of solvent stream 
        used_biomass.imass['l', 'SolubleLignin'] = 0 # No soluble lignin in biomass
        




    def _calculate_pressure_drop(self,
                                D,    
                                rho,                    
                                mu,                  
                                epsilon,              
                                u):
                                       
        Re = (D*rho*u)/mu
        if Re/(1-epsilon) < 500:
            dP = ((1-epsilon)/(epsilon**3))*(1.75+(150*(1-epsilon)/Re))
        elif 1000 < Re/(1-epsilon) < 5000:
            dP = 6.8*(((1-epsilon)**1.2)/epsilon**3)*Re**-0.2
        return dP
    
        

    def _design(self):
        diameter, length, actual_per_reactor_volume = self._size_bed()   # Calling size bed function to determine diameter and length 

        self.set_design_result('Diameter', 'ft', diameter)  
        self.set_design_result('Length', 'ft', length)
        self.set_design_result('Reactor volume', 'm3', actual_per_reactor_volume)


        
        # Calculates weight based off pressure, diameter and length
        # Adds vcessel type wall thickness, vessel weight, diameter and length to dictionary
        # But diameter and length are already there because of set_design_result above
        self.design_results.update(
            self._vertical_vessel_design(    
                self.P*(1/6894.76),
                self.design_results['Diameter'],
                self.design_results['Length']
            )
        )
        
                            

        pressure_drop = self._calculate_pressure_drop( 0.004,    # poplar particle diameter in [m]
        800, #self.ins[1].rho,                    # methanol water density [kg/m3]
        0.0006, # self.ins[1].get_property('mu', 'kg/m/s'), # methanol water viscosity [mu]
        0.5, #self.epsilon,     # Void fraction 
        0.1 # self.superficial_velocity * 3.28 # # superficial velocity [m/s]                                                
        )                  
        
        self.set_design_result('Pressure drop', 'bar', pressure_drop)
        self.pump_1.P = (self.P - self.ins[1].P) + pressure_drop
        self.pump_1.simulate()

        self.heat_exchanger_1.T = self.T
        self.heat_exchanger_1.simulate()
        





        

    def _cost(self):
        design = self.design_results # Calling the dictionary used to store design results in design method above 

        baseline_purchase_costs = self.baseline_purchase_costs # Dictionary for storing baseline costs

        weight = design['Weight']  # weight parameter stores the value from the 'Weight' key in the design dictionnary

        # Calculates the baseline purchase cost based off diameter length and weight
        baseline_purchase_costs.update( 
            self._vessel_purchase_cost(weight, design['Diameter'], design['Length'])
        )

        self.parallel['self'] = self.N_beds # Used to create multiple of the same beds
        # self.parallel['pump_1'] = 1


        
        '''
          **** Considerations needed *****
          - Pressure drop
          - Vessel material
          - How are 3 running and 1 regenerating? Need to add 
          - Void fraction and overdesign
          
          
        '''



        

        