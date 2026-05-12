"""
Tests for SolvolysisReactor geometry-based sizing logic.

Run with:
    pytest lignin_saf/test_solvolysis_sizing.py -v

These tests verify:
  1. Volume balance: V_solid + V_free + V_solvent = V_max
     (V_solid = (1-void_frac)*V_biomass; interparticle voids are filled with solvent)
  2. Batch arithmetic: batches/day × biomass/batch = daily feed
  3. Q calculation: Q = V_solvent / tau_residence  (solvent = void volume only)
  4. Total system flow: Q_total = N_working × Q_per_reactor
  5. Reactor geometry: diameter and length from superficial velocity
  6. Design results populated correctly after simulate()
  7. Derived loading ≈ 9.27 L/kg (volume-first, consistent with Bartling et al.)
"""

import pytest
import math
from math import ceil
import biosteam as bst
from lignin_saf.chemicals import create_chemicals
from lignin_saf.ligsaf_settings import (
    rcf_conditions, feed_parameters, solvolysis_parameters,
    poplar_density, free_frac,
)


# ── Shared fixture ──────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def sizing_params():
    """Reference values computed from first principles for 2000 DMT/day feed.

    Volume-first approach: bed geometry (V_void = void_frac × V_biomass) drives Q.
    Q = V_void / tau_res; loading [L/kg] is a derived output, not an input.

    Uses the ideal staggering formula from SolvolysisReactor._size_bed():
    N_total = cycle_time / tau_0; N_working = N_total × (tau / cycle_time).
    At tau=3, tau_0=1: N_total=4, N_working=3, N_offline=1.
    """
    V_max_limit_    = 600       # m³ reference upper bound
    tau_s        = 3            # hr  time on stream
    tau_0        = 1            # hr  cleaning
    tau_res      = 1 / 3       # hr  hydraulic RT (20 min)
    u            = 0.01         # m/s superficial velocity (initial; may be reduced by L/D cap)
    rho_poplar   = 485          # kg/m³ bulk density
    void_frac_   = 0.5          # interparticle void fraction
    free_frac_   = 0.10

    cycle_time    = tau_s + tau_0                                # 4 hr
    feed_kgday    = feed_parameters['flow'] * 1e3               # 2,000,000 kg/day

    # Ideal stagger base
    N_total_base   = max(2, round(cycle_time / tau_0))
    N_working_base = min(N_total_base - 1, max(1, round(N_total_base * tau_s / cycle_time)))

    # Scale up by k until each vessel fits within V_max_limit.
    # k reduces V_max by splitting the daily feed into more, smaller batches.
    for k in range(1, 101):
        N_total   = k * N_total_base
        N_working = k * N_working_base
        batches_per_day   = N_total * (24 / cycle_time)
        biomass_per_batch = feed_kgday / batches_per_day
        V_biomass         = biomass_per_batch / rho_poplar
        V_solid           = (1 - void_frac_) * V_biomass
        V_void            = void_frac_ * V_biomass
        V_solvent         = V_void                              # solvent = void volume only
        V_max             = (V_solid + V_solvent) / (1.0 - free_frac_)  # = V_biomass / (1 - free_frac)
        Q_per_reactor     = V_solvent / tau_res                 # derived from geometry
        Q_total           = N_working * Q_per_reactor
        if V_max <= V_max_limit_:
            break

    V_free = free_frac_ * V_max

    LD_max   = 5.0
    A        = Q_per_reactor / (u * 3600)                       # m²
    diameter = 2 * (A / math.pi) ** 0.5                        # m
    length   = V_max / A                                        # m

    # Mirror the L/D enforcement from _size_bed()
    if length / diameter > LD_max:
        A        = (V_max * math.pi ** 0.5 / (2.0 * LD_max)) ** (2.0 / 3.0)
        u        = Q_per_reactor / (A * 3600)
        diameter = 2 * (A / math.pi) ** 0.5
        length   = V_max / A

    loading = Q_total * 1000.0 * 24.0 / feed_kgday             # derived [L/kg]

    return dict(
        V_max_limit=V_max_limit_,
        V_max=V_max, tau_s=tau_s, tau_0=tau_0, tau_res=tau_res,
        N_total=N_total, N_working=N_working, u=u,
        rho_poplar=rho_poplar, void_frac=void_frac_, free_frac=free_frac_,
        V_solid=V_solid,
        cycle_time=cycle_time, batches_per_day=batches_per_day,
        feed_kgday=feed_kgday, biomass_per_batch=biomass_per_batch,
        V_biomass=V_biomass, V_free=V_free, V_solvent=V_solvent, V_void=V_void,
        Q_per_reactor=Q_per_reactor, Q_total=Q_total, loading=loading,
        A=A, diameter=diameter, length=length,
    )


