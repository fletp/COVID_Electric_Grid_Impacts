#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 15:26:59 2020

@author: joshuageiser
"""

import os
import pandas as pd
import numpy as np

REGION_CITY_MAPPING = {'caiso': 'la',
                        'ercot': 'houston', 
                        'isone': 'boston', 
                        'nyiso': 'nyc', 
                        'pjm'  : 'chicago', 
                        'spp'  : 'kck'}

def get_io_filepaths():
    '''
    Returns a list containing tuples of input filepaths (for raw CSV data) and
    desired output filepaths for cleaned dataset. 

    Returns
    -------
    io_filepaths : List
        List containing tuples of form (input_filepath, output_filepath). The
        input dataset will be read in from input_filepath and the output data
        will be written to output_filepath

    '''
    
    io_filepaths = []
    
    # For output data
    data_output_dir = os.path.join(os.getcwd(), 'data', 'interim')
    data_output_dir = os.path.abspath(data_output_dir)
    
    # Generate a list containing tuples of input/output filepaths
    for region in REGION_CITY_MAPPING.keys():
        city = REGION_CITY_MAPPING[region]
        
        input_file = os.path.join(data_output_dir, f'{region}_{city}_second_pass.csv')
        output_file = os.path.join(data_output_dir, f'{region}_{city}_third_pass.csv')
        
        io_filepaths.append((input_file, output_file))
    
    
    return io_filepaths

def hr_str_to_int(hour):
    return int(hour.split(':')[0])
    

def remove_cols(df_in):
    
    cols_to_remove = [x for x in df_in.columns if '_next_' in x or '_load' in x]
    cols_to_remove.append('date')
    df_in = df_in.drop(cols_to_remove, axis=1)
    
    cols_to_remove = [x for x in df_in.columns if 'max_24_hour' in x or 'min_24_hour' in x or 'mean_24_hour' in x]
    df_in = df_in.drop(cols_to_remove, axis=1)
    
    return df_in

def update_holiday_col(df_in):
    '''
    Since there was a weird bug in the feature engineering that caused only 
    midnight of a holiday to be set to 1. This function ensures that all hours
    on a holiday are set to 1.
    '''
    
    holiday_indices = df_in.index[df_in['holiday'] == 1].tolist()
    
    holiday_dates = [df_in['date'][index] for index in holiday_indices]
        
    for holiday_date in holiday_dates:
        curr_holiday_indices = df_in.index[df_in['date'] == holiday_date].tolist()
        for curr_holiday_index in curr_holiday_indices:
            df_in.loc[curr_holiday_index, 'holiday'] = 1
            #df_in['holiday'][curr_holiday_index] = 1
    
    return df_in

def add_region_flags(df, input_filepath):
    """Add city/region flag columns to a dataset
    
    Args:
        df: pandas dataframe containing data for a particular city
        input_flepath: file path string containing the city/region
            information

    Returns: df with new flag columns for all possible cities/regions.
        The city/region column corresponding to this dataset's region
        is all ones, others are all zeros.
    """
    cur_region = os.path.basename(input_filepath).split('_')[0]
    for region, city in REGION_CITY_MAPPING.items():
        if region == cur_region:
            cur_flag = 1
        else:
            cur_flag = 0
        df[f'city_flag_{city}'] = cur_flag
    return df

def parse_third_pass(input_filepath, output_filepath):
    '''
    Parses through raw CSV dataset and writes it into a more usable CSV format.

    Parameters
    ----------
    input_filepath : String
        Filepath to input CSV dataset.
    output_filepath : String
        Filepath that output CSV data will be written to.

    Returns
    -------
    None.

    '''
    
    print(f'Parsing {os.path.basename(input_filepath)}')
    
    # Read in input weather datafile using pandas
    df_in = pd.read_csv(input_filepath)
    
    # Change hour column from string to int
    df_in['hour'] = df_in['hour'].apply(hr_str_to_int)
    
    # Update holiday column so that all hours in a holiday contain 1
    df_in = update_holiday_col(df_in)
    
    # Remove unneeded features
    df_in = remove_cols(df_in)

    # Add region/city flag columns
    df_in = add_region_flags(df_in, input_filepath)
    
    # Get the first row that contains non-null values for all columns
    # Uses the cum_avg_7_day_load column as reference
    test_list = df_in['cum_avg_7_day_relh'].isnull()
    start_index = [ind for ind,val in enumerate(test_list) if not val][0]
    
    # Rearrange column order
    cols = df_in.columns.tolist()
    new_cols = [cols[0], cols[2], cols[1]] + cols[3:]
    df_in = df_in[new_cols]
    
    # Start at first row with data in all columns
    df_out = df_in[start_index:]
    
    # Write file to output    
    pd.DataFrame(df_out).to_csv(output_filepath, index=None)
    
    return

def main():
    
    # Get a list containing tuples of input/output filepaths
    io_filepaths = get_io_filepaths()
    
    # io_filepaths = [io_filepaths[1]] # Just for Houston
    
    # Iterate through each region/city and parsing datafile
    for input_filepath,output_filepath in io_filepaths:
        parse_third_pass(input_filepath, output_filepath)
    

    return

if __name__ == "__main__":
    main()