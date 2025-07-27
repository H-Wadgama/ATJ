operators_per_section = 1  # operators per section from Seider recommendation
num_process_sections = 5  # number of proces sections from Seider recommendation [3 reactor, 2 separation]
num_operators_per_shift = operators_per_section * num_process_sections * 1  # multiplied by 2 for large continuous flow process (e.g., 1000 ton/day product). from Seider pg 505
num_shifts = 5  # number of shifts
pay_rate = 40  # $/hr
DWandB = num_operators_per_shift * num_shifts * 2080 * pay_rate  # direct wages and benefits. DWandB [$/year] = (operators/shift)*(5 shifts)*(40 hr/week)*(operating days/year-operator)*($/hr)
Dsalaries_benefits = 0.15 * DWandB  # direct salaries and benefits from Seider
O_supplies = 0.06 * DWandB  # Operating supplies and services from Seider
technical_assistance = 5 * 75000  # $/year. Technical assistance to manufacturing. assume 5 workers at $75000/year
control_lab = 5 * 80000  # $/year. Control laboratory. assume 5 workers at $80000/year
labor = DWandB + Dsalaries_benefits + O_supplies + technical_assistance + control_lab 


IRR = 0.10
duration = (2023, 2053)
depreciation = 'MACRS7'
income_tax = 0.21
operating_days = 330
lang_factor = 5.04
construction_schedule = (0.08, 0.60, 0.32)
WC_over_FCI = 0.05
labor_cost = labor
property_tax = 0.001
property_insurance = 0.005
maintenance = 0.01
administration = 0.005