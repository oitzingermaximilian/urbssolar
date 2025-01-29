import os
from matplotlib import ticker
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

# Read data from Excel file
excel_file = "Lernraten_EEM_Paper.xlsx"  # Replace with the actual file name
##########################################################################
#Plot1
df = pd.read_excel(excel_file,sheet_name="Capacity_LR")

# Convert Capacity from Recycling from MW to GW
df['Capacity from Recycling'] = df['Capacity from Recycling'] / 1000

# Plotting the first plot (barplot)
_factor = 1.2  # Adjust this factor to make the plot slightly larger
fig, ax = plt.subplots(figsize=(_factor * 8, _factor * 3.5))  # Increase figure size

# Adjust x_positions for more spacing between bars
x_positions = np.linspace(0, len(df['LR']) - 1, len(df['LR']))  # Spread out x positions
bar_width = 0.4  # Reduce bar width for better spacing

# Plot the bars
ax.bar(x_positions, df['Capacity from Recycling'], color='#F09319', zorder=2, width=bar_width, label='Capacity from Recycling')

# Add value labels on top of each bar (no decimals)
for i, (pos, capacity) in enumerate(zip(x_positions, df['Capacity from Recycling'])):
    if capacity > 0:  # Only add labels for non-zero values
        ax.text(pos, capacity + 40,  # Increase offset for better readability
                s=f"{int(round(capacity))}",  # Rounded to the nearest integer
                ha='center',
                fontsize=12)

# Set x-axis and y-axis labels
ax.set_xlabel("Learning Rate (in %)", fontsize=14, labelpad=15)  # Add padding for better spacing
ax.set_ylabel("Solar PV remanufacturing (in GW)", fontsize=14, labelpad=20)  # Add padding to y-axis label

# Set x-axis limits and adjust for increased spacing
ax.set_xlim(x_positions[0] - 0.5, x_positions[-1] + 0.5)
ax.set_ylim(0, 1500)

# Set x-axis ticks to cover all LR values with adjusted spacing
ax.set_xticks(x_positions)
ax.set_xticklabels(df['LR'], rotation=45, ha='right', fontsize=12)  # Use LR values as labels

# Add grid
ax.grid(which="major", axis="y", color="#758D99", alpha=0.2, zorder=1)

# Customize tick labels
plt.yticks(fontsize=13)

# Format y-axis labels: no decimal, spacing between thousands
formatter = FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", " "))  # Use spaces for thousands
ax.yaxis.set_major_formatter(formatter)

# Adjust layout to prevent label cutoff
plt.tight_layout()  # Automatically adjust to prevent clipping
plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.2)  # Add extra padding for safety

# Save the plot
fig.savefig(os.path.join("Capacity_from_Recycling_BarPlot_Spaced.pdf"), dpi=1000)

# Show the first plot
plt.show()
##########################################################################
#Plot2
# Plotting the second plot (boxplot)
category1 = df[df['LR'] < 3.5]
category2 = df[(df['LR'] >= 3.5) & (df['LR'] < 5)]
category3 = df[df['LR'] >= 5]

# Collect the percentage values for each category
category1_percentages = category1['Ratio to overall in %'].values  # Update column name accordingly
category2_percentages = category2['Ratio to overall in %'].values
category3_percentages = category3['Ratio to overall in %'].values

# New figure for second plot (boxplot)
fig2, ax2 = plt.subplots(figsize=(_factor * 6, _factor * 6))  # Square plot

# Define one color for all categories (orange)
_orange = '#FFA500'  # Pure orange

# Customize the appearance of the boxplots
ax2.boxplot([category1_percentages, category2_percentages, category3_percentages],
            positions=[1, 2, 3], showfliers=True, patch_artist=True,
            boxprops=dict(facecolor=_orange, color=_orange, linewidth=0.8, alpha=0.6),  # Lighter edges
            medianprops=dict(color='black', linewidth=2),
            whiskerprops=dict(color=_orange, linewidth=1.5),
            widths=0.3,  # Adjust width for more spacing between boxes
            capprops=dict(color=_orange, linewidth=1.5))

# Customize labels and title
ax2.set_xlabel("Learning Rate (in %)", fontsize=14)
ax2.set_ylabel("Ratio to overall Additions (%)", fontsize=14)

# Set x-ticks to match categories
ax2.set_xticks([1, 2, 3])
ax2.set_xticklabels(['LR < 3.5', '3.5 ≤ LR < 5', '5 ≤ LR'], fontsize=12)

