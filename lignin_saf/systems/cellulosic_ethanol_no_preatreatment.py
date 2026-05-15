# -*- coding: utf-8 -*-
"""
Cellulosic ethanol factory without dilute-acid pretreatment, for use
in the RCF integrated biorefinery.

The Carbohydrate_Pulp from RCF has already been delignified; it feeds
directly into enzymatic saccharification and fermentation, bypassing
the dilute-acid pretreatment step.

Pass ``add_denaturant=False`` when the ethanol product is routed to
catalytic upgrading (e.g. ETJ) rather than sold as fuel-grade ethanol.
``create_all_facilities`` always omits BT and WWT so the shared RCF
utilities serve the full biorefinery.
"""

import biosteam as bst
import thermosteam as tmo
from biorefineries.cellulosic.systems.fermentation import create_cellulosic_fermentation_system
from biorefineries.ethanol import create_ethanol_purification_system
from biorefineries.cellulosic import streams as s


__all__ = ('create_cellulosic_ethanol_system',)

@bst.SystemFactory(
    ID='cornstover_sys',
    ins=[dict(ID='Carbohydrate_Pulp'), s.denaturant],
    outs=[s.ethanol],
)
def create_cellulosic_ethanol_system(ins, outs, add_denaturant=True):
    pulp, denaturant = ins
    ethanol, = outs
    fermentation_sys = create_cellulosic_fermentation_system(
        ins=pulp,
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
    if not add_denaturant:
        udct['M701'].denaturant_fraction = 0.0
    ethanol, stillage, recycle_process_water = ethanol_purification_sys.outs
    recycled_water = tmo.Stream(Water=1,
                                T=47+273.15,
                                P=3.9*101325,
                                units='kg/hr')
    S401 = bst.PressureFilter('S401', (stillage, recycled_water))

    # BT (CHP) and WWT are omitted — the shared RCF utilities serve the full
    # biorefinery. blowdown_recycle=True: CT blowdown goes to PWC, not WWT.
    # Without pretreatment, WWT receives only S401.outs[1] (stillage filtrate).
    bst.create_all_facilities(
        pulp,
        WWT=False,
        CHP=False,
        HXN=False,
        blowdown_recycle=True,
        recycle_process_water_streams=[recycle_process_water],
    )
