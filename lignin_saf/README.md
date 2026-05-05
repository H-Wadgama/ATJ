# Lignin valorization to SAF through RCF

This is a BioSTEAM model for lignin valorization to SAF currently under development

The baseline model assumes a poplar feedstock (2000 dry metric ton per day) and methanol water as a solvent for RCF. The choice of biomass and solvent primarily due to the availability of literature data

## Setup

**Requirements:** Python 3.10, conda

```bash
conda create -n lignin_saf python=3.10
conda activate lignin_saf
pip install -r lignin_saf/requirements.txt
pip install -e .   # install the local package in editable mode
```

**Post-install patch for flexsolve:** `flexsolve==0.5.9` imports `scipy.differentiate.jacobian`, which requires scipy >= 1.14 but this project pins `scipy==1.11.4`. After installing, patch the file manually:

In `<env>/lib/site-packages/flexsolve/numerical_analysis.py`, replace:
```python
from scipy.differentiate import jacobian
```
with:
```python
try:
    from scipy.differentiate import jacobian
except ImportError:
    jacobian = None
```
Then delete `<env>/lib/site-packages/flexsolve/__pycache__/numerical_analysis.cpython-310.pyc` and restart your kernel.

## Running the model

The main working notebook is `rcf_system.ipynb`. Open it in VS Code or Jupyter and run cells sequentially.

For standalone scripts, two entry-point files are available:

- `rcf_purification.py` — builds and simulates the combined system (Areas 200–500): RCF + EtOAc LLE + WWT + BT. Good for quick iteration on the integrated process.
- `rcf_4_21_2026` — same combined system with an additional TEA call at the end. Used for cost analysis runs.

Both scripts follow the same pattern: set up thermodynamics, call the factory functions, assemble the combined system, simulate.

## Process areas

The proposed process areas are:
Area 100: Feed storage and handling
Area 200: RCF (reductive catalytic fractionation — solvolysis + hydrogenolysis + solvent recovery)
Area 300: Products recovery (EtOAc liquid–liquid extraction → purified lignin oil)
Area 400: Wastewater treatment
Area 500: Combustor, boiler and turbogenerator
Area 600: Product and feed chemical storage
Area 700: Utilities

Current design includes Area 200, 300, 400, and 500. Areas 100, 600, and 700 are not yet modeled.

## Key source files

| File | Role |
|---|---|
| `ligsaf_system.py` | `create_rcf_system(ins=None)` — Area 200 factory function |
| `ligsaf_purification_system.py` | `create_rcf_oil_purification_system(ins=None)` — Area 300 EtOAc LLE factory function |
| `monomer_purification.py` | `create_monomer_purification_system(ins=None)` — Area 300 hexane LLE monomer/dimer separation factory function |
| `ligsaf_utilities_system.py` | `create_rcf_utilities_system()` — Area 400 + 500 factory function; returns `(BT, WWT, gas_mixer)` |
| `ligsaf_units.py` | Custom BioSTEAM unit classes: `SolvolysisReactor`, `HydrogenolysisReactor`, `PSA`, `CatalystMixer` |
| `ligsaf_settings.py` | All process parameters, prices, biomass composition, partition coefficients |
| `ligsaf_chemicals.py` | Chemical property definitions |
| `rcf_purification.py` | Entry-point script: builds and simulates the combined system (Areas 200–500) |
| `rcf_system.ipynb` | Main interactive notebook for full integrated system analysis |

## Utilities system (Area 400 + 500)

`create_rcf_utilities_system()` in `ligsaf_utilities_system.py` returns a `(BT, WWT)` tuple. Call it after creating all upstream systems (so the named streams exist on the flowsheet) but before assembling the combined system.

```python
from lignin_saf.ligsaf_utilities_system import create_rcf_utilities_system

rcf_system               = create_rcf_system(ins=poplar_in)
rcf_oil_purification_sys = create_rcf_oil_purification_system(ins=F.RCF_Oil)
BT, WWT, gas_mixer       = create_rcf_utilities_system()

rcf_combined_system = bst.System(
    'Combined_RCF_System',
    path=(rcf_system, rcf_oil_purification_sys, WWT),
    facilities=[gas_mixer, BT],   # gas_mixer must precede BT
)
rcf_combined_system.simulate()
```

**BT** (`bst.facilities.BoilerTurbogenerator`, `fuel_price=0.2612`) receives:
- `ins[0]` — WWT sludge (`WWT.outs[1]`, dewatered biological sludge from S603)
- `ins[1]` — `gas_mixer` outlet: PSA purge gas + WWT biogas combined
- `ins[2–6]` — makeup water, natural gas, lime, boiler chemicals, air (auto-set by BioSTEAM)

