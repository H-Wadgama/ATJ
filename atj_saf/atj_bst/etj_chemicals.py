
import thermosteam as tmo
from biorefineries import cellulosic


def create_chemicals():
    
    """
    Create and return the complete chemical set for an ETJ biorefinery,
    extending the base cellulosic ethanol chemicals with olefins, paraffins,
    catalysts, and other required chemicals.

    References
    ----------
    [1] J. H. Miller, et al. 2023. NREL. https://docs.nrel.gov/docs/fy23osti/87121.pdf
    [2] D. Kim, et al. 2017. Combust. Flame. 179, 86-94. https://doi.org/10.1016/j.combustflame.2017.01.025
    [3] M. Zhang, Y. Yu. Ind. Eng. Chem. Res. 2013, 52, 9505-9514. https://doi.org/10.1021/ie401157c
    [4] J. Heveling, et al. Appl. Catal. A 1998, 173, 1-9. https://doi.org/10.1016/S0926-860X(98)00147-1
    [5] Tao, Ling, et al. Green Chem. 2017, 19, 1082-1101. https://doi.org/10.1039/C6GC02800D
    
    """
    # --- Base chemical set ---
    etj_chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()    

     # --- Ethanol-to-jet olefin intermediates ---
    ethylene = tmo.Chemical('Ethylene')
    butene = tmo.Chemical('Butene')          
    hexene = tmo.Chemical('Hex-1-ene')  
    decene = tmo.Chemical('Dec-1-ene')       
    octene = tmo.Chemical('Octadec-1-ene') 

    # --- Paraffin surrogates for fuel products ---
    butane = tmo.Chemical('Butane')          # Butane represents renewable naphtha [1]
    hexane = tmo.Chemical('Hexane')          # Hexane represents renewable naphtha as well [1]
    #octane = tmo.Chemical('Octane')         # Removed: Already present as 'Denaturant' in the base chemical set
    decane = tmo.Chemical('Decane')          # Decane represents SAF [1],[2]
    octadecane = tmo.Chemical('Octadecane')  # Octadecane represents renewable diesel

    # Other chemicals 
    hydrogen = tmo.Chemical('Hydrogen')
    coal = tmo.Chemical('Coal', search_db = False, default = True, phase = 's')

    # --- Catalysts ---
    syndol = tmo.Chemical('Syndol', search_db = False, default = True, phase = 's')             # Dehydration catalyst [3]
    ni_sial = tmo.Chemical('Nickel_SiAl', search_db = False, default = True, phase = 's')       # Oligomerization catalyst [4]
    co_mo = tmo.Chemical('CobaltMolybdenum', search_db = False, default = True, phase = 's')    # Hydrogenation catalyst [5]
    
    syndol.synonyms = ('Dehydration-Catalyst')  
    ni_sial.synonyms = ('Oligomerization_Catalyst')
    co_mo.synonyms = ('Hydrogenation_Catalyst')



    # --- Extend base set, skipping any chemicals already present ---    
    new_chemicals = [ethylene, butene, hexene, decene, octene, butane, hexane,
                 decane, octadecane, hydrogen, syndol, ni_sial, co_mo, coal]
    existing_ids = {c.ID for c in etj_chems}
    etj_chems.extend([c for c in new_chemicals if c.ID not in existing_ids])
    etj_chems.compile()  # Finalizing the chemical set
    
    return etj_chems


