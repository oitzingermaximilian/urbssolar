from kiwisolver import Constraint
from openpyxl.styles.builtins import output
import pandas as pd
from pyomo.environ import *

# Define the model
model = ConcreteModel()

#experimental data import
df = pd.read_excel('C:/Users/Gerald/Desktop/urbs-test/urbs/Input/urbs_solar_test.xlsx')
demand_dict = df.set_index('t')['EU27.Elec'].to_dict()
# Define timesteps (years from 2024 to 2050)
offset = 2024
length = 2050 - 2024
timesteps = range(offset, offset + length + 1)  # From 2024 to 2050 inclusive
dt = 1  # length of each time step (unit: years)

support_timeframes = range(offset, offset + length + 1)
model.cost_solar_list = ['Importcost','Storagecost','Eu Cost Primary','Eu Cost Secondary']
# Sets
model.y = Set(initialize=support_timeframes)
model.n = Param(initialize=5, within=NonNegativeIntegers)
model.y_end = Param(initialize=2050, within=NonNegativeIntegers)
model.l = Param(initialize=10, within=NonNegativeIntegers)
model.tm = Set(initialize=[1])  # Time periods
model.sit = Set(initialize=['Mid'])# Site types
# Parameters
model.Installed_Capacity_Q_s = Param(initialize=10)  # Initial installed capacity
model.y0 = Param(initialize=2024, within=NonNegativeIntegers)  # Initial year
model.Existing_Stock_Q_stock = Param(initialize=40)
model.IMPORTCOST = Param(initialize=100000)
model.STORAGECOST = Param(initialize=20000)
model.EU_primary_costs = Param(initialize=100)
model.EU_secondary_costs = Param(initialize=5)
model.FT = Param(initialize=3)  # Factor between 0 and 1
model.anti_dumping_index = Param(initialize=1.25)
model.deltaQ_EUprimary = Param(initialize=3)
model.IR_EU_primary = Param(initialize=10)
model.deltaQ_EUsecondary = Param(initialize=5)
model.IR_EU_secondary = Param(initialize=15)
model.DCR_solar = Param(initialize=20)
model.DR_primary = Param(initialize=1.2)
model.DR_secondary = Param(initialize=1.3)
# Demand parameter for each year

model.demand =  Param(model.y, initialize=demand_dict) #Param(model.y, initialize={
    #2024: 50.0, 2025: 52.0, 2026: 54.0, 2027: 56.0, 2028: 58.0,
    #2029: 60.0, 2030: 62.0, 2031: 64.0, 2032: 66.0, 2033: 68.0,
   # 2034: 70.0, 2035: 72.0, 2036: 74.0, 2037: 76.0, 2038: 78.0,
    #2039: 80.0, 2040: 82.0, 2041: 84.0, 2042: 86.0, 2043: 88.0,
    #2044: 90.0, 2045: 92.0, 2046: 94.0, 2047: 96.0, 2048: 98.0,
    #2049: 100.0, 2050: 102.0
#})
#Instalable Capacity each year

model.Q_Solar_new = Param(model.y, initialize={
    2024: 56.0, 2025: 56.0 * 1.05, 2026: 56.0 * 1.05**2, 2027: 56.0 * 1.05**3, 2028: 56.0 * 1.05**4,
    2029: 56.0 * 1.05**5, 2030: 56.0 * 1.05**6, 2031: 56.0 * 1.05**7, 2032: 56.0 * 1.05**8, 2033: 56.0 * 1.05**9,
    2034: 56.0 * 1.05**10, 2035: 56.0 * 1.05**11, 2036: 56.0 * 1.05**12, 2037: 56.0 * 1.05**13, 2038: 56.0 * 1.05**14,
    2039: 56.0 * 1.05**15, 2040: 56.0 * 1.05**16, 2041: 56.0 * 1.05**17, 2042: 56.0 * 1.05**18, 2043: 56.0 * 1.05**19,
    2044: 56.0 * 1.05**20, 2045: 56.0 * 1.05**21, 2046: 56.0 * 1.05**22, 2047: 56.0 * 1.05**23, 2048: 56.0 * 1.05**24,
    2049: 56.0 * 1.05**25, 2050: 56.0 * 1.05**26
})

# Variables
model.capacity_solar = Var(model.y, domain=NonNegativeReals)  # Capacity for each year
model.capacity_solar_new = Var(model.y, domain=NonNegativeReals)  # New capacity added each year
model.capacity_solar_imported = Var(model.y, domain=NonNegativeReals)
model.capacity_solar_stockout = Var(model.y, domain=NonNegativeReals)
model.capacity_solar_euprimary = Var(model.y, domain=NonNegativeReals)
model.capacity_solar_eusecondary = Var(model.y, domain=NonNegativeReals)
model.capacity_solar_stock = Var(model.y, domain=NonNegativeReals)
model.capacity_solar_stock_imported = Var(model.y, domain=NonNegativeReals)
model.importcost = Var(model.y, domain=NonNegativeReals)
model.storagecost = Var(model.y, domain=NonNegativeReals)
model.costs_eu_primary = Var(model.y, domain=NonNegativeReals)
model.costs_eu_secondary = Var(model.y, domain=NonNegativeReals)
model.sum_outofstock = Var(model.y, domain=NonNegativeReals)
model.sum_stock = Var(model.y, domain=NonNegativeReals)
model.anti_dumping_measures = Var(model.y, domain=NonNegativeReals)

