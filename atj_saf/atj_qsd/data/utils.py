comp_driver_efficiency = 1

conversion_factors = {
    'gal_to_m3' : 1/264.17       # 1 m3 = 264.17 gals
}

operating_parameters = {
    'operating_factor' : 0.9,    # % of time the plant operates annually
    'hours_per_annum' : 365*24,  # 8760 total hours 
}

fuel_properties = {
    'max_fuel_yield' : 0.56,  # kg Fuel/kg Ethanol -  From Wang et al https://docs.nrel.gov/docs/fy16osti/66291.pdf
    'percentage_yield' : 0.8,        # 80% theoretical yield
    'saf_density' : 776,             # kg/m3 at 15 C according to ASTM D7566 (https://www.spglobal.com/content/dam/spglobal/ci/en/documents/platts/en/our-methodology/methodology-specifications/biofuels/supporting-materials/faq-platts-saf-renewable-diesel.pdf)
    'rn_density' : 725              # kg/m3 
}


def calculate_ethanol_flow(req_saf = None):
    '''
        Calculate the hourly ethanol mass flow rate required to produce the given SAF output.

        Parameters:
        - req_saf (float, optional): Required SAF production in million gallons per year (MM gal/yr)
                                     If None, defaults to 9 MM Gal/yr for conventional atj baseline case

        Returns:
    - float: Ethanol feedstock flow rate (kg/hr)

    '''

    if req_saf is None:
        req_saf = 9 # MM gal/yr default value


    saf_mass_flow = req_saf*(1e6)*conversion_factors['gal_to_m3']*fuel_properties['saf_density'] # convert MMgal/yr to kg/yr
    etoh_flow = saf_mass_flow/(fuel_properties['max_fuel_yield']*fuel_properties['percentage_yield']*operating_parameters['operating_factor']*operating_parameters['hours_per_annum'])
    # feed_parameters['ethanol_flow'] = etoh_flow

    return etoh_flow

def ethanol_price_converter(price):
    '''
    Function to convert the price of ethanol from USD/gal to USD/kg as BioSTEAM takes in values in USD/kg
    '''
    updated_price = (price*264.172)/789  # 789 is the density of ethanol that is at 20 C from Aspen Plus, a value taken from 2011 Humbird report
    return updated_price

def ensure_unit_add_OPEX(system):
    """
    Ensure every unit in the system has an '_add_OPEX' attribute.
    Useful for applying additional costs, for instance catalyst replacement costs for catalytic reactors
    """
    for unit in system.units:
        if not hasattr(unit, '_add_OPEX'):
            unit._add_OPEX = 0.0