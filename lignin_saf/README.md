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

## Process areas

The proposed process areas are*:
Area 100: Feed storage and handling 
Area 200: RCF 
Area 300: Products recovery
Area 400: Wastewater treatment
Area 500: Combuster, boiler and turbogenerator
Area 600: Product and feed chemical storage
Area 700: Utilities

*Current design includes Area 200 and Area 300 only


The main process assumptions:
_The loss of carbohydrate retention in biomass pulp post RCF is due to solvent dissolution_: Carbohydrate retention can decrease due to solvent dissolution or  reaction within the solvent [1](https://pubs.rsc.org/en/content/articlelanding/2021/ee/d0ee02870c). Here we assume that the carbohydrates are only solubilized and are not reacting with the solvent. 


_The extraction efficiency of lignin is 100%_: We assume that delignification (i.e. solvolysis + extraction) is only dependent on the solvolysis reaction, and that the extraction efficiency is always 100%.


_Delignification extent is constant throughout residence time of solvolysis_: This assumption can be false since as the reaction proceeds, the content of lignin in biomass reduces and this could lead to concentration hotspots of lignin in the poplar bed. However, we assume that delignication stays constant throughout the biomass bed because the continuous flow of fresh solvent allows for a maximum diffusive flux between the solvent and the biomass [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). 


_Total RCF contact time is 3 hours, split between solvolysis (time on stream) and hydrogenolysis_: The total reported biomass contact time for poplar/methanol RCF in the literature is 3 hours. The solvolysis bed operates as a semi-batch unit: each bed is on-stream for 3 hours (time on stream, TOS) — the period during which biomass is loaded and solvent flows through continuously — then taken offline for 1 hour of cleaning/turnaround. Note that "time on stream" (3 hr, a property of the biomass batch) is distinct from the hydraulic residence time of the solvent (20 min, a property of the solvent flow rate through the bed). The hydrogenolysis reactor runs continuously with a 1-hour residence time. This gives a 4-hour cycle per bed and 6 batches per reactor per day. The kinetic basis for the 3-hour solvolysis time follows from Beckham and Roman-Leshkov's group showing solvolysis is the rate-limiting step [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256).

_Solvolysis reactor hydraulic residence time is 20 minutes_: Solvent flows through each operating bed at a rate that gives a 20-minute hydraulic residence time. The flow rate is defined on the actual fluid volume in the bed: interparticle void space (void_frac × V_biomass) is filled with solvent, so only the solid wood fraction — (1 − void_frac) × V_biomass — displaces solvent. This gives V_solvent = V_max − (1 − void_frac) × V_biomass − V_free ≈ 454 m³ per bed, and Q = V_solvent / tau_residence ≈ 1,362 m³/hr per operating reactor (total across 3 beds: ~4,086 m³/hr). The BioSTEAM model treats the solvolysis reactor as single-pass flow-through; internal recirculation is not modeled. Mass balances and TEA results are valid because delignification conversion (70%) is held fixed in the reaction specification. The system-wide 9 L/kg MeOH:biomass ratio (enforced by the `meoh_water_flow` specification in `ligsaf_system.py`) is a separate constraint and is unaffected by the hydraulic model.

_Solvolysis reactor geometry_: Each bed is sized as D ≈ 6.9 m, L ≈ 15.9 m (L/D ≈ 2.3) based on a superficial velocity of 0.01 m/s and a flow rate Q = V_solvent / tau_residence ≈ 454 m³ / (1/3 hr) ≈ 1,362 m³/hr per operating reactor (total across 3 operating beds: ~4,086 m³/hr). The vessel cost is extrapolated outside BioSTEAM's built-in correlation range (which covers L ≤ 40 ft / 12 m) — this is expected for large custom pressure vessels of this scale.





