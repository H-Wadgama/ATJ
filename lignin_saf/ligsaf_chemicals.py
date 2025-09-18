import thermosteam as tmo, biorefineries
from biorefineries import cellulosic


def create_chemicals():


    # copying cellulosic ethanol chemicals 
    ligsaf_chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()

    # Adding pre-existing chemicals
    methanol = tmo.Chemical('Methanol')
    hydrogen = tmo.Chemical('Hydrogen')
    methane = tmo.Chemical('Methane')
    activated_carbon = tmo.Chemical('ActivatedCarbon', search_db=False, default=True, phase='s')

    
    # Custom chemical properties estimated using NIST ThermoDataEngine (TDE) from Aspen Plus V14
    # Only propylguaiacol was native to Aspen, every other component was user defined
    # All six of these user defined components are the same as chosen by Bartling et al Fig S8
    # Constant properties like normal boiling point, critical temp, critical pressure were added
    # Custom models for heat capacity, density as functions of temperatures were NOT included
   
    propylguaiacol = tmo.Chemical(  # S-Lignin Monomer 
        'Propylguaiacol',
        default = True,      # Defaults all other properties 
        search_db=False,     # Since not present in database, do not search
        formula='C10H14O2',  # Chemical formulae
        phase='l',           # phase at rtp
        omega = 0.6411,      # accentric factor
        Tb = 541.7,          # [K]  normal boiling point
        # Tc = 749,            # [K]  critical temperature
        # Pc = 2.9e6,          # [Pa] critical pressure
        Hvap = 7.78e4,       # [J/mol] enthalpy of vaporization at 298 K
        rho = 1056.3,        # [kg/m3] density at rtp

    )
    propylguaiacol.synonyms = ('4-Propylguaiacol',) # Synonyms that can be used to refer to it

    
    propylsyringol = tmo.Chemical(   # G-Lignin Monomer 
        'Propylsyringol',
        default = True,
        search_db=False,
        formula='C11H16O3',
        phase='l',
        omega = 0.87334, 
        Tb = 617.3,      
        #Tc = 819,        
        # Pc = 2565348.3,   
        Hvap = 1.07e5,    
        rho  = 1274.3    
    )
    propylsyringol.synonyms = ('4-Propylsyringol',)

    syringaresinol = tmo.Chemical(  # S-Lignin Dimer 
        'Syringaresinol',
        default = True,
        search_db = False,
        formula = 'C22H26O8',
        phase = 'l',
        omega = 1.4608,
        Tb = 796.7,
        # Tc = 979,
        # Pc = 1.83e6,
        Hvap = 1.99e5,
        rho = 1596.5
    )

    g_dimer = tmo.Chemical(   # Couldn't find a chemical name so going with g_dimer
        'G_Dimer',
        default = True,
        search_db = False,
        MW = 362.42,
        phase = 'l',
        omega = 1.3966,
        Tb = 812.6,
        # Tc = 992,
        # Pc = 1.54e6,
        Hvap = 1.97e5,
        rho = 1497.3
    )

    s_oligomer = tmo.Chemical(
        'S_Oligomer',
        default = True,
        search_db = False,
        MW = 628.67,
        phase = 'l',
        omega = 0.78742,
        Tb = 921.4,
        # Tc = 1128,
        # Pc = 8.27e5
    )  

    g_oligomer = tmo.Chemical(    # Found little to no properties for G_Oligomer
        'G_Oligomer',
        default = True,
        search_db = False,
        MW = 540.65,
        phase = 'l'
    )


    # 4) Extend the base collection
    ligsaf_chems.extend([methanol, hydrogen, methane, activated_carbon, propylguaiacol, propylsyringol,syringaresinol,g_dimer,
                  s_oligomer, g_oligomer])

    ligsaf_chems.compile()  # Compiling all the chemicals to one string
    return ligsaf_chems