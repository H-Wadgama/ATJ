"""
Tests for SolvolysisReactor geometry-based sizing logic.

Run with:
    pytest lignin_saf/test_solvolysis_sizing.py -v

These tests verify:
  1. Volume balance: V_solid + V_free + V_solvent = V_max
     (V_solid = (1-void_frac)*V_biomass; interparticle voids are filled with solvent)
  2. Batch arithmetic: batches/day × biomass/batch = daily feed
  3. Q calculation: Q = V_solvent / tau_residence  (NOT V_max / tau_residence)
  4. Total system flow: Q_total = N_working × Q_per_reactor
  5. Reactor geometry: diameter and length from superficial velocity
  6. Design results populated correctly after simulate()
"""

import pytest
import math
import biosteam as bst
from lignin_saf.ligsaf_chemicals import create_chemicals
from lignin_saf.ligsaf_settings import (
    rcf_conditions, feed_parameters, solvolysis_parameters,
    poplar_density, free_frac,
)


# ── Shared fixture ──────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def sizing_params():
    """Reference values computed from first principles for 2000 DMT/day feed."""
    V_max        = 600          # m³ per bed
    tau_s        = 3            # hr  time on stream
    tau_0        = 1            # hr  cleaning
    tau_res      = 1 / 3       # hr  hydraulic RT (20 min)
    N_total      = 4
    N_working    = 3
    u            = 0.01         # m/s superficial velocity — gives L/D ≈ 2.3
    rho_poplar   = 485          # kg/m³ bulk density
    void_frac_   = 0.5          # interparticle void fraction
    free_frac_   = 0.10

    cycle_time         = tau_s + tau_0                          # 4 hr
    batches_per_day    = N_total * (24 / cycle_time)            # 24
    feed_kgday         = feed_parameters['flow'] * 1e3          # 2,000,000 kg/day
    biomass_per_batch  = feed_kgday / batches_per_day           # 83,333.3 kg

    V_biomass = biomass_per_batch / rho_poplar                  # m³ bulk biomass volume
    V_free    = free_frac_ * V_max                              # m³ headspace
    # Interparticle voids (void_frac × V_biomass) are filled with solvent.
    # Only solid wood [(1-void_frac) × V_biomass] excludes solvent.
    V_solid   = (1 - void_frac_) * V_biomass                   # m³ actual wood
    V_solvent = V_max - V_solid - V_free                        # m³ total solvent in bed

    Q_per_reactor = V_solvent / tau_res                         # m³/hr
    Q_total       = N_working * Q_per_reactor                   # m³/hr

    A        = Q_per_reactor / (u * 3600)                       # m²
    diameter = 2 * (A / math.pi) ** 0.5                        # m
    length   = V_max / A                                        # m

    return dict(
        V_max=V_max, tau_s=tau_s, tau_0=tau_0, tau_res=tau_res,
        N_total=N_total, N_working=N_working, u=u,
        rho_poplar=rho_poplar, void_frac=void_frac_, free_frac=free_frac_,
        V_solid=V_solid,
        cycle_time=cycle_time, batches_per_day=batches_per_day,
        feed_kgday=feed_kgday, biomass_per_batch=biomass_per_batch,
        V_biomass=V_biomass, V_free=V_free, V_solvent=V_solvent,
        Q_per_reactor=Q_per_reactor, Q_total=Q_total,
        A=A, diameter=diameter, length=length,
    )


# ── Pure-math tests (no BioSTEAM required) ─────────────────────────────────

