# Lignin valorization to SAF through RCF

This is a BioSTEAM model for lignin valorization to SAF currently under development

The baseline model assumes a poplar feedstock (2000 dry metric ton per day) and methanol water as a solvent for RCF. The choice of biomass and solvent primarily due to the availability of literature data

The main process assumptions:
_The loss of carbohydrate retention in biomass pulp post RCF is due to solvent dissolution_: Carbohydrate retention can decrease due to solvent dissolution or lost in side reactions. Since the reaction assembly is such that it allows for independent solvolysis and hydrogenolysis, we can assume that the loss of carbohydrate retention is exlusively due to dissolution in solvent


_Delignification extent is constant throughout residence time of solvolysis_: This assumption can be false since as the reaction proceeds, the content of lignin in biomass reduces and this could lead to concentration hotspots of lignin in the poplar bed. However, we assume that delignication stays constant throughout the biomass bed because the continuous flow of fresh solvent allows for a maximum diffusive flux between the solvent and the biomass [1](https://pubs.acs.org/doi/10.1021/acssuschemeng.8b01256). 