**WWT** (`bst.create_conventional_wastewater_treatment_system`, Humbird 2011 configuration) receives:
- `F.WW_10` — aqueous raffinate from EtOAc LLE (Area 300)
- `F.WastePulp` — decanter water bleed (Area 300); predominantly water, 5% EtOAc
- `F.RCF_WW` — combined RCF wastewater (Area 200)

The internal `SludgeCentrifuge` (S603) is patched after creation in `ligsaf_utilities_system.py`:

```python
for unit in WWT.units:
    if hasattr(unit, 'strict_moisture_content'):
        unit.strict_moisture_content = False   # ← change here to re-enable strict mode
    # To also change the target moisture fraction (default 0.79):
    # if hasattr(unit, 'moisture_content'):
    #     unit.moisture_content = 0.6
```

The Humbird 79% moisture target was calibrated for cellulosic-ethanol organic loadings. RCF wastewater has a different organic profile: `Acetate` is in `non_digestables` and passes through the bioreactors unreacted, accumulating in the S603 feed and reducing the available free water. `G_Dimer`/`S_Oligomer`/`G_Oligomer` now have molecular formulas (added to `ligsaf_chemicals.py`) and are therefore included in `get_digestable_organic_chemicals`, but in the current process configuration all three are fully captured in `Purified_RCF_Oil` and do not reach WWT. The primary remaining cause of the infeasibility is the Acetate accumulation. Set `strict_moisture_content=True` once WWT stream chemistry is validated against experimental RCF wastewater data.

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
| `S_Oligomer` | `C33H40O11` | `37.5 O2 + S_Oligomer → 33 CO2 + 20 Water` | resolved — explicit MW removed; MW now formula-derived (~612.67 Da) |
| `G_Oligomer` | `C31H40O8` | `37 O2 + G_Oligomer → 20 Water + 31 CO2` | correct |
| `Propylguaiacol` | `C10H14O2` | combusts correctly | correct |
| `Propylsyringol` | `C11H16O3` | combusts correctly | correct |
| `Syringaresinol` | `C22H26O8` | combusts correctly | correct |

**`S_Oligomer` MW — resolved:** The explicit `MW=628.67` parameter was removed; `S_Oligomer` is now defined with `formula='C33H40O11'` only, so thermosteam derives MW as ~612.67 Da and BT combustion is clean (no `Ash` term). **Open question:** confirm that `C33H40O11` (612.67 Da) is the correct molecular identity against Bartling et al. Fig S8 — if the correct structure has MW 628.67, change the formula to `C33H40O12`.

**Note on current process flows:** In the current configuration, `G_Dimer`, `S_Oligomer`, and `G_Oligomer` are fully recovered in `Purified_RCF_Oil` via EtOAc LLE and do not reach BT (`BT.ins[0]` and `BT.ins[1]` show zero flow for all three after simulation). The combustion reactions are defined as a safeguard in case any oligomers appear in a waste stream in the future.

**Adding more wastewater or fuel streams in the future:**

For WWT, extend the `ins` tuple in `create_rcf_utilities_system()`:
```python
WWT = bst.create_conventional_wastewater_treatment_system(
    'WWT', ins=(F.WW_10, F.WastePulp, F.RCF_WW, F.WW_Etoh, ...)
)
```

For BT, each combustion slot accepts one stream. Combine multiple feeds with a `bst.Mixer` first, then wire the mixer outlet to `BT.ins[0]` or `BT.ins[1]`, and add the mixers to `facilities` before BT:
```python
solid_mixer = bst.Mixer('MIX_BT_solid', ins=(F.Stream1, F.Stream2))
BT.ins[0] = solid_mixer.outs[0]
# in combined system: facilities=[solid_mixer, BT]
```


