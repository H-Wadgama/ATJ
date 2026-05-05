# lignin_saf/CLAUDE.md

Context for the RCF system and downstream purification system.

## rcf_system Overview

RCF (Reductive Catalytic Fractionation) loop that processes poplar biomass into crude lignin oil and a carbohydrate pulp. Two recycle streams: methanol solvent and hydrogen.

```python
rcf_system = bst.System('RCF_System',
    path=(meoh_h2o_mix, meoh_pump, meoh_heater, solvolysis_reactor, h2_mixer, h2_pre_heat,
          hydrogenolysis_reactor, R102, pre_psa_pump, pre_psa_flash, pre_psa_heater,
          psa_system, h2_pump, crude_distillation, meoh_purifier_col, meoh_mixer, cooler_2,
          water_remover, pulp_purifier, wastewater_mixer, catalyst_stream),
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
| RCF106_H | `hydrogenolysis_reactor` | `HydrogenolysisReactor` (custom) | Hydrogenolyze lignin oil to C5–C15 monomers; continuous fixed-bed | T=200°C, P=60 bar, τ_res=1/3 hr (20 min), void_frac=0.7, free_frac=0.20, V_max_limit=100 m³, LD∈[3,10]; N_reactors derived from sizing |
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
| D601 | `pulp_purifier` | Flash | Flash-dry `Wet_Pulp`; remove residual MeOH/water before `Carbohydrate_Pulp` exits | T=400 K, P=1 atm; `outs[1]` = `Carbohydrate_Pulp`; `outs[0]` vapor currently unrecovered (future: route to WWT or solvent recovery) |
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
| `RCF_Oil` | `water_remover` (FLASH118) | Crude lignin oil: 50% monomers, 25% dimers, 25% oligomers; C5–C15 range | → `rcf_oil_purification_sys` (EtOAc LLE) |
| `Carbohydrate_Pulp` | `pulp_purifier` (D601) | Cellulose-rich pulp, 90% cellulose retention; residual MeOH/water removed | → `etoh_system` (cellulosic ethanol) |
| `RCF_WW` | `wastewater_mixer` | Combined wastewater (light organics, unconverted solvent) | → wastewater treatment |
| `Purge_Light_Gases` | `psa_system` (PSA111) | Non-H₂ light gases | purged / flared |

## Open implementation items

**`pulp_purifier` vapor outlet (D601, `outs[0]`):** The flash overhead contains evaporated MeOH and water stripped from the biomass pulp. It is currently unconnected — the solvent is not recovered. A future implementation should route this stream to `wastewater_mixer` (for WWT) or to a dedicated solvent recovery unit. When doing so, move `pulp_purifier` before `wastewater_mixer` in the path and add `pulp_purifier.outs[0]` to `wastewater_mixer.ins`.

**`SolvolysisReactor._run()` solvent retention — hardcoded to `('Methanol', 'Water')`:** The loop that deposits a small fraction of solvent into the biomass stream is:
```python
for chem_id in ('Methanol', 'Water'):
    used_biomass.imass[chem_id] = used_solvent.imass[chem_id] * 0.005