#Extension Pyomo Variables to use in urbs

model.costs_eu_primary_full = Var(model.tm, model.y, model.sit, domain=NonNegativeReals)
model.costs_eu_primary_full = Var(model.tm, model.y, model.sit, domain=NonNegativeReals)
model.costs_eu_primary_full = Var(model.tm, model.y, model.sit, domain=NonNegativeReals)
model.costs_eu_primary_full = Var(model.tm, model.y, model.sit, domain=NonNegativeReals)
# Constraints

# Constraint 1: capacity_solar_y = capacity_solar_y-1 + capacity_solar_new_y for all y > y0
def capacity_solar_growth_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar[y] == m.capacity_solar[y-1] + m.capacity_solar_new[y]

model.capacity_solar_growth_constraint = Constraint(model.y, rule=capacity_solar_growth_rule)

# Constraint 2: capacity_solar_y = Installed_Capacity_Q_s + capacity_solar_new_y for y = y0
def initial_capacity_rule(m, y):
    if y == m.y0:
        return m.capacity_solar[y] == m.Installed_Capacity_Q_s + m.capacity_solar_new[y]
    else:
        return Constraint.Skip

model.initial_capacity_constraint = Constraint(model.y, rule=initial_capacity_rule)

#Constraint 3: capacity_solar_new_y = sum of capacities for all y

def capacity_solar_new_rule(m, y):
    return m.capacity_solar_new[y] == m.capacity_solar_imported[y] + m.capacity_solar_stockout[y] + m.capacity_solar_euprimary[y] + m.capacity_solar_eusecondary[y]

model.capacity_solar_new_constraint = Constraint(model.y, rule=capacity_solar_new_rule)

#Constraint 4:
def capacity_solar_stock_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar_stock[y] == m.capacity_solar_stock[y-1] + m.capacity_solar_stock_imported[y] - m.capacity_solar_stockout[y]

model.capacity_solar_stock_constraint = Constraint(model.y, rule=capacity_solar_stock_rule)

#Constraint 5:
def capacity_solar_stock_initial_rule(m, y):
    if y == m.y0:
        return model.capacity_solar_stock[y] == m.Existing_Stock_Q_stock + m.capacity_solar_stock_imported[y] - m.capacity_solar_stockout[y]
    else:
        return Constraint.Skip

model.capacity_solar_stock_initial_constraint = Constraint(model.y, rule=capacity_solar_stock_initial_rule)

#Constraint 6:
def importcost_solar_rule(m, y):
    return m.importcost[y] == m.IMPORTCOST * (m.capacity_solar_imported[y]+ m.capacity_solar_stock_imported[y])

model.importcost_solar_constraint = Constraint(model.y, rule=importcost_solar_rule)

#Constraint 7:
def storagecost_solar_rule(m, y):
    return m.storagecost[y] == m.STORAGECOST * m.capacity_solar_stock[y]

model.storagecost_solar_constraint = Constraint(model.y, rule=storagecost_solar_rule)

#Constraint 8:
def manufacturingcost_primary_solar_rule(m, y):
    return  m.costs_eu_primary[y] == m.EU_primary_costs * m.capacity_solar_euprimary[y]

model.manufacturingcost_primary_solar_constraint = Constraint(model.y, rule=manufacturingcost_primary_solar_rule)

#Constraint 9:
def manufacturingcost_secondary_solar_rule(m, y):
    return  m.costs_eu_secondary[y] == m.EU_secondary_costs * m.capacity_solar_eusecondary[y]

model.manufacturingcost_secondary_solar_constraint = Constraint(model.y, rule=manufacturingcost_secondary_solar_rule)

#Constraint 10&11: stock turnover
def compute_sum_outofstock_rule(m, y):
    if y <= max(m.y) - m.n:
        return sum(m.capacity_solar_stockout[j] for j in range(y, y + m.n)) - m.sum_outofstock[y] == 0
    else:
        return Constraint.Skip

model.compute_sum_outofstock_constraint = Constraint(model.y, rule=compute_sum_outofstock_rule)

def stock_turnover_rule(m, y):
    if y <= max(m.y) - m.n:
        return m.sum_outofstock[y] >= m.FT * (1 / m.n) * sum(m.capacity_solar_stock[j] for j in range(y, y + m.n))
    else:
        return Constraint.Skip