# Set y-axis limits explicitly to keep it between 0 and 100
ax2.set_ylim(0, 100)

# Format y-axis labels
formatter = ticker.FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", " "))  # Space-separated thousands
ax2.yaxis.set_major_formatter(formatter)

# Add grid
ax2.grid(which="major", axis="y", color="#758D99", alpha=0.2)

# Adjust layout for readability
plt.tight_layout()
fig2.savefig(os.path.join("LR_capacity_distribution.pdf"), dpi=1000)

# Show the second plot
plt.show()
##########################################################################
#Plot3
from scipy import interpolate

# Example DataFrame (replace with your actual data)
df_new = pd.read_excel(excel_file,sheet_name="StockLVL_vs_Remanufacturing")

# Convert Remanufacturing from MW to GW
df_new['Remanufacturing'] = df_new['Remanufacturing'] / 1000

df_new['CUmulativeStocklvl'] = df_new['CUmulativeStocklvl'] / 1000

# Define colors for each Learning Rate (optional, customize as needed)
colors = {
    1: '#1f77b4',
    2: '#ff7f0e',
    2.5: '#2ca02c',
    3: '#d62728',
    3.5: '#9467bd',
    3.55: '#8c564b',
    3.6: '#e377c2',
    3.7: '#7f7f7f',
    3.75: '#bcbd22',
    4: '#17becf',
    4.5: '#1a55FF',
    5: '#FF5733',
    10: '#33FF57',
    25: '#FF33A1'
}

# Plotting
_factor = 1.2  # Adjust this factor to control the size of the plot
fig3, ax3 = plt.subplots(figsize=(_factor * 8, _factor * 4))

# Plot each Learning Rate as a dot
for lr in df_new['Learning Rate in %'].unique():
    subset = df_new[df_new['Learning Rate in %'] == lr]
    ax3.plot(
        subset['CUmulativeStocklvl'],
        subset['Remanufacturing'],
        linewidth=0.,  # No line, just markers
        color=colors[lr],  # Use the color for this Learning Rate
        zorder=3,
        label=f'LR {lr}%',  # Label for the legend
        marker='o',
        markersize=8,
        markeredgecolor = 'black',  # Add black border around the markers
        markeredgewidth = 1
        )



# Format y-axis and x-axis labels with commas and spaces
ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))
ax3.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))

# Add grid
ax3.grid(which="major", axis="y", color="#758D99", alpha=0.5, zorder=1,linestyle='--')
ax3.grid(which="major", axis="x", color="#758D99", alpha=0.5, zorder=1,linestyle='--')

# Set axis labels
ax3.set_ylabel("Solar PV remanufacturing (in GW)", fontsize=13)
ax3.set_xlabel("Cumulative solar module stockpile level (in GW)", fontsize=13)

# Customize legend
# Anzahl der Legenden Einträge (hier 14, du kannst es auch dynamisch berechnen)
n_entries = len(df_new['Learning Rate in %'].unique())

# Legende aufteilen: 2 Reihen und 7 Spalten
ncol = 7
nrow = int(np.ceil(n_entries / ncol))  # Anzahl der Reihen (dynamisch berechnet)

# Customize legend
legend = ax3.legend(
    loc="upper right",  # Positioniert die Legende oben rechts
    facecolor="white",
    fontsize=10,
    handlelength=1.0,
    handletextpad=0.5,
    ncol=ncol,  # 7 Spalten für die Legende
    borderpad=0.5,
    columnspacing=1,
    edgecolor="black",
    frameon=True,
    bbox_to_anchor=(1, 1),  # Position der Legende (sicherstellen, dass sie rechts bleibt)
    shadow=False,
    framealpha=1,
)

# Optional: Legende sortieren (alphabetisch nach LR-Wert)
handles, labels = ax3.get_legend_handles_labels()
labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: float(t[0].split(' ')[1].replace('%', '')), reverse=False))

# Aktualisierte Legende mit sortierten Einträgen
ax3.legend(
    handles=handles,
    labels=labels,
    loc="upper right",
    fontsize=10,
    handlelength=1.0,
    handletextpad=0.5,
    ncol=ncol,
    borderpad=0.5,
    columnspacing=1,
    edgecolor="black",
    frameon=True,
    bbox_to_anchor=(1, 1),  # Die Position leicht nach rechts verschieben
    shadow=False,
    framealpha=1,
)
# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot
fig3.savefig("solar_stock_level_remanufacturing.pdf", dpi=1000)