```
This was restricted from a generic `for chem in solvent.chemicals` loop (which caused trace gases — CH4, CO, H2 — to accumulate in the pulp via the MeOH recycle) to explicitly name only the solvent components. If the solvent system is changed in the future (e.g. to ethanol/water, THF/water), this tuple must be updated to match the new solvent identity.

## Process Conditions (from ligsaf_settings.py)

| Parameter | Value |
|---|---|
| Solvolysis T / P / τ | 200°C / 60 bar / 3 hr (time on stream) + 1/3 hr hydraulic RT |
| Hydrogenolysis T / P / τ_res | 200°C / 60 bar / 20 min (1/3 hr hydraulic RT); continuous, catalyst on-stream indefinitely |
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

## HydrogenolysisReactor Sizing Model

`_size_bed()` in `ligsaf_units.py` uses a **continuous flow** approach. The catalyst is on-stream indefinitely; reactor volume is derived from the hydraulic residence time and total feed volumetric flow.

**Volume accounting:**
```
Q_total          = ins[0].F_vol + ins[1].F_vol          # liquid solvent/lignin + H₂ gas [m³/hr]
V_fluid          = Q_total × tau_residence               # fluid holdup in bed voids [m³]
V_bed            = V_fluid / void_frac                   # packed bed volume (voids + catalyst) [m³]
V_reactor_total  = V_bed / (1 − free_frac)               # add 20% free headspace above bed [m³]
N_reactors       = ceil(V_reactor_total / V_max_limit)   # integer parallel vessels
V_per_reactor    = V_reactor_total / N_reactors
Q_per_reactor    = Q_total / N_reactors
```

**L/D enforcement — [LD_min, LD_max]:**
Cross-section A and geometry are derived from `superficial_velocity`. If the natural L/D falls outside [3, 10], A is adjusted analytically to the nearest bound and `self.superficial_velocity` is updated:
```
A = (V_per_reactor × √π / (2 × LD_target))^(2/3)
u = Q_per_reactor / (A × 3600)
```

**Default parameters:**

| Parameter | Default | Meaning |
|---|---|---|
| `tau_residence` | 1/3 hr (20 min) | Hydraulic RT — determines V_fluid from Q |
| `void_frac` | 0.7 | Catalyst bed void fraction (fluid-occupied fraction) |
| `free_frac` | 0.20 | Free headspace as fraction of total reactor volume |
| `V_max_limit` | 100 m³ | Hard upper bound per vessel; N_reactors scales up to satisfy |
| `LD_min` / `LD_max` | 3.0 / 10.0 | L/D bounds; u adjusted analytically at either limit |

**Design results reported:** `Reactor volume`, `Total volume`, `Residence time`, `Number of reactors`, `Diameter`, `Length`, `Duty`, `Catalyst loading cost`.

## Downstream Systems (outside rcf_system)

- `rcf_oil_purification_sys` — built by `create_rcf_oil_purification_system()` in `ligsaf_purification_system.py`; EtOAc LLE on `RCF_Oil` → `Purified_RCF_Oil`
- `etoh_system` — cellulosic ethanol from `biorefineries.cellulosic`, fed by `Carbohydrate_Pulp`
- `monomer_purification_sys` — hexane LLE for monomer/dimer separation; built by `create_monomer_purification_system()` in `monomer_purification.py`; K-values are placeholders (K=2.0 for all monomers) pending experimental hexane/water LLE data
- `combined_sys` — full integrated system wrapping all of the above (330 days/yr × 24 hr)
- `combined_sys_hx` — same with `HeatExchangerNetwork` (T_min_app=10°C)

## RCF Oil Purification System

Built by `create_rcf_oil_purification_system(ins=None)` in `ligsaf_purification_system.py`. Accepts the crude `RCF_Oil` stream from FLASH118 and recovers it as `Purified_RCF_Oil` via ethyl acetate liquid–liquid extraction.

**Import pattern:**
```python
from lignin_saf.ligsaf_purification_system import create_rcf_oil_purification_system
rcf_oil_purification_sys = create_rcf_oil_purification_system(ins=F.RCF_Oil)
rcf_oil_purification_sys.simulate()
```
If `ins=None`, `F.RCF_Oil` is grabbed from the main flowsheet — `rcf_system` must be simulated first.

**Unit operations:**

| Unit ID | Variable Name | Type | Function | Key Parameters |
|---|---|---|---|---|
| MIX200 | `solvent_mixer` | Mixer | Mix fresh EtOAc makeup + solvent recycle | spec sets makeup = total required − recycle |
| LLE200 | `lle_column` | MultiStageMixerSettlers | 3-stage countercurrent EtOAc/water LLE | N_stages=3, feed_stages=(0, −1); lignin products partition to EtOAc extract |
| FLASH201 | `oil_flash` | Flash | Evaporate EtOAc overhead; **`Purified_RCF_Oil`** exits as bottoms | T=400 K, P=1 atm |
| HX202 | `solvent_cooler` | HXutility | Condense EtOAc vapor | V=0, rigorous |
| CENT203 | `solvent_decanter` | LiquidsSplitCentrifuge | Split EtOAc from water; EtOAc → `solvent_recycle` | EtOAc split = 0.95 |

**Recycle:** `solvent_recycle` (CENT203 → MIX200). Fresh EtOAc makeup computed by the `adjust_fresh_solvent_flow` spec on every iteration.

**Output streams:**

| Stream | Source | Description |
|---|---|---|
| `Purified_RCF_Oil` | FLASH201 bottoms | Concentrated lignin oil (monomers + dimers + oligomers), EtOAc removed |
| `WW_10` | LLE200 raffinate | Aqueous phase from LLE; to WWT |
| `WastePulp` | CENT203 second outlet | Water/EtOAc bleed from decanter; to WWT |

**Parameters (all in `ligsaf_settings.py` → `etoac_purification` dict):**

| Parameter | Value | Notes |
|---|---|---|
| `solvent_to_crude_ratio` | 1.1 L/kg | EtOAc volume per kg crude RCF oil; from 10.1039/D2RE00275B |
| `etoac_h2o_ratio` | 1.0 v/v | EtOAc : water ratio in solvent; from D2RE00275B |
| `N_stages` | 3 | Extraction stages; from ACS SCE 2024, 12, 12919 |
| `EtOAc_recycle_split` | 0.95 | Fraction of EtOAc recovered in centrifuge |
| `oil_flash_T` | 400 K | Flash temperature to evaporate EtOAc |
| `oil_flash_P` | 101325 Pa | Flash pressure |

**Partition coefficients (`etoac_partition_IDs` / `etoac_partition_K` in `ligsaf_settings.py`):**

K = c_extract (EtOAc-rich) / c_raffinate (water-rich). All values are placeholders pending experimental LLE data.

| Component | K |
|---|---|
| Water | 0.01 (strongly prefers aqueous phase) |
| Propylguaiacol | 200 |
| Propylsyringol | 200 |
| Syringaresinol | 500 |
| G_Dimer | 109 |
| S_Oligomer | 200 |
| G_Oligomer | 200 |

## Monomer Purification System

Built by `create_monomer_purification_system(ins=None)` in `monomer_purification.py`. Accepts `Purified_RCF_Oil` (bottoms of FLASH201) and separates monomers/dimers from oligomers via hexane liquid–liquid extraction.

**Import pattern:**
```python
from lignin_saf.monomer_purification import create_monomer_purification_system
monomer_purification_sys = create_monomer_purification_system(ins=F.Purified_RCF_Oil)
monomer_purification_sys.simulate()
```
If `ins=None`, `F.Purified_RCF_Oil` is taken from the main flowsheet — `rcf_oil_purification_sys` must be simulated first.

**Unit operations:**

| Unit ID | Variable Name | Type | Function | Key Parameters |
|---|---|---|---|---|
| MIX300 | `hexane_mixer` | Mixer | Mix fresh hexane makeup + hexane recycle | spec sets makeup = total required − recycle |
| LLE300 | `lle_column` | MultiStageMixerSettlers | 3-stage countercurrent hexane/water LLE | N_stages=3, feed_stages=(0, −1); monomers/dimers partition to hexane extract; S_Oligomer/G_Oligomer unlisted → stay in raffinate |
| FLASH301 | `monomer_flash` | Flash | Evaporate hexane overhead; **`RCF_Monomers`** exits as bottoms | T=400 K, P=1 atm |
| HX302 | `solvent_cooler` | HXutility | Condense hexane vapor | V=0, rigorous |
| CENT303 | `solvent_decanter` | LiquidsSplitCentrifuge | Split hexane from water; hexane → `hexane_recycle` | Hexane split = 0.95 |
| FLASH304 | `raffinate_flash` | Flash | Flash LLE raffinate; **`RCF_Oligomers`** exits as bottoms | T=400 K, P=1 atm |

**Recycle:** `hexane_recycle` (CENT303 → MIX300). Fresh hexane makeup computed by the `adjust_fresh_solvent_flow` spec on every iteration.

**Output streams:**

| Stream | Source | Description |
|---|---|---|
| `RCF_Monomers` | FLASH301 bottoms | Monomers and dimers (Propylguaiacol, Propylsyringol, Syringaresinol, G_Dimer); hexane removed |
| `RCF_Oligomers` | FLASH304 bottoms | Oligomers (S_Oligomer, G_Oligomer) recovered from aqueous raffinate |
| `WW_11` | CENT303 second outlet | Water bleed from hexane decanter; to WWT |
| `WW_21` | FLASH304 overhead | Water overhead from raffinate flash; to WWT |

**Parameters (all in `ligsaf_settings.py` → `hexane_purification` dict):**

| Parameter | Value | Notes |
|---|---|---|
| `solvent_to_oil_ratio` | 5 kg/kg | Hexane mass per kg purified RCF oil |
| `water_hexane_ratio` | 1.0 v/v | Water : hexane volume ratio in solvent feed |
| `N_stages` | 3 | Extraction stages |
| `hexane_recycle_split` | 0.95 | Fraction of hexane recovered in centrifuge |
| `oil_flash_T` | 400 K | Flash T to evaporate hexane from monomer extract |
| `raffinate_flash_T` | 400 K | Flash T to separate oligomers from raffinate water |

**Partition coefficients (`hexane_partition_IDs` / `hexane_partition_K` in `ligsaf_settings.py`):**

K = c_extract (hexane-rich) / c_raffinate (water-rich). All values are placeholders. `S_Oligomer` and `G_Oligomer` are not listed — unlisted components default to the aqueous raffinate in `MultiStageMixerSettlers`.

| Component | K |
|---|---|
| Water | 0.01 (strongly prefers aqueous phase) |
| Propylguaiacol | 2.0 (placeholder) |
| Propylsyringol | 2.0 (placeholder) |
| Syringaresinol | 2.0 (placeholder) |
| G_Dimer | 2.0 (placeholder) |

## Utilities System (Area 400 + 500)

Built by `create_rcf_utilities_system()` in `ligsaf_utilities_system.py`. Returns `(BT, WWT, gas_mixer)`. Call after all upstream factory functions so the required named streams exist on the flowsheet.

**Assembly pattern:**
```python
rcf_system               = create_rcf_system(ins=poplar_in)
rcf_oil_purification_sys = create_rcf_oil_purification_system(ins=F.RCF_Oil)
BT, WWT, gas_mixer       = create_rcf_utilities_system()

