




import biosteam as bst, numpy as np
from math import ceil

from typing import Optional
from biosteam.units.design_tools import (
    PressureVessel, 
)
 
from lignin_saf.ligsaf_settings import solvolysis_parameters

class SolvolysisReactor(bst.Unit, bst.units.design_tools.PressureVessel):

    """
    Plug flow reactor for solvolysis reaction, where a solvent is used to solubilize lignin present
    in plant cell wall

    In reality, lignin will also be partially depolymerized, but this phenomena is not captured in 
    current design but may be included in a future implementation
    Design based off [1],[2]. Pressure drop calculations from [3]

    By default,  current design supports multiples of 3 identical biomass beds, with 2x operational beds at any given time, 
    offset by 1 hour each. With a 3 hr reaction time + 1 hr turnaround, this gives near continuous throughput
    Example... t = 0 - 1 hr : bed 1, bed 2 online, bed 3 cleaning, 
                t = 1 - 2 hr, bed 2, bed 3 online, bed 1 cleaning
    Since at any given time, the complete throughput is mantained by 2x reactors, the total volumetric flow rate 
    of solvent is constant

    The maximum volume of an individual reactor was fixed at 600 m3, similar to what was suggested in Bartling et al
    For the solvent flow rate of 9 L/kg dry biomass, this corresponds to  
    
    Assumed: Extraction efficiency constant along the reaction residence time
    No energy released on extraction of lignin. Although this assumption might be revised in the future
    
    
    
    References
    ----------------------------------------------------------------------------------
        [1] Bartling, Andrew W., et al. 
        "Techno-economic analysis and life cycle assessment of a biorefinery utilizing
        reductive catalytic fractionation." Energy & Environmental Science 14.8 (2021): 4147-4168.

        [2] Anderson, Eric M., et al. 
        "Flowthrough reductive catalytic fractionation of biomass." Joule 1.3 (2017): 613-622.

        [3] Froment, Gilbert F., Kenneth B. Bischoff, and Juray De Wilde. 
        Chemical reactor analysis and design. Vol. 2. New York: Wiley, 1990.
   -----------------------------------------------------------------------------------

    
    """



    _F_BM_default = {'Horizontal pressure vessel': 3.05,
                     'Vertical pressure vessel': 4.16,
                     'Platform and ladders': 1.}                   

    auxiliary_unit_names = (
        'pump_1', 'heat_exchanger_1'
    )

    _N_ins = 2
    _N_outs = 2
    
    _units = {**PressureVessel._units,
              'Pressure drop': 'bar',
              'Batch time': 'hr',
              'Turnaround time': 'hr',
              'Residence time': 'hr',
              'Total beds': "",
              'Beds in service': "",
              'Total volume': 'm3',
              'Reactor volume': 'm3'}
    


    # Default operating temperature [K]
    T_default: float = 463.15                   # 190 C from  https://doi.org/10.1016/j.joule.2017.10.004

    #: Default operating pressure [Pa]
    P_default:  float = 6e6                     # 6 MPa from https://doi.org/10.1016/j.joule.2017.10.004
    
    #: Default residence time [hr]
    tau_default: float = 2                      # Total 3 hr RCF reaction time divided into 2:1 since solvolysis is more kinetically limiting according to https://pubs.acs.org/doi/full/10.1021/acssuschemeng.8b01256

    #: Default cleaning and unloading time (hr).
    tau_0_default: float  = 1                    # from https://doi.org/10.1039/D1EE01642C
    
    # Default superficial velocity of solvent (m/s)
    superficial_velocity_default: float = 1      # Just assumed 

    # Default methanol decomposition (%)
    methanol_decomposition_default: float = 0.005 # From https://doi.org/10.1039/D1EE01642C

    # Default poplar bed void fraction (epsilon)
    void_frac_default: float = 0.5                # Just assumed here, can be fine tuned once data is known. Assyned because this value gives a low value for pressure drop


    # Default working volume fraction 
    working_vol_default: float = 0.8              # Just assumed based off engineering judgement
 
    # Default poplar diameter [m]
    poplar_diameter_default: float = 0.004        # https://doi.org/10.1039/D1EE01642C mentions < 5mm, Here 4 mm is considered
    
    # Default maximum vessel volume [m3]
    V_max_default: float = 600                    # Bartling paper considered reactor volume as 600 m3



    def _init(
            self,
            T: Optional[float] = None, 
            P: Optional[float] = None,
            tau: Optional[float] = None,
            vessel_material: Optional[str] = None,
            vessel_type: Optional[str] = None,
            tau_0: Optional[float] = None,  
            superficial_velocity: Optional[float] = None,
            methanol_decomposition: Optional[float] = None,
            void_frac: Optional[float] = None,
            working_vol: Optional[float] = None,
            poplar_diameter: Optional[float] = None,
            V_max: Optional[float] = None,
            *,
            reaction_1,
            reaction_2
            ):
        
        
        self.T = self.T_default if T is None else T
        self.P = self.P_default if P is None else P
        self.tau = self.tau_default if tau is None else tau
        self.vessel_material = 'Stainless steel 316' if vessel_material is None else vessel_material
        self.vessel_type = 'Vertical' if vessel_type is None else vessel_type
        self.tau_0 = self.tau_0_default if tau_0 is None else tau_0
        self.superficial_velocity = self.superficial_velocity_default if superficial_velocity is None else superficial_velocity
        self.methanol_decomposition = self.methanol_decomposition_default if methanol_decomposition is None else methanol_decomposition
        self.void_frac = self.void_frac_default if void_frac is None else void_frac
        self.working_vol = self.working_vol_default if working_vol is None else working_vol
        self.poplar_diameter = self.poplar_diameter_default if poplar_diameter is None else poplar_diameter
        self.V_max = self.V_max_default if V_max is None else V_max
        self.reaction_1 = reaction_1
        self.reaction_2 = reaction_2
        pump_1 = self.auxiliary('pump_1', bst.Pump, ins = self.ins[1])
        # heat_exchanger_1 = self.auxiliary('heat_exchanger_1', bst.HXutility, pump_1.outs[0])







    def _size_bed(self):
        
        #### Reactor volume sizing ########

        cycle_time = self.tau + self.tau_0                         # [hr] Total time for a cycle of operation (includes reaction + cleaning-loading-unloading)
        working_vol = self.working_vol                             # Working volume fraction for a reactor to allow suficient mass transfer by allowing enough contact time 
        solvent = self.ins[1]                                      # Preheated solvent inlet

        V_theoretical = solvent.F_vol * self.tau                   # [m3] Theoretical volume required for solvolysis 
        V_actual = V_theoretical/(working_vol * self.void_frac)    # [m3] Actual volume required based off void fraction in poplar bed, and fraction working volume over total reactor length
        N_working = ceil(V_actual/self.V_max)                      # Number of working reactors, rounded off the to the next number
        N_offline = ceil(N_working*(self.tau_0/cycle_time))        # Number of offline beds, calculated based off cleaning time and the total cycle time, rounded off to the next number
        N_total = N_working + N_offline
        V_total = N_total * self.V_max

        

        ##### Reactor diameter and length ########

        u  = self.superficial_velocity                      # [m/s]
        Q_per_reactor_m3 = solvent.F_vol/N_working          # [m3/hr] Volumetric flow rate processed by any reactor
        self.area = A  = Q_per_reactor_m3/(u*3600)          # [m3] Cross sectional area for each reactor
        self.diameter = diameter = 2 * (A/np.pi) ** 0.5     # [m] Diameter of each reactor
        self.length = length = self.V_max/A                 # [m] Length of each reactor

        
        return length, diameter, N_total, N_working, V_total

        
    def _run(self):
        biomass, solvent = self.ins
        used_biomass, used_solvent = self.outs

        used_solvent.copy_like(solvent) 
        used_biomass.copy_like(biomass) 

        used_solvent.P = self.P                                             # Outlet pressure is set to reactor pressure. Inlet pressure will be greater to account for pressure drop
        used_solvent.T = self.T                                             # Since isothermal operation
        

        self.reaction_1(used_biomass) 
        self.reaction_2(used_solvent)
        

        solubilized_lignin = used_biomass.imass['SolubleLignin'] 
        used_solvent.imass['l', 'SolubleLignin'] += solubilized_lignin      # Soluble lignin dissolves in solvent effluent stream 
        used_biomass.imass['SolubleLignin'] = 0                             # No soluble lignin remaining in biomass (assuming 100% extraction efficiency)



        extractives = used_biomass.imass['Extract']                         # From Table S1 https://www.rsc.org/suppdata/d1/gc/d1gc01591e/d1gc01591e1.pdf,
                                                                            # it follows that the extractives component of poplar is 'extracted' in the solvent stream
        used_solvent.imass['l','Extract'] = (1-solvolysis_parameters['Extractives_retention'])*extractives
        used_biomass.imass['Extract'] = (solvolysis_parameters['Extractives_retention'])*extractives

        acetate = used_biomass.imass['Acetate']
        used_solvent.imass['l', 'Acetate'] =  acetate *(1-solvolysis_parameters['Acetate_retention']) # Assuming acetate dissolves as acetic acid with methanol,
                                                                             # BioSTEAM Chemicals assumes same properties for acetic acid and acetate, otherwise is acetate was a pseudocomponent, it might have still stayed in solid phase
        used_biomass.imass['Acetate'] = acetate*solvolysis_parameters['Acetate_retention']


        cellulose_mass = used_biomass.imass['Glucan']
        used_solvent.imass['l', 'Glucan'] = cellulose_mass*(1-solvolysis_parameters['Cellulose_retention']) # Dissolved cellulose assumed to be in liquid phase as solution with solvent
        used_biomass.imass['Glucan'] =  cellulose_mass*solvolysis_parameters['Cellulose_retention']
                                                               

        xylose_mass = used_biomass.imass['Xylan']
        used_solvent.imass['l', 'Xylan'] = xylose_mass * (1-solvolysis_parameters['Xylose_retention']) # Dissolved xylose assumed to be  liquid phase as solution with solvent
        used_biomass.imass['Xylan'] = xylose_mass * solvolysis_parameters['Xylose_retention']

        arabinan_mass = used_biomass.imass['Arabinan']
        used_solvent.imass['l', 'Arabinan'] = arabinan_mass * (1-solvolysis_parameters['Arabinan_retention'])

        used_biomass.imass['Arabinan'] = arabinan_mass * solvolysis_parameters['Arabinan_retention']
        
        mannan_mass = used_biomass.imass['Mannan']
        used_solvent.imass['l', 'Mannan'] = mannan_mass * (1-solvolysis_parameters['Mannan_retention']) 
        used_biomass.imass['Mannan'] = mannan_mass * solvolysis_parameters['Mannan_retention']

        galactan_mass = used_biomass.imass['Galactan']
        used_solvent.imass['l', 'Galactan'] = galactan_mass * (1-solvolysis_parameters['Galactan_retention']) 
        used_biomass.imass['Galactan'] = galactan_mass * solvolysis_parameters['Galactan_retention']
        

        # The temperature and pressure of the carbohydrate pulp is not changed here, I'm assuming I obtain the pulp at ambient conditons 
        # once RCF reaction is complete for downstream processing
        



    def _calculate_pressure_drop(self, bed_length):

        D = self.poplar_diameter                                # [m] poplar particle diameter
        rho = self.ins[1].rho                                   # [kg/m3] 
        mu = self.ins[1].get_property('mu', 'kg/m/s')           # [Pa s] methanol water viscosity 
        epsilon = self.void_frac                                # Void fraction 
        u = self.superficial_velocity                           # [m/s] superficial velocity  

        
        
        Re = (D*rho*u)/mu
        if Re/(1-epsilon) < 500: # Erun equation
            f = ((1-epsilon)/(epsilon**3))*(1.75+(150*(1-epsilon)/Re))
            dP = (f * ((rho*(u**2))/D)* bed_length)*1e-5                # [bar] 1e-5 converts Pa to bar
        elif 1000 < Re/(1-epsilon) < 5000: # Handley and Heggs
            f = ((1-epsilon)/(epsilon**3))*(1.24+(368*(1-epsilon)/Re))
            dP = (f * ((rho*(u**2))/D)* bed_length)*1e-5
        else: # Hicks equation which fits in Wentz and Thodos results for very high Re
            f = 6.8*(((1-epsilon)**1.2)/epsilon**3)*Re**-0.2
            dP = (f * ((rho*(u**2))/D) * bed_length)*1e-5
        return dP

        

    def _design(self):
        length, diameter, N_reactors, N_operating, total_volume = self._size_bed()   # Calling size bed function to determine diameter and length 
        


        
        
        
        cycle_time = self.tau + self.tau_0

        self.set_design_result('Diameter', 'ft', diameter)  
        self.set_design_result('Length', 'ft', length)
        self.set_design_result('Reactor volume', 'm3', self.V_max_default)
        self.set_design_result('Total volume', 'm3', total_volume)
        self.set_design_result('Total beds', '', N_reactors)
        self.set_design_result('Beds in service', '', N_operating)
        self.set_design_result('Residence time', 'hr', self.tau)
        self.set_design_result('Turnaround time', 'hr', self.tau_0)
        self.set_design_result('Batch time', 'hr', cycle_time)

        
        
        # Calculates weight based off pressure, diameter and length
        # Adds vcessel type wall thickness, vessel weight, diameter and length to dictionary
        # But diameter and length are already there because of set_design_result above
        
        self.design_results.update(
            self._vertical_vessel_design(    
                self.P*(1/6894.76),
                self.design_results['Diameter']*3.28084,
                self.design_results['Length']*3.28084
            )
        )
        
                            

        pressure_drop = self._calculate_pressure_drop(length)                  
        
        self.set_design_result('Pressure drop', 'bar', pressure_drop)
        self.pump_1.P = (self.P - self.ins[1].P) + (pressure_drop*1e5)
        self.pump_1.simulate()





    def _cost(self):
        design = self.design_results # Calling the dictionary used to store design results in design method above 

        baseline_purchase_costs = self.baseline_purchase_costs # Dictionary for storing baseline costs

        weight = design['Weight']  # weight parameter stores the value from the 'Weight' key in the design dictionnary
        
        N_reactors = design['Total beds']
        # Calculates the baseline purchase cost based off diameter length and weight
        baseline_purchase_costs.update( 
            self._vessel_purchase_cost(weight, design['Diameter'], design['Length'])
        )

        self.parallel['self'] = N_reactors # Used to create multiple of the same beds
        self.parallel['pump_1'] = 1 # Just one pump needed, valves will redirect to whichever bed is online


        
       
        """
        ---------
          
        Parameters that can be further fine-tuned based on industry/national lab data
        - Void fraction of poplar bed: Herein assumed 0.5, this is subject to change
        - Working volue fraction: Herein assumed 80%, but can change depending on how well mass transfer occurs in real reactors
        - V_max: Maximum volume of a single reactor, herein assumed as 600 m3 based on Bartling et al 2021 paper, but subject to change
        - residence time: Herein 2 hrs, but could change based on which regime is more limiting. 


        ----------

        """

    

        



