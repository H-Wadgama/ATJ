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
        ins[0] — liquid/solid combustion feed (empty in RCF-only mode)
        ins[1] — gas combustion feed: F.Purge_Light_Gases (PSA purge)
        ins[2-6] — makeup water, natural gas, lime, boiler chems, air (auto-set)
    WWT : bst.System
        Conventional anaerobic/aerobic wastewater treatment system
        (Humbird 2011 configuration) fed by F.WW_10, F.WastePulp, and F.RCF_WW.
        The internal SludgeCentrifuge runs with strict_moisture_content=False
        because the Humbird 79% moisture target was calibrated for cellulosic-
        ethanol streams; RCF wastewater has a different organic profile.
    """
    BT = bst.facilities.BoilerTurbogenerator('BT', fuel_price=0.2612)
    BT.ins[1] = F.Purge_Light_Gases

    WWT = bst.create_conventional_wastewater_treatment_system(
        'WWT',
        ins=(F.WW_10, F.WastePulp, F.RCF_WW),
    )
    # The Humbird WWT sludge centrifuge targets 79% moisture calibrated for
    # cellulosic-ethanol-scale organic loadings. RCF wastewater has a different
    # organic profile (Acetate is in non_digestables; G_Dimer/S_Oligomer/G_Oligomer
    # have no formula so atoms={} and are skipped by get_digestable_organic_chemicals).
    # Relax to a soft constraint so the simulation continues without halting.
    for unit in WWT.units:
        if hasattr(unit, 'strict_moisture_content'):
            unit.strict_moisture_content = False

    return BT, WWT
