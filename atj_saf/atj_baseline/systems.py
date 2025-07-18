import qsdsan as qs, biosteam as bst, thermosteam as tmo, numpy as np, pandas as pd
from qsdsan.sanunits import _heat_exchanging

from atj_saf import atj_baseline
#import atj_chemicals

from atj_chemicals import *

qs.set_thermo(chemicals) # assigning pure chemical thermo properties to the chemicals

etoh_in = qs.SanStream(
    'etoh_in',
    Ethanol = 100,
    Water =  100*((1-0.995)/(0.995)),
    units = 'kg/hr',
    T = 323.15,
    P = 101325,
    phase = 'l',
    price = 0.90) # 2.75/gal

etoh_in.show(composition = True)

'''
chem = qs.Chemicals(['Water', 'Ethanol'], cache = True)
qs.set_thermo(chem)


stream = qs.SanStream(Water = 100, T = 300)
hx_1 = qs.sanunits._heat_exchanging.HXutility(ins = stream, T = 400, rigorous = True)
hx_1.simulate()

hx_1.outs[0].show(composition = True)

'''