# --------------------------------------------------------------------------------------------------
# Functions for Trigger Monitoring Dashboard
#
# Author - Nitin Magima
# Date - 2024
# Version - 1.0
# --------------------------------------------------------------------------------------------------

# ==================================================================================================
#
# IMPORTANT - DISCLAIMER AND RIGHTS STATEMENT
# This is a set of scripts written by the Financial Instruments Team at the International Research
# Institute for Climate and Society (IRI) part of The Columbia Climate School, Columbia University
# They are shared for educational purposes only.  Anyone who uses this code or its
# functionality or structure, assumes full liability and should inform and credit IRI.
#
# ==================================================================================================

# Loading Packages
import requests
import pandas as pd
from IPython.display import HTML
import yaml


def load_config(file_path="config.yaml"):
    """
    Loads configuration data from a YAML file.

    Args:
    - config_file (str): Path to the YAML configuration file.

    Returns:
    - dict: Dictionary containing configuration data.
    """    
    with open(file_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def get_data(maproom, mode, region, season, predictor, predictand, year,
             issue_month0, freq, include_upcoming, threshold_protocol, username, password):
    """
    Retrieves data from an API endpoint and combines it into a DataFrame.

    Args:
    - maproom (str): Maproom value.
    - mode (int): Mode value.
    - region (list): List of region values.
    - season (str): Season value.
    - predictor (str): Predictor value.
    - predictand (str): Predictand value.
    - issue_month0 (int): Issue month value.
    - freq (int): Frequency value.
    - include_upcoming (str): Include upcoming value.
    - threshold_protocol (int): Threshold protocol value.
    - username (str): Username for API authentication.
    - password (str): Password for API authentication.

    Returns:
    - DataFrame: returns a dataframe with a single row of the latest trigger information.
    """
    
    # Make a GET request to the API
    region_str = ",".join(map(str, region))  # Convert region values to a comma-separated string
    api_url = (f"http://iridl.ldeo.columbia.edu/fbfmaproom2/{maproom}/"
               f"export?season={season}&issue_month0={issue_month0}&freq={freq}&predictor"
               f"={predictor}&predictand={predictand}&include_upcoming={include_upcoming}&mode={mode}"
               f"&region={region_str}")

    # Constructing the design tool URL
    tool_url = (f"https://iridl.ldeo.columbia.edu/fbfmaproom2/{maproom}?mode={mode}&map_column={predictor}"
               f"&season={season}&predictors={predictor}&predictand={predictand}&year={year}"
               f"&issue_month0={issue_month0}&freq={freq}&severity=0&include_upcoming={include_upcoming}")

    auth = (username, password)
    response = requests.get(api_url, auth=auth)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON data
        json_data = response.json()

        # Flatten nested dictionaries using json_normalize
        flattened_data = pd.json_normalize(json_data)

        # Initialize a list to store non-nested columns
        non_nested_columns = []

        # Check for columns with nested data (list of dictionaries) and expand them
        for column in flattened_data.columns:
            if isinstance(flattened_data[column][0], list):
                # Expand nested dictionaries in the list column
                expanded_data = pd.json_normalize(flattened_data[column].explode(), sep='_')

                # Combine the expanded columns with the original DataFrame
                flattened_data = pd.concat([flattened_data, expanded_data], axis=1)

                # Drop the original list column
                flattened_data = flattened_data.drop(column, axis=1)
            else:
                # Save non-nested columns to the list
                non_nested_columns.append(column)

        # Create a separate DataFrame for non-nested columns
        non_nested_df = flattened_data[non_nested_columns]

        # Create a new DataFrame using the data from the first row of non-nested DataFrame
        melted_non_nested_df = pd.DataFrame({
            'Metric': non_nested_df.columns,
            'Value': non_nested_df.iloc[0].values
        })

        melted_non_nested_df = melted_non_nested_df.iloc[:2, :]

        replace_values = {'threshold': 'Forecast Threshold', 'skill.accuracy': 'Forecast Accuracy'}
        melted_non_nested_df['Metric'] = melted_non_nested_df['Metric'].replace(replace_values)


        # Convert melted_non_nested_df to a dictionary
        melted_non_nested_dict = melted_non_nested_df.set_index('Metric')['Value'].to_dict()

        # Convert flattened data to Pandas DataFrame
        df = pd.DataFrame(flattened_data).drop(non_nested_df.columns, axis=1, errors='ignore')
        df['triggered'] = df[predictor] > melted_non_nested_dict['Forecast Threshold']
        df['trigger difference'] = df[predictor] - melted_non_nested_dict['Forecast Threshold']
        df['Adjusted Forecast Threshold'] = melted_non_nested_dict['Forecast Threshold'] + threshold_protocol
        df['Triggered Adjusted'] = df[predictor] > melted_non_nested_dict['Forecast Threshold']
        df.rename(columns={predictor: 'forecast'}, inplace=True)
        df['forecast'] = df['forecast']
        df['trigger difference'] = df['trigger difference']
        df = df.loc[:, ['forecast', 'trigger difference', 'triggered',
                        'Triggered Adjusted', 'Adjusted Forecast Threshold']].iloc[1, :].to_frame().T

        melted_non_nested_df['Value'] = melted_non_nested_df['Value']

        # Combine df and melted_non_nested_df
        melted_non_nested_df = melted_non_nested_df.T  # Transpose the DataFrame
        melted_non_nested_df.columns = melted_non_nested_df.iloc[0]  # Set the first row as column names
        melted_non_nested_df = melted_non_nested_df.iloc[1:, :].reset_index(drop=True).rename_axis(None,
                                                                                                   axis=1)  # Reset index
        combined_df = pd.concat([df.reset_index(drop=True), melted_non_nested_df], axis=1).reset_index(drop=True)
        combined_df['Frequency (%)'] = f"{freq}%"
        combined_df['Forecast Accuracy (%)'] = combined_df['Forecast Accuracy'] * 100
        combined_df['Threshold Protocol'] = f"{threshold_protocol}"

        month_mapping = {
            0: 'Jan',
            1: 'Feb',
            2: 'Mar',
            3: 'Apr',
            4: 'May',
            5: 'Jun',
            6: 'Jul',
            7: 'Aug',
            8: 'Sep',
            9: 'Oct',
            10: 'Nov',
            11: 'Dec'
        }

        combined_df['Issue Month'] = issue_month0
        combined_df['Issue Month'] = combined_df['Issue Month'].map(month_mapping)

        # After preparing your final DataFrame (e.g., combined_df), add the hyperlink
        combined_df['Design Tool URL'] = f"<a href='{tool_url}'>Design Tool Link</a>"

        # Rearrange the columns in a specific sequence
        if threshold_protocol == 0:
            desired_columns = ['Frequency (%)', 'Issue Month', 'forecast', 'Forecast Threshold', 'trigger difference',
                               'Forecast Accuracy (%)', 'triggered', 'Design Tool URL']
            combined_df = combined_df[desired_columns]
        else:
            desired_columns = ['Frequency (%)', 'Issue Month', 'forecast', 'Forecast Threshold', 'trigger difference',
                               'Forecast Accuracy (%)', 'triggered', 'Adjusted Forecast Threshold',
                               'Threshold Protocol', 'Triggered Adjusted', 'Design Tool URL']
            combined_df = combined_df[desired_columns]

        combined_df = combined_df.rename(columns={
                                            'forecast': 'Forecast',
                                            'triggered': 'Triggered',
                                            'trigger difference': 'Trigger Difference'
                                        })

        # Return the combined DataFrame
        return combined_df
    else:
        # Return an empty DataFrame or handle the error as needed
        print(f"Error: {response.status_code}")
        return pd.DataFrame()


def get_admin_data(maproom, level, username, password, need_valid_keys, valid_keys=None):
    """
    Retrieves administrative data from an API endpoint.

    Args:
    - maproom (str): Maproom value.
    - level (str): Level of administrative data.

    Returns:
    - DataFrame: DataFrame containing administrative data.
    """
    # Construct the API URL with the provided parameters
    api_url = f"http://iridl.ldeo.columbia.edu/fbfmaproom2/regions?country={maproom}&level={level}"

    # Make a GET request to the API
    if username and password:
        auth = (username, password)
        response = requests.get(api_url, auth=auth)
    else:
        response = requests.get(api_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON data
        json_data = response.json()

        # Create a DataFrame from the JSON data
        df = pd.DataFrame(json_data)

        # Extract "key" and "label" from the "regions" column
        df[['key', 'label']] = df['regions'].apply(pd.Series)

        # Filter keys if valid_keys is provided
        if level != 0:
            if need_valid_keys is True:
                df = df[df['key'].isin(valid_keys)]

        # Drop the original "regions" column if needed
        df = df.drop('regions', axis=1)

        return df
    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code}")
        return None


def get_trigger_tables(maproom, mode, season, predictor, predictand, year,
                       issue_month, frequencies, include_upcoming, threshold_protocol, username, password,
                       need_valid_keys, valid_keys):
    """
    Retrieves trigger tables based on specified parameters.

    Args:
    - maproom (str): Maproom value.
    - mode (int): Mode value.
    - season (str): Season value.
    - predictor (str): Predictor value.
    - predictand (str): Predictand value.
    - issue_month (list): List of issue month values.
    - frequencies (list): List of frequency values.
    - include_upcoming (str): Include upcoming value.
    - threshold_protocol (int): Threshold protocol value.
    - username (str): Username for API authentication.
    - password (str): Password for API authentication.
    - need_valid_keys (bool): Flag indicating if valid keys are needed.
    - valid_keys (list): List of valid keys.

    Returns:
    - dict: Dictionary containing trigger tables.
    """
    print("Fetching....")
    # Initialize a dictionary to store admin tables
    admin_tables = {}

    # Creating trigger tables

    admin_name = f"admin{mode}_tables"
    admin_tables[admin_name] = {}
    admin_data = get_admin_data(maproom, mode, username=username, password=password,
                                need_valid_keys=need_valid_keys, valid_keys=valid_keys)

    for freq in frequencies:
        for month in issue_month:
            # Iterate over each key value
            if isinstance(admin_data, pd.Series):
                for region_key, label in admin_data.items():
                    print(region_key, label)
                    table_name = f"output_freq_{freq}_mode_{mode}_month_{month}_region_{region_key}_table"

                    df = get_data(maproom=maproom, mode=mode, region=[region_key],
                                  season=season, predictor=predictor, predictand=predictand, year = year,
                                  issue_month0=month, freq=freq, include_upcoming=include_upcoming,
                                  threshold_protocol=threshold_protocol, username=username, password=password)

                    df.insert(0, 'Admin Name', label)
                    admin_tables[admin_name][table_name] = df

            elif isinstance(admin_data, pd.DataFrame):
                for index, row in admin_data.iterrows():
                    region_key, label = row['key'], row['label']

                    table_name = f"output_freq_{freq}_mode_{mode}_month_{month}_region_{region_key}_table"

                    df = get_data(maproom=maproom, mode=mode, region=[region_key],
                                  season=season, predictor=predictor, predictand=predictand, year = year,
                                  issue_month0=month, freq=freq, include_upcoming=include_upcoming,
                                  threshold_protocol=threshold_protocol, username=username, password=password)

                    df.insert(0, 'Admin Name', label)
                    admin_tables[admin_name][table_name] = df

            else:
                # Handle other cases or raise an error
                raise ValueError("Unexpected output type from get_admin_data.")

    return admin_tables

def generate_colors(n):
    """
    Generates a list of n distinct colors in HSL format.
    
    Args:
        n (int): The number of distinct colors to generate.
        
    Returns:
        List[str]: A list of colors.
    """
    return [f"hsl({int((360 / n) * i)}, 100%, 70%)" for i in range(n)]

def style_and_render_df_with_hyperlinks(df):
    # Define columns to style
    columns_to_style = ['Admin Name', 'Frequency (%)', 'Issue Month']
    
    # Calculate the total number of unique values across all columns
    unique_values_count = sum(df[col].nunique() for col in columns_to_style)
    
    # Generate a unique color for each unique value across all columns
    unique_colors = generate_colors(unique_values_count)
    
    # Assign a distinct segment of colors to each column
    color_index = 0
    color_maps = {}
    for column in columns_to_style:
        unique_values = df[column].unique()
        color_maps[column] = {value: unique_colors[color_index + i] for i, value in enumerate(unique_values)}
        color_index += len(unique_values)
    
    # Function to apply colors based on the value for a given column
    def apply_color(val, column):
        if pd.isnull(val):
            return ''  # Return default style for NaN values
        return f'background-color: {color_maps[column].get(val, "")};'
    
    # Initialize the styled DataFrame
    styled_df = df.style
    
    # Apply the styles to each column individually
    for column in columns_to_style:
        styled_df = styled_df.map(lambda val, col=column: apply_color(val, col), subset=[column])
    
    # Apply boolean highlights for 'triggered' and 'Triggered Adjusted' columns
    true_color, false_color = '#CCFFCC', '#FFCC99'
    
    # Assuming styled_df is your DataFrame styled object, and true_color/false_color are defined
    columns_to_style = ['Triggered', 'Triggered Adjusted']
    
    for col in columns_to_style:
        try:
            # Check if column exists by trying to access it
            if col in styled_df.columns:
                # Apply the styling if column exists
                styled_df = styled_df.map(lambda val: f'background-color: {true_color if val else false_color}', subset=[col])
            else:
                # If the column does not exist in the DataFrame, this line will not be executed
                pass
        except KeyError as e:
            print(f"Column not found: {e}")
            # Handle the case where the column does not exist, e.g., by logging or passing
            continue
    
    # Format numerical columns
    styled_df = styled_df.format({'forecast': "{:.2f}", 'trigger difference': "{:.2f}", 'Forecast Accuracy (%)': "{:.2%}"})
    
    # Render to HTML
    rendered_html = styled_df.to_html(escape=False)
    display(HTML(rendered_html))

def fetch_fewsnet_maadagascar(df):
    # API URL
    url = 'https://fdw.fews.net/api/ipcphase/?format=json&country_code=MG&fields=simple'
    
    # Make the API call
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        
        # Convert to DataFrame for better visualization
        df = pd.DataFrame(data)
    else:
        print(f'Failed to retrieve data. Status code: {response.status_code}')
    
    # Parse date columns
    date_columns = ['projection_start', 'projection_end', 'reporting_date']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')  # Convert to datetime, making invalid parsing set as NaT
    
    # Check for missing values in the dataset
    missing_values = df.isnull().sum()
    
    # Convert relevant text columns to categorical types for efficiency
    categorical_columns = ['source_organization', 'country', 'geographic_group', 'fewsnet_region', 'classification_scale', 'scenario_name', 'description', 'scenario', 'collection_status', 'status', 'data_usage_policy']
    for col in categorical_columns:
        df[col] = df[col].astype('category')
    
    description_order = ['Minimal', 'Stressed', 'Crisis', 'Emergency', 'Famine']
    df['description'] = pd.Categorical(df['description'], categories=description_order, ordered=True)
    
    # Convert 'projection_start' and 'projection_end' to datetime to extract months for filtering
    df['projection_start_month'] = pd.to_datetime(df['projection_start']).dt.month
    df['projection_end_month'] = pd.to_datetime(df['projection_end']).dt.month
    
    # Define the months of interest: October(10), November(11), December(12), January(1), February(2)
    months_of_interest = [10, 11, 12, 1, 2]
    
    # Filter rows where any of the months of interest falls between or is included in the projection start or end months
    df = df[df.apply(lambda row: any(month in months_of_interest for month in range(row['projection_start_month'], row['projection_end_month'] + 1)), axis=1)]
    
    # Extract years from 'projection_start' and 'projection_end'
    df['projection_start_year'] = pd.to_datetime(df['projection_start']).dt.year
    df['projection_end_year'] = pd.to_datetime(df['projection_end']).dt.year
    
    # Define the years of interest
    years_of_interest = [2023, 2024]
    
    # Filter rows where either projection start or end year is in the years of interest
    df = df[df.apply(lambda row: row['projection_start_year'] in years_of_interest or row['projection_end_year'] in years_of_interest, axis=1)]
    
    # Display the structure of the DataFrame after these changes and the count of missing values
    df.info(), missing_values

    # Filtering the data for scenarios labeled as 'CS' or 'Current Situation'
    df = df[df['scenario'] == 'CS']
    
    # String search to filter the dataset for the specified regions 
    regions_of_interest = ["Atsimo-Atsinanana", "Anosy", "Atsimo-Andrefana", "Androy"]
    df = df[
        df['geographic_unit_full_name'].str.contains('|'.join(regions_of_interest))
    ]
    
    # Creating a function to determine the region based on 'geographic_unit_full_name'
    def determine_region(name):
        for region in regions_of_interest:
            if region in name:
                return region
        return None  # Returns None if no specific region is found
    
    # Applying the function to create the 'region' column
    df['region'] = df['geographic_unit_full_name'].apply(determine_region)
    
    # Analyze the distribution of food security scenarios for the latest year in these regions
    description_counts_latest_year = df['description'].value_counts()

    # Performing a groupby operation on the 'region' column along with 'is_allowing_for_assistance' and 'description'
    region_groupby_assistance_description = df.groupby(['region','is_allowing_for_assistance','description']).size().unstack(fill_value=0)
    
    description_counts_latest_year, df['region'].value_counts(), region_groupby_assistance_description