# Show the plot
plt.show()
##########################################################################
#Plot4
# Example DataFrame (replace with your actual data)
df_new = pd.read_excel(excel_file, sheet_name="StockLVL_vs_Remanufacturing")

# Convert Remanufacturing from MW to GW
df_new['Remanufacturing'] = df_new['Remanufacturing'] / 1000
df_new['CUmulativeStocklvl'] = df_new['CUmulativeStocklvl'] / 1000

# Group the points based on Learning Rate
group1 = df_new[(df_new['Learning Rate in %'] >= 1) & (df_new['Learning Rate in %'] <= 4)]
group2 = df_new[(df_new['Learning Rate in %'] >= 4.5) & (df_new['Learning Rate in %'] <= 25)]

# Filter out points where Remanufacturing is 0
group1 = group1[group1['Remanufacturing'] > 0]
group2 = group2[group2['Remanufacturing'] > 0]

# Define colors for each Learning Rate (optional, customize as needed)
colors = {
    1: '#1f77b4',
    2: '#ff7f0e',
    2.5: '#2ca02c',
    3: '#d62728',
    3.5: '#9467bd',
    3.55: '#8c564b',
    3.6: '#e377c2',
    3.7: '#7f7f7f',
    3.75: '#bcbd22',
    4: '#17becf',
    4.5: '#1a55FF',
    5: '#FF5733',
    10: '#33FF57',
    25: '#FF33A1'
}

# Plotting
_factor = 1.2  # Adjust this factor to control the size of the plot
fig4, ax4 = plt.subplots(figsize=(_factor * 8, _factor * 4))

# Plot each Learning Rate as a dot with different colors
for lr in df_new['Learning Rate in %'].unique():
    subset = df_new[df_new['Learning Rate in %'] == lr]
    ax4.plot(
        subset['CUmulativeStocklvl'],
        subset['Remanufacturing'],
        linewidth=0.,  # No line, just markers
        color=colors[lr],  # Use the color for this Learning Rate
        zorder=3,
        label=f'LR {lr}%',  # Label for the legend
        marker='o',
        markersize=8,
        markeredgecolor='black',  # Add black border around the markers
        markeredgewidth=1
    )

# Function to plot ellipses around the data points
def plot_ellipse(ax, group, color):
    # Fit ellipse using the covariance of the points
    xy = np.column_stack([group['CUmulativeStocklvl'], group['Remanufacturing']])
    mean = np.mean(xy, axis=0)
    cov = np.cov(xy.T)

    # Calculate eigenvalues and eigenvectors of the covariance matrix
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = eigvals.argsort()[::-1]
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]

    # Calculate ellipse parameters
    angle = np.arctan2(eigvecs[1, 0], eigvecs[0, 0]) * 180 / np.pi
    width, height = 2 * np.sqrt(eigvals)

    # Plot ellipse
    ellipse = plt.matplotlib.patches.Ellipse(
        mean, width, height, angle=angle, edgecolor=color, facecolor=color, lw=1.5, linestyle='-', zorder=1, alpha=0.4
    )
    ax.add_patch(ellipse)


# Plot circle around Group 1
if not group1.empty:
    # Calculate mean position of Group 1
    center_x = group1['CUmulativeStocklvl'].mean()
    center_y = group1['Remanufacturing'].mean()

    # Calculate radius as the maximum distance from the center
    distances = np.sqrt((group1['CUmulativeStocklvl'] - center_x) ** 2 +
                        (group1['Remanufacturing'] - center_y) ** 2)
    radius = distances.max()

    # Plot the circle
    circle = plt.matplotlib.patches.Circle(
        (center_x, center_y),
        radius,
        color='blue',
        alpha=0.4,
        zorder=1,
        label='_nolegend_',
        lw = 1.5,
    )
    ax4.add_patch(circle)

# Plot ellipse for Group 2
if not group2.empty:
    plot_ellipse(ax4, group2, 'red')

# Format y-axis and x-axis labels with commas and spaces
ax4.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))
ax4.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " ")))

# Add grid
ax4.grid(which="major", axis="y", color="#758D99", alpha=0.5, zorder=1, linestyle='--')
ax4.grid(which="major", axis="x", color="#758D99", alpha=0.5, zorder=1, linestyle='--')

