from biorefineries import cellulosic
import biosteam as bst
from biosteam import main_flowsheet as F


def create_cellulosic_ethanol_system_no_facilities(ins):
    """
    Create and simulate the cellulosic ethanol system, then strip its
    internally-created BT and WWT from the flowsheet so the shared RCF
    utilities can serve both subsystems without naming conflicts.

    ``create_cellulosic_ethanol_system`` calls ``bst.create_all_facilities``
    internally, which hardcodes unit IDs (M601, WWTC, R601-S604 for WWT;
    auto-IDs for slurry_mixer, gas_mixer, BT for CHP). Those IDs conflict
    with ``create_rcf_utilities_system``, which also creates M601, BT, etc.
    This function must therefore be called BEFORE ``create_rcf_utilities_system``.

    Parameters
    ----------
    ins : bst.Stream
        Feed stream — pass ``F.Carbohydrate_Pulp``.

    Returns
    -------
    ethanol_system : bst.System
        Ethanol process only (U101, pretreatment, fermentation, purification,
        S401); no BT or WWT in its facilities.
    ww_streams : list[bst.Stream]
        Wastewater streams that were feeding the ethanol WWT (M601).
        Route these to the shared RCF WWT after calling
        ``create_rcf_utilities_system``.
    combustible_solids : list[bst.Stream]
        Solid combustible streams (e.g. filter cake from S401) that were
        feeding the ethanol BT's slurry slot.
    combustible_gases : list[bst.Stream]
        Gas combustible streams that were feeding the ethanol BT's gas slot.
    """
    ethanol_system = cellulosic.create_cellulosic_ethanol_system(ins=ins)
    ethanol_system.simulate()

    etoh_slurry_mixer = F.unit.slurry_mixer
    etoh_gas_mixer    = F.unit.gas_mixer
    etoh_M601         = F.unit.M601

    combustible_solids = [s for s in etoh_slurry_mixer.ins if s.source is not None]
    combustible_gases  = [s for s in etoh_gas_mixer.ins  if s.source is not None]
    ww_streams         = [s for s in etoh_M601.ins       if s.source is not None]

    # Patch S603 before emptying M601 so that when ethanol_system re-runs
    # inside the combined simulation it gets zero feed and S603 doesn't raise
    # InfeasibleRegion ("not enough water to meet moisture-content target").
    for unit in etoh_M601.system.units:
        if hasattr(unit, 'strict_moisture_content'):
            unit.strict_moisture_content = False

    # Disconnect streams so the removed utility units receive empty inputs on
    # re-simulate and do not double-route streams to the shared utilities.
    etoh_slurry_mixer.ins.clear()
    etoh_gas_mixer.ins.clear()
    etoh_M601.ins.clear()

    etoh_BT = next(u for u in ethanol_system.facilities
                   if isinstance(u, bst.facilities.BoilerTurbogenerator))
    F.remove_unit_and_associated_streams(etoh_slurry_mixer.ID)
    F.remove_unit_and_associated_streams(etoh_gas_mixer.ID)
    F.remove_unit_and_associated_streams(etoh_BT.ID)

    for uid in ('M601', 'WWTC', 'R601', 'M602', 'R602',
                'S601', 'S602', 'M603', 'S603', 'M604', 'S604'):
        F.remove_unit_and_associated_streams(uid)

    return ethanol_system, ww_streams, combustible_solids, combustible_gases


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
        ins[0] — WWT.outs[1] (dewatered sludge, solid/liquid combustion slot)
        ins[1] — gas_mixer outlet (PSA purge + WWT biogas combined)
        ins[2-6] — makeup water, natural gas, lime, boiler chems, air (auto-set)
    WWT : bst.System
        Conventional anaerobic/aerobic wastewater treatment system
        (Humbird 2011 configuration) fed by F.WW_10, F.WastePulp, and F.RCF_WW.
        The internal SludgeCentrifuge runs with strict_moisture_content=False
        because the Humbird 79% moisture target was calibrated for cellulosic-
        ethanol streams; RCF wastewater has a different organic profile.
    gas_mixer : bst.Mixer
        Combines F.Purge_Light_Gases (PSA purge) and WWT.outs[0] (biogas).
        Must be listed before BT in the combined system's facilities list.
    """
    BT = bst.facilities.BoilerTurbogenerator('BT', fuel_price=0.2612)

    WWT = bst.create_conventional_wastewater_treatment_system(
        'WWT',
        ins=(F.WW_10, F.WastePulp, F.RCF_WW, F.WW_11, F.WW_12),
    )
    # The Humbird WWT sludge centrifuge targets 79% moisture calibrated for
    # cellulosic-ethanol-scale organic loadings. RCF wastewater has a different
    # organic profile (Acetate is in non_digestables; G_Dimer/S_Oligomer/G_Oligomer
    # have no formula so atoms={} and are skipped by get_digestable_organic_chemicals).
    # Relax to a soft constraint so the simulation continues without halting.
    for unit in WWT.units:
        if hasattr(unit, 'strict_moisture_content'):
            unit.strict_moisture_content = False

    # Route WWT outputs to BT.
    # outs[0] = biogas (CH4/CO2), outs[1] = dewatered sludge.
    # A mixer combines biogas with PSA purge gas before the gas combustion slot.
    # gas_mixer must precede BT in facilities so its outlet is populated first.
    BT.ins[0] = WWT.outs[1]
    gas_mixer = bst.Mixer('MIX_BT_gas', ins=(F.Purge_Light_Gases, WWT.outs[0]))
    BT.ins[1] = gas_mixer.outs[0]

    return BT, WWT, gas_mixer
