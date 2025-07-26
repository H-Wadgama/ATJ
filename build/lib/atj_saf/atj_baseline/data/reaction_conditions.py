
import biosteam as bst, qsdsan as qs



dehydration_parameters = {
    'dehyd_temp' : 481+273.15,   
    'dehyd_pressure' : 1.063e6, 
    'dehyd_conv' : 0.995,       
    'dehyd_WHSV' : 0.3,
    'catalyst_lifetime' : 2 
}




oligomerization_parameters = {
    'olig_temp' : 393.15,     # in K corresponding to 120 C
    'olig_pressure' : 3.5e6,    # 30 bar
    'olig_conv'    : 0.993,       # 99.3% conversion from Heveling paper
    'olig_WHSV'    : 1.5,    # Weighted Hourly Space Velocity
    'catalyst_lifetime' : 1

}

hydrogenation_parameters = {
    'hydgn_temp' : 623.15,    # in K corresponding to 250 c
    'hydgn_pressure' : 3.5e6,   # 3More info in HydrogenationReactor class documentation
    'hydgn_conv' : 1.0, 
    'hydgn_WHSV' : 3,
    'catalyst_lifetime' : 3
}