class TestSizingMath:

    def test_cycle_time(self, sizing_params):
        """tau_s + tau_0 = 4 hr → 6 batches/reactor/day."""
        assert sizing_params['cycle_time'] == pytest.approx(4.0)

    def test_batches_per_day(self, sizing_params):
        """4 beds × 6 batches/bed/day = 24 total batches."""
        assert sizing_params['batches_per_day'] == pytest.approx(24.0)

    def test_biomass_per_batch(self, sizing_params):
        """2,000,000 kg/day ÷ 24 batches = 83,333.3 kg/batch."""
        assert sizing_params['biomass_per_batch'] == pytest.approx(83333.33, rel=1e-4)

    def test_volume_balance(self, sizing_params):
        """V_solid + V_free + V_solvent must equal V_max exactly."""
        p = sizing_params
        total = p['V_solid'] + p['V_free'] + p['V_solvent']
        assert total == pytest.approx(p['V_max'], rel=1e-9)

    def test_V_biomass(self, sizing_params):
        """83,333 kg / 485 kg/m³ ≈ 171.8 m³ bulk volume."""
        p = sizing_params
        assert p['V_biomass'] == pytest.approx(p['biomass_per_batch'] / p['rho_poplar'], rel=1e-6)

    def test_V_solid(self, sizing_params):
        """Solid wood volume = (1 - void_frac) × V_biomass = 0.5 × 171.8 ≈ 85.9 m³."""
        p = sizing_params
        assert p['V_solid'] == pytest.approx((1 - p['void_frac']) * p['V_biomass'], rel=1e-9)

    def test_V_free(self, sizing_params):
        """10% of 600 m³ = 60 m³."""
        p = sizing_params
        assert p['V_free'] == pytest.approx(p['free_frac'] * p['V_max'], rel=1e-9)

    def test_V_solvent_positive(self, sizing_params):
        """Solvent volume must be positive — solid biomass + headspace must fit."""
        assert sizing_params['V_solvent'] > 0

    def test_V_solvent_includes_interparticle_void(self, sizing_params):
        """
        V_solvent = V_max - V_solid - V_free
                  = (V_max - V_biomass - V_free) + void_frac * V_biomass
        The interparticle void space (void_frac × V_biomass ≈ 85.9 m³) is solvent,
        so V_solvent ≈ 454.1 m³, not 368.2 m³ (old incorrect calculation).
        """
        p = sizing_params
        expected = p['V_max'] - p['V_solid'] - p['V_free']
        assert p['V_solvent'] == pytest.approx(expected, rel=1e-9)
        # Check it's larger than the old (incorrect) value
        old_wrong = p['V_max'] - p['V_biomass'] - p['V_free']
        assert p['V_solvent'] > old_wrong

    def test_Q_uses_V_solvent_not_V_max(self, sizing_params):
        """
        Q = V_solvent / tau_residence, NOT V_max / tau_residence.

        V_max / tau_res would give 1800 m³/hr (wrong).
        V_solvent / tau_res gives ~1104 m³/hr (correct).
        The hydraulic residence time is defined on the fluid volume only.
        """
        p = sizing_params
        Q_correct = p['V_solvent'] / p['tau_res']
        Q_wrong   = p['V_max']    / p['tau_res']

        assert p['Q_per_reactor'] == pytest.approx(Q_correct, rel=1e-6)
        assert p['Q_per_reactor'] != pytest.approx(Q_wrong,   rel=1e-3), (
            "Q_per_reactor is using V_max instead of V_solvent"
        )

    def test_Q_per_reactor_approx(self, sizing_params):
        """For 2000 DMT/day: Q per reactor ≈ 1362 m³/hr (V_solvent ≈ 454 m³ / 20 min)."""
        p = sizing_params
        # V_solvent ≈ 454 m³, tau_res = 1/3 hr → Q ≈ 1362 m³/hr
        assert p['Q_per_reactor'] == pytest.approx(1362, abs=10)

    def test_total_flow_three_reactors(self, sizing_params):
        """Total Q = N_working × Q_per_reactor = 3 × 1104 ≈ 3312 m³/hr."""
        p = sizing_params
        assert p['Q_total'] == pytest.approx(3 * p['Q_per_reactor'], rel=1e-9)

    def test_superficial_velocity_consistent(self, sizing_params):
        """u = Q / A must recover the specified superficial velocity."""
        p = sizing_params
        u_recovered = p['Q_per_reactor'] / (p['A'] * 3600)
        assert u_recovered == pytest.approx(p['u'], rel=1e-6)

    def test_LD_ratio_reasonable(self, sizing_params):
        """
        L/D should be less than 5 for a compact packed-bed vessel.
        With u=0.01 m/s and Q based on V_solvent (≈1104 m³/hr), A ≈ 31 m²,
        D ≈ 6.3 m, L ≈ 20 m → L/D ≈ 3.1.
        """
        p = sizing_params
        LD = p['length'] / p['diameter']
        assert 2 < LD < 5, f"L/D = {LD:.2f} is outside the expected 2–5 range"

    def test_throughput_closure(self, sizing_params):
        """batches/day × biomass/batch must recover daily feed exactly."""
        p = sizing_params
        recovered = p['batches_per_day'] * p['biomass_per_batch']
        assert recovered == pytest.approx(p['feed_kgday'], rel=1e-6)


# ── Integration tests (require BioSTEAM + lignin_saf package) ──────────────

