# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

This project uses a conda environment named `pyfuel` (Python 3.10):

```bash
conda activate pyfuel
pip install -r requirements.txt
pip install -e .   # install package in editable mode for development
```

Key pinned dependencies: `biosteam==2.47.0`, `qsdsan==1.4.1`, `numba==0.60.0`, `numpy==1.26.4`, `scipy==1.11.4`.

**Post-install patch required for flexsolve:** `flexsolve>=0.5.9` imports `scipy.differentiate.jacobian` which only exists in scipy>=1.14, conflicting with the pinned `scipy==1.11.4`. After installing, patch the installed file:

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
Then delete `<env>/lib/site-packages/flexsolve/__pycache__/numerical_analysis.cpython-310.pyc`.

**graphviz is required** for `system.diagram()` and `system.save_report()`. Install via conda (not pip):
```bash
conda install graphviz
```
Without graphviz, `save_report` will produce an empty Excel file with no stream or cost data.

Each sub-project also has its own `requirements.txt`:
- `lignin_saf/requirements.txt` — dependencies for the lignin SAF model only (excludes `qsdsan`)

## Running the Models

**ATJ baseline simulation (CLI):**
```bash
python -m atj_saf.main
```
This simulates the system and prints the Minimum Jet Selling Price (MJSP) in $/gal.

**Interactive analysis** is done primarily through Jupyter notebooks:
- `atj_saf/atj_bst/etj_bst_system.ipynb` — BioSTEAM-native ATJ/ETJ system with uncertainty, sensitivity, and contour plot analysis
- `lignin_saf/rcf_system.ipynb` — Integrated RCF + cellulosic ethanol system (main active notebook)

**RCF system as a standalone script:**
- `lignin_saf/rcf_4_21_2026` — Thin entry-point script for the RCF loop. Sets up thermo, defines the Poplar feedstock stream, then calls `create_rcf_system()` from `ligsaf_system.py`. Use this for quick iteration on the RCF loop in isolation.

```python
# Pattern used in rcf_4_21_2026 — mirrors cellulosic_ethanol_legacy.py
chems = create_chemicals()
bst.settings.set_thermo(chems)
bst.settings.CEPCI = 541.7
chems.define_group('Poplar', ...)   # must be defined before creating Poplar stream
poplar_in = bst.Stream('Poplar_In', Poplar=..., Water=..., phase='l', units='kg/d')
rcf_system = create_rcf_system(ins=poplar_in)
rcf_system.simulate()
rcf_system.show()
```

## Architecture Overview

The repo contains two independent SAF process models, each with its own chemicals, units, systems, and TEA:

### 1. `atj_saf/` — Alcohol-to-Jet (ATJ) SAF

Three-step conversion: **ethanol → ethylene (dehydration) → olefins (oligomerization) → SAF (hydrogenation)**. Products are renewable naphtha (C4–C6), SAF (C10), and renewable diesel (C18).

Two sub-implementations exist:

| Sub-package | Framework | Entry point |
|---|---|---|
| `atj_baseline/` | QSDsan (`qs.SanStream`, `qs.System`) | `atj_saf/main.py` → `systems.py` |
| `atj_bst/` | Pure BioSTEAM (`bst.Stream`, `bst.System`) + `biorefineries` | `etj_bst_system.ipynb` |

**Key files in `atj_saf/atj_baseline/`:**
- `systems.py` — `create_atj_system()` builds the full unit-by-unit flowsheet; `perform_tea()` sets up TEA
- `atj_chemicals.py` — chemical property definitions
- `units/catalytic_reactors.py` — custom `AdiabaticReactor` and `IsothermalReactor`
- `units/PSA.py` — pressure swing adsorption for H₂ recovery
- `units/storage_tanks.py` — ethanol, hydrogen, and hydrocarbon product tanks
- `data/prices.py` — all feedstock and product prices
- `data/catalytic_reaction_data.py` — reaction conversions and selectivities
- `tea_saf.py` / `tea_abstract.py` — `ConventionalEthanolTEA` class

**Key files in `atj_saf/atj_bst/`:**
- `etj_system.py` — `create_etj_system()` (BioSTEAM version)
- `etj_settings.py` — all process parameters and prices
- `atj_bst_units.py` — custom unit operations
- `atj_bst_tea_saf.py` / `atj_bst_tea_abstract.py` — TEA class
- `cellulosic_tea_etj.py` — TEA for cellulosic ethanol co-production variant
- Plot files: `breakdown_plot.py`, `uncertainty_plot.py`, `selectivity_plot.py`, `capacity_contour.py`

### 2. `lignin_saf/` — Lignin RCF to SAF

