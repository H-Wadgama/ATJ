# BioSTEAMS native cellulosic ethanol production created without BT and WWT, which were then natively added
# This script can be used as a test in the future for checking whether BT and WWT are correctly routed 
# No MSP difference between solo_ethanol_no_facilities.py and solo_ethanol.py indicating that mass balance was converged


from lignin_saf.ligsaf_settings import feed_parameters, prices
from lignin_saf.ethanol_production import create_cellulosic_ethanol_system
from biorefineries import cellulosic

from biosteam import main_flowsheet as F
import biosteam as bst


chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()

bst.settings.set_thermo(chems)

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

etoh_system = create_cellulosic_ethanol_system(ins=poplar_in)
etoh_system.simulate()

# --- Explicitly route the same streams the stock system routes ---
# Verified against cellulosic.create_cellulosic_ethanol_system (solo_ethanol.py):
#   WWT M601 <- pretreatment_wastewater + S401.outs[1] (stillage filtrate, s48)
#   BT ins[0] <- S401.outs[0] (filter cake) + WWT sludge via solids_to_BT mixer
#   BT ins[1] <- WWT biogas only (fermentation vent is atmospheric, not burned)
#   PWC ins[0] <- WWT.outs[2] (RO treated water, ~479,000 kg/hr)
#       In the stock system this is wired via M4 (a pass-through mixer from S604).
#       Here we wire directly since M2 (the placeholder mixer created by
#       create_all_facilities when WWT=False) has no inlets and is inert.
#   CT blowdown -> PWC via blowdown_recycle=True (matches stock factory default)
#   brine (WWT.outs[3]) -> unconnected, same as stock system

etoh_ww     = [F.pretreatment_wastewater, F.unit.S401.outs[1]]
etoh_solids = [F.unit.S401.outs[0]]

WWT = bst.create_conventional_wastewater_treatment_system('WWT', ins=etoh_ww)

# Wire WWT RO-treated water back to PWC — in the stock system create_all_facilities(WWT=True)
# does this automatically via M4. Here we bypass the empty placeholder M2 and connect
# directly. The WWT->PWC feedback is weak enough that no iterative convergence is needed.
F.unit.PWC.ins[0] = WWT.outs[2]

solids_to_BT = bst.Mixer('MIX_BT_solids', ins=[WWT.outs[1]] + etoh_solids)
gas_mixer    = bst.Mixer('MIX_BT_gas',    ins=[WWT.outs[0]])

BT = bst.facilities.BoilerTurbogenerator('BT', fuel_price=0.2612)
BT.ins[0] = solids_to_BT.outs[0]
BT.ins[1] = gas_mixer.outs[0]

combined_etoh_system = bst.System(
    'Combined_Ethanol_System',
    path=(etoh_system, WWT),
    facilities=[solids_to_BT, gas_mixer, BT],
)
combined_etoh_system.simulate()
