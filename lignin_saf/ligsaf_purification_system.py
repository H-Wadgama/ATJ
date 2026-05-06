import biosteam as bst
import numpy as np
from biosteam import main_flowsheet as F

from lignin_saf.ligsaf_settings import (
    etoac_purification,
    etoac_partition_IDs,
    etoac_partition_K,
    prices,
)


def create_rcf_oil_purification_system(ins=None):
    """
    Build and return the RCF crude oil ethyl acetate LLE purification system.

    Separates the crude lignin oil (output of RCF_System FLASH118) into a
    purified RCF oil stream via liquid-liquid extraction with ethyl acetate /
    water, followed by flash evaporation to recover the solvent for recycle.

    Parameters
    ----------
    ins : bst.Stream, optional
        Crude RCF oil inlet. If None, F.RCF_Oil is taken from the main
        flowsheet — rcf_system must have been simulated first.

    Returns
    -------
    bst.System
        'RCF_Oil_Purification_System' with solvent_recycle converged.

    Notes
    -----
    Caller must configure thermodynamics before calling:
        chems = create_chemicals()
        bst.settings.set_thermo(chems)
        bst.settings.CEPCI = 541.7

    Key output streams (accessible via F.<name> after simulate()):
        Purified_RCF_Oil — bottoms of FLASH201; concentrated lignin oil
        WW_10            — aqueous raffinate from LLE200; to wastewater treatment
        WastePulp        — water/EtOAc bleed from CENT203 decanter; to wastewater treatment
    """
    crude_rcf = F.RCF_Oil if ins is None else ins

    solvent_to_crude = etoac_purification['solvent_to_crude_ratio']
    etoac_h2o_ratio  = etoac_purification['etoac_h2o_ratio']
    N_stages         = etoac_purification['N_stages']
    recycle_split    = etoac_purification['EtOAc_recycle_split']
    flash_T          = etoac_purification['oil_flash_T']
    flash_P          = etoac_purification['oil_flash_P']

    partition_data = {
        'K':                   np.array(etoac_partition_K, dtype=float),
        'IDs':                 etoac_partition_IDs,
        'raffinate_chemicals': ['Water'],
        'extract_chemicals':   ['EthylAcetate'],
    }

    # ── Streams ───────────────────────────────────────────────────────────────
    solvent_recycle = bst.Stream('solvent_recycle')
    ethyl_acetate_in = bst.Stream(
        'EthylAcetate_in',
        EthylAcetate=solvent_to_crude * crude_rcf.F_mass,
        Water=solvent_to_crude * crude_rcf.F_mass * etoac_h2o_ratio,
        units='kg/hr',
        #price=prices['EthylAcetate'],
    )

    # ── Unit operations ───────────────────────────────────────────────────────

    # Fresh EtOAc makeup + recycle; spec sets makeup to cover the deficit each iteration
    solvent_mixer = bst.units.Mixer('MIX200', ins=(ethyl_acetate_in, solvent_recycle), rigorous=False)

    @solvent_mixer.add_specification(run=True)
    def adjust_fresh_solvent_flow():
        fresh   = solvent_mixer.ins[0]
        recycle = solvent_mixer.ins[1]
        fresh.imass['EthylAcetate'] = (solvent_to_crude * crude_rcf.F_mass) - recycle.imass['EthylAcetate']
        fresh.imass['Water']        = (solvent_to_crude * crude_rcf.F_mass * etoac_h2o_ratio) - recycle.imass['Water']

    # LLE: crude oil contacts EtOAc/water countercurrently; lignin products partition into EtOAc extract
    lle_column = bst.MultiStageMixerSettlers(
        'LLE200',
        ins=(crude_rcf, solvent_mixer-0),
        outs=('', 'WW_10'),
        feed_stages=(0, -1),
        N_stages=N_stages,
        partition_data=partition_data,
        use_cache=True,
    )

    # Flash EtOAc overhead; purified oil exits as bottoms
    oil_flash = bst.units.Flash(
        'FLASH201',
        ins=lle_column-0,
        outs=('', 'Purified_RCF_Oil'),
        T=flash_T,
        P=flash_P,
    )

    # Condense EtOAc vapor for decanting
    solvent_cooler = bst.units.HXutility(
        'HX202',
        ins=oil_flash-0,
        V=0,
        rigorous=True,
    )

    # Split EtOAc from water; EtOAc-rich phase recycled, water bleed to wastewater
    solvent_decanter = bst.LiquidsSplitCentrifuge(
        'CENT203',
        ins=solvent_cooler-0,
        outs=(solvent_recycle, 'WastePulp'),
        split={'EthylAcetate': recycle_split},
    )

    # ── Assemble system ───────────────────────────────────────────────────────
    return bst.System(
        'RCF_Oil_Purification_System',
        path=(solvent_mixer, lle_column, oil_flash, solvent_cooler, solvent_decanter),
        recycle=solvent_recycle,
    )
