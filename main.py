# Importing required libraries
import os
import pandas as pd
import matplotlib.pyplot as plt

def load_data():
    ''' Function to load cycle time data from a CSV file. '''

    df = pd.read_csv('data/cycle_time.csv', sep=';')

    # Printing the first few rows of the dataframe to verify data loading
    print('\nFirst few rows of the loaded data:')
    print(df.head().to_string(index=False))

    return df

def analyse_cycle_time(dataframe):
    ''' Compute basic statistics for cycle time data 

    Parameters:
        dataframe (pd.DataFrame): The dataframe containing cycle time data.

    Returns: 
        stats (dict): A dictionary containing mean, max, min and standard deviation of the cycle time data.
    
    '''

    stats = {
        'mean': dataframe['cycle_time'].mean(),
        'max': dataframe['cycle_time'].max(),
        'min': dataframe['cycle_time'].min(),
        'std': dataframe['cycle_time'].std()
    }
    
    # Prints the computed statistics in a readable format
    print('\nCycle Time Data Statistics:')
    for i, j in stats.items():
        print(f'{i} = {j:.2f}s')
    return stats

def detect_anomalies(df, min_limit=50, max_limit=70):
    ''' 
    Detects cycle time values outside a specified range in a dataframe
    
    Parameters:
        df: pandas.DataFrame
        min_limit: int or float, optional, default=50
        max_limit: int or float, optional, default=70
        
    Returns:
        pandas.DataFrame containing only the rows from the original where 'cycle_time' is outside the range
    
    '''

    # Filter rows where the cycle time is outside the allowed range
    anomalies = df[(df['cycle_time'] < min_limit) | (df['cycle_time'] > max_limit)] # Filters rows where cycle_time is lower than min or higher than max


    if anomalies.empty:
        print('\nNo anomalies detected.')
    else:
        print('\nAnomalies detected:')
        print(anomalies[['time', 'cycle_time']].to_string(index=False))

    return anomalies