model.stock_turnover_constraint = Constraint(model.y, rule=stock_turnover_rule)

#Constraint 12:
def anti_dumping_measures_rule(m, y):
    return m.anti_dumping_measures[y] == m.anti_dumping_index * (m.capacity_solar_imported[y]+ m.capacity_solar_stock_imported[y])

model.anti_dumping_measures_constraint = Constraint(model.y,rule=anti_dumping_measures_rule)


#Constraint 13:
def capacity_solar_new_limit_rule(m, y):
    return m.capacity_solar_new[y] <= m.Q_Solar_new[y]

#model.capacity_solar_new_limit_constraint = Constraint(model.y, rule=capacity_solar_new_limit_rule)

#Constraint 14: time delay constraint for Eu primary
def timedelay_EU_primary_production_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar_euprimary[y] - m.capacity_solar_euprimary[y-1] <= \
            m.deltaQ_EUprimary + m.IR_EU_primary * m.capacity_solar_euprimary[y-1]

model.timedelay_EU_primary_production_constraint = Constraint(model.y,rule=timedelay_EU_primary_production_rule)

#Constraint 15: time delay constraint for EU secondary
def timedelay_EU_secondary_production_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar_eusecondary[y] - m.capacity_solar_eusecondary[y-1] <= \
            m.deltaQ_EUsecondary + m.IR_EU_secondary * m.capacity_solar_eusecondary[y-1]


model.timedelay_EU_secondary_production_constraint = Constraint(model.y,rule=timedelay_EU_secondary_production_rule)

#Constraint 16:
def constraint1_EU_secondary_to_total_rule(m, y):
    if m.y0 <= y-m.l:
        return m.capacity_solar_eusecondary[y] <= m.capacity_solar_new[y-m.l]
    else:
        return Constraint.Skip

model.constraint_EU_secondary1_to_total_constraint = Constraint(model.y,rule=constraint1_EU_secondary_to_total_rule)

#Constraint 17:
def constraint2_EU_secondary_to_total_rule(m, y):
    if m.y0 >= y-m.l:
        return m.capacity_solar_eusecondary[y] <= m.DCR_solar * m.capacity_solar[y]
    else:
        return Constraint.Skip

model.constraint_EU_secondary2_to_total_constraint = Constraint(model.y,rule=constraint2_EU_secondary_to_total_rule)

#Constraint 18:
def constraint_EU_primary_to_total_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar_euprimary[y] >= m.DR_primary * m.capacity_solar_euprimary[y-1]

model.constraint_EU_primary_to_total_constraint = Constraint(model.y,rule=constraint_EU_primary_to_total_rule)

#Constraint 19:
def constraint_EU_secondary_to_secondary_rule(m, y):
    if y == m.y0:
        return Constraint.Skip
    else:
        return m.capacity_solar_eusecondary[y] >= m.DR_secondary * m.capacity_solar_eusecondary[y-1]

model.constraint_EU_secondary_to_secondary_constraint = Constraint(model.y,rule=constraint_EU_secondary_to_secondary_rule)
#Constraint 20:
#Constraint 21:
#change variables so they are usable in urbs
# Demand constraint: Ensure capacity solar meets or exceeds demand for each year
def demand_constraint_rule(m, y):
    return m.capacity_solar[y] >= m.demand[y]

model.demand_constraint = Constraint(model.y, rule=demand_constraint_rule)

# Objective Function: Minimize the total new capacity added
def objective_rule(m):
    total_import_cost = sum(m.importcost[y] for y in m.y)
    total_storage_cost = sum(m.storagecost[y] for y in m.y)
    total_manufacture_cost = sum(m.costs_eu_primary[y] for y in m.y)
    total_recycling_cost = sum(m.costs_eu_secondary[y] for y in m.y)
    print('Urbs Solar Costs:', total_import_cost, total_storage_cost, total_manufacture_cost, total_recycling_cost)
    return total_import_cost + total_storage_cost + total_manufacture_cost + total_recycling_cost

model.objective = Objective(rule=objective_rule, sense=minimize)


# Solve the model
solver = SolverFactory('glpk')
results = solver.solve(model, tee=True)

# Display results
print("Results:")
for y in model.y:
    print(f"Year {y}: Capacity Solar = {model.capacity_solar[y].value}")
    print(f"Year {y}: Capacity Solar New = {model.capacity_solar_new[y].value}")
    print(f"Year {y}: Capacity Solar Stock = {model.capacity_solar_stock[y].value}")
    print(f"Year {y}: Importcost = {model.importcost[y].value}")
    print(f"Year {y}: Storagecost = {model.storagecost[y].value}")
    print(f"Year {y}: Manufacturing Cost Primary = {model.costs_eu_primary[y].value}")
    print(f"Year {y}: Manufacturing Cost Secondary = {model.costs_eu_secondary[y].value}")


# Display the model status
model.display()





