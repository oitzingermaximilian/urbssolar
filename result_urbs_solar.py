import os
import pandas as pd
import matplotlib.pyplot as plt

# Set the directory where the results are located
result_dir = 'result/urbs-rerun-20241202T1854'  # Adjust this path as needed

for filename in os.listdir(result_dir):
    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
        file_path = os.path.join(result_dir, filename)
        try:
            df = pd.read_excel(file_path, sheet_name="us_capacity")
            print(f"Processing file: {filename}")
            if df['Site'].notna().any():
                site_value = df['Site'].dropna().iloc[0]
                df['Site'].fillna(site_value, inplace=True)

            df['Stf'].fillna(method='ffill', inplace=True)
            df['Stf'] = df['Stf'].astype(float)  # Ensure 'Stf' is float

            # Initial solar capacity to be added (260,000 MW = 260 GW)
            initial_capacity_mw = 260000
            years = df['Stf'].unique()

            initial_capacity_df = pd.DataFrame({
                'Stf': years,
                'Process': ['initial_solar_capacity'] * len(years),
                'Total': [initial_capacity_mw] * len(years)
            })

            df_combined = pd.concat([df, initial_capacity_df], ignore_index=True)
            df_pivot = df_combined.pivot_table(index='Stf', columns='Process', values='Total', aggfunc='sum', fill_value=0)

            # Convert capacities from MW to GW
            df_pivot_gw = df_pivot / 1e3
            df_pivot_gw = df_pivot_gw[['initial_solar_capacity'] +
                                        [col for col in df_pivot_gw.columns if col != 'initial_solar_capacity']]
            ax = df_pivot_gw.plot(kind='bar', stacked=True, figsize=(10, 6))
            plt.title(f'Total Capacities by Year for {filename}')
            plt.xlabel('Year')
            plt.ylabel('Total Capacity (GW)')
            plt.legend(title='Process', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(ticks=range(len(df_pivot.index)), labels=[int(year) for year in df_pivot.index], rotation=90, fontsize=8)
            plt.grid(axis='y')

            # Save
            output_file = os.path.join(result_dir, f'{filename}_total_capacities.png')
            plt.tight_layout()
            plt.savefig(output_file)
            print(f'Saved stacked bar plot as: {output_file}')
            plt.clf()

            #next plot
            df_solar = df[df['Process'].str.startswith('capacity_solar_')]
            initial_capacity_df = pd.DataFrame({
                'Stf': years,
                'Process': ['initial_solar_capacity'] * len(years),
                'Total': [initial_capacity_mw] * len(years)
            })
            df_solar = pd.concat([df_solar, initial_capacity_df], ignore_index=True)
            df_solar_pivot = df_solar.pivot_table(index='Stf', columns='Process', values='Total', aggfunc='sum', fill_value=0)
            df_solar_pivot_gw = df_solar_pivot / 1e3  # Convert MW to GW
            df_solar_pivot_gw = df_solar_pivot_gw[['initial_solar_capacity'] +
                                                  [col for col in df_solar_pivot_gw.columns if col != 'initial_solar_capacity']]
            ax_solar = df_solar_pivot_gw.plot(kind='bar', stacked=True, figsize=(10, 6))
            plt.title(f'Solar Capacities by Year for {filename}')
            plt.xlabel('Year')
            plt.ylabel('Total Capacity (GW)')
            plt.legend(title='Solar Process', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(ticks=range(len(df_solar_pivot.index)), labels=[int(year) for year in df_solar_pivot.index], rotation=90, fontsize=8)
            plt.grid(axis='y')

            # Save
            output_file_solar = os.path.join(result_dir, f'{filename}_solar_capacities.png')
            plt.tight_layout()
            plt.savefig(output_file_solar)
            print(f'Saved solar capacities plot as: {output_file_solar}')

            # new plot
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = plt.cm.tab10(range(len(df_solar_pivot_gw.columns)))  # Define colors
            ax.stackplot(df_solar_pivot_gw.index, *df_solar_pivot_gw.T.values, labels=df_solar_pivot_gw.columns, colors=colors)
            ax.set_title(f'Total Capacities Over Time for {filename}', fontsize=14)
            ax.set_xlabel('Year', fontsize=12)
            ax.set_ylabel('Total Capacity (GW)', fontsize=12)
            ax.legend(title='Process', loc='upper left', bbox_to_anchor=(1, 1), fontsize=10)
            ax.set_xticks(df_solar_pivot_gw.index)
            ax.set_xticklabels([int(year) for year in df_solar_pivot_gw.index], rotation=90, fontsize=8)

            plt.tight_layout()
            output_file_stack = os.path.join(result_dir, f'stackplot_total_solar_capacities_{filename}.png')
            plt.savefig(output_file_stack)  # Save the stack plot
            print(f'Saved stack plot as: {output_file_stack}')
            plt.clf()  # Clear the current figure

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

#cost plots
for filename in os.listdir(result_dir):
    if filename.startswith("scenario_") and filename.endswith(".xlsx"):
        file_path = os.path.join(result_dir, filename)
        try:
            df = pd.read_excel(file_path, sheet_name="Combined Costs Urbs Solar")
            print(f"Processing file: {filename}")
            if df['pro'].notna().any():
                pro_value = df['pro'].dropna().iloc[0]
                df['pro'].fillna(pro_value, inplace=True)

            df['stf'].fillna(method='ffill', inplace=True)
            df['stf'] = df['stf'].astype(float)

            df_pivot = df.pivot_table(index='stf', columns='pro', values='Total_Cost', aggfunc='sum', fill_value=0)

            ax = df_pivot.plot(kind='bar', stacked=True, figsize=(10, 6))
            plt.title('Total Costs by Year')
            plt.xlabel('Year')
            plt.ylabel('Total Cost')
            plt.legend(title='Process', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(ticks=range(len(df_pivot.index)), labels=[int(year) for year in df_pivot.index], rotation=90, fontsize=8)
            plt.grid(axis='y')

            plt.tight_layout()
            output_file_stack = os.path.join(result_dir, f'barplot_totalcosts_{filename}.png')
            plt.savefig(output_file_stack)  # Save the stack plot
            print(f'Saved stack plot as: {output_file_stack}')
            plt.clf()  # Clear the current figure

            if 'Total_Cost' in df.columns:
                # Step 4: Group by year (assuming 'Year' is in 'Stf') and sum total costs
                df_total_costs = df.groupby('stf')['Total_Cost'].sum().reset_index()

                # Step 5: Create a line plot for total costs over time
                plt.figure(figsize=(10, 6))
                plt.plot(df_total_costs['stf'], df_total_costs['Total_Cost'], linestyle='-', color='blue')

                # Step 6: Customize the line plot
                plt.title('Total Costs Over Time')
                plt.xlabel('Year')
                plt.ylabel('Total Cost in €')  # Adjust based on your currency
                plt.xticks(rotation=45)  # Rotate x-ticks for better visibility

                # Save the plot
                output_file = os.path.join(result_dir, f'total_costs_over_time_{filename}.png')
                plt.tight_layout()  # Adjust layout to make room for labels
                plt.savefig(output_file)
                print(f'Saved line plot as: {output_file}')

                plt.clf()  # Clear the figure

        except Exception as e:
            print(f"Error processing file {filename}: {e}")