def generate_plot(df, output_filename):
    
    results_dir = os.path.join(os.getcwd(), 'results') # Defines the path to the results directory
    os.makedirs(results_dir, exist_ok=True) # Creates the results directory if it doesn't exist

    # Complete path to save the plot
    output_path = os.path.join(results_dir, output_filename)

    # Plotting the cycle time data
    plt.figure()
    plt.plot(df['time'], df['cycle_time'], marker='o')
    plt.axhline(50, color='red', linestyle='--')
    plt.axhline(70, color='red', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Cycle Time (s)')
    plt.title('Cycle Time monitoring')
    plt.grid()

    # Saves the plot to the specified path
    plt.savefig(output_path)
    plt.close()
    print(f'\nPlot saved to: {output_path}')

def calculate_kpis(df, min_limit=50, max_limit=70):
    '''
    Calculates key performance indicators (KPIs) for cycle time data

    Parameters: 
        df: pandas.DataFrame
        min_limit: int or float, optional, default=50
        max_limit: int or float, optional, default=70

    Returns: 
        kpis (dict): A dictionary containing various KPIs
    '''

    total = len(df)
    
    within_range = df[(df['cycle_time'] >= min_limit) & (df['cycle_time'] <= max_limit)] #...
    outside_range = df[(df['cycle_time'] < min_limit) | (df['cycle_time'] > max_limit)] #...

    kpis = {
        'mean': df['cycle_time'].mean(),
        'max': df['cycle_time'].max(),
        'min': df['cycle_time'].min(),
        'std': df['cycle_time'].std(),
        'range': df['cycle_time'].max() - df['cycle_time'].min(),
        'coef_variation (%)': (df['cycle_time'].std() / df['cycle_time'].mean()) * 100,
        'total_measurements': total,
        'within_spec': len(within_range),
        'out_of_spec': len(outside_range),
        'compliance_rate (%)': (len(within_range) / total) * 100,
        'non_compliance_rate (%)': (len(outside_range) / total) * 100
    }

    print('\nProcess KPIs:')
    for k, v in kpis.items():
        print(f'{k}: {v:.2f}')

    return kpis

def six_sigma_rule_detection(df):
    '''
    Detects anomalies in the process according to common Six Sigma SPC rules:
    - Rule 1: 1 point outside 3 standard deviations from the mean (already handled by LCL/UCL)
    - Rule 2: 9 points in a row on same side of the mean
    - Rule 3: 6 points in a row increasing or decreasing
    - Rule 4: 14 points in a row alternating up and down
    '''

    mean = df['cycle_time'].mean()
    std = df['cycle_time'].std()

    ucl = mean + 3 * std
    lcl = mean - 3 * std

    violations = []

    # Rule 1: points outside UCL/LCL
    rule1 = df[(df['cycle_time'] > ucl) | (df['cycle_time'] < lcl)]
    violations.append(('Rule 1 - 3 Sigma Violation', rule1))

    # Rule 2: 9 points in a row on same side of the mean
    above_mean_count = 0
    below_mean_count = 0
    indices_rule2 = []

    for i, val in enumerate(df['cycle_time']):
        if val > mean:
            above_mean_count += 1
            below_mean_count = 0
        elif val < mean:
            below_mean_count += 1
            above_mean_count = 0
        
        if above_mean_count >= 9 or below_mean_count >= 9:
            indices_rule2.append(i)

            # Resets the counters after detecting a violation to avoid counting overlapping sequences
            above_mean_count = 0
            below_mean_count = 0

    if indices_rule2:
        rule2 = df.iloc[indices_rule2]
        violations.append(('Rule 2 - 9 Points Same Side of Mean', rule2))

    # Rule 3: 6 points in a row increasing or decreasing
    indices_rule3 = []

    for i in range(len(df) - 5):
        window = df['cycle_time'].iloc[i:i+6].values
        if all(window[j] < window[j+1] for j in range(5)) or all(window[j] > window[j+1] for j in range(5)):
            indices_rule3.append(i)

    if indices_rule3:
        violations.append(('Rule 3 - 6 Points Increasing/Decreasing', df.iloc[list(set(indices_rule3))]))

    # Rule 4: 14 points in a row alternating up and down
    indices_rule4 = []

    for i in range(len(df) - 13):
        window = df['cycle_time'].iloc[i:i+14].values
        if all((window[j] < window[j+1] if j % 2 == 0 else window[j] > window[j+1]) for j in range(13)):
            indices_rule4.append(i)

    if indices_rule4:
        violations.append(('Rule 4 - 14 Points Alternating Up/Down', df.iloc[list(set(indices_rule4))]))

    return violations

def export_to_excel(df, anomalies, kpis, filename='report.xlsx'):
    '''
    Exports data to an Excel file with multiple sheets

    Parameters:
        df: pandas.DataFrame - The original dataframe containing cycle time data
        anomalies: pandas.DataFrame - A dataframe containing detected anomalies
        kpis: dict - A dictionary containing calculated KPIs
        filename: str, optional, default='report.xlsx' - The name of the Excel file to save
    '''

    output_path = os.path.join(os.getcwd(), 'results', filename) # Defines the path to save the Excel report

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer: 
        df.to_excel(writer, sheet_name='Data', index=False) 
        anomalies.to_excel(writer, sheet_name='Anomalies', index=False) 
        kpis_df = pd.DataFrame(list(kpis.items()), columns=['Metric', 'Value']) 
        kpis_df.to_excel(writer, sheet_name='KPIs', index=False) 

    print(f'\nExcel report saved to: {output_path}')

def control_chart(df, output_filename):

    results_dir = os.path.join(os.getcwd(), 'results') # Defines the path to the results directory
    output_path = os.path.join(results_dir, output_filename) # Complete path to save the control chart

    mean = df['cycle_time'].mean()
    std = df['cycle_time'].std()

    ucl = mean + 3 * std
    lcl = mean - 3 * std

    plt.figure()
    plt.plot(df['time'], df['cycle_time'], marker='o')
    plt.axhline(mean, color='green', linestyle='--', label='Mean')
    plt.axhline(ucl, color='red', linestyle='--', label='UCL (Mean + 3*Std)')
    plt.axhline(lcl, color='red', linestyle='--', label='LCL (Mean - 3*Std)')
    plt.title('Control Chart (SPC)')
    plt.xlabel('Time')
    plt.ylabel('Cycle Time (s)')
    plt.legend()
    plt.grid()

    # Saves the plot to the specified path
    plt.savefig(output_path)
    plt.close()
    print(f'\nControl chart saved to: {output_path}')


def main():
    df = load_data()
    stats = analyse_cycle_time(df)
    anomalies = detect_anomalies(df)
    generate_plot(df, 'cycle_time_plot.png')
    kpis = calculate_kpis(df)
    violations = six_sigma_rule_detection(df)
    export_to_excel(df, anomalies, kpis)
    control_chart(df, 'control_chart.png')

if __name__ == "__main__":
    main()