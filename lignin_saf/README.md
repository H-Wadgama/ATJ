# Lignin valorization to SAF through RCF

This is a BioSTEAM model for lignin valorization to SAF currently under development

The baseline model assumes a poplar feedstock (2000 dry metric ton per day) and methanol water as a solvent for RCF. The choice of biomass and solvent primarily due to the availability of literature data

The main process assumptions:
_The loss of carbohydrate retention in biomass pulp post RCF is due to solvent dissolution_: Carbohydrate retention can decrease due to solvent dissolution or  reaction within the solvent [1](https://pubs.rsc.org/en/content/articlelanding/2021/ee/d0ee02870c). Here we assume that the carbohydrates are only solubilized and are not reacting with the solvent. 


_The extraction efficiency of lignin is 100%_: We assume that delignification (i.e. solvolysis + extraction) is only dependent on the solvolysis reaction, and that the extraction efficiency is always 100%.


_Delignification extent is constant throughout residence time of solvolysis_: This assumption can be false since as the reaction proceeds, the content of lignin in biomass reduces and this could lead to concentration hotspots of lignin in the poplar bed. However, we assume that delignication stays constant throughout the biomass bed because the continuous flow of fresh solvent allows for a maximum diffusive flux between the solvent and the biomass [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). 


_Residence time across RCF is divided in the ratio of 2:1_ Across the literature, the reported residence time in RCF for poplar/methanol systems has been 3 hours, but studies haven't quantified the breakdown of this residence time between the solvolysis and hydrogenolysis+hydrogenation steps. While residence time won't be distributed for batch systems, it will be distributed for flow-through assemblies where the biomass beds and catalyst beds are essentially separate reactors. Kinetic study Bekham and Yuriy Roman-Leshkov's group has implied that in typical RCF conditions employed in the literature, solvolysis is the kinetically limiting step [2](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256) and therefore, I divide the residence time as 2 hour in solvolysis and 1 hour in hydrogenolysis for the total residence time to equal 3 hour. This ratio might be different depending on how much exactly is solvolyis limiting the overall rate. It is to note that a study by Brandi et al on beech wood sawdust [3](https://pubs.rsc.org/en/content/articlelanding/2023/su/d2su00076h) reveals the distribution of residence time as equal (50 minutes for each step) but that was the only breakdown I found, and given the kinetic considerations, I think 2 hours for solvolysis and 1 hour for hydrogenolysis is more appropriate. 





