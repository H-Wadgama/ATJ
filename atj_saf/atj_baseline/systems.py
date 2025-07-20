import qsdsan as qs, biosteam as bst, thermosteam as tmo, numpy as np, pandas as pd
from qsdsan.sanunits import _heat_exchanging
bst.nbtutorial()

from atj_saf import atj_baseline
#import atj_chemicals

from atj_chemicals import *
from data.feed_conditions import *
from units.etoh_storage_tank import *
from units.dehydration import *
from units.atj_compressor import *
from units.oligomerization import *
from units.atj_pump import *
from data.reaction_conditions import *
from data.parameters import *
from data.prices import *
from data.olig_selectivity import *


qs.set_thermo(chemicals) # assigning pure chemical thermo properties to the chemicals

etoh_in = qs.SanStream(
    'etoh_in',
    Ethanol = 100,
    Water =  100*((1-feed_parameters['purity'])/(feed_parameters['purity'])),
    units = 'kg/hr',
    T = feed_parameters['temperature'],
    P = feed_parameters['pressure'],
    phase = feed_parameters['phase'],
    price = 0.90) # 2.75/gal

#etoh_in.show()

# Recycle streams
dehyd_recycle = qs.SanStream(phase = 'g')

#dehyd_recycle.show()

etoh_storage = EthanolStorageTank(ins = etoh_in)
etoh_storage.simulate()

pump_1 = Pump('PUMP1', ins = etoh_storage.outs[0], P = 1373000)    # Pressure from the patent
pump_1.simulate()

furnace_1 = _heat_exchanging.HXutility('FURNACE_1', ins = pump_1.outs[0], T = 500, rigorous = True)
furnace_1.simulate()

mixer_1 = qs.sanunits.Mixer('MIXER_1', ins = (furnace_1.outs[0], dehyd_recycle), rigorous = True, init_with = 'MultiStream')
mixer_1.simulate()

furnace_2 =  _heat_exchanging.HXutility('FURNACE_01', ins = mixer_1.outs[0], T = 481+ 273.15, rigorous = True)
furnace_2.simulate()

dehydration_rxn = bst.Reaction('Ethanol -> Water + Ethylene', reactant = 'Ethanol', 
                               X = dehydration_parameters['dehyd_conv'], basis = 'mol')


dehyd_1 = DehydrationReactor('DEHYD_1', ins = furnace_2.outs[0],
                         conversion = dehydration_parameters['dehyd_conv'],
                          temperature = dehydration_parameters['dehyd_temp'],
                          pressure = dehydration_parameters['dehyd_pressure'],
                          WHSV = dehydration_parameters['dehyd_WHSV'],
                          catalyst_price=price_data['dehydration_catalyst'], 
                          catalyst_lifetime = dehydration_parameters['catalyst_lfetime'],
                            reaction = dehydration_rxn)
dehyd_1.simulate()

splitter_1 = qs.sanunits.Splitter('SPLIT_1', ins = dehyd_1.outs[0], outs = ('flash_in', dehyd_recycle), split = 0.3, init_with = 'MultiStream')
splitter_1.simulate()

flash_1 = qs.sanunits.Flash('FLASH_1', ins = splitter_1.outs[0], outs = ('ETHYLENE_WATER', 'WW_1'), T= 420,  P = 1.063e6)
flash_1.simulate()

comp_1 = Compressor('COMP_1', ins = flash_1.outs[0], P = 2e6, vle = True, eta = 0.72, driver_efficiency = comp_driver_efficiency)
comp_1.simulate()

distillation_1 = qs.sanunits.BinaryDistillation('DISTILLATION_1', ins = comp_1.outs[0], 
                                                outs = ('ethylene_water', 'WW'),
                                    LHK = ('Ethylene', 'Water'), 
                                    P = 2e+06,
                                    y_top = 0.999, x_bot = 0.001, k = 2,
                                    is_divided = True)
distillation_1.check_LHK = False
distillation_1.simulate()

comp_2 = Compressor('COMP_2', ins = distillation_1.outs[0], P = 3.5e6, vle = True, eta = 0.72, driver_efficiency = comp_driver_efficiency)
comp_2.simulate()

distillation_2 = qs.sanunits.BinaryDistillation('DISTILLATION_2', ins = comp_2.outs[0],
                                    LHK = ('Ethylene', 'Ethanol'),
                                    P = 3.5e+06,
                                    y_top = 0.9999, x_bot = 0.0001, k = 2,
                                    is_divided = True)
distillation_2.simulate()


cooler_1 = _heat_exchanging.HXutility('COOLER_1', ins = distillation_2.outs[1], outs = 'WW_2', T = 300, rigorous = True)
cooler_1.simulate()

splitter_2 = qs.sanunits.Splitter('SPLIT_2', ins = distillation_1.outs[1], split = 0.6, init_with = 'MultiStream')
splitter_2.simulate()

hx_2 = _heat_exchanging.HXprocess('HX_2', ins = (distillation_2.outs[0], splitter_2.outs[0]), init_with = 'MultiStream')
hx_2.simulate()

cooler_2 = _heat_exchanging.HXutility('COOLER_2', ins = hx_2.outs[1], outs = 'WW_3', T = 300, rigorous = True)
cooler_2.simulate()

cooler_3 = _heat_exchanging.HXutility('COOLER_3', ins = hx_2.outs[0], T = 393.15, rigorous = True)
cooler_3.simulate()

ethylene_recycle = qs.SanStream('ethylene_recycle')

mixer_3 = qs.sanunits.Mixer(ID = 'MIXER_3', ins = (cooler_3.outs[0],ethylene_recycle), rigorous = True, init_with = 'MultiStream')
mixer_3.simulate()

oligomerization_rxn = bst.ParallelReaction([
    # Reaction definition                                     # Reactant                    # Conversion
    bst.Reaction('2Ethylene -> Butene',             reactant = 'Ethylene',        X = 0.993*biofuel_composition['C4H8'], basis = 'mol', correct_atomic_balance = True),
    bst.Reaction('1.5Ethylene -> Hex-1-ene',            reactant = 'Ethylene',       X = 0.993*biofuel_composition['C6H12'], basis = 'mol', correct_atomic_balance = True),
    bst.Reaction('5Ethylene -> Dec-1-ene',            reactant = 'Ethylene',       X = 0.993*biofuel_composition['C10H20'], basis = 'mol', correct_atomic_balance = True),
    bst.Reaction('9Ethylene -> Octadec-1-ene',            reactant = 'Ethylene',       X = 0.993*biofuel_composition['C18H36'], basis = 'mol', correct_atomic_balance = True)])

olig_1 = OligomerizationReactor('OLIG_1', ins = mixer_3.outs[0], init_with = 'MultiStream',
                              conversion = oligomerization_parameters['olig_conv'], 
                             temperature = oligomerization_parameters['olig_temp'],
                             pressure = oligomerization_parameters['olig_pressure'],
                             WHSV = oligomerization_parameters['olig_WHSV'],
                             catalyst_price = price_data['oligomerization_catalyst'],
                            reaction = oligomerization_rxn)

olig_1.simulate()

olig_1.results()