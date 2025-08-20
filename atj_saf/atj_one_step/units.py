from pint import UnitRegistry


u = UnitRegistry()
Q_ = u.Quantity  # convenience alias


# Adding units
'''
u.define("million = 1e6 = MM = mil")
u.define("mgpy = MM * gallon / year = mgpy = MMgal_per_year")
'''

try:
    u.MGal  # if already defined elsewhere, this won't run
except Exception:
    u.define("MGal = 1e6 * gallon = MGAL = million_gallon")
    u.define("mgpy = MGal / year = MGAL_per_year")