Two-reactor RCF process: **poplar → solvolysis + hydrogenolysis → lignin oil monomers**, co-producing cellulosic ethanol from the carbohydrate pulp. Feedstock: 2,000 dry MT/day poplar. CEPCI basis: 541.7 (2016 USD).

**Key files:**
- `rcf_system.ipynb` — main working notebook; builds and simulates the full integrated system
- `rcf_4_21_2026` — standalone Python script for the RCF loop only (`rcf_system`); no integrated downstream systems. All units are defined without individual `.simulate()` calls — phase assignments are handled via `add_specification` decorators and `rcf_system.simulate()` drives convergence of both recycle loops.
- `cellulosic_ethanol_legacy.py` — minimal script that builds and simulates the cellulosic ethanol system in isolation using `cellulosic.create_cellulosic_ethanol_system()`; useful as a reference for how BioSTEAM factory functions work
- `ligsaf_units.py` — custom units: `SolvolysisReactor`, `HydrogenolysisReactor`, `PSA`, `CatalystMixer`
- `ligsaf_settings.py` — all RCF process parameters (conditions, catalyst loading, biomass composition, oil composition)
- `ligsaf_chemicals.py` — chemical definitions for the RCF system
- `ligsaf_abstract_tea.py` — `AbstractTEA` base class (imported by `ligsaf_tea.py`)
- `cellulosic_tea.py` — `CellulosicEthanolTEA` used for the integrated system TEA
- `ligsaf_tea.py` — `ConventionalEthanolTEA` alternative
- `ligsaf_system.py` — **`create_rcf_system(ins=None)`** factory function; encapsulates all 20 unit operations, both recycle loops, and all `add_specification` decorators. Returns a ready-to-simulate `bst.System`. Import and call pattern:
  ```python
  from lignin_saf.ligsaf_system import create_rcf_system
  rcf_system = create_rcf_system(ins=poplar_in)  # ins=None uses default feed from ligsaf_settings
  ```
  Note: `chems.define_group('Poplar', ...)` must be called before creating any stream with `Poplar` as a component — do this in the calling script after `bst.settings.set_thermo(chems)`, before passing `ins` to the factory.

**`SolvolysisReactor` sizing model (flow-rate-first, semi-batch, ideal stagger):**

Reactor sizing in `_size_bed()` (`ligsaf_units.py`) follows a three-stage logic:

**Stage 1 — N_total from ideal stagger formula:**
```
N_total_base = round(cycle_time / tau_0)          # e.g. round(4/1) = 4
N_working    = round(N_total_base × tau/cycle_time) # e.g. round(4 × 3/4) = 3
N_offline    = N_total_base − N_working             # e.g. 1
```
This ensures exactly N_offline beds are always in their cleaning window (τ₀) — the ideal stagger condition. At least 1 cleaning slot and 1 active slot are guaranteed.

**Stage 2 — V_max_limit enforcement by k-multiplier scaling:**
If the base count gives vessel volumes above V_max_limit (600 m³), N_total is scaled by integer k = 1, 2, 3, … until V_max ≤ V_max_limit. Stagger timing is preserved exactly because N_total = k × N_total_base and N_working = k × N_working_base.

**Stage 3 — Geometry with L/D cap:**
Cross-section A and diameter/length are derived from Q_per_reactor and superficial_velocity. If L/D > LD_max (default 5.0), superficial velocity is reduced analytically to hit L/D = LD_max exactly. `self.superficial_velocity` is updated so pressure drop uses the adjusted value.

**Key parameters:**

| Parameter | Default | Meaning |
|---|---|---|
| `methanol_loading_per_pass` | 5.45 L/kg | System-level solvent flow rate [L per kg daily biomass]. Sets Q_total; also equals total solvent contact per batch (L/kg) via ideal stagger identity. |
| `V_max_limit` | 600 m³ | Hard upper bound per vessel; k-multiplier scales until satisfied. |
| `tau_s` | 3 hr | Time on stream per batch (biomass contact time) |
| `tau_s_res` | 1/3 hr (20 min) | Hydraulic residence time — experimentally derived, independent of void_frac/Q |
| `poplar_density` | 485 kg/m³ | Bulk density of poplar chips |
| `free_frac` | 0.10 | Fraction of reactor volume kept as headspace |
| `LD_max` | 5.0 | Max L/D ratio; u reduced analytically if exceeded |

**V_solvent has two contributions (both in `_size_bed()`):**
```
V_void    = void_frac × V_biomass              # interparticle voids, always saturated
V_dynamic = Q_per_reactor × tau_residence       # dynamic holdup from experimental HRT
V_solvent = V_void + V_dynamic
V_max     = (V_solid + V_solvent) / (1 − free_frac)
```

