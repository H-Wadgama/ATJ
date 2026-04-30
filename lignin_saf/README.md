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

- `rcf_purification.py` — runs the RCF system followed by the EtOAc LLE purification system and prints results. Good for quick iteration on Area 200–300.
- `rcf_4_21_2026` — runs the RCF loop only (no purification).

Both scripts follow the same pattern: set up thermodynamics, call the factory function, simulate, inspect.

## Process areas

The proposed process areas are*:
Area 100: Feed storage and handling 
Area 200: RCF (reductive catalytic fractionation — solvolysis + hydrogenolysis + solvent recovery)
Area 300: Products recovery (EtOAc liquid–liquid extraction → purified lignin oil)
Area 400: Wastewater treatment
Area 500: Combustor, boiler and turbogenerator
Area 600: Product and feed chemical storage
Area 700: Utilities

*Current design includes Area 200 and Area 300 only

## Key source files

| File | Role |
|---|---|
| `ligsaf_system.py` | `create_rcf_system(ins=None)` — Area 200 factory function |
| `ligsaf_purification_system.py` | `create_rcf_oil_purification_system(ins=None)` — Area 300 factory function |
| `ligsaf_units.py` | Custom BioSTEAM unit classes: `SolvolysisReactor`, `HydrogenolysisReactor`, `PSA`, `CatalystMixer` |
| `ligsaf_settings.py` | All process parameters, prices, biomass composition, partition coefficients |
| `ligsaf_chemicals.py` | Chemical property definitions |
| `rcf_purification.py` | Entry-point script: runs Area 200 + Area 300 sequentially |
| `rcf_system.ipynb` | Main interactive notebook for full integrated system analysis |


The main process assumptions:
_The loss of carbohydrate retention in biomass pulp post RCF is due to solvent dissolution_: Carbohydrate retention can decrease due to solvent dissolution or  reaction within the solvent [1](https://pubs.rsc.org/en/content/articlelanding/2021/ee/d0ee02870c). Here we assume that the carbohydrates are only solubilized and are not reacting with the solvent. 


_The extraction efficiency of lignin is 100%_: We assume that delignification (i.e. solvolysis + extraction) is only dependent on the solvolysis reaction, and that the extraction efficiency is always 100%.


_Delignification extent is constant throughout residence time of solvolysis_: This assumption can be false since as the reaction proceeds, the content of lignin in biomass reduces and this could lead to concentration hotspots of lignin in the poplar bed. However, we assume that delignication stays constant throughout the biomass bed because the continuous flow of fresh solvent allows for a maximum diffusive flux between the solvent and the biomass [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). 


_Total RCF solvolysis time on stream is 3 hours_: The solvolysis bed operates as a semi-batch unit: each bed is on-stream for 3 hours (time on stream, TOS) — the period during which biomass is loaded and solvent flows through continuously — then taken offline for 1 hour of cleaning/turnaround. Note that "time on stream" (3 hr, a property of the biomass batch) is distinct from the hydraulic residence time of the solvent (20 min, a property of the solvent flow rate through the bed). This gives a 4-hour cycle per solvolysis bed and 6 batches per reactor per day. The kinetic basis for the 3-hour solvolysis time follows from Beckham and Roman-Leshkov's group showing solvolysis is the rate-limiting step [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). The hydrogenolysis reactor is modelled as a fully continuous fixed-bed reactor; it is sized from a 20-minute (1/3 hr) hydraulic residence time applied to the combined liquid + hydrogen feed volumetric flow.

_Solvolysis reactor hydraulic residence time is 20 minutes (experimentally derived)_: The 20-minute hydraulic residence time (`tau_residence`) comes from experimental RCF data. It determines the solvent flow rate through each active bed. The total solvent volume per bed is V_solvent = V_void × (1 + free_frac), where V_void = void_frac × V_biomass is the interparticle void volume and the free_frac term adds excess solvent beyond the voids to satisfy mass transfer considerations. The flow rate follows directly — Q_per_reactor = V_solvent / tau_residence. The BioSTEAM model treats the solvolysis reactor as single-pass flow-through; internal recirculation is not modeled. Mass balances and TEA results are valid because delignification conversion (70%) is held fixed in the reaction specification.

_Solvolysis reactor sizing uses a volume-first model with ideal stagger scheduling_: Bed geometry drives the design — the solvent loading [L/kg] is a derived output, not a user input. The reactor volume is set by how much biomass fits per batch (from the ideal stagger schedule and bulk density), and the solvent flow rate follows from the solvent volume and residence time (Q = V_solvent / tau_res, where V_solvent = V_void × (1 + free_frac)). The number of reactors is determined in three stages: (1) **Ideal stagger**: N_total = round(cycle_time / tau_0), N_working = round(N_total × tau / cycle_time) — this gives perfectly staggered scheduling with exactly N_offline beds always cleaning. (2) **V_max enforcement**: V_max = V_solid + V_solvent; if this exceeds V_max_limit (600 m³), N_total is scaled by integer multiples (k = 1, 2, …) — each step increases batches_per_day and reduces biomass_per_batch, shrinking V_max until it fits. (3) **L/D cap**: if L/D > LD_max (default 5.0, targeting the ideal packed-bed range of 3–5), the superficial velocity is reduced analytically to hit L/D = 5 exactly; pressure drop is recomputed at the adjusted velocity.

At the base case (tau=3 hr, tau_0=1 hr, tau_res=20 min, void_frac=0.5, free_frac=0.10), this gives N_total=4, N_working=3, V_max ≈ 180 m³ per vessel, D ≈ 3.58 m, L ≈ 17.9 m, Q_total ≈ 851 m³/hr, and a derived solvent loading of ~10.2 L/kg. The vessel cost is extrapolated outside BioSTEAM's built-in correlation range (L ≤ 40 ft / 12 m) — this is expected for large custom pressure vessels of this scale.


_Hydrogenolysis reactor is a continuous fixed-bed reactor sized from hydraulic residence time_: The hydrogenolysis reactor is fully continuous — the NiC catalyst is on-stream indefinitely with no batch cycles. Reactor volume is derived from the total feed volumetric flow (liquid solvent + dissolved lignin + hydrogen gas) and a 20-minute (1/3 hr) hydraulic residence time: V_fluid = Q_total × τ_res, with V_bed = V_fluid / void_frac (void_frac = 0.7) and V_reactor = V_bed / (1 − free_frac) where free_frac = 0.20 is the headspace fraction above the packed bed. The number of parallel reactors is derived automatically as N = ceil(V_reactor / 100 m³). Reactor geometry (D, L) is computed from superficial velocity with L/D enforced within [3, 10]: if the natural L/D falls outside this range the superficial velocity is adjusted analytically to the nearest bound.





