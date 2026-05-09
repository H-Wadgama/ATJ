# -*- coding: utf-8 -*-
"""
.. autofunction:: biorefineries.cellulosic.systems.cellulosic_ethanol.create_cellulosic_ethanol_system

"""

import biosteam as bst
import thermosteam as tmo
from biorefineries.cellulosic.systems.pretreatment import create_dilute_acid_pretreatment_system
from biorefineries.cellulosic.systems.fermentation import create_cellulosic_fermentation_system
from biorefineries.ethanol import create_ethanol_purification_system
from biorefineries.cellulosic import streams as s
from biorefineries.cellulosic import units


__all__ = ('create_cellulosic_ethanol_system',)

@bst.SystemFactory(
    ID='cornstover_sys',
    ins=[*create_dilute_acid_pretreatment_system.ins,
          s.denaturant],
    outs=[s.ethanol],
)
def create_cellulosic_ethanol_system(ins, outs):
    feedstock, sulfuric_acid, ammonia, denaturant = ins
    ethanol, = outs
    U101 = units.FeedStockHandling('U101', feedstock)
    U101.cost_items['System'].cost = 0.
    pretreatment_sys = create_dilute_acid_pretreatment_system(
        ins=[U101-0, sulfuric_acid, ammonia],
        mockup=True
    )
    fermentation_sys = create_cellulosic_fermentation_system(
        ins=pretreatment_sys-0,
        mockup=True,
    )
    ethanol_purification_sys, udct = create_ethanol_purification_system(
        ins=[fermentation_sys-1, denaturant],
        outs=[ethanol],
        udct=True,
        IDs={'Beer pump': 'P401',
             'Beer column heat exchange': 'H401',
             'Beer column': 'D402',
             'Beer column bottoms product pump': 'P402',
             'Distillation': 'D403',
             'Distillation bottoms product pump': 'P403',
             'Ethanol-denaturant mixer': 'M701',
             'Recycle mixer': 'M402',
             'Heat exchanger to superheat vapor to molecular sieves': 'H402',
             'Molecular sieves': 'U401',
             'Ethanol condenser': 'H403',
             'Ethanol day tank': 'T701',
             'Ethanol day tank pump': 'P701',
             'Denaturant storage': 'T702',
             'Denaturant pump': 'P702',
             'Product tank': 'T703'},
        mockup=True,
    )
    udct['H401'].dT = 10
    udct['D402'].k = 1.4
    udct['D403'].k = 1.4
    ethanol, stillage, recycle_process_water = ethanol_purification_sys.outs
    recycled_water = tmo.Stream(Water=1,
                                T=47+273.15,
                                P=3.9*101325,
                                units='kg/hr')
    S401 = bst.PressureFilter('S401', (stillage, recycled_water))

    # BT (CHP) and WWT are omitted — the shared RCF utilities in
    # ligsaf_utilities_system.py serve the entire integrated biorefinery.
    # blowdown_recycle=True routes CT blowdown to PWC instead of WWT.
    bst.create_all_facilities(
        feedstock,
        WWT=False,
        CHP=False,
        HXN=False,
        blowdown_recycle=True,
        recycle_process_water_streams=[recycle_process_water],
    )
