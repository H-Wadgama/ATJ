
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

# Tip 4: Setting up auxiliaries can be tricky, so here's a short kind of guide to help you avoid errors down the line

Auxiliaries can be handy because they can do associated unit operations for instance inlet compressing/heating, outlet splitting, etc within your unit operation. The reason I feel this helps rather than having these units as separate global units as you would otherwise do, is that they can allow the user to place better estimates on the CAPEX and OPEX of the complete operation, and also because it allows the user to place conditions within these different units, making it a more dynamic system. For example if one has a PSA unit, an auxiliary would be a feed compressor that increases the pressure to the feed pressure. If this is a separate global unit, it will make its own separate estimates outside of your PSA class. Moreover, if I want this pump to only function if the incoming pressure is less than the feed pressure, I can do that through an if statement within my PSA class. These sort of functionalities make auxiliary units quite an integral part of BioSTEAM.
The problem with auxiliaries (or atleast what I face typically) is wiring issues - you connect a parent stream to the auxiliary, or the auxiliary stream to the parent and things get a bit messy. I've addressed some common pain points I experienced when designing a class for Pressure Swing Adsorption of Hydrogen.

## Tip 4.1. For auxiliaries that function on the incoming stream, do the following to prevent errors!
Define them in the  `_init` class and make sure that their `ins` are set to `self.ins[0]`(or whatever index the inlet stream you want to attach it to)
```bash
self.feed_pump = self.auxiliary('feed_pump', bst.IsentropicCompressor, ins=self.ins[0], P = self.P_feed)
```
Next, define the logic you want in `_run`. In my case, I want this pump to compress the inlet, but only if the incoming pressure is less than the feed PSA pressure. Otherwise, I don't want to simulate a pump.

``` bash
def _run(self):
   if self.ins[0].P < self.P_feed:    # Setting the condition, if inlet P is less than PSA P
      self.feed_pump.P = self.P_feed # The outlet pressure of pump equals PSA P
      self.feed_pump.simulate()      # The pump is simulated
   else:
      self.feed_pump.outs[0].copy_like(self.ins[0])  # The pump does nothing and outlet is the same as its inlet
```
Now because the feed is compressed, the systems self.ins[0] automatically becomes the outlet of the pump:
```bash
feed, = self.feed_pump.outs[0]
```
This way, whatever stream is coming in the system, it will be checked for its pressure and if its pressure is less than PSA pressure, the pump will do its job.

Note that even though I just set the pump functionalities in `_init()` and `_run()` it still does the design and the costing for it. This is not an issue, and BioSTEAM's smart enough to deduce these things.

 
## Tip 4.2. For setting up auxiliaries at the outlet, do this!
Setting up auxiliaries for the outlets can be a bit more involved. Here for the same PSA class, i introduce a vaccuum pump. The vaccuum pump essentially increases the pressure of the purge to atmospheric pressure, but only if the pressure of the purge was lower than atmospheric to begin with. This is how it will be done.

Inside `_init()`, I define a temporary stream that will be my pseudo-outlet:
```bash
self._raw_extract = bst.Stream()
```
and then for my vaccuum pump:
```bash
self.vaccuum_pump = self.auxiliary('vaccuum_pump', bst.IsentropicCompressor, ins = self._raw_extract, outs = self.outs[1], P = 101325)  # Outs are what I want the system outs to be, the self._raw_extract is a temporary stream
```
The `self._raw_extract` is an internally created stream only to alter its composition and properties to make it mimic the actual system outlet.

Then inside `_run`, I define the properties of this stream:

```bash
self._raw_extract.copy_like(feed)
self._raw_extract.imol['Hydrogen'] = feed.imol['Hydrogen'] - raffinate.imol['Hydrogen']
self._raw_extract.phase = 'g'
self._raw_extract.T = self.ins[0].T
self._raw_extract.P = self.P_purge
```
Now `P_purge` here is 0.25e5, and I want to increase the pressure to atmospheric. For that I define logic for my vaccuum pump.

