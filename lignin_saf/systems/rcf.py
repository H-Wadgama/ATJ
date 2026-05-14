import biosteam as bst
from lignin_saf.ligsaf_units import SolvolysisReactor, HydrogenolysisReactor, PSA, CatalystMixer
from lignin_saf.ligsaf_chemicals import create_chemicals
from lignin_saf.ligsaf_settings import (
    rcf_oil_yield, prices, feed_parameters, rcf_conditions,
    solvolysis_parameters, meoh_h2o, h2_biomass_ratio, RCF_catalyst,
    poplar_density, free_frac,
    V_max_limit, condensation_extent, h2_pressure
)


def create_rcf_system(ins=None):
    """
    Build and return the RCF loop as a bst.System.

    Parameters
    ----------
    ins : bst.Stream, optional
        Poplar feedstock stream. If None, a default stream is created
        from feed_parameters in ligsaf_settings.py.

    Returns
    -------
    bst.System
        'RCF_System' with meoh_recycle and hydrogen_recycle converged.

    Notes
    -----
    Caller is responsible for setting up thermodynamics before calling:
        chems = create_chemicals()
        bst.settings.set_thermo(chems)
        bst.settings.CEPCI = 541.7
    """
    chems = bst.settings.chemicals

    # Poplar pseudocomponent group (Bartling et al Table S1)
    # Re-defining is safe — thermosteam silently overwrites existing groups
    chems.define_group(
        name='Poplar',
        IDs=['Glucan', 'Xylan', 'Arabinan', 'Mannan', 'Galactan',
             'Sucrose', 'Lignin', 'Acetate', 'Extract', 'Ash'],
        composition=[0.464, 0.134, 0.002, 0.037, 0.014,
                     0.001, 0.285, 0.035, 0.016, 0.012],
        wt=True
    )

    # ── Feedstock ─────────────────────────────────────────────────────────────
    if ins is None:
        ins = bst.Stream('Poplar_In',
                         Poplar=feed_parameters['flow'] * 1e3,
                         Water=feed_parameters['moisture'] * feed_parameters['flow'] * 1e3,
                         phase='l', units='kg/d', price=prices['Feedstock'])

    # ── Recycle streams ───────────────────────────────────────────────────────
    meoh_recycle = bst.MultiStream('Meoh_recycle', phases=('s', 'l', 'g'))
    hydrogen_recycle = bst.Stream('hydrogen_recycle', P=3e6, phase='g')

    # ── Co-feeds ──────────────────────────────────────────────────────────────
    # Methanol and water split into separate streams so price applies only to methanol
    meoh_in = bst.Stream('Meoh_in', Methanol=0.0, phase='l', units='kg/hr', price=prices['Methanol'])
    water_in_meoh = bst.Stream('Water_in_meoh', Water=0.0, phase='l', units='kg/hr')

    hydrogen_in = bst.Stream('Hydrogen_In',
                             Hydrogen=h2_biomass_ratio * 2e6,
                             units='kg/day',
                             T=80 + 273.15,   # 80°C PEM electrolyzer outlet
                             P=h2_pressure,           # 30 bar PEM electrolyzer outlet
                             phase='g',
                             price = prices['Hydrogen'])

    # ── Unit operations ───────────────────────────────────────────────────────

    # MeOH mixer: adjusts fresh feed to make up for what the recycle doesn't supply
    meoh_h2o_mix = bst.units.Mixer('MIX100', ins=(meoh_in, water_in_meoh, meoh_recycle), rigorous=True)

    @meoh_h2o_mix.add_specification(run=True)
    def meoh_water_flow():
        meoh_fresh     = meoh_h2o_mix.ins[0]
        water_fresh    = meoh_h2o_mix.ins[1]
        recycle_solvent = meoh_h2o_mix.ins[2]
        total_vol_hr = solvolysis_reactor.compute_Q_total()  # m³/hr — derived from bed geometry
        meoh_flow_mol = (
            total_vol_hr * meoh_h2o / (meoh_h2o + 1)
            * chems['Methanol'].rho(phase='l', T=rcf_conditions['T'], P=rcf_conditions['P'])
            * (1 / chems['Methanol'].MW)
        )
        water_flow_mol = (
            total_vol_hr / (meoh_h2o + 1)
            * chems['Water'].rho(phase='l', T=rcf_conditions['T'], P=rcf_conditions['P'])
            * (1 / chems['Water'].MW)
        )
        meoh_fresh.imol['Methanol']  = meoh_flow_mol  - recycle_solvent.imol['Methanol']
        water_fresh.imol['Water']    = water_flow_mol - recycle_solvent.imol['Water']
        meoh_h2o_mix.outs[0].phases = ('s', 'l', 'g')  # needed by downstream reactors

    meoh_pump = bst.units.Pump('PUMP101', ins=meoh_h2o_mix-0, P=rcf_conditions['P'])

    meoh_heater = bst.units.HXutility('HX102', ins=meoh_pump-0, T=rcf_conditions['T'], rigorous=True)

    @meoh_heater.add_specification(run=True)
    def set_meoh_heater_phases():
        meoh_heater.outs[0].phases = ('l', 'g')

    # Solvolysis reactions
    solvolysis_rxn = bst.Reaction(
        'Lignin -> SolubleLignin', reactant='Lignin',
        X=solvolysis_parameters['Delignification'],
        basis='wt', correct_atomic_balance=False
    )
    methanol_decomposition_rxn = bst.ParallelReaction([
        bst.Reaction('Methanol,l -> Methane,g', reactant='Methanol', phases='lg',
                     X=solvolysis_parameters['MeOH_CH4'], basis='wt', correct_atomic_balance=False),
        bst.Reaction('Methanol,l -> CO,g', reactant='Methanol', phases='lg',
                     X=solvolysis_parameters['MeOH_CO'], basis='wt', correct_atomic_balance=False),
    ])

    solvolysis_reactor = SolvolysisReactor(
        'RCF103_S',
        ins=(ins, meoh_heater-0),
        outs=('Wet_Pulp', 'Solvolysis_Liquor'),
        T=rcf_conditions['T'],
        P=rcf_conditions['P'],
        tau=rcf_conditions['tau_s'],               # 3 hr time on stream per batch
        tau_0=1,                                   # 1 hr cleaning/turnaround
        tau_residence=rcf_conditions['tau_s_res'], # 20 min hydraulic residence time
        void_frac=0.5,
        superficial_velocity=0.01,
        poplar_density=poplar_density,             # 485 kg/m³ bulk density
        free_frac=free_frac,                       # 10% free headspace
        V_max_limit=V_max_limit,                   # hard upper bound on vessel volume
        reaction_1=solvolysis_rxn,
        reaction_2=methanol_decomposition_rxn,
    )

    # H2 mixer: adjusts fresh H2 to make up for recycle shortfall
    h2_mixer = bst.units.Mixer('MIX104', ins=(hydrogen_in, hydrogen_recycle))

    @h2_mixer.add_specification(run=True)
    def h2_flow():
        fresh_h2 = h2_mixer.ins[0]
        recycle_h2 = h2_mixer.ins[1]
        fresh_h2.imass['Hydrogen'] = (h2_biomass_ratio * (2e6 / 24)) - recycle_h2.imass['Hydrogen']
        h2_mixer.outs[0].phase = 'g'

    h2_pre_heat = bst.units.HXutility('HX105', ins=h2_mixer-0, T=rcf_conditions['T'], rigorous=True)

    @h2_pre_heat.add_specification(run=True)
    def set_h2_preheat_phase():
        h2_pre_heat.outs[0].phase = 'g'

    # Hydrogenolysis reactions
    # The six parallel reactions are designed so that ΣXi = Monomers + Dimers + Oligomers = 1.0
    # for any condensation_extent (algebraic identity). BioSTEAM's ParallelReaction captures the
    # initial reactant amount and subtracts Xi×SL0 sequentially; the check raises InfeasibleRegion
    # when remaining < -1e-12. At high delignification (large SL0), floating-point error in the
    # sum can exceed this threshold. Scale all X values by (1 - 1e-6) to leave ~1 ppm unconverted
    # and keep the residual well above -1e-12 for any feasible SL0.
    _X_scale = 1.0 - 1e-6
    hydrogenolysis = bst.ParallelReaction([
        bst.Reaction('SolubleLignin,l -> Propylguaiacol,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * rcf_oil_yield['Monomers'] * 0.5*(1-condensation_extent), basis='wt', correct_atomic_balance=False),
        bst.Reaction('SolubleLignin,l -> Propylsyringol,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * rcf_oil_yield['Monomers'] * 0.5*(1-condensation_extent), basis='wt', correct_atomic_balance=False),
        bst.Reaction('SolubleLignin,l -> Syringaresinol,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * rcf_oil_yield['Dimers'] * 0.5, basis='wt', correct_atomic_balance=False),
        bst.Reaction('SolubleLignin,l -> G_Dimer,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * rcf_oil_yield['Dimers'] * 0.5, basis='wt', correct_atomic_balance=False),
        bst.Reaction('SolubleLignin,l -> S_Oligomer,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * (rcf_oil_yield['Oligomers'] * 0.5 + rcf_oil_yield['Monomers'] * 0.5 * condensation_extent), basis='wt', correct_atomic_balance=False),
        bst.Reaction('SolubleLignin,l -> G_Oligomer,l', reactant='SolubleLignin', phases='lg',
                     X=_X_scale * (rcf_oil_yield['Oligomers'] * 0.5 + rcf_oil_yield['Monomers'] * 0.5 * condensation_extent), basis='wt', correct_atomic_balance=False),
    ])

    hydrogenolysis_reactor = HydrogenolysisReactor(
        'RCF106_H',
        ins=(solvolysis_reactor.outs[1], h2_pre_heat-0),
        P=rcf_conditions['P'],
        T=rcf_conditions['T'],
        superficial_velocity=0.003,
        reaction=hydrogenolysis,
    )

    R102 = bst.units.Flash('FLASH107', ins=hydrogenolysis_reactor-0, T=320, P=5e5)

    pre_psa_pump = bst.units.IsentropicCompressor('PUMP108', ins=R102-0, P=5e5, vle=True)
    pre_psa_flash = bst.units.Flash('FLASH109', ins=pre_psa_pump-0, T=260, P=5e5)

    pre_psa_heater = bst.units.HXutility('HX110', ins=pre_psa_flash-0, T=303, rigorous=True)

    @pre_psa_heater.add_specification(run=True)
    def set_psa_inlet_phase():
        pre_psa_heater.outs[0].phase = 'g'

    psa_system = PSA('PSA111', ins=pre_psa_heater.outs[0], outs=('', 'Purge_Light_Gases'))

    h2_pump = bst.units.IsentropicCompressor('PUMP112', ins=psa_system-0, outs=hydrogen_recycle,
                                              P=3e6, vle=True)

    @h2_pump.add_specification(run=True)
    def set_h2_pump_phase():
        h2_pump.outs[0].phase = 'g'

    crude_distillation = bst.units.BinaryDistillation(
        'DIST113', ins=R102-1,
        LHK=('Methanol', 'Water'),
        Lr=0.9995, Hr=1 - 0.967, P=101325,
        vessel_material='Stainless steel 316',
        k=2, partial_condenser=True,
    )

    meoh_purifier_col = bst.units.BinaryDistillation(
        'DIST114', ins=crude_distillation-0,
        outs=('', 'To_WW_Treatment'),
        LHK=('Methanol', 'Water'),
        y_top=0.9, x_bot=0.001, P=101325, k=2,
    )

    meoh_mixer = bst.units.Mixer('MIX116', ins=(meoh_purifier_col-0, pre_psa_flash-1), rigorous=True)

    cooler_2 = bst.units.HXutility('HX117', ins=meoh_mixer.outs[0], outs=meoh_recycle,
                                    V=0, rigorous=True)

    water_remover = bst.units.Flash('FLASH118', ins=crude_distillation-1,
                                    outs=('To_WW_Treatment_2', 'RCF_Oil'), T=400, P=101325)

    wastewater_mixer = bst.Mixer(
        ins=(meoh_purifier_col.outs[1], water_remover.outs[0]), outs='RCF_WW'
    )

      # outs[0]: evaporated MeOH/water from pulp — currently unrecovered (future: route to WWT or solvent recovery)
    pulp_purifier = bst.Flash('D601', solvolysis_reactor.outs[0], outs=('', 'Carbohydrate_Pulp'), T=400, P=1e5)


    catalyst = bst.Stream(
        'RCF_Catalyst',
        NiC=RCF_catalyst['loading'] * (feed_parameters['flow'] * 1e3) * RCF_catalyst['loading'],
        units='kg/yr', price=prices['NiC_catalyst'],
    )
    catalyst_stream = CatalystMixer(ins=catalyst)

    # ── Assemble system ───────────────────────────────────────────────────────
    return bst.System(
        'RCF_System',
        path=(
            meoh_h2o_mix, meoh_pump, meoh_heater, solvolysis_reactor,
            h2_mixer, h2_pre_heat, hydrogenolysis_reactor,
            R102, pre_psa_pump, pre_psa_flash, pre_psa_heater,
            psa_system, h2_pump, crude_distillation, meoh_purifier_col,
            meoh_mixer, cooler_2, water_remover, wastewater_mixer, pulp_purifier,
            catalyst_stream,
        ),
        recycle=(meoh_recycle, hydrogen_recycle),
    )
