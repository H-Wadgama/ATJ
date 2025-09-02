
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

# Tip 2: Define critical temperature and critical pressure of pseudocomponents only if you are sure about the models used for their temperature dependent properties like  heat capacity etc

I was trying to define lignin monomers for the RCF process, and defined one component as:

```bash
propylguaiacol = tmo.Chemical(  # S-Lignin Monomer 
        'Propylguaiacol',
        default = True,      # Defaults all other properties 
        search_db=False,     # Since not present in database, do not search
        formula='C10H14O2',  # Chemical formulae
        phase='l',           # phase at rtp
        omega = 0.6411,      # accentric factor
        Tb = 541.7,          # [K]  normal boiling point
        Tc = 749,            # [K]  critical temperature
        Pc = 2.9e6,          # [Pa] critical pressure
        Hvap = 7.78e4,       # [J/mol] enthalpy of vaporization at 298 K
        rho = 1056.3,        # [kg/m3] density at rtp

    )
    propylguaiacol.synonyms = ('4-Propylguaiacol',) # Synonyms that can be used to refer to it
```

I found these values using Aspen NIST TDE, and naturally thought of adding all the values I could find from there. I did not add the models for the temperature dependent properties like density, heat capacity etc.

I created a stream that was simply heated to a required temperature. The stream consisted of propylguaiacol and methanol:

```bash
stream = bst.MultiStream(l = [('Propylguaiacol', 100), ('Methanol', 1000)], phases = ('l', 'g'))
heat_1 = bst.units.HXutility(ins = stream, T = 800, rigorous = True)
heat_1.simulate()
```
I ran into the following error:

```
---------------------------------------------------------------------------
RuntimeError                              Traceback (most recent call last)
File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermo\utils\t_dependent_property.py:4270, in TDependentProperty.T_dependent_property_integral(self, T1, T2)
   4269 if T1 <= Tmax:
-> 4270     integral += self.extrapolate_integral(Tmax, T2, method)
   4271 else:

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermo\utils\t_dependent_property.py:4806, in TDependentProperty.extrapolate_integral(self, T1, T2, method, in_range)
   4805 else:
-> 4806     extrapolation_coeffs[key] = coeffs = self._get_extrapolation_coeffs(*key)
   4807 v, d = coeffs

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermo\utils\t_dependent_property.py:4472, in TDependentProperty._get_extrapolation_coeffs(self, extrapolation, method, low)
   4471 if extrapolation == 'linear':
-> 4472     v = self.calculate(T, method=method)
   4473     d = self.calculate_derivative(T, method)

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermo\heat_capacity.py:1026, in HeatCapacityLiquid.calculate(self, T, method)
   1025 elif method == ROWLINSON_POLING:
-> 1026     Cpgm = self.Cpgm(T) if hasattr(self.Cpgm, '__call__') else self.Cpgm
   1027     return Rowlinson_Poling(T, self.Tc, self.omega, Cpgm)

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermo\utils\t_dependent_property.py:3091, in TDependentProperty.T_dependent_property(self, T)
   3090     if self.RAISE_PROPERTY_CALCULATION_ERROR:
-> 3091         raise RuntimeError(f"No {self.name.lower()} method selected for component with CASRN '{self.CASRN}'")
...
   4279         )
   4280     else:
   4281         return None

RuntimeError: Failed to extrapolate integral of liquid heat capacity method 'ROWLINSON_POLING' between T=748.9 to 800.0 K for component with CASRN 'None'
```
When I searched for the heat capacity models my new defined propylguaiacol was using I figured:

```bash
chems['Propylguaiacol'].Cn
```
```
HeatCapacityLiquid(MW=166.21696, Tc=749, omega=0.6411, Cpgm=HeatCapacityGas(MW=166.21696, extrapolation="linear", method=None), extrapolation="linear", method="ROWLINSON_POLING", Tmin=224.7, Tmax=748.9)
```

This meant that for the liquid phase heat capacity, propylguaiacol was using the Rowlinson Poling method which scales heat capacity according to the critical temperature and pressure and the accentric factor. However, I am not sure about this method and its applicability for this kind of component, and so its best if I don't use it to try predict properties. Moreover, I know that it is a non-volatile specie and will likely not evaporate across the system and so it makes more sense to use a common Cp value.

The way biosteam uses Cp for pseudo components of biomass is assign it with a value of 1.36 J/g/K and so for Cellulose at 500 K, the Cp can be determined from:

```bash
chems['Cellulose'].Cn(500)
```
```
221.15977840000002
```
Even if I change the temperature I still get the same value, because the function is essentially just a straight line. 
I can check this by:
```bash
chems['Cellulose'].Cn
```
```
HeatCapacityLiquid(MW=162.1406, Cpgm=HeatCapacityGas(MW=162.1406, extrapolation="linear", method=None), extrapolation="linear", method="USER_METHOD", Tmin=0.0, Tmax=inf)
```
Where heat capacity is just a straight line without any slope from T = 0 to T = inf.

And the reason for this is that Cellulose does not have its Tc and Pc temperatures so BioSTEAM does not try defaulting it to Rowlinson Polani and just gives it this linear default method.

Therefore for my pseudocomponent lignin monomer propylguaiacol, I am going to remove Tc and Pc. It was good to determine them from Aspen Plus TDE, because I know they are non volatiles now, and then I can just force BioSTEAM to default it to a user defined linear method where the heat capacity will be the components MW * 1.36. Since the model is constant infinitely, it assumes that the components always stay in the liquid phase (otherwise it would have a valid range of operation until the normal boilig point or something)


# Tip 3: Remember that some unit operations do require one argument to simulate, and others don't

For instance a good ole pump on BioSTEAM can simply be simulated by:
```bash
ole_pump = bst.units.Pump('Ole_Pump')
ole_pump.simulate()
```

This pump really won't do anything (you haven't specified the inlets or the outlet pressure required), but the code still works.

However, if I try to simulate a valve:

```bash
ole_valve = bst.units.IsenthalpicValve('Ole_Valve')
ole_valve.simulate()
```
I get an error:

```
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Cell In[239], line 1
----> 1 ole_valve = bst.units.IsenthalpicValve('Ole_Valve')
      2 ole_valve.simulate()

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\biosteam\_unit.py:611, in Unit.__init__(self, ID, ins, outs, thermo, **kwargs)
    607 self._utility_cost = None
    609 self._recycle_system = None
--> 611 super().__init__(ID, ins, outs, thermo, **kwargs)
    613 self._assert_compatible_property_package()

File c:\Users\hwadg\anaconda3\envs\pyfuel\lib\site-packages\thermosteam\network.py:1052, in AbstractUnit.__init__(self, ID, ins, outs, thermo, **kwargs)
   1049 #: Auxiliary unit operation names.
   1050 self.auxiliary_unit_names = list(self.auxiliary_unit_names)
-> 1052 self._init(**kwargs)

TypeError: IsenthalpicValve._init() missing 1 required positional argument: 'P'
```

This is just strange on BioSTEAMs part. Seems to not interfere terribly with daily bst operations so its fine I suppose