```bash
if self.P_purge < 101325:           # If Purge pressure is less than atmospheric
   self.vaccuum_pump.P = 101326    # Set vaccuum pump pressure to atmospheric
   self.vaccuum_pump.simulate()    # Simulate the pump

else:
   self.vaccuum_pump.outs[0].copy_like(self._raw_extract) # Otherwise, the outlet is just the _raw_extract stream without any pumping
```
Note that since we already defined the pump outlet as `self.outs[1]`, in the `else` statement above, we are kind of just making the PSA `outs[1]` stream equals to `self._raw_extract`

This is it! 

## Tip 4.3. If you want a custom number of the auxiliary units, do this!
Typically the way auxiliaries are set is that they equal the number of parallel units you decide on. For instance, if I have 12 beds for my adsorption column, I use the `self.parallel` feature in my `_design()` class:

```bash
self.parallel['self'] = self.N_beds  # 'self' argument here refers to the parent class

```

Since `self.N_beds`equals 12 here, I basically create 12 of the units, so for an adsorption column, I create 12 of these vessels. The utilities also scale accordingly.

However, for my PSA system, I just want 1 feed pump and 1 vaccuum pump. To make sure this is the case, after defining parallel units, I also define:

```bash
self.parallel['feed_pump']   = 1   
self.parallel['vaccuum_pump']   = 1  
```

This ensures that I only have 1 feed, and vaccuum pump simulating. 
Note that if I check my design results, I might still see vaccuum pump and feed pump x 12, but if you really see the diagram of the unit operation, or try removing the `self.parallel['feed_pump'] = 1`, you will see that the costing indeed scales up to x12 indicating that indeed you can define the number of auxiliaires with the code above.   

## Tip 5. If you want to display output graphviz diagrams, make sure you use this one argument

Obviously, any kind of graphviz file runs on the condition that graphviz is installed in your system. What I didn't realize was that using this one line of code really makes a difference
```bash
bst.nbtutorial()
```
Once this is set, every graphviz output file you create, you can hower over the unit operations to identify what their duties are, what the purchase costs are and what their utility requirements are. Similar thing for streams where temperature, pressures and flows are easily avaialble.

This makes a ton of difference whenever designing a project. Rather than using 
```bash
unit_op.results()
```
and also
```bash
unit_op
```
to separately display stream information and design results, `bst.nbtutorial()` makes evaluating your flowsheet a lot easier.

Otherwise, if graphviz is installed but this argument is set to false, be prepared to see a lot of numbers for every svg

```
120334934134:c->120334851048:w Carbohydrate Pulp 120334934134:c->120341758448:w Solvolysis Liquor 120334934221:c->120334934134:c 120334425476:e->120334934134:c Poplar In 120341758460:e->120334934221:c s4 120334934134 RCF103-S Solvolysis reactor 120334934221 RCF103-S Pump 1 120334425476 120334851048 120341758460 120341758448
```
This is what a typical diagram looked like for me before the magical `bst.nbtutorial()`

# Integrating two systems can be a bit tricky, so make sure you follow these steps
Lately, I was trying to connect the RCF system I've built with the cellulosic ethanol system native to BioSTEAM. For context, the carbohydrate pulp from the RCF reactor is the feed to the ethanol system, so what I tried was simulating the RCF system, setting the ins of the ethanol system as the carbohydrate pulp from the RCF, and then simulating the ethanol system, and finally creating an integrated system which kind of just simulated the two. Sounds good right? But the problem was that BioSTEAM created two of the facilities, so I had a boiler turbogenerator from my RCF system, and then a seperate one from my cellulosic system. Similar situation for the wastewater treatment. Considering that, especially the boiler turbogenerator has a very high CAPEX, I would want to have one central BT for my system. Thats when things got a bit tricky.
I tried using the following BioSTEAM commands:

