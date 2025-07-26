
import qsdsan as qs, biosteam as bst, thermosteam as tmo, numpy as np, pandas as pd
from qsdsan.sanunits import _heat_exchanging
bst.nbtutorial()

#from atj_saf import atj_baseline

def create_atj_system():
    from . import atj_chemicals
    from .atj_chemicals import chemicals
    from .units.catalytic_reactors import AdiabaticReactor, IsothermalReactor
    from .units.atj_pump import Pump
    from .units.atj_compressor import Compressor
    from .units.storage_tanks import EthanolStorageTank, HydrogenStorageTank, HydrocarbonProductTank
    from .units.PSA import PressureSwingAdsorption
    from .data.feed_conditions import feed_parameters
    from .data.catalytic_reaction_data import dehyd_data, olig_data, hydgn_data, prod_selectivity
    from .data.prices import price_data

    qs.set_thermo(chemicals) # assigning pure chemical thermo properties to the chemicals

    etoh_in = qs.SanStream(
        'etoh_in',
        Ethanol = 100,
        Water =  100*((1-feed_parameters['purity'])/(feed_parameters['purity'])),
        units = 'kg/hr',
        T = feed_parameters['temperature'],
        P = feed_parameters['pressure'],
        phase = feed_parameters['phase'],
        price = 0.90) 
    


    # Reactions

    #1) Gas phase dehydration of ethanol to ethylene 
    dehydration_rxn = bst.Reaction('Ethanol,g -> Water,g + Ethylene,g', reactant = 'Ethanol', 
                               X = dehyd_data['conv'], phases = 'lg',  basis = 'mol')

    
    #2) Ethylene oligomerization to olefins in gas and liquid phase
    oligomerization_rxn = bst.ParallelReaction([
    # Reaction definition                                     # Reactant                    # Conversion
    bst.Reaction('2Ethylene,g -> Butene,g',            reactant = 'Ethylene',     X = olig_data['conv']*prod_selectivity['C4H8'],    basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('1.5Ethylene,g -> Hex-1-ene,g',       reactant = 'Ethylene',     X = olig_data['conv']*prod_selectivity['C6H12'],   basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('5Ethylene,g -> Dec-1-ene,l',         reactant = 'Ethylene',     X = olig_data['conv']*prod_selectivity['C10H20'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('9Ethylene,g -> Octadec-1-ene,l',     reactant = 'Ethylene',     X = olig_data['conv']*prod_selectivity['C18H36'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True)])


    hydrogenation_rxn = bst.ParallelReaction([
    # Reaction definition                                           # Reactant                    # Conversion
    bst.Reaction('Butene,g + Hydrogen,g -> Butane,g',               reactant = 'Butene',          X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Butene,l + Hydrogen,g -> Butane,l',               reactant = 'Butene',          X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Hex-1-ene,g + Hydrogen,g -> Hexane,g',            reactant = 'Hex-1-ene',       X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Hex-1-ene,l + Hydrogen,g -> Hexane,l',            reactant = 'Hex-1-ene',       X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Dec-1-ene,l + Hydrogen,g -> Decane,l',            reactant = 'Dec-1-ene',       X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Dec-1-ene,g + Hydrogen,g -> Decane,g',            reactant = 'Dec-1-ene',       X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Octadec-1-ene,l + Hydrogen,g -> Octadecane,l',    reactant = 'Octadec-1-ene',   X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True),
    bst.Reaction('Octadec-1-ene,g + Hydrogen,g -> Octadecane,g',    reactant = 'Octadec-1-ene',   X = hydgn_data['conv'],  basis = 'mol',  phases = 'lg',  correct_atomic_balance = True)])



    # Recycle streams
    dehyd_recycle = bst.MultiStream('dehyd_recycle', phases = ('g','l'))         # Unreacted ethanol
    ethylene_recycle = bst.MultiStream('ethylene_recycle', phases = ('g','l'))   # Unreacted ethylene   
    h2_recycle= qs.SanStream(ID = 'h2_recycle', P = 3e6, phase = 'g')            # Excess hydrogen


    etoh_storage = EthanolStorageTank(ins = etoh_in)
    etoh_storage.simulate()
    
    pump_1 = Pump('PUMP1', ins = etoh_storage.outs[0], P = 1373000)    
    pump_1.simulate()
    
    furnace_1 = _heat_exchanging.HXutility('FURNACE_1', ins = pump_1.outs[0], T = 500, rigorous = True)
    furnace_1.simulate()

    mixer_1 = qs.sanunits.Mixer('MIXER_1', ins = (furnace_1.outs[0], dehyd_recycle), rigorous = True, init_with = 'MultiStream')
    mixer_1.simulate()

    furnace_2 =  _heat_exchanging.HXutility('FURNACE_2', ins = mixer_1.outs[0], T = 481 + 273.15, rigorous = True)
    furnace_2.simulate()

    
    dehyd_1 = AdiabaticReactor('DEHYD_1', ins = furnace_2.outs[0],
                         conversion = dehyd_data['conv'],
                          temperature = dehyd_data['temp'],
                          pressure = dehyd_data['pressure'],
                          WHSV = dehyd_data['whsv'],
                          catalyst_price=price_data['dehydration_catalyst'],
                             catalyst_lifetime = dehyd_data['catalyst_lifetime'],
                            reaction = dehydration_rxn)
    
    dehyd_1.simulate()

    splitter_1 = qs.sanunits.Splitter(ins = dehyd_1.outs[0], outs = ('flash_in', dehyd_recycle), split = 0.3, init_with = 'MultiStream')
    splitter_1.simulate()
    
    flash_1 = qs.sanunits.Flash('FLASH_1', ins = splitter_1.outs[0], outs = ('ETHYLENE_WATER', 'WW_1'), T= 420,  P = 1.063e6)
    flash_1.simulate()


    comp_1 = Compressor('COMP_1', ins = flash_1.outs[0], P = 2e6, vle = True, eta = 0.72, driver_efficiency = 1)
    comp_1.simulate()   

    distillation_1 = qs.sanunits.BinaryDistillation('DISTILLATION_1', ins = comp_1.outs[0], 
                                                outs = ('ethylene_water', 'WW'),
                                    LHK = ('Ethylene', 'Water'), 
                                    P = 2e+06,
                                    y_top = 0.999, x_bot = 0.001, k = 2,
                                    is_divided = True)
    distillation_1.check_LHK = False   # Does not check for volatile components that might show up in lights
    distillation_1.simulate()

    comp_2 = Compressor('COMP_2', ins = distillation_1.outs[0], P = olig_data['pressure'], vle = True, eta = 0.72, driver_efficiency = 1)
    comp_2.simulate()

    distillation_2 = qs.sanunits.BinaryDistillation('DISTILLATION_2', ins = comp_2.outs[0],
                                    LHK = ('Ethylene', 'Ethanol'),
                                    P = 3.5e+06,
                                    y_top = 0.9999, x_bot = 0.0001, k = 2,
                                    is_divided = True)
    distillation_2.simulate()

    cooler_1 = _heat_exchanging.HXutility('COOLER_1', ins = distillation_2.outs[1], outs = 'WW_2', T = 300, rigorous = True)
    cooler_1.simulate()

    splitter_2 = qs.sanunits.Splitter('SPLIT2', ins = distillation_1.outs[1], split = 0.6, init_with = 'MultiStream')
    splitter_2.simulate()

    hx_1 = _heat_exchanging.HXprocess('HX_1', ins = (distillation_2.outs[0], splitter_2.outs[0]), init_with = 'MultiStream')
    hx_1.simulate()

    cooler_2 = _heat_exchanging.HXutility('COOLER_2', ins = hx_1.outs[0], outs = 'WW_3', T = 300, rigorous = True)
    cooler_2.simulate()

    mixer_2 = qs.sanunits.Mixer(ID = 'MIXER_3', ins = (cooler_2.outs[0],ethylene_recycle), rigorous = True, init_with = 'MultiStream')
    mixer_2.simulate()

    olig_1 = IsothermalReactor('OLIG_1', ins = mixer_2.outs[0], init_with = 'MultiStream',
                              conversion = olig_data['conv'],
                             temperature = olig_data['temp'],
                             pressure = olig_data['pressure'],
                             WHSV = olig_data['whsv'],
                             catalyst_price = price_data['oligomerization_catalyst'],
                            reaction = oligomerization_rxn)
    olig_1.simulate()


    splitter_3 = qs.sanunits.Splitter('SPLIITER_3', ins = olig_1.outs[0], outs = (ethylene_recycle,'oligs'),  split = {'Ethylene':1.0}, init_with = 'MultiStream')
    splitter_3.simulate()

    h2_in = qs.SanStream(ID = 'h2_in',  P = 3e6, phase= 'g')
    mixer_3 = qs.sanunits.Mixer('mix_try', ins = (h2_in, h2_recycle), rigorous = True, init_with = 'MultiStream')
    @mixer_3.add_specification(run = True)
    def h2_flow():
        h2_flow = 3*((olig_1.outs[0].imol['Butene'] + olig_1.outs[0].imol['Hex-1-ene']
                      + olig_1.outs[0].imol['Dec-1-ene'] + olig_1.outs[0].imol['Octadec-1-ene']))
        
        h2_in.imol['Hydrogen'] = h2_flow - h2_recycle.imol['Hydrogen']
    mixer_3.simulate()

    h2_storage = HydrogenStorageTank('H2_STORAGE',ins = mixer_3.outs[0])
    h2_storage.simulate()


    mixer_4 = qs.sanunits.Mixer(ins = (h2_storage.outs[0], splitter_3.outs[1]), rigorous = True, init_with = 'MultiStream')
    mixer_4.simulate()

    hx_2 = _heat_exchanging.HXprocess('HX_2', ins = (splitter_2.outs[1], mixer_4.outs[0]), init_with = 'MultiStream')
    hx_2.simulate()

    cooler_4 = _heat_exchanging.HXutility('COOLER_4', ins = hx_2.outs[0], outs = 'WW_4', T = 300, rigorous = True)
    cooler_4.simulate()

    furnace_3 = _heat_exchanging.HXutility('FURNACE_3', ins = hx_2.outs[1], T = 350 +273.15, rigorous = True)
    furnace_3.simulate()


    hydgn_1 = AdiabaticReactor('hydgn', ins = furnace_3.outs[0], init_with = 'MultiStream',
                            conversion = hydgn_data['conv'],
                            temperature = hydgn_data['temp'],
                            pressure = hydgn_data['pressure'],
                            WHSV = hydgn_data['whsv'],
                            catalyst_price = price_data['hydrogenation_catalyst'],
                            reaction = hydrogenation_rxn)
    hydgn_1.simulate()


    cooler_5 = _heat_exchanging.HXutility('COOLER_5', ins = hydgn_1.outs[0], T = 700, rigorous = True, init_with = 'MultiStream')
    cooler_5.simulate()

    h_none = _heat_exchanging.HXutility('H_NONE4', ins = cooler_5.outs[0], T = 700)
    h_none.simulate()

    psa_hydrogen = PressureSwingAdsorption('PSA', ins = h_none.outs[0], outs = (h2_recycle, 'fuel'), split = {'Hydrogen':1},  init_with = 'MultiStream')
    psa_hydrogen.simulate()


    my_sys = qs.System('my_sys', path = (etoh_storage, pump_1, furnace_1, mixer_1, furnace_2, dehyd_1, splitter_1, flash_1, comp_1, 
                                         distillation_1, comp_2, distillation_2, cooler_1, splitter_2, hx_2, cooler_2, mixer_2,
                                         olig_1, splitter_3, mixer_3, h2_storage, mixer_4, hx_2, cooler_4, furnace_3, hydgn_1, cooler_5, 
                                         h_none, psa_hydrogen ))

    
    
    
    
    return my_sys

atj_system = create_atj_system()




#from . import atj_chemicals
#from .units import dehydration, oligomerization, atj_compressor, atj_pump
#from .data import feed_conditions, reaction_conditions, parameters, prices, olig_selectivity
'''
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

pump_1.outs[0].show()

furnace_1 = _heat_exchanging.HXutility('FURNACE_1', ins = pump_1.outs[0], T = 500, rigorous = False)
furnace_1.simulate()

mixer_1 = qs.sanunits.Mixer('MIXER_1', ins = (furnace_1.outs[0], dehyd_recycle), rigorous = False, init_with = 'MultiStream')
mixer_1.simulate()

furnace_2 =  _heat_exchanging.HXutility('FURNACE_02', ins = mixer_1.outs[0], T = 481+ 273.15, rigorous = False)
furnace_2.simulate()


dehydration_rxn = bst.Reaction('Ethanol -> Water + Ethylene', reactant = 'Ethanol', 
                               X = dehydration_parameters['dehyd_conv'], basis = 'mol')


dehyd_1 = DehydrationReactor('DEHYD_1', ins = furnace_2.outs[0],
                         conversion = dehydration_parameters['dehyd_conv'],
                          temperature = dehydration_parameters['dehyd_temp'],
                          pressure = dehydration_parameters['dehyd_pressure'],
                          WHSV = dehydration_parameters['dehyd_WHSV'],
                          catalyst_price=price_data['dehydration_catalyst'], 
                          catalyst_lifetime = dehydration_parameters['catalyst_lifetime'],
                            reaction = dehydration_rxn)
dehyd_1.simulate()

dehyd_1.outs[0]




splitter_1 = qs.sanunits.Splitter('SPLIT_1', ins = dehyd_1.outs[0], outs = ('flash_in', dehyd_recycle), split = 0.3, init_with = 'MultiStream')
splitter_1.simulate()
splitter_1.outs[0].show()


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


cooler_1 = _heat_exchanging.HXutility('COOLER_1', ins = distillation_2.outs[1], outs = 'WW_2', T = 300, rigorous = False)
cooler_1.simulate()

splitter_2 = qs.sanunits.Splitter('SPLIT_2', ins = distillation_1.outs[1], split = 0.6, init_with = 'MultiStream')
splitter_2.simulate()

hx_2 = _heat_exchanging.HXprocess('HX_2', ins = (distillation_2.outs[0], splitter_2.outs[0]), init_with = 'MultiStream')
hx_2.simulate()

cooler_2 = _heat_exchanging.HXutility('COOLER_2', ins = hx_2.outs[1], outs = 'WW_3', T = 300, rigorous = False)
cooler_2.simulate()

cooler_3 = _heat_exchanging.HXutility('COOLER_3', ins = hx_2.outs[0], T = 393.15, rigorous = False)
cooler_3.simulate()

ethylene_recycle = qs.SanStream('ethylene_recycle')

mixer_3 = qs.sanunits.Mixer(ID = 'MIXER_3', ins = (cooler_3.outs[0],ethylene_recycle), rigorous = False, init_with = 'MultiStream')
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


olig_1.outs[0].show()
'''