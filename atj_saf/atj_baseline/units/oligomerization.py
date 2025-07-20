import biosteam as bst, qsdsan as qs, math

class OligomerizationReactor(qs.SanUnit):

    '''
    Reactor for ethanol conversion to ethylene to oligomers
    
    '''

    
    _N_ins = 1
    _N_outs = 1

    _units = {
        'Catalyst Weight': 'kg',
        'Volume': 'L',
        'Pressure': 'psi',
        'Length': 'ft',
        'Diameter': 'ft',
        'Wall thickness': 'in',
        'Vessel Weight': 'lb',
        'Duty': 'kJ/hr'}

    def __init__(self, ID = '', ins = None, outs = (), thermo = None, init_with = 'SanStream',
                 uptime_ratio = 0.9,
        conversion = 1.0, biofuel_composition = {              # More info in the OligomerizationReactor class doc.
                    'C4H8'  : 0.2,          # 0.2
                    'C6H12' : 0.15,          # 0.15
                    'C10H20': 0.62,          # 0.62
                    'C18H36': 0.03,          # 0.03
                    },           
        temperature = 393.15, pressure = 3e+6, WHSV = 1.5, 
        aspect_ratio = 3.0, catalyst_density  = 0.4, catalyst_lifetime = 1, catalyst_price = 145.2):
        
        qs.SanUnit.__init__(self, ID, ins, outs, thermo, init_with)
        self.uptime_ratio = uptime_ratio
        self.conversion = conversion
        self.biofuel_composition = biofuel_composition
        self.temperature = temperature
        self.pressure = pressure
        self.WHSV = WHSV
        self.aspect_ratio = aspect_ratio
        self.catalyst_density = catalyst_density
        self.catalyst_lifetime = catalyst_lifetime
        self.catalyst_price = catalyst_price

    def _run(self):
        inf, = self.ins
        eff, = self.outs
        #eff.mix_from(self.ins, energy_balance = False)
        x = self.conversion
        eff.imass['Ethylene'] = (1-x)*inf.imass['Ethylene']
        eff.imass['Water'] = inf.imass['Water']
        eff.imass['Ethanol'] = inf.imass['Ethanol']
        eff.imass['Butene'] = biofuel_composition['C4H8']*inf.imass['Ethylene']*x
        eff.imass['Hex-1-ene'] = biofuel_composition['C6H12']*inf.imass['Ethylene']*x
        eff.imass['Dec-1-ene'] = biofuel_composition['C10H20']*inf.imass['Ethylene']*x
        eff.imass['Octadec-1-ene'] = biofuel_composition['C18H36']*inf.imass['Ethylene']*x
        #eff.phase = recycle.phase = 'g'
        #eff.T = inf.T
        eff.P = inf.P
        #eff.T = inf.T
        #eff.phase = 'g'
        
        #eff.temperature = recycle.temperature = self.temperature
        #eff.pressure = recycle.pressure = self.pressure
        # eff.vle(
        # Oligomerization outlet phase should be liquid like Aspen, but I need to include capability to compute VLE
        
        #eff.P = inf.P
        
    def _design(self):
        D = self.design_results
        #inf, c2h4 = self.ins
        feed_flow = self.ins[0].F_mass
        catalyst_weight = feed_flow/self.WHSV 
        reactor_volume = (catalyst_weight/self.catalyst_density)*1.15 #15% extra for volume
        
        diameter =  ((4*((reactor_volume*0.001)/(0.3048**3)))/
                     (3.14*self.aspect_ratio))**(1/3)
        length = self.aspect_ratio*diameter

        #compute vessel total weight and wall thickness
        # Change this
        S = 15000.0     # Vessel material stress value (assume carbon-steel) 
        Ca = 1.0/8.0    # Corrosion Allowance in inches
        Je = 0.85       # weld efficiency
        dia = diameter
        rho_M = 490  # lb/ft^3

        P = (self.pressure/101325) * 14.7
        
        P_gauge = abs(P - 14.7)
        P1 = P_gauge + 30.0
        P2 = 1.1 * P_gauge
        if P1 > P2:
            PT = P1
        else:
            PT = P2
            
        # Calculate the wall thickness and surface area
        # Shell
        SWT = (PT * dia *12.0) / (2.0 * S * Je - 1.2 * PT) + Ca
        SSA = 3.142 * dia * length
        if dia < 15.0 and PT > (100 - 14.7):
            # Elliptical Heads
            HWT = (PT * dia *12.0) / (2.0 * S * Je - 0.2 * PT) + Ca
            HSA = 1.09 * dia ** 2
        elif dia > 15.0:
            # Hemispherical Heads
            HWT = (PT * dia*12.0) / (4.0 * S * Je - 0.4 * PT) + Ca
            HSA = 1.571 * dia ** 2
        else:
            # Dished Heads
            HWT = 0.885 * (PT * dia *12.0) / (S * Je - 0.1 * PT) + Ca
            HSA = 0.842 * dia ** 2
    
        # Approximate the vessel wall thickness, whichever is larger
        if SWT > HWT:
            ts = SWT
        else:
            ts = HWT

        # Minimum thickness for vessel rigidity may be larger
        if dia < 4:
            ts_min = 1/4
        elif dia < 6:
            ts_min = 5/16
        elif dia < 8:
            ts_min = 3/8
        elif dia < 10:
            ts_min = 7/16
        elif dia < 12:
            ts_min = 1/2
        else:
            ts_min = ts
        if ts < ts_min:
            ts = ts_min
        VW = rho_M * ts/12 * (SSA + 2.0 * HSA)  # in lb
        VW = round(VW, 2)

        # Adding utility
        self.outs[0].T= self.ins[0].T
        # duty =  self.outs[0].H - self.ins[0].H + self.outs[0].Hf - self.ins[0].Hf
        duty =  self.outs[0].H - self.ins[0].H + self.outs[0].Hf - self.ins[0].Hf
        # duty < 0: raise RuntimeError(f'{repr(self)} is cooling.') # Duty must be greater than 0
        
        D['Catalyst Weight'] = catalyst_weight
        D['Volume'] = reactor_volume
        D['Vessel Weight'] = VW
        D['Length'] = length
        D['Diameter'] = diameter
        D['Wall thickness'] = ts
        D['Duty'] = duty


    def _cost(self):
        D = self.design_results
        purchase_costs = self.baseline_purchase_costs
        utility = self.add_heat_utility
        #self.baseline_purchase_costs.update(purchase_costs)
        
        lnW = math.log(D['Vessel Weight'])
        C_v = 2.0*(math.exp(5.6336 + 0.4599 * lnW + 0.00582 * lnW * lnW))
        C_pl = 2275.*D['Diameter']**0.20294
        purchase_costs['Horizontal pressure vessel'] = C_v # 2.1 as vessel will be SS312 https://pubs.acs.org/doi/10.1021/i100018a019
        purchase_costs['Platform and ladders'] = C_pl
        purchase_costs['Catalyst'] = self.catalyst_price * D['Catalyst Weight']
        #utility_cost = 2    # change duty
        #self.power_utility(utility_cost*D['Duty'])
        heat_utility = self.add_heat_utility(D['Duty'], self.temperature, heat_transfer_efficiency = 1)
        add_OPEX = (D['Catalyst Weight']*self.catalyst_price)/(365*24*self.uptime_ratio*self.catalyst_lifetime)
        self._add_OPEX = {'Additional OPEX': add_OPEX}        
     
# getter setter to ensure values of conversion 0 < x < 1
    @property
    def conversion(self):
        '''Conversion of ethanol to ethylene in this reactor'''
        return self._conversion
    @conversion.setter
    def conversion(self, i):
        if not 0 <= i <= 1:
            raise AttributeError('`conversion` must be within [0, 1], '
                                    f'the provided value {i} is outside this range.')
        self._conversion = i