```bash
integrated_sys.units[74].disconnect(inlets =integrated_sys.units[74].ins[0])    
integrated_sys.units[74].simulate()
```
and also 
```bash
integrated_sys.units[74].ins.remove(integrated_sys.units[74].ins[0])
integrated_sys.units[74].simulate()
```
The problem with either was that even when I use `disconnect` or `remove`, when I resimulated my system, my changes were essentially undone. For some reason, these changes were not permenant. 

The solution that exists is to first remove the faciliites from one of your systems. So because I had more control over my RCF system (since I defined all the unit operations myself), I went ahead and deleted the BT and WWT systems.
Then I simulated that system, followed by creating the cellulosic ethanol system, and gave it my rcf_system pulp as feed
```bash
ethanol = cellulosic.create_cellulosic_ethanol_system(ins = rcf_system.products[0])
ethanol.simulate()          
```
So essentially I simulated both systems, but didn't integrate them yet. Next what I do is that I scan through all the unit operations in my etoh_system using the following code:
```bash
for i,unit in enumerate(etoh_system.units):
    print(i, unit.ID)
```
Which yields:
```
0 U101
1 H2SO4_storage
2 T201
3 M201
.
.
.
55 P702
56 M701
57 T703
58 M3
59 P403
60 M4
61 CWP
62 ADP
63 CT
64 FWT
65 CIP
66 BT
67 PWC
```
This helps me because it gives me all the relevant IDs for the unit operations in ethanol system. I need to know these because I didn't make the system myself, and BioSTEAM makes it kind of hard to access these unit ops otherwise
Since the BT has an ID of 66, I go ahead and access it:
```bash
etoh_system.units[66]
```
```
BoilerTurbogenerator: BT
ins...
[0] to_boiler  from  Mixer-M2
    phase: 'l', T: 313.12 K, P: 101325 Pa
    flow (kmol/hr): Water              997
                    Ethanol            0.00281
                    AceticAcid         0.785
                    Furfural           0.115
                    Glycerol           0.0702
                    LacticAcid         0.692
                    SuccinicAcid       0.137
                    DAP                0.0618
                    AmmoniumSulfate    1.03
                    HMF                0.0876
                    SO2                0.000241
                    Glucose            0.107
                    Xylose             0.272
                    Arabinose          0.482
                    Extract            2.58
                    Ash                4.13e+03
                    NaOH               0.786
                    Lignin             82.5
                    SolubleLignin      0.164
                    GlucoseOligomer    0.267
                    GalactoseOligomer  0.000677
                    MannoseOligomer    0.000354
                    XyloseOligomer     0.113
                    ArabinoseOligomer  0.0138
                    Z_mobilis          32.5
                    Protein            126
                    Glucan             7.78
                    Xylan              3.22
                    Xylitol            0.192
                    Cellobiose         0.0355
                    Arabinan           1.08
                    Mannan             3.1
                    Galactan           0.725
                    WWTsludge          43.8
                    Cellulase          0.994
[1] gas_to_boiler  from  Mixer-M3
    phase: 'g', T: 307.65 K, P: 101325 Pa
    flow (kmol/hr): Water         37.1
                    Ethanol       0.000147
                    AceticAcid    0.00877
                    Furfural      0.00849
                    Glycerol      4.27e-08
                    LacticAcid    2.52e-06
                    SuccinicAcid  6.7e-09
                    CH4           351
                    CO2           337
[2] makeup_water  
    phase: 'l', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): Water  427
[3] natural_gas  
    phase: 'g', T: 288.71 K, P: 101560 Pa
    flow: 0
[4] FGD_lime  
    phase: 'l', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): Water  9.94
                    Lime   2.49
[5] boiler_chemicals  
    phase: 'l', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): Ash  0.496
[6] air  
    phase: 'g', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): N2  3.6e+04
                    O2  8.37e+03
outs...
[0] emissions  
    phase: 'g', T: 397.77 K, P: 101325 Pa
    flow (kmol/hr): Water  2.27e+03
                    P4O10  0.0154
                    N2     3.6e+04
                    O2     6.59e+03
                    SO2    0.166
                    CO2    1.67e+03
[1] blowdown  
    phase: 'l', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): Water  427
[2] ash  
    phase: 'l', T: 298.15 K, P: 101325 Pa
    flow (kmol/hr): Water  73.5
                    CaSO4  1.91
                    Ash    4.15e+03
```