# ── Pure-math tests (no BioSTEAM required) ─────────────────────────────────

class TestSizingMath:

    def test_cycle_time(self, sizing_params):
        """tau_s + tau_0 = 4 hr → 6 batches/reactor/day."""
        assert sizing_params['cycle_time'] == pytest.approx(4.0)

    def test_batches_per_day(self, sizing_params):
        """N_total beds × (24 hr / cycle_time) batches/bed/day."""
        p = sizing_params
        expected = p['N_total'] * (24.0 / p['cycle_time'])
        assert p['batches_per_day'] == pytest.approx(expected)

    def test_biomass_per_batch(self, sizing_params):
        """feed_kgday / batches_per_day = kg/batch."""
        p = sizing_params
        assert p['biomass_per_batch'] == pytest.approx(p['feed_kgday'] / p['batches_per_day'], rel=1e-6)

    def test_volume_balance(self, sizing_params):
        """V_solid + V_free + V_solvent must equal V_max exactly."""
        p = sizing_params
        total = p['V_solid'] + p['V_free'] + p['V_solvent']
        assert total == pytest.approx(p['V_max'], rel=1e-9)

    def test_V_biomass(self, sizing_params):
        """83,333 kg / 485 kg/m³ ≈ 171.8 m³ bulk volume (N_total=4, 24 batches/day)."""
        p = sizing_params
        assert p['V_biomass'] == pytest.approx(p['biomass_per_batch'] / p['rho_poplar'], rel=1e-6)

    def test_V_solid(self, sizing_params):
        """Solid wood volume = (1 - void_frac) × V_biomass = 0.5 × 171.8 ≈ 85.9 m³."""
        p = sizing_params
        assert p['V_solid'] == pytest.approx((1 - p['void_frac']) * p['V_biomass'], rel=1e-9)

    def test_V_free(self, sizing_params):
        """10% of V_max is kept as headspace."""
        p = sizing_params
        assert p['V_free'] == pytest.approx(p['free_frac'] * p['V_max'], rel=1e-9)

    def test_V_solvent_positive(self, sizing_params):
        """Solvent volume must be positive — solid biomass + headspace must fit."""
        assert sizing_params['V_solvent'] > 0

    def test_V_solvent_equals_V_void(self, sizing_params):
        """
        V_solvent = V_void = void_frac × V_biomass (solvent fills interparticle voids only).
        No dynamic holdup term — Q is derived from geometry, not the other way around.
        """
        p = sizing_params
        assert p['V_solvent'] == pytest.approx(p['V_void'], rel=1e-9)

    def test_Q_derived_from_void_volume(self, sizing_params):
        """
        Q_per_reactor = V_solvent / tau_residence = V_void / tau_res.
        V_max / tau_res would be wrong (larger than Q).
        """
        p = sizing_params
        Q_from_void = p['V_solvent'] / p['tau_res']
        Q_wrong     = p['V_max'] / p['tau_res']

        assert p['Q_per_reactor'] == pytest.approx(Q_from_void, rel=1e-6)
        assert p['Q_per_reactor'] != pytest.approx(Q_wrong, rel=1e-3), (
            "Q_per_reactor is using V_max instead of V_solvent (= V_void)"
        )

    def test_Q_per_reactor_approx(self, sizing_params):
        """Q = V_solvent / tau_residence (void volume drives flow rate)."""
        p = sizing_params
        assert p['Q_per_reactor'] == pytest.approx(p['V_solvent'] / p['tau_res'], rel=1e-6)

    def test_total_flow_three_reactors(self, sizing_params):
        """Total Q = N_working × Q_per_reactor."""
        p = sizing_params
        assert p['Q_total'] == pytest.approx(p['N_working'] * p['Q_per_reactor'], rel=1e-9)

    def test_superficial_velocity_consistent(self, sizing_params):
        """u = Q / A must recover the specified superficial velocity."""
        p = sizing_params
        u_recovered = p['Q_per_reactor'] / (p['A'] * 3600)
        assert u_recovered == pytest.approx(p['u'], rel=1e-6)

    def test_LD_ratio_reasonable(self, sizing_params):
        """
        L/D is capped at LD_max=5 (upper end of ideal 3–5 range).
        Natural L/D (without cap) would be > 5; after analytical u reduction it is exactly 5.
        """
        p = sizing_params
        LD = p['length'] / p['diameter']
        assert LD == pytest.approx(5.0, rel=0.01), f"L/D = {LD:.2f} should be ≈5 after cap"

    def test_throughput_closure(self, sizing_params):
        """batches/day × biomass/batch must recover daily feed exactly."""
        p = sizing_params
        recovered = p['batches_per_day'] * p['biomass_per_batch']
        assert recovered == pytest.approx(p['feed_kgday'], rel=1e-6)

    def test_derived_loading(self, sizing_params):
        """Derived loading ≈ 9.27 L/kg — consistent with Bartling et al. 9 L/kg literature value."""
        p = sizing_params
        assert p['loading'] == pytest.approx(9.27, abs=0.1), (
            f"Derived loading = {p['loading']:.2f} L/kg; expected ≈9.27 L/kg"
        )


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
        # Ideal stagger: N_total = cycle_time / tau_0 = 4/1 = 4
        assert simulated_reactor.design_results['Total beds'] == 4

    def test_beds_in_service(self, simulated_reactor):
        # N_working = N_total × (tau / cycle_time) = 4 × (3/4) = 3
        assert simulated_reactor.design_results['Beds in service'] == 3

    def test_reactor_volume(self, simulated_reactor):
        # V_max = V_biomass / (1 - free_frac) = 171.8 / 0.9 ≈ 190.9 m³
        assert simulated_reactor.design_results['Reactor volume'] == pytest.approx(190.9, abs=1.0)

    def test_time_on_stream(self, simulated_reactor):
        assert simulated_reactor.design_results['Time on stream'] == pytest.approx(3.0)

    def test_residence_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Residence time'] == pytest.approx(1 / 3, rel=1e-6)

    def test_turnaround_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Turnaround time'] == pytest.approx(1.0)

    def test_batch_time(self, simulated_reactor):
        assert simulated_reactor.design_results['Batch time'] == pytest.approx(4.0)

    def test_V_biomass_approx(self, simulated_reactor):
        """Bulk biomass volume per bed = biomass_per_batch / poplar_density for base N_total=4."""
        V_bm = simulated_reactor.design_results['Biomass volume per bed']
        # N_total=4, batches/day=24, biomass/batch=83333 kg, V_biomass=171.8 m³
        assert V_bm == pytest.approx(171.8, abs=1.0)

    def test_V_solvent_approx(self, simulated_reactor):
        """Solvent volume per bed = V_void = void_frac × V_biomass ≈ 85.9 m³."""
        V_sol = simulated_reactor.design_results['Solvent volume per bed']
        # V_void = 0.5 × 171.8 = 85.9 m³ (no dynamic holdup)
        assert V_sol == pytest.approx(85.9, abs=1.0)

    def test_volume_balance_in_results(self, simulated_reactor):
        """V_solid + V_free + V_solvent == V_max (solid = (1-void_frac)*V_biomass)."""
        dr       = simulated_reactor.design_results
        void_frac_ = simulated_reactor.void_frac
        V_solid  = (1 - void_frac_) * dr['Biomass volume per bed']
        V_max_actual = simulated_reactor.V_max
        total    = V_solid + free_frac * V_max_actual + dr['Solvent volume per bed']
        assert total == pytest.approx(V_max_actual, abs=0.5)

    def test_Q_based_on_void_volume(self, simulated_reactor):
        """
        Verify Q implied by geometry = V_solvent / tau_res.
        V_solvent = V_void (no dynamic holdup); Q is fully determined by bed geometry.
        """
        dr    = simulated_reactor.design_results
        u     = simulated_reactor.superficial_velocity
        D_m   = dr['Diameter'] / 3.28084
        A     = math.pi / 4 * D_m ** 2
        Q_implied = A * u * 3600                                  # m³/hr

        V_sol    = dr['Solvent volume per bed']
        tau_res  = simulated_reactor.tau_residence
        Q_expected = V_sol / tau_res                              # Q = V_void / tau_res

        assert Q_implied == pytest.approx(Q_expected, rel=1e-3), (
            f"Q implied by geometry ({Q_implied:.1f} m³/hr) does not match "
            f"V_solvent/tau_res ({Q_expected:.1f} m³/hr)"
        )

    def test_LD_ratio(self, simulated_reactor):
        """
        L/D is enforced at LD_max=5 (ideal packed-bed range 3–5, hard limit 10).
        Superficial velocity is reduced analytically from 0.01 m/s to hit L/D = 5 exactly.
        Pressure drop is recomputed at the reduced u via self.superficial_velocity update.
        """
        dr   = simulated_reactor.design_results
        LD   = dr['Length'] / dr['Diameter']   # both in ft, ratio same
        assert LD == pytest.approx(5.0, rel=0.01), f"L/D = {LD:.2f} should be ≈5 after cap"

    def test_derived_loading(self, simulated_reactor):
        """Derived solvent loading ≈ 9.27 L/kg (volume-first; consistent with Bartling 9 L/kg)."""
        loading = simulated_reactor.design_results['Solvent loading']
        assert loading == pytest.approx(9.27, abs=0.1), (
            f"Derived loading = {loading:.2f} L/kg; expected ≈9.27 L/kg"
        )