@pytest.fixture(scope='module')
def simulated_reactor():
    """Build and simulate a minimal SolvolysisReactor, return the unit."""
    from lignin_saf.ligsaf_units import SolvolysisReactor

    chems = create_chemicals()
    bst.settings.set_thermo(chems)
    bst.settings.CEPCI = 541.7

    chems.define_group(
        name='Poplar',
        IDs=['Glucan', 'Xylan', 'Arabinan', 'Mannan', 'Galactan',
             'Sucrose', 'Lignin', 'Acetate', 'Extract', 'Ash'],
        composition=[0.464, 0.134, 0.002, 0.037, 0.014,
                     0.001, 0.285, 0.035, 0.016, 0.012],
        wt=True
    )

    biomass = bst.Stream('Test_Poplar',
                         Poplar=feed_parameters['flow'] * 1e3,
                         Water=feed_parameters['moisture'] * feed_parameters['flow'] * 1e3,
                         phase='l', units='kg/d')

    # Solvent must be a MultiStream with phases ('l','g') to match the phase
    # requirement of the methanol decomposition reactions (phases='lg')
    solvent = bst.MultiStream('Test_Solvent', phases=('l', 'g'),
                              T=rcf_conditions['T'], P=rcf_conditions['P'])
    solvent.imass['l', 'Methanol'] = 1e5   # kg/hr
    solvent.imass['l', 'Water']    = 1e4   # kg/hr

    solvolysis_rxn = bst.Reaction(
        'Lignin -> SolubleLignin', reactant='Lignin',
        X=solvolysis_parameters['Delignification'],
        basis='wt', correct_atomic_balance=False,
    )
    meoh_decomp = bst.ParallelReaction([
        bst.Reaction('Methanol,l -> Methane,g', reactant='Methanol', phases='lg',
                     X=solvolysis_parameters['MeOH_CH4'], basis='wt',
                     correct_atomic_balance=False),
        bst.Reaction('Methanol,l -> CO,g', reactant='Methanol', phases='lg',
                     X=solvolysis_parameters['MeOH_CO'], basis='wt',
                     correct_atomic_balance=False),
    ])

    reactor = SolvolysisReactor(
        'Test_RCF103',
        ins=(biomass, solvent),
        outs=('Test_Pulp', 'Test_Liquor'),
        T=rcf_conditions['T'],
        P=rcf_conditions['P'],
        tau=rcf_conditions['tau_s'],
        tau_0=1,
        tau_residence=rcf_conditions['tau_s_res'],
        void_frac=0.5,
        superficial_velocity=0.01,
        poplar_density=poplar_density,
        free_frac=free_frac,
        reaction_1=solvolysis_rxn,
        reaction_2=meoh_decomp,
    )
    reactor.simulate()
    return reactor


class TestDesignResults:

    def test_total_beds(self, simulated_reactor):
        assert simulated_reactor.design_results['Total beds'] == 4

    def test_beds_in_service(self, simulated_reactor):
        assert simulated_reactor.design_results['Beds in service'] == 3

    def test_reactor_volume(self, simulated_reactor):
        assert simulated_reactor.design_results['Reactor volume'] == pytest.approx(600, rel=1e-6)

    def test_time_on_stream(self, simulated_reactor):
        assert simulated_reactor.design_results['Time on stream'] == pytest.approx(3.0)

    def test_residence_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Residence time'] == pytest.approx(1 / 3, rel=1e-6)

    def test_turnaround_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Turnaround time'] == pytest.approx(1.0)

    def test_batch_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Batch time'] == pytest.approx(4.0)

    def test_V_biomass_approx(self, simulated_reactor):
        """Bulk biomass volume per bed ≈ 171.8 m³ for 2000 DMT/day."""
        V_bm = simulated_reactor.design_results['Biomass volume per bed']
        assert V_bm == pytest.approx(171.8, abs=1.0)

    def test_V_solvent_approx(self, simulated_reactor):
        """Solvent volume per bed ≈ 454.1 m³ (includes interparticle void space)."""
        V_sol = simulated_reactor.design_results['Solvent volume per bed']
        assert V_sol == pytest.approx(454.1, abs=1.0)

    def test_volume_balance_in_results(self, simulated_reactor):
        """V_solid + V_free + V_solvent == V_max (solid = (1-void_frac)*V_biomass)."""
        dr       = simulated_reactor.design_results
        void_frac_ = simulated_reactor.void_frac
        V_solid  = (1 - void_frac_) * dr['Biomass volume per bed']
        total    = V_solid + free_frac * 600 + dr['Solvent volume per bed']
        assert total == pytest.approx(600, abs=0.5)

    def test_Q_based_on_V_solvent(self, simulated_reactor):
        """
        Verify the reactor's internal Q is V_solvent/tau_res, not V_max/tau_res.
        Check via area: A = Q/(u×3600), so Q = A × u × 3600.
        """
        dr    = simulated_reactor.design_results
        u     = simulated_reactor.superficial_velocity
        # Diameter stored in ft in design_results; convert back to m
        D_m   = dr['Diameter'] / 3.28084
        A     = math.pi / 4 * D_m ** 2
        Q_implied = A * u * 3600                                  # m³/hr

        V_sol    = dr['Solvent volume per bed']
        tau_res  = simulated_reactor.tau_residence
        Q_expected = V_sol / tau_res

        assert Q_implied == pytest.approx(Q_expected, rel=1e-3), (
            f"Q implied by geometry ({Q_implied:.1f} m³/hr) does not match "
            f"V_solvent/tau_res ({Q_expected:.1f} m³/hr)"
        )

    def test_LD_ratio(self, simulated_reactor):
        """
        L/D should be less than 5 for a compact packed-bed vessel.
        With u=0.01 m/s and Q = V_solvent/tau_residence ≈ 1104 m³/hr:
        A ≈ 31 m², D ≈ 6.3 m, L ≈ 20 m → L/D ≈ 3.1.
        """
        dr   = simulated_reactor.design_results
        LD   = dr['Length'] / dr['Diameter']   # both in ft, ratio same
        assert 2 < LD < 5, f"L/D = {LD:.2f} outside expected 2–5 range"
