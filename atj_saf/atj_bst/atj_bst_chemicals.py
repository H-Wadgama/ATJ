

import thermosteam as tmo, biorefineries as bf
from biorefineries import cellulosic


def create_chemicals():


    atj_chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()    
    ethylene = tmo.Chemical('Ethylene')
    butene = tmo.Chemical('Butene')          # Butene and hexene are representative surrogates for renewable naphtha
    hexene = tmo.Chemical('Hex-1-ene')  
    decene = tmo.Chemical('Dec-1-ene')       # Decene is representative for SAF
    octene = tmo.Chemical('Octadec-1-ene')   # Octadecene is representative for renewable diesel
    butane = tmo.Chemical('Butane')
    hexane = tmo.Chemical('Hexane')
    octane = tmo.Chemical('Octane')
    decane = tmo.Chemical('Decane')
    octadecane = tmo.Chemical('Octadecane')    
    
    
    hydrogen = tmo.Chemical('Hydrogen')
    syndol = tmo.Chemical('Syndol', search_db = False, default = True, phase = 's')
    ni_sial = tmo.Chemical('Nickel_SiAl', search_db = False, default = True, phase = 's')
    co_mo = tmo.Chemical('CobaltMolybdenum', search_db = False, default = True, phase = 's')
    syndol.synonyms = ('Dehydration-Catalyst',) 
    ni_sial.synonyms = ('Oligomerization_Catalyst')
    co_mo.synonyms = ('Hydrogenation_Catalyst')



   
    # 4) Extend the base collection
    atj_chems.extend([ethylene, butene, hexene, decene, octene, butane, hexane,
                      octane, decane, octadecane, hydrogen, syndol,
                        ni_sial, co_mo, ])

    atj_chems.compile()  # Compiling all the chemicals to one string
    return atj_chems


