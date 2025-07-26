
import biosteam as bst, qsdsan as qs



dehyd_data = {
    'temp' : 481+273.15,   
    'pressure' : 1.063e6, 
    'conv' : 0.995,       
    'whsv' : 0.3,
    'catalyst_lifetime' : 2 
}




olig_data = {
    'temp' : 393.15,     # in K corresponding to 120 C
    'pressure' : 3.5e6,    # 30 bar
    'conv'    : 0.993,       # 99.3% conversion from Heveling paper
    'whsv'    : 1.5,    # Weighted Hourly Space Velocity
    'catalyst_lifetime' : 1

}

prod_selectivity = {              # More info in the OligomerizationReactor class doc.
                    'C4H8'  : 0.2,          # 0.2
                    'C6H12' : 0.15,          # 0.15
                    'C10H20': 0.62,          # 0.62
                    'C18H36': 0.03,          # 0.03
                    }           


hydgn_data = {
    'temp' : 623.15,    # in K corresponding to 250 c
    'pressure' : 3.5e6,   # 3More info in HydrogenationReactor class documentation
    'conv' : 1.0, 
    'whsv' : 3,
    'catalyst_lifetime' : 3
}
