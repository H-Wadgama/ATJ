import qsdsan as qs, biosteam as bst, thermosteam as tmo, numpy as np, pandas as pd
from qsdsan.sanunits import _heat_exchanging
bst.nbtutorial()

from atj_saf import atj_baseline
#import atj_chemicals

from atj_chemicals import *
from data.feed_conditions import *
from units.etoh_storage_tank import *
from units.dehydration import *
from units.atj_pump import *
from data.reaction_conditions import *
from data.prices import *


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


# Recycle streams
dehyd_recycle = qs.SanStream(phase = 'g')


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

print(dehyd_1.outs[0].show())

'''
chem = qs.Chemicals(['Water', 'Ethanol'], cache = True)
qs.set_thermo(chem)


stream = qs.SanStream(Water = 100, T = 300)
hx_1 = qs.sanunits._heat_exchanging.HXutility(ins = stream, T = 400, rigorous = True)
hx_1.simulate()

hx_1.outs[0].show(composition = True)

'''
