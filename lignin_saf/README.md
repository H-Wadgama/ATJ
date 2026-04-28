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

_Solvolysis reactor hydraulic residence time is 20 minutes (experimentally derived)_: The 20-minute hydraulic residence time (`tau_residence`) comes from experimental RCF data, not from the bed geometry. It determines the dynamic solvent holdup inside each active bed: V_dynamic = Q_per_reactor × tau_residence. The total solvent in the bed also includes the interparticle void space (void_frac × V_biomass), which is always saturated at steady state: V_solvent = V_void + V_dynamic. The BioSTEAM model treats the solvolysis reactor as single-pass flow-through; internal recirculation is not modeled. Mass balances and TEA results are valid because delignification conversion (70%) is held fixed in the reaction specification.

_Solvolysis reactor sizing uses a flow-rate-first model with ideal stagger scheduling_: `methanol_loading_per_pass` (default 5.45 L/kg, in `ligsaf_settings.py`) is a system-level specific flow rate — L of solvent per kg of daily biomass throughput. It sets the total solvent volumetric flow: Q_total = loading × feed / 1000 / 24 [m³/hr]. The number of reactors is determined in three stages: (1) **Ideal stagger**: N_total = round(cycle_time / tau_0), N_working = round(N_total × tau / cycle_time) — this gives perfectly staggered scheduling with exactly N_offline beds always cleaning. (2) **V_max enforcement**: if the resulting vessel volume exceeds V_max_limit (600 m³), N_total is scaled by integer multiples (k = 1, 2, …) preserving the stagger ratio, until each vessel fits. (3) **L/D cap**: if L/D > LD_max (default 5.0, targeting the ideal packed-bed range of 3–5), the superficial velocity is reduced analytically to hit L/D = 5 exactly; pressure drop is recomputed at the adjusted velocity.

At the base-case loading of 5.45 L/kg (tau=3 hr, tau_0=1 hr, tau_res=20 min), this gives N_total=4, N_working=3, V_max ≈ 247 m³ per vessel (well under the 600 m³ limit), D ≈ 3.98 m, L ≈ 19.9 m, and an effective superficial velocity of 0.0034 m/s. A key identity of the ideal stagger formula: the total solvent passing through one bed per batch = solvent_loading [L/kg], exactly matching the L/kg convention used in RCF literature (e.g. Bartling et al. 9 L/kg). The vessel cost is extrapolated outside BioSTEAM's built-in correlation range (L ≤ 40 ft / 12 m) — this is expected for large custom pressure vessels of this scale.