The main process assumptions:
_The loss of carbohydrate retention in biomass pulp post RCF is due to solvent dissolution_: Carbohydrate retention can decrease due to solvent dissolution or  reaction within the solvent [1](https://pubs.rsc.org/en/content/articlelanding/2021/ee/d0ee02870c). Here we assume that the carbohydrates are only solubilized and are not reacting with the solvent. 


_The extraction efficiency of lignin is 100%_: We assume that delignification (i.e. solvolysis + extraction) is only dependent on the solvolysis reaction, and that the extraction efficiency is always 100%.


_Delignification extent is constant throughout residence time of solvolysis_: This assumption can be false since as the reaction proceeds, the content of lignin in biomass reduces and this could lead to concentration hotspots of lignin in the poplar bed. However, we assume that delignication stays constant throughout the biomass bed because the continuous flow of fresh solvent allows for a maximum diffusive flux between the solvent and the biomass [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). 


_Total RCF solvolysis time on stream is 3 hours_: The solvolysis bed operates as a semi-batch unit: each bed is on-stream for 3 hours (time on stream, TOS) — the period during which biomass is loaded and solvent flows through continuously — then taken offline for 1 hour of cleaning/turnaround. Note that "time on stream" (3 hr, a property of the biomass batch) is distinct from the hydraulic residence time of the solvent (20 min, a property of the solvent flow rate through the bed). This gives a 4-hour cycle per solvolysis bed and 6 batches per reactor per day. The kinetic basis for the 3-hour solvolysis time follows from Beckham and Roman-Leshkov's group showing solvolysis is the rate-limiting step [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). The hydrogenolysis reactor is modelled as a fully continuous fixed-bed reactor; it is sized from a 20-minute (1/3 hr) hydraulic residence time applied to the combined liquid + hydrogen feed volumetric flow.

_Solvolysis reactor hydraulic residence time is 20 minutes (experimentally derived)_: The 20-minute hydraulic residence time (`tau_residence`) comes from experimental RCF data. It determines the solvent flow rate through each active bed. The total solvent volume per bed is V_solvent = V_void × (1 + free_frac), where V_void = void_frac × V_biomass is the interparticle void volume and the free_frac term adds excess solvent beyond the voids to satisfy mass transfer considerations. The flow rate follows directly — Q_per_reactor = V_solvent / tau_residence. The BioSTEAM model treats the solvolysis reactor as single-pass flow-through; internal recirculation is not modeled. Mass balances and TEA results are valid because delignification conversion (70%) is held fixed in the reaction specification.

_Solvolysis reactor sizing uses a volume-first model with ideal stagger scheduling_: Bed geometry drives the design — the solvent loading [L/kg] is a derived output, not a user input. The reactor volume is set by how much biomass fits per batch (from the ideal stagger schedule and bulk density), and the solvent flow rate follows from the solvent volume and residence time (Q = V_solvent / tau_res, where V_solvent = V_void × (1 + free_frac)). The number of reactors is determined in three stages: (1) **Ideal stagger**: N_total = round(cycle_time / tau_0), N_working = round(N_total × tau / cycle_time) — this gives perfectly staggered scheduling with exactly N_offline beds always cleaning. (2) **V_max enforcement**: V_max = V_solid + V_solvent; if this exceeds V_max_limit (600 m³), N_total is scaled by integer multiples (k = 1, 2, …) — each step increases batches_per_day and reduces biomass_per_batch, shrinking V_max until it fits. (3) **L/D cap**: if L/D > LD_max (default 5.0, targeting the ideal packed-bed range of 3–5), the superficial velocity is reduced analytically to hit L/D = 5 exactly; pressure drop is recomputed at the adjusted velocity.

At the base case (tau=3 hr, tau_0=1 hr, tau_res=20 min, void_frac=0.5, free_frac=0.10), this gives N_total=4, N_working=3, V_max ≈ 180 m³ per vessel, D ≈ 3.58 m, L ≈ 17.9 m, Q_total ≈ 851 m³/hr, and a derived solvent loading of ~10.2 L/kg. The vessel cost is extrapolated outside BioSTEAM's built-in correlation range (L ≤ 40 ft / 12 m) — this is expected for large custom pressure vessels of this scale.


_Hydrogenolysis reactor is a continuous fixed-bed reactor sized from hydraulic residence time_: The hydrogenolysis reactor is fully continuous — the NiC catalyst is on-stream indefinitely with no batch cycles. Reactor volume is derived from the total feed volumetric flow (liquid solvent + dissolved lignin + hydrogen gas) and a 20-minute (1/3 hr) hydraulic residence time: V_fluid = Q_total × τ_res, with V_bed = V_fluid / void_frac (void_frac = 0.7) and V_reactor = V_bed / (1 − free_frac) where free_frac = 0.20 is the headspace fraction above the packed bed. The number of parallel reactors is derived automatically as N = ceil(V_reactor / 100 m³). Reactor geometry (D, L) is computed from superficial velocity with L/D enforced within [3, 10]: if the natural L/D falls outside this range the superficial velocity is adjusted analytically to the nearest bound.





