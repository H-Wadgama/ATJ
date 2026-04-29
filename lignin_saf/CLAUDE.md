# lignin_saf/CLAUDE.md

Context for the `rcf_system` defined in `rcf_system.ipynb`.

## rcf_system Overview

RCF (Reductive Catalytic Fractionation) loop that processes poplar biomass into crude lignin oil and a carbohydrate pulp. Two recycle streams: methanol solvent and hydrogen.

```python
rcf_system = bst.System('RCF_System',
    path=(meoh_h2o_mix, meoh_pump, meoh_heater, solvolysis_reactor, h2_mixer, h2_pre_heat,
          hydrogenolysis_reactor, R102, pre_psa_pump, pre_psa_flash, pre_psa_heater,
          psa_system, h2_pump, crude_distillation, meoh_purifier_col, meoh_mixer, cooler_2,
          water_remover, wastewater_mixer, catalyst_stream),
    recycle=(meoh_recycle, hydrogen_recycle))
```

## Input Streams

| Stream | Contents | Conditions |
|---|---|---|
| `poplar_in` | 2,000 dry MT/day poplar + 20% moisture | Liquid, ambient |
| `meoh_in` | Fresh methanol make-up; flow derived from bed geometry by `meoh_water_flow` spec (~9.27 L/kg dry biomass) | Liquid |
| `hydrogen_in` | Fresh H₂, 0.054 kg/kg dry biomass (from PEM electrolysis) | Gas, 80°C, 30 bar |

## Unit Operations

| Unit ID | Variable Name | Type | Function | Key Parameters |
|---|---|---|---|---|
| MIX100 | `meoh_h2o_mix` | Mixer | Mix fresh MeOH + MeOH recycle | — |
| PUMP101 | `meoh_pump` | Pump | Pressurize MeOH | P = 60 bar |
| HX102 | `meoh_heater` | HXutility | Heat MeOH | T = 200°C, rigorous VLE |
| RCF103_S | `solvolysis_reactor` | `SolvolysisReactor` (custom) | Solvolysis: delignify biomass; produce pulp + liquor | T=200°C, P=60 bar, τ_s=3 hr, τ_0=1 hr, τ_res=1/3 hr, void_frac=0.5, V_max_limit=600 m³, LD_max=5.0; solvent loading derived (~9.27 L/kg) |
| MIX104 | `h2_mixer` | Mixer | Mix fresh H₂ + H₂ recycle | — |
| HX105 | `h2_pre_heat` | HXutility | Heat H₂ | T = 200°C, rigorous |
| RCF106-H | `hydrogenolysis_reactor` | `HydrogenolysisReactor` (custom) | Hydrogenolyze lignin oil to C5–C15 monomers | T=200°C, P=60 bar, τ=1 hr, v=0.003 m/s, N_reactors=8 |
| — | `R102` | (flash/separator step inside hydrogenolysis path) | Phase separation after reactor | — |
| PUMP108 | `pre_psa_pump` | IsentropicCompressor | Compress vapor for PSA | P = 5 bar, vle=True |
| FLASH109 | `pre_psa_flash` | Flash | Cool/condense before PSA | T = 260 K, P = 5 bar |
| HX110 | `pre_psa_heater` | HXutility | Reheat gas to PSA inlet | T = 303 K (30°C), rigorous |
| PSA111 | `psa_system` | `PSA` (custom) | Recover H₂; purge light gases | — |
| PUMP112 | `h2_pump` | IsentropicCompressor | Recompress H₂ recycle | P = 30 bar, vle=True, gas phase enforced |
| DIST113 | `crude_distillation` | BinaryDistillation | Separate MeOH/water from hydrogenolysis liquids | LHK=(Methanol, Water), Lr=0.9995, Hr=0.033, P=1 atm |
| DIST114 | `meoh_purifier_col` | BinaryDistillation | Purify MeOH to spec | LHK=(Methanol, Water), y_top=0.9, x_bot=0.001, P=1 atm |
| MIX116 | `meoh_mixer` | Mixer | Combine purified MeOH + FLASH109 condensate | — |
| HX117 | `cooler_2` | HXutility (cooler) | Cool MeOH → `meoh_recycle` | V=0 (saturated liquid), rigorous |
| FLASH118 | `water_remover` | Flash | Separate water from crude RCF oil | T=400 K, P=1 atm |
| — | `wastewater_mixer` | Mixer | Combine all wastewater → `RCF_WW` | — |
| — | `catalyst_stream` | `CatalystMixer` (custom) | Track NiC catalyst replacement cost | 0.1 kg/kg dry biomass, replaced 1×/year |

Note: FLASH107 (between `hydrogenolysis_reactor` and `pre_psa_pump`) performs the initial vapor-liquid split at T=320 K, P=5 bar — its variable name may be `R102` or an intermediate flash step.

## Recycle Loops

| Recycle Stream | Path |
|---|---|
| `meoh_recycle` | `cooler_2` (HX117) → `meoh_h2o_mix` (MIX100) |
| `hydrogen_recycle` | `h2_pump` (PUMP112) → `h2_mixer` (MIX104) |

Recycle specs: fresh feed in each mixer is adjusted so that `fresh + recycle = required total`. BioSTEAM iterates until both recycles converge.

## Output Streams

