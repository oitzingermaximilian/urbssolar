import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

# Read the new data from 'us_balance'
_results_dir = 'result/Intertemp-20241023T1429'
file_path = os.path.join(_results_dir, 'scenario_base.xlsx')
df = pd.read_excel(file_path, sheet_name='us_balance')

# Extract unique years (Stf column)
years = df['Stf'].unique()

# Define the energy sources (categories)
carriers = ['Biomass Plant', 'Wind (onshore)', 'Wind (offshore)', 'Nuclear Plant',
            'Hydro (run-of-river)', 'Hydro (reservoir)', 'Gas Plant (CCGT)', 'Coal Plant',
            'Coal Lignite', 'Solar']

# Initialize empty DataFrames for each year (to store energy demand by carrier)
energy_dem_y = pd.DataFrame(index=carriers, columns=years)

# Fill the DataFrame with the values from your dataset
for year in years:
    temp_df = df[df['Stf'] == year]
    for carrier in carriers:
        energy_dem_y.loc[carrier, year] = pd.to_numeric(temp_df[temp_df['Process'] == carrier]['Value'], errors='coerce').sum()

# Convert the data into TWh for plotting and handle NaNs
energy_dem_plot = energy_dem_y / 1e6  # Convert to TWh
energy_dem_plot = energy_dem_plot.apply(pd.to_numeric, errors='coerce')  # Ensure all values are numeric
energy_dem_plot.fillna(0, inplace=True)  # Replace NaN values with 0

# Generate the stackplot
fig, ax = plt.subplots(figsize=(10, 6))

# Prepare the data for stackplot
x = years
y = energy_dem_plot.values  # Values to be stacked

# Define colors for each energy source
colors = {
    'Biomass Plant': '#FFB347',         # Pastel blue for biomass
    'Wind (onshore)': '#77DD77',        # Pastel green for onshore wind
    'Wind (offshore)': '#006400',       # Dark green for offshore wind
    'Nuclear Plant': '#FFB6C1',         # Light pastel pink for nuclear
    'Hydro (run-of-river)': '#A0C4E1',  # Light pastel blue for run-of-river hydro
    'Hydro (reservoir)': '#74B3D6',     # Slightly darker pastel blue for reservoir hydro
    'Solar': '#FDFD96',                 # Pastel yellow for solar
    'Gas Plant (CCGT)': '#FF6961',      # Light red for gas
    'Coal Plant': '#B0B0B0',            # Light grey for coal plant
    'Coal Lignite': '#808080'           # Dark grey for coal lignite
}

# Stackplot for each carrier
ax.stackplot(x, y, labels=carriers, colors=[colors[carrier] for carrier in carriers], alpha=0.8)

# Set grid, labels, and limits
ax.grid(which="major", axis="y", color="#758D99", alpha=0.4, zorder=1)
ax.set_ylabel('Energy produced in TWh', fontsize=17)
ax.set_ylim([0, energy_dem_plot.sum(axis=0).max() + 10])
ax.set_yticklabels(ax.get_yticks(), fontsize=15)

# Set ticks for all years (including unlabeled ones)
ax.set_xticks(years)  # Set ticks for every year

# Label specific years, keeping other years unlabeled
ax.set_xticklabels([str(year) if year in [2025, 2030, 2035, 2040, 2045, 2050] else ''
                    for year in years], fontsize=17)

# Customize tick appearance
ax.tick_params(axis='x', which='major', length=5)  # Short ticks for all years
ax.tick_params(axis='x', which='minor', length=3)  # Even smaller ticks for any minor ones (optional)

# Add a legend for the stackplot above the plot
ax.legend(loc='lower center', facecolor='White', fontsize=12, framealpha=0.8,
          ncol=3, borderpad=0.75, edgecolor="black", bbox_to_anchor=(0.5, 1.05))

# Final layout adjustments and save the figure
plt.tight_layout()
#fig_dem_name = os.path.join(_results_dir, 'demand_' + 'scenario_name' + '.pdf')  # Replace 'scenario_name' with an actual name or variable if needed
#plt.savefig(fig_dem_name)
plt.show()