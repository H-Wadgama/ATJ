    
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
from lignin_saf.ligsaf_units import HydrodeoxygenationReactor




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
rcf_combined_system.show()



# Hydrodeoxygenation reactions

hydrodeoxygenation_rxn = bst.ParallelReaction([
    bst.Reaction('Propylguaiacol,l + 6Hydrogen,g -> 1propylcyclohexane,l + 2Water,l + Methane,g', reactant='Propylguaiacol', phases='lg',
                    X=1.0, basis='mol'),
    bst.Reaction('1Propylsyringol,l + 8Hydrogen,g -> 1propylcyclohexane,l + 3Water,l + 2Methane,g', reactant='Propylsyringol', phases='lg',
                    X=1.0, basis='mol'),
])

h2_in = bst.Stream(ID = 'Hydrogen_In', Hydrogen = 300 , units = 'kmol/hr', P = h2_pressure, phase = 'g')


dodcane_required = hdo_params['solvent_req']   #m3/kg of lignin oil
dodecane_flow = F.RCF_Monomers.F_mass * dodcane_required
solvent_stream = bst.Stream(ID = 'Dodecane_In', Dodecane = dodecane_flow, units = 'm3/hr', P = 101325, T = 300, phase = 'l')


catalyst_required = hdo_params['catalyst_req']      # kg/kg of lignin oil
catalyst_flow = F.RCF_Monomers.F_mass * catalyst_required
catalyst_stream =  bst.Stream(ID = 'HDO_Catalyst_In', Ni2PSiO2 = catalyst_flow, units = 'kg/hr', phase = 's')


mixer = bst.units.Mixer(ins = (h2_in, F.RCF_Monomers, solvent_stream), rigorous = True)
mixer.simulate()


compressor = bst.units.IsentropicCompressor(ins = mixer-0, P = hdo_params['P'], vle = True)
compressor.simulate()

heater = bst.units.HXutility(ins = compressor-0, T = hdo_params['T'], rigorous= True)
heater.simulate()


HDO = HydrodeoxygenationReactor(ins = (compressor-0, catalyst_stream),
                                T = hdo_params['T'],
                                P = hdo_params['P'],
                                tau = hdo_params['tau'],
                                tau_0 = hdo_params['tau_0'],
                                free_frac = hdo_params['free_frac'],
                                V_max = hdo_params['V_max'],
                                aspect_ratio = hdo_params['aspect_ratio'],
                                reaction_1 = hydrodeoxygenation_rxn)
HDO.simulate()