rcf_combined_system = bst.System(
    'Combined_RCF_System',
    path=(rcf_system, rcf_oil_purification_sys, WWT),  # WWT is a System → path
    facilities=[gas_mixer, BT],                         # gas_mixer must precede BT
)
rcf_combined_system.simulate()
```

**BT** — `bst.facilities.BoilerTurbogenerator('BT', fuel_price=0.2612)`:

| Slot | Contents |
|---|---|
| `ins[0]` | WWT sludge (`WWT.outs[1]`) — dewatered biological sludge from S603 |
| `ins[1]` | `gas_mixer` outlet — PSA purge gas + WWT biogas combined |
| `ins[2–6]` | Makeup water, natural gas, lime, boiler chems, air (auto-set) |

**`gas_mixer`** — `bst.Mixer('MIX_BT_gas', ins=(F.Purge_Light_Gases, WWT.outs[0]))`:
Combines PSA purge gas and WWT biogas before the BT gas combustion slot. Listed before `BT` in `facilities` so its outlet is populated before BT consumes it.

**WWT** — `bst.create_conventional_wastewater_treatment_system('WWT', ...)` (Humbird 2011):

| Inlet stream | Source |
|---|---|
| `F.WW_10` | LLE200 raffinate (Area 300) — predominantly water |
| `F.WastePulp` | CENT203 decanter bleed (Area 300) — predominantly water + 5% EtOAc |
| `F.RCF_WW` | Combined RCF wastewater (Area 200) |

Note: `WastePulp` is predominantly water. In `CENT203`, `split={'EthylAcetate': 0.95}` means Water defaults to split=0.0 (all water → `outs[1]` = WastePulp). Only 5% of EtOAc ends up in WastePulp.

The internal `SludgeCentrifuge` (S603) is patched after WWT creation in `create_rcf_utilities_system()` (`ligsaf_utilities_system.py`):

```python
for unit in WWT.units:
    if hasattr(unit, 'strict_moisture_content'):
        unit.strict_moisture_content = False   # ← toggle here
    # To adjust the target moisture fraction (default 0.79 from Humbird):
    # if hasattr(unit, 'moisture_content'):
    #     unit.moisture_content = 0.6
