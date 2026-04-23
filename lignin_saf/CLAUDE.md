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
| `meoh_in` | Fresh methanol make-up; system-level loading fixed at 9 L/kg dry biomass by `meoh_water_flow` spec | Liquid |
| `hydrogen_in` | Fresh H₂, 0.054 kg/kg dry biomass (from PEM electrolysis) | Gas, 80°C, 30 bar |

## Unit Operations

| Unit ID | Variable Name | Type | Function | Key Parameters |
|---|---|---|---|---|
| MIX100 | `meoh_h2o_mix` | Mixer | Mix fresh MeOH + MeOH recycle | — |
| PUMP101 | `meoh_pump` | Pump | Pressurize MeOH | P = 60 bar |
| HX102 | `meoh_heater` | HXutility | Heat MeOH | T = 200°C, rigorous VLE |
| RCF103_S | `solvolysis_reactor` | `SolvolysisReactor` (custom) | Solvolysis: delignify biomass; produce pulp + liquor | T=200°C, P=60 bar, τ_s=3 hr (time on stream), τ_0=1 hr (cleaning), τ_res=20 min, void_frac=0.5, v=0.01 m/s, solvent_loading=5.45 L/kg, V_max_limit=600 m³ |
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
| Solvolysis T / P / τ | 200°C / 60 bar / 3 hr (time on stream) + 20 min hydraulic RT |
| Hydrogenolysis T / P / τ | 200°C / 60 bar / 1 hr |
| Per-pass solvent loading (`methanol_loading_per_pass`) | 5.45 L/kg dry biomass — drives reactor SIZING (N_total and V_max computed from this) |
| Max vessel volume (`V_max_limit`) | 600 m³ — hard upper bound; N_total is the minimum number of reactors such that V_max ≤ this limit |
| System-level MeOH loading (`methanol_to_biomass`) | 9 L/kg dry biomass — enforces total MeOH mass balance flow in `meoh_water_flow` spec; independent of reactor sizing |
| H₂:biomass ratio | 0.054 kg H₂/kg dry biomass |
| NiC catalyst loading | 0.1 kg/kg dry biomass |
| Lignin delignification | 70% → RCF oil |
| Cellulose retention in pulp | 90% |
| RCF oil composition | 50% monomers / 25% dimers / 25% oligomers |
| Operating basis | 330 days/yr × 24 hr/day |
| CEPCI basis | 541.7 (2016 USD) |

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