The `gas_to_boiler` is of my interest, since I want to send the PSA waste gases to this stream. Since this comes from `Mixer-M3` I go ahead and check that mixer (again, the IDs above really help pinpoint the ID of the mixer)
```bash
etoh_system.units[58]
```
```
Mixer: M3
ins...
[0] biogas  from  AnaerobicDigestion-R601
    phase: 'g', T: 307.65 K, P: 101325 Pa
    flow (kmol/hr): Water         37.1
                    Ethanol       0.000147
                    AceticAcid    0.00877
                    Furfural      0.00849
                    Glycerol      4.27e-08
                    LacticAcid    2.52e-06
                    SuccinicAcid  6.7e-09
                    CH4           351
                    CO2           337
outs...
[0] gas_to_boiler  to  BoilerTurbogenerator-BT
    phase: 'g', T: 307.65 K, P: 101325 Pa
    flow (kmol/hr): Water         37.1
                    Ethanol       0.000147
                    AceticAcid    0.00877
                    Furfural      0.00849
                    Glycerol      4.27e-08
                    LacticAcid    2.52e-06
                    SuccinicAcid  6.7e-09
                    CH4           351
                    CO2           337
```
So what I need to do is that for this mixer, I add another inlet which is the PSA waste gases from my RCF system

```bash
# Reconnecting streams
etoh_system.units[58].ins[1] = rcf_system.products[1] # The purge light gases from PSA will go to the boiler turbogenererator
```

And voila! All set. 

I now create the integrated system and simulate it
```bash
integrated_sys = bst.System('RCF_EtOH',
                        path=(rcf_system, etoh_system))
integrated_sys.simulate()
```

Sure enough, the mixer (whose ID will now have changed so we need to display the IDs of the integrated system) will have another inlet, this time also the waste gases from the PSA.

# Utility consumption or conversion can be understood using the powerutility object

For a boiler turbogenerator, the power utility can be accessed as:

```bash
F.BT.power_utility    # F references the flowsheet and BT is the Boiler Turbogenerator
```
This yields
```
PowerUtility:
consumption: 123 kW
production: 525 kW
power: -402 kW
cost: -31.4 USD/hr
```

So there is a net production here. 
Any of the elements within the PowerUtility object can be accessed easily:
```bash
F.BT.power_utility.power
```
Which yields
```
-401.6976008593439
```

Heat utilities can also be accessed using
```bash
F.BT.heat_utilities
```
Which yields a list of all the heat utilities. These cannot be accessed like power utilitys using the dot notation as it is a list and not an object
```
[<medium_pressure_steam: -2.99e+06 kJ/hr, -82.5 kmol/hr, -22.7 USD/hr>,
 <high_pressure_steam: -2.14e+07 kJ/hr, -664 kmol/hr, -211 USD/hr>,
 <natural_gas: -1.89e+07 kJ/hr, -32 kmol/hr, -112 USD/hr>,
 <low_pressure_steam: -9.33e+05 kJ/hr, -24.1 kmol/hr, -5.73 USD/hr>,
 <cooling_water: -3.33e+05 kJ/hr, 228 kmol/hr, 0.111 USD/hr>]
```
Any individual utility can be accessed however, with an index 
```bash
F.BT.heat_utilities[1]
```
```
HeatUtility: high_pressure_steam
duty:-2.14e+07 kJ/hr
flow:-664 kmol/hr
cost:-211 USD/hr
```

This output is actually an object, and so any individual attribute is accessible using the dot notation.
```bash
F.BT.heat_utilities[1].duty
```
Yields:
```
-21372240.87254549
```