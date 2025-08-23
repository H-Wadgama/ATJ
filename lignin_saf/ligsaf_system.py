import biosteam as bst, thermosteam as tmo, numpy as np, pandas as pd
bst.nbtutorial() # Ignore warnings



def create_ligsaf_system():
    from . import ligsaf_chemicals
    from .ligsaf_chemicals import ligsaf_chemicals
    from .reactor import SolvolysisReactor
    # from .ligsaf_utils import 


    bst.Flowsheet.flowsheet.default
    bst.settings.set_thermo(ligsaf_chemicals)


    bst.settings.CEPCI = 541.7   # CEPCI for 2016
    
    
    
    # Defining poplar group based off composition given in Bartling et al [1] Table S1

    ligsaf_chemicals.define_group(
        name='Poplar',
        IDs=['Cellulose',   # Cellulase break this down to glucose
            'Xylan',       # Hemicellulose
            'Arabinan',    # Hemicellulose
            'Mannan',      # Hemicellulose
            'Galactan',    # Hemicellulose
            'Sucrose',   
            'Lignin',
            'Acetate',
            'Extract',
            'Ash'],
        composition=[0.464,      # Dry wt composition, feed also has 20 wt% moisture content
                    0.134,
                    0.002,
                    0.037,
                    0.014,
                    0.001,
                    0.285,
                    0.035,
                    0.016,
                    0.012],
        wt=True
    )

   # RCF conditions from Bartling et al 2021

    rcf_temp = 200 + 273.15            # K 
    rcf_pressure = 60 * 1e5            # Pascal
    rcf_residence_time = 3             # hr
    reactor_operation = 'Isothermal'
    solvent_water_ratio = 9            # 9:1 methanol to water ratio on a vol basis
    catalyst_biomass = 0.1             # catalyst to dry biomass bed ratio
    replacement = 1                    # once replacement of catalyst every year
    biomass_deliginfication = 0.7      # 70% biomass is assumed deligniified
    methanol_decomp = 0.005              # methanol decompositin rate %
    cellulose_retention = 0.9          # 90% 
    xylose_retention = 0.93            # 93% 
    methanol_to_biomass = 9           # 90 mL / g of biomass from https://doi.org/10.1016/j.copbio.2018.12.005



    lignin_monomers = 0.5
    lignin_dimers = 0.25
    lignin_oligomers = 0.25 


    poplar_in = bst.MultiStream('Poplar_In',
                s=[('Poplar', 2e6)], l=[('Water', 0.2*2e6)], 
                 phases = ('s','l'), units='kg/d')
    
    meoh_in = bst.Stream('Methanol_In',
                     Methanol = methanol_to_biomass*poplar_in.F_mass, Water = methanol_to_biomass*poplar_in.F_mass*(1/solvent_water_ratio),
                     units = 'L/hr',
                     T = 300,
                     P = 1e5,
                     phase = 'l'
    )
    
    solvolysis = bst.Reaction('Lignin,s -> SolubleLignin,l', reactant = 'Lignin', phases = 'sl', X = 0.7, basis = 'wt', correct_atomic_balance = False) # Since pseudocomponents, i dont think it has a compatible elemental formulae built in

    rcf_1 = SolvolysisReactor(ins = (poplar_in, meoh_in), N_beds = 4, reaction = solvolysis)
    rcf_1.simulate()

    ligsaf_sys = bst.System('ligsaf', path = rcf_1)

    return ligsaf_sys

ligsaf_system = create_ligsaf_system()






