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

**`SolvolysisReactor` sizing model (geometry-based, semi-batch):**

Reactor sizing is driven by two user-defined parameters in `ligsaf_settings.py`: the per-pass solvent loading (`methanol_loading_per_pass`) and a hard vessel-size ceiling (`V_max_limit`). `_size_bed()` iterates N_total upward from 2 and stops at the minimum number of reactors that keeps each vessel at or below the limit.

| Parameter | Value | Meaning |
|---|---|---|
| `methanol_loading_per_pass` | 5.45 L/kg | Per-pass solvent charge inside one reactor bed per batch, per kg dry biomass. **Primary sizing input — change this to resize the system.** |
| `V_max_limit` | 600 m³ | Hard upper bound on vessel volume; no reactor may exceed this. |
| `tau_s` | 3 hr | Time on stream per batch (biomass contact time) |
| `tau_s_res` | 1/3 hr (20 min) | Hydraulic residence time of solvent per pass |
| `poplar_density` | 485 kg/m³ | Bulk density of poplar chips |
| `free_frac` | 0.10 | Fraction of reactor volume kept free (headspace) |

Sizing logic in `SolvolysisReactor._size_bed()` for each candidate N_total:
- cycle_time = tau_s + tau_0 = 4 hr → 6 batches/reactor/day
- biomass_per_batch = 2,000,000 kg/day ÷ (N_total × 6 batches/day)
- V_solid = (1 − void_frac) × biomass_per_batch / poplar_density  (actual wood; interparticle voids are solvent)
- V_solvent = methanol_loading_per_pass × biomass_per_batch / 1000  (solvent charge, L → m³)
- V_max = (V_solid + V_solvent) / (1 − free_frac)  ← accept if V_max ≤ V_max_limit + 0.5 m³

**Base case (5.45 L/kg):** N_total = 4, V_max ≈ 600 m³, 24 batches/day, biomass/batch = 83,333 kg, V_solvent = 454 m³/bed.

**Example sensitivity (2,000 DMT/day feed, V_max_limit = 600 m³):**
| `methanol_loading_per_pass` | N_total | V_max (m³) | Biomass/reactor (kg) |
|---|---|---|---|
| 5.45 L/kg | 4 | ~600 | 83,333 |
| 6.39–7.07 L/kg | 5 | 550–600 | 66,667 |
| 11.93 L/kg | 8 | ~600 | 41,667 |

**Q per reactor = V_solvent / tau_residence** (hydraulic RT defined on fluid volume only — using V_max would be incorrect). Total flow = N_working × Q_per_reactor. Superficial velocity (0.01 m/s) sets D and L from Q.

- BioSTEAM vessel cost correlation is valid for L ≤ 40 ft (12 m); vessel length (~16 m = 52 ft) exceeds this. A `CostWarning` is expected and cost is extrapolated — acceptable for large custom pressure vessels.
- BioSTEAM model treats the reactor as single-pass flow-through (no internal recirculation). Mass balances and TEA are valid because delignification (70%) is a fixed conversion in `_run()`.
- **`methanol_to_biomass = 9 L/kg`** is a separate parameter in `ligsaf_settings.py` that controls the total MeOH mass balance flow (fresh + recycle) via the `meoh_water_flow` specification in `ligsaf_system.py`. It is **not** the same as `methanol_loading_per_pass` and is not updated automatically when you change the per-pass loading.

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