| Stream | Source Unit | Description | Downstream |
|---|---|---|---|
| `RCF_Oil` | `water_remover` (FLASH118) | Crude lignin oil: 50% monomers, 25% dimers, 25% oligomers; C5–C15 range | → `rcf_oil_purification_sys` (ethyl acetate LLE) |
| `Carbohydrate_Pulp` | `solvolysis_reactor` (RCF103-S) | Cellulose-rich pulp, 90% cellulose retention | → `etoh_system` (cellulosic ethanol) |
| `RCF_WW` | `wastewater_mixer` | Combined wastewater (light organics, unconverted solvent) | → wastewater treatment |
| `Purge_Light_Gases` | `psa_system` (PSA111) | Non-H₂ light gases | purged / flared |

## Process Conditions (from ligsaf_settings.py)

| Parameter | Value |
|---|---|
| Solvolysis T / P / τ | 200°C / 60 bar / 3 hr (time on stream) + 1/3 hr hydraulic RT |
| Hydrogenolysis T / P / τ | 200°C / 60 bar / 1 hr |
| Solvent loading | ~9.27 L/kg — derived from bed geometry (Q = V_void / τ_res); reported as `design_results['Solvent loading']`; consistent with Bartling et al. 9 L/kg |
| Max vessel volume (`V_max_limit`) | 600 m³ — hard upper bound enforced by k-multiplier scaling of N_total |
| H₂:biomass ratio | 0.054 kg H₂/kg dry biomass |
| NiC catalyst loading | 0.1 kg/kg dry biomass |
| Lignin delignification | 70% → RCF oil |
| Cellulose retention in pulp | 90% |
| RCF oil composition | 50% monomers / 25% dimers / 25% oligomers |
| Operating basis | 330 days/yr × 24 hr/day |
| CEPCI basis | 541.7 (2016 USD) |

## SolvolysisReactor Sizing Model

`_size_bed()` in `ligsaf_units.py` uses a three-stage **volume-first** approach. Bed geometry fully determines solvent volume; Q and loading are derived outputs.

**Stage 1 — Ideal stagger formula:**
```
N_total_base = round(cycle_time / tau_0)                       # = 4 at base case
N_working    = round(N_total_base × tau / cycle_time)          # = 3
N_offline    = N_total_base − N_working                        # = 1
batches/day  = 24 / tau_0  (independent of tau)
```

**Stage 2 — k-multiplier scaling to enforce V_max_limit:**
```
for k = 1, 2, 3, …:
    N_total = k × N_total_base,  N_working = k × N_working_base
    V_void        = void_frac × V_biomass          # interparticle voids = solvent volume
    V_solvent     = V_void                         # solvent fills voids only (no dynamic term)
    V_max         = (V_solid + V_solvent) / (1 − free_frac)  = V_biomass / (1 − free_frac)
    Q_per_reactor = V_solvent / tau_residence      # derived from geometry
    Q_total       = N_working × Q_per_reactor
    accept if V_max ≤ V_max_limit
```
k reduces V_max by increasing batches_per_day (smaller biomass_per_batch → smaller V_biomass).

**Stage 3 — L/D enforcement:**
If natural L/D > LD_max (default 5.0), superficial_velocity is reduced analytically:
```
A_new = (V_max × √π / (2 × LD_max))^(2/3)
u_adj = Q_per_reactor / (A_new × 3600)
```
`self.superficial_velocity` is updated so pressure drop uses the adjusted value.

**Base case results (tau=3, tau_0=1, tau_res=1/3 hr, void_frac=0.5):**

| Quantity | Value |
|---|---|
| N_total / N_working | 4 / 3 |
| Biomass per batch | 83,333 kg |
| V_void (= V_solvent) per bed | 85.9 m³ |
| V_max per vessel | ~191 m³ |
| Q_total / Q_per_reactor | 773 / 258 m³/hr |
| Derived loading | ~9.27 L/kg (consistent with Bartling et al. 9 L/kg) |
| D / L / L/D | 3.63 m / 18.4 m / 5.0 |
| Effective u (after L/D cap) | ~0.0069 m/s |

**`compute_Q_total()` method:** Returns Q_total [m³/hr] from geometry without side effects. Called by the `meoh_water_flow` spec in `ligsaf_system.py` on every recycle iteration to set the methanol feed flow.

## Downstream Systems (outside rcf_system)

- `etoh_system` — cellulosic ethanol from `biorefineries.cellulosic`, fed by `Carbohydrate_Pulp`
- `rcf_oil_purification_sys` — ethyl acetate LLE to isolate monomers from `RCF_Oil`
- `monomer_purification_sys` — hexane LLE for final monomer separation
- `combined_sys` — full integrated system wrapping all of the above (330 days/yr × 24 hr)
- `combined_sys_hx` — same with `HeatExchangerNetwork` (T_min_app=10°C)

## Key Source Files

| File | Contents |
|---|---|
| `ligsaf_units.py` | `SolvolysisReactor`, `HydrogenolysisReactor`, `PSA`, `CatalystMixer` class definitions |
| `ligsaf_settings.py` | All process parameters, reaction conditions, prices, biomass composition |
| `ligsaf_chemicals.py` | Chemical property definitions for the RCF system |
| `cellulosic_tea.py` | `CellulosicEthanolTEA` class used for integrated system TEA |
| `rcf.py` | RCF-specific helper functions |