# Set axis labels
ax4.set_ylabel("Solar PV remanufacturing (in GW)", fontsize=13)
ax4.set_xlabel("Cumulative solar module stockpile level (in GW)", fontsize=13)

# Customize legend (excluding ellipses and circles from the legend)
n_entries = len(df_new['Learning Rate in %'].unique())
ncol = 7
nrow = int(np.ceil(n_entries / ncol))

handles, labels = ax4.get_legend_handles_labels()
labels, handles = zip(
    *sorted(zip(labels, handles), key=lambda t: float(t[0].split(' ')[1].replace('%', '')), reverse=False)
)
ax4.legend(
    handles=handles,
    labels=labels,
    loc="upper right",
    fontsize=10,
    handlelength=1.0,
    handletextpad=0.5,
    ncol=ncol,
    borderpad=0.5,
    columnspacing=1,
    edgecolor="black",
    frameon=True,
    bbox_to_anchor=(1, 1),
    shadow=False,
    framealpha=1,
)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the plot
fig4.savefig("solar_stock_level_remanufacturing_with_circle_and_ellipse.pdf", dpi=1000)

# Show the plot
plt.show()

##########################################################################
#Plot5

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Load your data
df_5 = pd.read_excel(excel_file, sheet_name="Stock_and_Recycling")

# Convert values from MW to GW
stock_columns = [col for col in df_5.columns if col.startswith('STOCK')]
rec_columns = [col for col in df_5.columns if col.startswith('REC')]

df_5[stock_columns] = df_5[stock_columns] / 1000
df_5[rec_columns] = df_5[rec_columns] / 1000

# Prepare data for boxplot
years = df_5['Stf'].unique()

# Plot the boxplot
fig, ax = plt.subplots(figsize=(16, 6))

_color_ind = '#344CB7'
_color_rec = 'orange'

for idx, year in enumerate(years):
    # Plot Stock values
    stock_values = df_5[df_5['Stf'] == year][stock_columns].values.flatten()
    ax.boxplot(stock_values, positions=[idx - 0.2], showfliers=False,
               patch_artist=True,
               boxprops=dict(facecolor=_color_ind, color=_color_ind),
               medianprops=dict(color=_color_ind),
               whiskerprops=dict(color=_color_ind),
               widths=0.4,
               capprops=dict(color=_color_ind)
               )
    min_val_stock = stock_values.min()
    max_val_stock = stock_values.max()
    ax.plot(idx - 0.2, min_val_stock, '*', markersize=4, color=_color_ind)
    ax.plot(idx - 0.2, max_val_stock, '*', markersize=4, color=_color_ind)

    # Plot Recycling values
    rec_values = df_5[df_5['Stf'] == year][rec_columns].values.flatten()
    ax.boxplot(rec_values, positions=[idx + 0.2], showfliers=False,
               patch_artist=True,
               boxprops=dict(facecolor=_color_rec, color=_color_rec),
               medianprops=dict(color=_color_rec),
               whiskerprops=dict(color=_color_rec),
               widths=0.4,
               capprops=dict(color=_color_rec)
               )
    min_val_rec = rec_values.min()
    max_val_rec = rec_values.max()
    ax.plot(idx + 0.2, min_val_rec, '*', markersize=4, color=_color_rec)
    ax.plot(idx + 0.2, max_val_rec, '*', markersize=4, color=_color_rec)

# Customize legend
legend_elements = [
    Line2D([0], [0], color=_color_ind, lw=4, label='Stock Level'),
    Line2D([0], [0], color=_color_rec, lw=4, label='solar PV from remanufacturing')
]
_legend = ax.legend(
    handles=legend_elements,
    loc="upper left",
    facecolor="white",
    fontsize=14,
    handlelength=0.75,
    handletextpad=0.5,
    ncol=2,
    borderpad=0.5,
    columnspacing=1,
    edgecolor="black",
    frameon=True,
    bbox_to_anchor=(0, 1),
    shadow=False,
    framealpha=1,
)

# Customize the plot
ax.set_xticks(range(len(years)))
ax.set_xticklabels(years, fontsize=12, rotation=45)
ax.set_ylabel("Capacities (in GW)", fontsize=14)
ax.set_xlabel("Year", fontsize=14)
ax.grid(which="major", axis="y", color="#758D99", alpha=0.2, zorder=1)

plt.tight_layout()
plt.savefig("stock_recycling_boxplot.pdf", dpi=1000)
plt.show()









