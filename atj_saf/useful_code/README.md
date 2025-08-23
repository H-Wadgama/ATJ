
# BioSTEAM useful tips and tricks
Lessons learnt through trial and error

## Tip 1. Always work with MultiStream for chemical reaction systems


Make sure you pay attention to the phases if you try to react something. Suppose I define an inlet stream as just bst.Stream and all solids and another inlet as bst.Stream with all liquids, if I use these to react, the outlet stream will only occupy one of these phases. Therefore to ensure that you can adequately capture the phases, use MultiStream especially when dealing with any kind of chemical reaction designs (as they usually involve heterogeneity)



Also, for chemical reactions, if your inlet stream is multiphase and you try running the reaction only in one phase, it is going to give you the error: "Reaction and stram phases do not match"


```bash
hydrogenolysis = bst.ParallelReaction([
    bst.Reaction('SolubleLignin,l ->Propylguaiacol,l', reactant = 'SolubleLignin', phases = 'l', X = 0.25, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l ->Propylsyringol,l', reactant = 'SolubleLignin', phases = 'l', X = 0.25, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> Syringaresinol,l', reactant= 'SolubleLignin',phases = 'l', X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> G_Dimer,l', reactant= 'SolubleLignin', phases = 'l',X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> S_Oligomer,l', reactant= 'SolubleLignin',phases = 'l', X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> G_Oligomer,l', reactant= 'SolubleLignin', phases = 'l',X = 0.125, basis = 'wt', correct_atomic_balance=False),
])
```

The reactant looks like:
```
MultiStream: s29
phases: ('g', 'l', 's'), T: 463.15 K, P: 6e+06 Pa
flow (kmol/hr): (l) Water          4.15e+04
                    SolubleLignin  109
                    Methanol       1.64e+05
                (s) Extract        7.4
                    Acetate        48.6
                    Arabinan       0.631
                    Galactan       3.6
```

When I try to run this, I get the error

```
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Cell In[87], line 1
----> 1 hydrogenolysis(solvolysis_liquor)

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermosteam\reaction\_reaction.py:490, in Reaction.__call__(self, material, T, P, phase, time)
    489 def __call__(self, material, T=None, P=None, phase=None, time=None):
--> 490     values, config, original = as_material_array(
    491         material, self._basis, self._phases, self.chemicals
    492     )
    493     if values.ndim == 2 and not isinstance(self._reactant_index, tuple):
    494         for i in values: self._reaction(i)

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermosteam\reaction\_reaction.py:71, in as_material_array(material, basis, phases, chemicals)
     69 if isa(material, tmo.Stream):
     70     if phases and material.phases != phases:
---> 71         raise ValueError("reaction and stream phases do not match")
     72     if material.chemicals is chemicals:
     73         config = None

ValueError: reaction and stream phases do not match
```

Even though `SolubleLignin` is in the liquid phase in the reactant, the reaction has trouble because it 
thinks that the reaction is just 1 phase, while the reactant is 3 phases and feels as if they are a mismatch.
Therefore, to make this work, the reaction needs to be modified and the phases need to be defined as all 3 phases (since the reactant is 3 phase), even though the actual reaction only takes place in the liquid phase


```bash
hydrogenolysis = bst.ParallelReaction([
    bst.Reaction('SolubleLignin,l ->Propylguaiacol,l', reactant = 'SolubleLignin', phases = 'slg', X = 0.25, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l ->Propylsyringol,l', reactant = 'SolubleLignin', phases = 'slg', X = 0.25, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> Syringaresinol,l', reactant= 'SolubleLignin',phases = 'slg', X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> G_Dimer,l', reactant= 'SolubleLignin', phases = 'slg',X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> S_Oligomer,l', reactant= 'SolubleLignin',phases = 'slg', X = 0.125, basis = 'wt', correct_atomic_balance=False),
    bst.Reaction('SolubleLignin,l -> G_Oligomer,l', reactant= 'SolubleLignin', phases = 'slg',X = 0.125, basis = 'wt', correct_atomic_balance=False),
])
```