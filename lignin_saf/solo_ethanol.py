# Native biosteam's cellulosic ethanol production simulated




import biosteam as bst
from biorefineries import cellulosic
from lignin_saf.ligsaf_settings import feed_parameters, prices


chems = cellulosic.create_cellulosic_ethanol_chemicals().copy()

bst.settings.set_thermo(chems)

chems.define_group(
    name='Poplar',
    IDs=['Glucan', 'Xylan', 'Arabinan', 'Mannan', 'Galactan',
         'Sucrose', 'Lignin', 'Acetate', 'Extract', 'Ash'],
    composition=[0.464, 0.134, 0.002, 0.037, 0.014,
                 0.001, 0.285, 0.035, 0.016, 0.012],
    wt=True
)

poplar_in = bst.Stream('Poplar_In',
                       Poplar=feed_parameters['flow'] * 1e3,
                       Water=feed_parameters['moisture'] * feed_parameters['flow'] * 1e3,
                       phase='l', units='kg/d', price=prices['Feedstock'])

complete_etoh_system = cellulosic.create_cellulosic_ethanol_system(ins=poplar_in)

complete_etoh_system.simulate()
