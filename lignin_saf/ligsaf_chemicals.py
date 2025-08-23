import biosteam as bst, biorefineries as bf
from biorefineries import cellulosic


ligsaf_chemicals = cellulosic.create_cellulosic_ethanol_chemicals().copy()   # Creating a copy of the cellulosic ethanol chemicals


# Appending methanol and other relevant chemicals I would require 
add_chems = bst.Chemicals(['Methanol',  
                           'Hydrogen'])

ligsaf_chemicals.extend(add_chems)

