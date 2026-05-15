    
from biosteam import main_flowsheet as F
import biosteam as bst
import thermosteam as tmo
import pandas as pd
import numpy as np


from lignin_saf.ligsaf_chemicals import create_chemicals
from lignin_saf.ligsaf_settings import feed_parameters, prices
from lignin_saf.systems.rcf import create_rcf_system
from lignin_saf.systems.rcf_oil_purification import create_rcf_oil_purification_system
from lignin_saf.systems.monomer_purification import create_monomer_purification_system
from lignin_saf.systems.ligsaf_utilities import create_rcf_utilities_system
from lignin_saf.ligsaf_settings import hdo_params, h2_pressure
from lignin_saf.ligsaf_units import HydrodeoxygenationReactor, PSA




chems = create_chemicals()
bst.settings.set_thermo(chems)
bst.settings.CEPCI = 541.7   # 2016 USD basis

# Poplar group must be defined before creating any stream that references it
chems.define_group(
    name='Poplar',
    IDs=['Glucan', 'Xylan', 'Arabinan', 'Mannan', 'Galactan',
         'Sucrose', 'Lignin', 'Acetate', 'Extract', 'Ash'],
    composition=[0.464, 0.134, 0.002, 0.037, 0.014,
                 0.001, 0.285, 0.035, 0.016, 0.012],
    wt=True
)

poplar_in = bst.Stream('Poplar_In',
                       Poplar=feed_parameters['flow'] * 1e3,
                       Water=feed_parameters['moisture'] * feed_parameters['flow'] * 1e3,
                       phase='l', units='kg/d', price=prices['Feedstock'])

# ── Area 200: RCF process ──────────────────────────────────────────────────
rcf_system = create_rcf_system(ins=poplar_in)
rcf_system.simulate()

# ── Area 300: Purification ─────────────────────────────────────────────────
rcf_oil_purification_sys = create_rcf_oil_purification_system(ins=F.RCF_Oil)
monomer_purification_sys = create_monomer_purification_system(ins=F.Purified_RCF_Oil)
rcf_oil_purification_sys.simulate()
monomer_purification_sys.simulate()
BT, WWT, gas_mixer = create_rcf_utilities_system()

rcf_combined_system = bst.System(
    'Combined_RCF_System',
    path=(rcf_system, rcf_oil_purification_sys, monomer_purification_sys, WWT),
    facilities=[gas_mixer, BT],
)
rcf_combined_system.simulate()


# Hydrodeoxygenation reactions

hydrodeoxygenation_rxn = bst.ParallelReaction([
    bst.Reaction('Propylguaiacol,l + 6Hydrogen,g -> 1propylcyclohexane,l + 2Water,l + Methane,g', reactant='Propylguaiacol', phases='lg',
                    X=1.0, basis='mol'),
    bst.Reaction('1Propylsyringol,l + 8Hydrogen,g -> 1propylcyclohexane,l + 3Water,l + 2Methane,g', reactant='Propylsyringol', phases='lg',
                    X=1.0, basis='mol'),
])

# Hydrogen required is 6 x moles of PG and 8 x moles of PS, but we also feed some excess which is recirculated
h2_required = (6*(F.RCF_Monomers.imol['Propylguaiacol']) + 8*(F.RCF_Monomers.imol['Propylguaiacol']))*hdo_params['h2_excess']


hdo_h2_in = bst.Stream(ID = 'HDO_H2_IN', Hydrogen = h2_required , units = 'kmol/hr', P = h2_pressure, phase = 'g') 


dodcane_required = hdo_params['solvent_req']   #m3/kg of lignin oil
dodecane_flow = F.RCF_Monomers.F_mass * dodcane_required
hdo_dodecane_in = bst.Stream(ID = 'HDO_DODECANE_IN', Dodecane = dodecane_flow, units = 'm3/hr', P = 101325, T = 300, phase = 'l')


catalyst_required = hdo_params['catalyst_req']      # kg/kg of lignin oil
catalyst_flow = F.RCF_Monomers.F_mass * catalyst_required
hdo_cat_in =  bst.Stream(ID = 'HDO_CAT_IN', Ni2PSiO2 = catalyst_flow, units = 'kg/hr', phase = 's')

# Mixes the monomers, hydrogen and solvent 
hdo_mix_1 = bst.units.Mixer(ID = 'HDO-MIX1', ins = (hdo_h2_in, F.RCF_Monomers, hdo_dodecane_in), rigorous = True)


# Compressing to the pressure required for HDO
hdo_comp_1 = bst.units.IsentropicCompressor('HDO-COMP1', ins = hdo_mix_1-0, P = hdo_params['P'], vle = True)

# Heating to the required temperature for HDO
hdo_hx_1 = bst.units.HXutility(ID = 'HDO-HX1', ins = hdo_comp_1-0, T = hdo_params['T'], rigorous= True)

# HDO reactor 
hdo_rxr_1 = HydrodeoxygenationReactor(ID = 'HDO-RXR1', ins = (hdo_hx_1-0, hdo_cat_in),
                                T = hdo_params['T'],
                                P = hdo_params['P'],
                                tau = hdo_params['tau'],
                                tau_0 = hdo_params['tau_0'],
                                free_frac = hdo_params['free_frac'],
                                V_max = hdo_params['V_max'],
                                aspect_ratio = hdo_params['aspect_ratio'],
                                reaction_1 = hydrodeoxygenation_rxn)

# Cooling the batch reactor before getting the contents out
hdo_hx_2 = bst.units.HXutility(ID = 'HDO-HX2', ins = hdo_rxr_1-0, T = 400, rigorous = True)


# Depressurizing for safety
hdO_v_1 = bst.units.IsenthalpicValve(ID = 'HDO-V1', ins = hdo_hx_2-0, P = 101325, vle = True)


# Flashing the gaseous components
hdo_flsh_1 = bst.units.Flash(ID = 'HDO-FLSH1', ins = hdO_v_1-0, T = 298, P = 101325)


# Another flash downstream to remove water before PSA
# The liquid outlet is almost pure water and has very little levels of methane, have to think about where to outlet this 
hdo_flsh_2 = bst.units.Flash(ID = 'HDO-FLSH2', ins = hdo_flsh_1-0, T = 275, P = 5e5)


# I believe 303 is a requirement for PSA but I'll need to double check
hdo_hx_3 = bst.units.HXutility(ID = 'HDO-HX3', ins=hdo_flsh_2-0, T=303, rigorous=True)


# PSA for HDO - the hdo_gases will need to be routed to BT gas feed for combustion
hdo_psa_1 = PSA(ID = 'HDO-PSA1', ins=hdo_hx_3-0, outs=('', 'hdo_gases')) 


# The bottoms of the hdo_solvent_recovery needs to be recycled
hdo_col_1 = bst.units.BinaryDistillation(ID = 'HDO-COL1', ins=hdo_flsh_1-1,
    LHK=('propylcyclohexane', 'Dodecane'),
    Lr=0.99, Hr=1 - 0.0001, P=101325,
    vessel_material='Stainless steel 316',
    k=2, partial_condenser=True,
)

# The HDO_WW stream will eventually be routed to the centralized WWT, but that will probably happen later
hdo_col_2 = bst.units.BinaryDistillation(ID = 'HDO-COL2',
    ins= hdo_col_1-0,
    outs = ('HDO_WW', 'SAF_CycloAlkane'),
    LHK=('Water', 'Propylcyclohexane'),
    y_top=0.9, x_bot=0.001, P=101325, k=2,
)