from lignin_saf.ligsaf_settings import rcf_oil_yield, h2_consumption, feed_parameters, catalyst_loading, prices

class HydrogenolysisReactor(bst.Unit, bst.units.design_tools.PressureVessel):


    #auxiliary_unit_names = (
    #    'heat_exchanger_2'
    #)
    _F_BM_default = {**bst.design_tools.PressureVessel._F_BM_default}
    
    _N_ins = 2
    _N_outs = 1
    
    _units = {**PressureVessel._units,
              # 'Pressure drop': 'bar',
              'Duty': 'kJ/hr',
              'Residence time': 'hr',
              'Reactor volume': 'm3',
              'Total volume': 'm3',
              'Catalyst loading cost': 'USD'}
    


    # Default operating temperature [K]
    T_default: float = 463.15  # 190 C from  https://doi.org/10.1016/j.joule.2017.10.004

    #: Default operating pressure [Pa]
    P_default:  float = 6e6 # 6 MPa from https://doi.org/10.1016/j.joule.2017.10.004
    
    #: Default residence time [hr]
    tau_default: float = 1

    # Default superficial velocity of solvent (m/s)
    superficial_velocity_default: float = 0.001 # Just assumed 

    # Default catalyst bed void fraction (epsilon)
    void_frac_default: float = 0.7    


    # Default working volume fraction 
    working_vol_default: float = 0.9
 
    # Default catayyst diameter [m]
    # poplar_diameter_default: float = 0.004   
    

    h2_consumption_default: float = h2_consumption   #  kg per dry kg biomass feed

    N_reactors_default: float = 2   # Number of reactors

    def _init(
            self,
            # add_OPEX: {},
            T: Optional[float] = None, 
            P: Optional[float] = None,
            tau: Optional[float] = None,
            vessel_material: Optional[str] = None,
            vessel_type: Optional[str] = None,
            superficial_velocity: Optional[float] = None,
            void_frac: Optional[float] = None,
            working_vol: Optional[float] = None,
            h2_consumption: Optional[float] = None,
            N_reactors: Optional[float] = None,
            *,
            reaction
            ):
        
        # self.add_OPEX = add_OPEX.copy()
        self.T = self.T_default if T is None else T
        self.P = self.P_default if P is None else P
        self.tau = self.tau_default if tau is None else tau
        self.vessel_material = 'Stainless steel 316' if vessel_material is None else vessel_material
        self.vessel_type = 'Vertical' if vessel_type is None else vessel_type
        self.superficial_velocity = self.superficial_velocity_default if superficial_velocity is None else superficial_velocity
        self.void_frac = self.void_frac_default if void_frac is None else void_frac
        self.working_vol = self.working_vol_default if working_vol is None else working_vol
        self.h2_consumption = self.h2_consumption_default if h2_consumption is None else h2_consumption
        self.N_reactors = self.N_reactors_default if N_reactors is None else N_reactors
        self.reaction = reaction
        #pump_1 = self.auxiliary('pump_1', bst.Pump, ins = self.ins[1])
        heat_exchanger_2 = self.auxiliary('heat_exchanger_2', bst.HXutility)


    def _size_bed(self):

        #### Reactor volume sizing ########

        residence_time = self.tau
        occupied_frac = 1 - self.void_frac  
        working_vol = self.working_vol        
        gaseous_flow = self.ins[1]
        gas_V_w = gaseous_flow.F_vol * residence_time # [m3] Total liquid working volume
        V_actual = gas_V_w/(self.void_frac * working_vol)/self.N_reactors  # [m3]

        ##### Reactor diameter and length ########
        u  = self.superficial_velocity

        Q_per_reactor_m3 = gaseous_flow.F_vol/self.N_reactors    # [m3/hr] Volumetric flow rate processed by any reactor
        self.area = A  = Q_per_reactor_m3/(u*3600)
        self.diameter = diameter = 2 * (A/np.pi) ** 0.5
        self.length = length = V_actual/A
        V_total = V_actual*self.N_reactors

        
        return length, diameter, V_actual, V_total
        
    def _run(self):
        solvent, hydrogen = self.ins
        effluent, = self.outs

        

        effluent.copy_like(solvent)
        self.reaction(effluent)

        h2 = hydrogen.imass['Hydrogen'] 

        effluent.imass['g', 'Hydrogen'] = h2 - ((self.h2_consumption)*(2e6/24)) # 5 % h2 consumption

        effluent.T = self.T # Assuming isothermal operation
        effluent.P = self.P # Assuming no P drop




    #def _calculate_pressure_drop(self):
        # NOT OPERATIONAL FOR HYDROGENOLYSIS REACTOR

        #D = self.poplar_diameter # [m] poplar particle diameter
        #rho_solv = self.ins[1].rho  # [kg/m3] methanol water density
        #mu = self.ins[1].get_property('mu', 'kg/m/s') # [Pa s] methanol water viscosity 
        #epsilon = self.void_frac # Void fraction 
        #u = self.superficial_velocity # [m/s] superficial velocity          
        
        #Re = (D*rho_solv*u)/mu
        #if Re/(1-epsilon) < 500: # Erun equation
        #    dP = ((1-epsilon)/(epsilon**3))*(1.75+(150*(1-epsilon)/Re))
        #elif 1000 < Re/(1-epsilon) < 5000: # Handley and Heggs
        #    dP = ((1-epsilon)/(epsilon**3))*(1.24+(368*(1-epsilon)/Re))
        #else: # Hicks equation which fits in Wentz and Thodos results for very high Re
        #    dP = 6.8*(((1-epsilon)**1.2)/epsilon**3)*Re**-0.2
        #return dP

        

    def _design(self):
        length,diameter, V_actual, V_total = self._size_bed()   # Calling size bed function to determine diameter and length 


        self.set_design_result('Diameter', 'ft', diameter)  
        self.set_design_result('Length', 'ft', length)
        self.set_design_result('Reactor volume', 'm3', V_actual)
        self.set_design_result('Total volume', 'm3', V_total)

        self.set_design_result('Residence time', 'hr', self.tau)


        
        # Calculates weight based off pressure, diameter and length
        # Adds vcessel type wall thickness, vessel weight, diameter and length to dictionary
        # But diameter and length are already there because of set_design_result above
        self.design_results.update(
            self._vertical_vessel_design(    
                self.P*(1/6894.76),
                self.design_results['Diameter']*3.28084,
                self.design_results['Length']*3.28084
            )
        )
        
        duty = (rcf_oil_yield['Monomers'])**0.5 * self.ins[0].imol['SolubleLignin'] *1000 * 60.5 * 4.184 
        # 70.7 wt% (equivalent to mol% as studies use it interchangeably) B-O-4 linkages in lignin * Solubilized lignin flow [kmol/hr] * 1000 [mol/kmol] * 60.5 kcal/1 mol of B-0-4 linkage * 4184 kJ/kcal

        heat_utility = self.add_heat_utility(duty, self.T) # BioSTEAM automatically setting utility based off duty
                                             
        self.set_design_result('Duty', 'kJ/hr', duty)
        #pressure_drop = self._calculate_pressure_drop()                  
        
        #self.set_design_result('Pressure drop', 'bar', pressure_drop)
        #self.pump_1.P = (self.P - self.ins[1].P) + (pressure_drop*1e5)
        #self.pump_1.simulate()


        

    #def _init_results(self):
    #    super()._init_results()
    #    self.add_OPEX = {}



        

    def _cost(self):
        design = self.design_results # Calling the dictionary used to store design results in design method above 

        baseline_purchase_costs = self.baseline_purchase_costs # Dictionary for storing baseline costs

        weight = design['Weight']  # weight parameter stores the value from the 'Weight' key in the design dictionnary


        catalyst_cost_total = prices['NiC_catalyst']*catalyst_loading*(feed_parameters['flow']*1e3)

        design['Catalyst loading cost'] = catalyst_cost_total

        # Calculates the baseline purchase cost based off diameter length and weight
        baseline_purchase_costs.update( 
            self._vessel_purchase_cost(weight, design['Diameter'], design['Length'])
        )

        self.parallel['self'] = self.N_reactors # Used to create multiple of the same beds

        #add_OPEX = (design['Catalyst loading cost']*2)
        #self._add_OPEX = {'Additional OPEX': add_OPEX} 
        
        """
        Need to add costs for catalyst replacement, current design only has 1 time loading cost
        Duty has been added successfully
        """