```

**Why this is needed:** The Humbird 79% moisture target was calibrated for cellulosic-ethanol organic loadings. RCF wastewater has a different organic profile:
- `Acetate` is in `non_digestables` → passes through the bioreactors unreacted and accumulates in the S603 feed, reducing available free water
- `G_Dimer`, `S_Oligomer`, `G_Oligomer` now have molecular formulas in `ligsaf_chemicals.py` and are included in `get_digestable_organic_chemicals`, but in the current configuration all three are fully captured in `Purified_RCF_Oil` and do not reach WWT

The primary cause of the infeasibility is Acetate accumulation. `strict_moisture_content=False` lets the centrifuge use whatever water is available without raising `InfeasibleRegion`. Set it back to `True` once WWT stream chemistry is validated against experimental RCF wastewater data.

**WWT outputs:**

| Slot | Stream | Description | Routed to |
|---|---|---|---|
| `WWT.outs[0]` | biogas | CH4 + CO2 from anaerobic digestion | `gas_mixer` → `BT.ins[1]` |
| `WWT.outs[1]` | sludge | dewatered biological sludge from S603 | `BT.ins[0]` |
| `WWT.outs[2]` | RO treated water | clean permeate from reverse osmosis | unconnected |
| `WWT.outs[3]` | brine | RO reject | unconnected |

**BT combustion reactions — current status:**

BioSTEAM's BT auto-derives combustion reactions from a chemical's elemental formula (`CₓHᵧOᵤ + O₂ → CO₂ + H₂O`). Formulas have been added to all six RCF lignin chemicals in `ligsaf_chemicals.py`; BT now generates combustion reactions for all of them:

| Chemical | Formula | BT combustion reaction | Status |
|---|---|---|---|
| `G_Dimer` | `C20H26O6` | `23.5 O2 + G_Dimer → 13 Water + 20 CO2` | correct |
| `S_Oligomer` | `C33H40O11` | `37.5 O2 + S_Oligomer → 33 CO2 + 20 Water` | resolved — explicit MW removed; MW formula-derived (~612.67 Da) |
| `G_Oligomer` | `C31H40O8` | `37 O2 + G_Oligomer → 20 Water + 31 CO2` | correct |
| `Propylguaiacol` | `C10H14O2` | combusts correctly | correct |
| `Propylsyringol` | `C11H16O3` | combusts correctly | correct |
| `Syringaresinol` | `C22H26O8` | combusts correctly | correct |

**`S_Oligomer` MW — resolved:** The explicit `MW=628.67` was removed; `S_Oligomer` is now defined with `formula='C33H40O11'` only, so thermosteam derives MW as ~612.67 Da and BT combustion produces no `Ash`. **Open question:** verify that `C33H40O11` is the correct structure against Bartling et al. Fig S8 — if the correct MW is 628.67, change the formula to `C33H40O12`.

**Note on current process flows:** In the current configuration, `G_Dimer`, `S_Oligomer`, and `G_Oligomer` are fully recovered in `Purified_RCF_Oil` via EtOAc LLE and do not reach BT (`BT.ins[0]` and `BT.ins[1]` show zero flow for all three after simulation). The combustion reactions are defined as a safeguard in case any oligomers appear in a waste stream in the future.

**Extending BT and WWT with more streams:**
- WWT: add streams to the `ins` tuple inside `create_rcf_utilities_system()`.
- BT: each combustion slot takes one stream; use a `bst.Mixer` to combine multiple feeds, add the mixer to `facilities` before BT, and wire `BT.ins[0]` or `BT.ins[1]` to the mixer outlet.

## Key Source Files

| File | Contents |
|---|---|
| `ligsaf_units.py` | `SolvolysisReactor`, `HydrogenolysisReactor`, `PSA`, `CatalystMixer` class definitions |
| `ligsaf_settings.py` | All process parameters, reaction conditions, prices, biomass composition, EtOAc and hexane LLE partition data |
| `ligsaf_system.py` | `create_rcf_system(ins=None)` — Area 200 factory function |
| `ligsaf_purification_system.py` | `create_rcf_oil_purification_system(ins=None)` — Area 300 EtOAc LLE factory function |
| `monomer_purification.py` | `create_monomer_purification_system(ins=None)` — Area 300 hexane LLE monomer/dimer separation factory function |
| `ligsaf_utilities_system.py` | `create_rcf_utilities_system()` — Area 400 + 500; returns `(BT, WWT, gas_mixer)` |
| `ligsaf_chemicals.py` | Chemical property definitions for the RCF system |
| `cellulosic_tea.py` | `CellulosicEthanolTEA` class used for integrated system TEA |
| `rcf_purification.py` | Entry-point script: builds and simulates the combined system (Areas 200–500) |
| `rcf.py` | RCF-specific helper functions |
