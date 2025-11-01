"""

Ethanol-to-Jet biorefinery for Sustainable Aviation Fuel production 
The Pennsylvania State University
Chemical Engineering Department
S2D2 Lab (Dr. Rui Shi)
@author: Hafi Wadgama

This file contains:
Utility functions that can be used for the biorefinery

Detailed information about the literature values is provided in Supplementary of doi....

"""

def calculate_ethanol_flow(req_saf = None, operating_factor = None):
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

    if operating_factor is None:
        operating_factor = 0.9


    etoh_flow = ((1/0.56)*(1/0.8)*req_saf*1e6*(1/264.17)*776)/(operating_factor*365*24)
    
    return etoh_flow