**Q_total and flow rate:**
```
Q_total       = methanol_loading_per_pass × dry_biomass_kgday / 1000 / 24  [m³/hr]
Q_per_reactor = Q_total / N_working
```
`Q_total` is identical to `total_vol_hr` in the `meoh_water_flow` spec (`ligsaf_system.py:80`) — both parameters use the same flow-rate interpretation of `methanol_loading_per_pass`.

**Useful identity:** With ideal stagger, total solvent contact per batch = Q_per_reactor × τ / biomass_per_batch = `methanol_loading_per_pass` [L/kg] exactly. This matches the L/kg convention in RCF literature (Bartling et al. 9 L/kg).

**Base case (5.45 L/kg, tau=3, tau_0=1, tau_res=1/3 hr):**

| Quantity | Value |
|---|---|
| N_total / N_working / N_offline | 4 / 3 / 1 |
| Biomass per batch | 83,333 kg |
| V_max per vessel | ~247 m³ (well under 600 m³ limit) |
| Total system volume | ~988 m³ |
| Q_total / Q_per_reactor | 454 / 151 m³/hr |
| V_void + V_dynamic | 85.9 + 50.5 = 136.4 m³/bed |
| D / L / L/D | 3.98 m / 19.9 m / 5.0 |
| Effective u (after L/D cap) | 0.0034 m/s (reduced from 0.01 m/s) |

**batches/day = 24/tau_0** regardless of tau — a consequence of the ideal stagger formula. So changing tau only changes N_total/N_working, not the number of batches.

**Tests:** `lignin_saf/test_solvolysis_sizing.py` — pytest suite covering volume balance, batch arithmetic, Q correctness (dynamic term recovers Q: Q = (V_solvent − V_void) / tau_res), L/D cap, and all design result keys. Run with:
```bash
pytest lignin_saf/test_solvolysis_sizing.py -v
```

**Tests:** `lignin_saf/test_solvolysis_sizing.py` — pytest suite covering volume balance (V_solid + V_free + V_solvent = V_max), batch arithmetic, Q correctness (V_solvent not V_max), L/D bounds, and all design result keys. Run with:
```bash
pytest lignin_saf/test_solvolysis_sizing.py -v
```

**Integrated systems built in `rcf_system.ipynb`:**
- `rcf_system` — RCF loop (MIX100 through FLASH118)
- `etoh_system` — cellulosic ethanol system from `biorefineries.cellulosic`
- `rcf_oil_purification_sys` — ethyl acetate LLE
- `monomer_purification_sys` — hexane LLE
- `combined_sys` — full integrated system (330 days/yr × 24 hrs)
- `combined_sys_hx` — same with `HeatExchangerNetwork` (T_min_app = 10°C)

## Git Workflow

After completing any meaningful unit of work, commit and push changes to GitHub so progress is never lost. Use clear, descriptive commit messages that explain what was done.

```bash
git add <specific-files>
git commit -m "short description of what changed and why"
git push origin main
```

Prefer staging specific files over `git add .` to avoid accidentally committing large outputs or temporary files. A `.gitignore` is in place that excludes `*.xlsx`, `*.png`, and `*.svg` output files — these are generated locally and should not be committed.

## Framework Conventions

- **BioSTEAM** (`import biosteam as bst`) is the primary process simulation framework. Systems are built by instantiating unit operations sequentially, connecting them via streams, then wrapping in `bst.System(path=(...), recycle=(...))`.
- **`atj_baseline`** additionally uses **QSDsan** (`import qsdsan as qs`) — units use `qs.SanStream` instead of `bst.Stream` and sanunits for standard operations.
- **`atj_bst`** and **`lignin_saf`** use pure BioSTEAM with the `biorefineries` package for the cellulosic ethanol sub-system.
- Custom reactor units subclass BioSTEAM's `Unit` and add OPEX via `add_OPEX` for catalyst replacement costs.
- TEA classes subclass BioSTEAM's `TEA`; MJSP/MSP is solved via `tea.solve_price(product_stream)`.
- CEPCI is set globally: `bst.settings.CEPCI = <value>` (541.7 for 2016, 800.8 for 2023).
- **Unit IDs** may only contain letters, numbers, and underscores — no hyphens or spaces (e.g. use `'RCF103_S'` not `'RCF103-S'`). Stream IDs follow the same rule.
- **Do not call `.simulate()` on individual units before assembling a `bst.System`.** Phase assignments that need to persist across recycle iterations should be placed inside `add_specification` decorators, not after standalone simulate calls.