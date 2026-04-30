import biosteam as bst
from biosteam import main_flowsheet as F


def create_rcf_utilities_system():
    """
    Create the BoilerTurbogenerator and conventional wastewater treatment
    system for the integrated RCF process.

    Call after simulating `rcf_system` and `rcf_oil_purification_sys` so
    that the required streams are populated on the main flowsheet:
      - F.Purge_Light_Gases  (PSA purge gas, from rcf_system)
      - F.WW_10              (LLE aqueous raffinate, from rcf_oil_purification_sys)
      - F.WastePulp          (decanter water bleed, from rcf_oil_purification_sys)
      - F.RCF_WW             (combined RCF wastewater, from rcf_system)

    Returns
    -------
    BT : bst.facilities.BoilerTurbogenerator
        ins[0] — liquid/solid combustion feed (empty; no solid waste in RCF-only mode)
        ins[1] — gas combustion feed (F.Purge_Light_Gases)
        ins[2-6] — makeup water, natural gas, lime, boiler chems, air (auto-set)
    WWT : bst.System
        Conventional anaerobic/aerobic wastewater treatment system
        (Humbird 2011 configuration) fed by WW_10, WastePulp, and RCF_WW.
    """
    BT = bst.facilities.BoilerTurbogenerator('BT', fuel_price=0.2612)
    BT.ins[1] = F.Purge_Light_Gases

    WWT = bst.create_conventional_wastewater_treatment_system(
        'WWT',
        ins=(F.WW_10, F.WastePulp, F.RCF_WW),
    )

    return BT, WWT