class PSA(bst.Unit, bst.units.design_tools.PressureVessel):


    """
    Design and costing of a Pressure Swing Adsorption system for purifying H2 from mix gases C0, CH4
    The model primarily follows the four bed [pressurization, feed, blowdown, purge] sequence in [1], 
    Adsorbent is Zeolite 5A, and adsorption isotherm data from [2] is used. The feed pressure was chosen
    as 5 bar deliberately because adsorption isotherms in Fig 3 [2] indicate linear isotherms until ≈ 5 bar
    pressure. 



    but deviates on some occassions by using parameters more suited for H2 purification. These deviations
    are highlighted in this docstring 


    Deviations:
    Ideally the recovery should be calculated based on eq (6) from [3].
    However, the calculation of recovery through this equation yields a value < 25 %. This is undesirable
    and commercial PSA systems for H2 have recoverys in the range of 85 - 90 %. Therefore, recovery is not
    calculated by rather a value of 85% is used.

    The model was designed for 2 beds, however, commercial H2 systems have upto 12 beds. 
    [3] mentions how the recovery for 2 bed H2 systems is low and hence 12 beds are used.
    Though the use of multiple beds will have multiple equalization stages, for the sake of simplification and for non-dynamic modeling, 
    the equalization stages are ignored.


    Model assumptions:
    Ideal gas mixture
    Isothermal operation
    Negligible axial dispersion/axial pressure gradients
    Constant pressure during feed and purge
    Linear isotherms


    References
    [1] Ruthven, D. M., Farooq, S., & Knaebel, K. S. (1996). 
        Pressure swing adsorption. John Wiley & Sons.

    [2] Yang, J., Lee, C. H., & Chang, J. W. (1997). 
    Separation of hydrogen mixtures by a two-bed pressure swing adsorption process using zeolite 5A. 
    Industrial & engineering chemistry research, 36(7), 2789-2798.

    [3] Kayser, J. C., & Knaebel, K. S. (1986). 
        Pressure swing adsorption: experimental study of an equilibrium theory. 
        Chemical engineering science, 41(11), 2931-2938.
    """


    _F_BM_default = {'Horizontal pressure vessel': 3.05,
                     'Vertical pressure vessel': 4.16,
                     'Platform and ladders': 1.}



    auxiliary_unit_names = (
        'feed_pump',
        'vaccuum_pump'
    )

    _N_ins = 1
    _N_outs = 2
    
    _units = {**PressureVessel._units,
              'Feed step time': 's',
              'Recovery' : '%',
               'Mass of adsorbent per bed': 'kg',
               'No. of beds': '',
              'Bed volume': 'm3',
              'Adsorbent cost': 'USD'}
    


    # Default recovery
    R_default: float = 0.85             # [%] From Ruthven et al, description of commercial scale PSA H2 systems

    # Default feed P
    P_feed_default: float = 5e5         # [Pa] Adsorption isotherms for CO and CH4 roughly linear till 5 atm in https://pubs.acs.org/doi/full/10.1021/ie960728h, and since I assume BLI[3], I operate in linear isotherm pressure range

    # Default purge P
    P_purge_default: float = 0.25e5     # [Pa]  Assumed, low pressure here to give a high cycle pressure

    #: Default adsorbent diameter
    pellet_dia_default = 1.57           # [mm] https://pubs.acs.org/doi/full/10.1021/ie960728h
    
    #: Default bed density
    bed_density_default: float = 795     # [kg/m3] from https://pubs.acs.org/doi/full/10.1021/ie960728h


    #: Default void fraction
    ex_void_frac_default: float = 0.315  #  https://pubs.acs.org/doi/full/10.1021/ie960728h

    N_beds_default: float = 12           # [%] From Ruthven et al, description of commercial scale PSA H2 systems

    adsorbent_cost_default: float = 5   # [$/kg] for zeolite 5A from Ruthven et al design example

    h2_purity_default: float = 1        # [%] 100% pure H2 assumed (ideally 99.99% is mentioned, so decided to go with just 100%)


    def _init(
            self,
            R: Optional[float] = None, 
            P_feed: Optional[float] = None, 
            P_purge: Optional[float] = None,
            pellet_dia: Optional[float] = None,
            bed_density: Optional[float] = None,
            vessel_material: Optional[str] = None,
            vessel_type: Optional[str] = None,
            ex_void_frac: Optional[float] = None,
            N_beds: Optional[int] = None,
            adsorbent_cost: Optional[float] = None,
            h2_purity: Optional[float] = None
            ):
        
        
        
        self.R = self.R_default if R is None else R
        self.P_feed = self.P_feed_default if P_feed is None else P_feed
        self.P_purge = self.P_purge_default if P_purge is None else P_purge
        self.pellet_dia = self.pellet_dia_default if pellet_dia is None else pellet_dia
        self.bed_density = self.bed_density_default if bed_density is None else bed_density
        self.vessel_material = 'Stainless steel 316' if vessel_material is None else vessel_material
        self.vessel_type = 'Vertical' if vessel_type is None else vessel_type
        self.ex_void_frac = self.ex_void_frac_default if ex_void_frac is None else ex_void_frac
        self.N_beds = self.N_beds_default if N_beds is None else N_beds
        self.adsorbent_cost = self.adsorbent_cost_default if adsorbent_cost is None else adsorbent_cost
        self.h2_purity = self.h2_purity_default if h2_purity is None else h2_purity

        self._raw_extract = bst.Stream()
 
        if self.ins[0].P > self.P_feed:
            raise ValueError(f'Inlet pressure ({(self.ins[0].P)/1e5} bar) is greater than PSA feed pressure ({(self.P_feed)/1e5} bar)\n Make sure inlet pressure is either less than or equal to the required PSA feed pressure!')
        self.feed_pump = self.auxiliary('feed_pump', bst.IsentropicCompressor, ins=self.ins[0], P = self.P_feed)
        self.vaccuum_pump = self.auxiliary('vaccuum_pump', bst.IsentropicCompressor, ins = self._raw_extract, outs = self.outs[1], P = 101325)
    
       
        
    
    def _selectivity_parameter(self):
        k_A = 0.2              # slope of equilibrium isotherm of component A ()
        k_B = 0.01
        ex_void_frac = self.ex_void_frac
        beta_A = (ex_void_frac+(1-ex_void_frac)*k_A)
        beta = (ex_void_frac+(1-ex_void_frac)*k_B)/(ex_void_frac+(1-ex_void_frac)*k_A)
        return beta_A, beta


    def _cycle_pressure(self):
        P_H = 5                 # [bar]   Avergae bed pressure during high pressure feed, bar
        P_L = 0.25              # [bar]   Average bed pressure during low pressure purge, bar
        P_cycle = P_H / P_L     # [ratio] PSA cycle pressure ratio
        return P_H, P_L, P_cycle
    

    def _Re(self):
        pellet_dia = self.pellet_dia                            # [mm] Diameter of adsorbent pellets
        inlet_mu = self.ins[0].get_property('mu', 'kg/m/s')        # [kg/m/s] Dynamic viscosity of feed
        mol_in = self.ins[0].F_mol * (1000/3600)                   # [mol/s] Feed flow rate 
        Re = (mol_in*(2e-3))*(pellet_dia*(1e-4))/(inlet_mu)  
        return Re

    
        

    def _adsorbent_req(self):
        beta_A, beta = self._selectivity_parameter()   
        P_H, P_L, P_cycle = self._cycle_pressure()
        Re = self._Re()

        feed = self.ins[0]
        mol_in = feed.F_mol * (1000/3600)                   # [mol/s] Feed flow rate 
        gas_constant = 8.205e-5                             # [m3atm/K/mol] Universal gas constant        bed_density = self.bed_density

        void_frac = self.ex_void_frac

        theta_tf = mol_in/P_cycle
        theta = (void_frac*P_L)/(beta_A*gas_constant*feed.T)   #[mol/m3] Vads
        V_ads_tf = theta_tf/theta

        Acs = (Re/15)  # [m2] Guess value of 15 is used, similar to design example by Ruthven et al, but this could be different for H2/CO/CH4 systems. Example by Rutvehn was for O2 separation from air
        bed_dia = 2*(Acs/np.pi)**0.5     # [m]
        L_tf = V_ads_tf/Acs
        L_guess = 2*bed_dia
        tf = L_guess/L_tf   # [s] Feed step duration
        V_ads = V_ads_tf *tf # [m3]
        m_ads = V_ads * self.bed_density
        return V_ads, m_ads, tf, L_guess, bed_dia




        
    def _run(self):

        if self.ins[0].P < self.P_feed:
            self.feed_pump.P = self.P_feed
            self.feed_pump.simulate()
        else:
            self.feed_pump.outs[0].copy_like(self.ins[0])


        feed = self.feed_pump.outs[0]
        feed.phase = 'g'
        raffinate,  = self.outs[0]


        mol_in = feed.F_mol                           # [Kmol/hr] Feed flow rate 
        y_F = feed.imol['Hydrogen']/feed.F_mol       # [frac] mol fraction of hydrogen in feed
        R = self.R
        mol_out = mol_in * y_F * R 

        raffinate.imol['Hydrogen'] = mol_out
        raffinate.P = self.P_feed          # No presure drop
        raffinate.T = self.ins[0].T        # isothermal operation
        raffinate.phase = 'g'

        
        self._raw_extract.copy_like(feed)
        
        self._raw_extract.imol['Hydrogen'] = feed.imol['Hydrogen'] - raffinate.imol['Hydrogen']
        self._raw_extract.phase = 'g'
        self._raw_extract.T = self.ins[0].T
        self._raw_extract.P = self.P_purge



            
        



       

        

    def _design(self):
        V_ads, m_ads, tf, L_guess, bed_dia = self._adsorbent_req()  
        P_H, P_L, P_cycle = self._cycle_pressure()


    
        

        self.set_design_result('Diameter', 'ft', bed_dia) 
        self.set_design_result('Length', 'ft', L_guess)
        self.set_design_result('Feed step time', 's', tf)
        self.set_design_result('Mass of adsorbent per bed', 'kg', m_ads)
        self.set_design_result('Bed volume', 'm3', V_ads)
   

 
        
        # Calculates weight based off pressure, diameter and length
        # Adds vcessel type wall thickness, vessel weight, diameter and length to dictionary
        # But diameter and length are already there because of set_design_result above
        
        self.design_results.update(
            self._vertical_vessel_design(    
                P_H*(1/6894.76),
                self.design_results['Diameter']*3.28084,
                self.design_results['Length']*3.28084
            )
        )
        

        if self.P_purge < 101325:
            self.vaccuum_pump.P = 101326
            self.vaccuum_pump.simulate()

        else:
            self.vaccuum_pump.outs[0].copy_like(self._raw_extract)

        
        self.parallel['self'] = self.N_beds # Used to create multiple of the same beds
        
        self.parallel['feed_pump']   = 1     # Just one feed pump for the beds
        self.parallel['vaccuum_pump']   = 1  # Just one vaccuum pump for the beds





    def _cost(self):
        design = self.design_results # Calling the dictionary used to store design results in design method above 

        baseline_purchase_costs = self.baseline_purchase_costs # Dictionary for storing baseline costs

        weight = design['Weight']  # weight parameter stores the value from the 'Weight' key in the design dictionnary


        adsorbent_cost = self.adsorbent_cost
        adsorbent_cost_per_bed = adsorbent_cost * design['Mass of adsorbent per bed'] 
        
        baseline_purchase_costs['Adsorbent cost'] = adsorbent_cost_per_bed



        # Calculates the baseline purchase cost based off diameter length and weight
        baseline_purchase_costs.update( 
            self._vessel_purchase_cost(weight, design['Diameter'], design['Length'])
        )
        
        self.vaccuum_pump._cost()          
   
        


        
  



        

        
