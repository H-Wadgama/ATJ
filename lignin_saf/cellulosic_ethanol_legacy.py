import biosteam as bst
import thermosteam as tmo
import biorefineries as bf
from biorefineries import cellulosic
from biosteam import main_flowsheet as F
from cellulosic_tea import create_cellulosic_ethanol_tea



chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()

bst.settings.set_thermo(chems) # Setting thermodynamic property pacakge for the chemicals



stover = bst.Stream(
                ID='Stover',
                price=0.0516,
                total_flow=104229.16,
                units='kg/hr',
                Water=0.20215,
                Sucrose=0.00623,
                Extract=0.11846,
                Acetate=0.01464,
                Ash=0.03986,
                Lignin=0.12744,
                Protein=0.02507,
                Glucan=0.28302,
                Xylan=0.15788,
                Arabinan=0.01925,
                Mannan=0.00485,
                Galactan=0.00116,
            )


etoh_system = cellulosic.create_cellulosic_ethanol_system(ins = stover)


etoh_system.simulate()


etoh_system.show()