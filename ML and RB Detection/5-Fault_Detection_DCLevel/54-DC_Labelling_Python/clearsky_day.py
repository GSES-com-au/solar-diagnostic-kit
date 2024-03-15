# -*- coding: utf-8 -*-
"""
Created at 16/5/2023

@author: Yinyan Liu, The University of New South Wales (UNSW)
"""
'''
Identify the clear-sky days for further labelling to avoid too much noise
'''

## ======================================================
## = IMPORT PACKAGES
## ======================================================
import pandas as pd

class ClearSkyDay():
    """
    methods related to clear sky day detection

    Method: (based on daily data)
        get_ghi_data : fetch the generation of the clear-sky model
        get_expected_data : fetch the expected generation of a PV site based on the weather data from the BOM dataset
        detect_clear_sky_day : Check whether a certain day is a clear sky day or not.
    """
    def __init__(self, threshold_low_cloudiness, clearsky_data_path, expected_data_path,
                 site_id, time_start, time_end):
        '''
        initial the global parameters
        :param threshold_low_cloudiness: the threshold value for the clear-sky day selection
        '''
        self.threshold_low_cloudiness = threshold_low_cloudiness
        self.clearsky_data_path = clearsky_data_path
        self.expected_data_path = expected_data_path
        self.siteid = site_id
        self.time_start = time_start
        self.time_end = time_end

    def read_raw_data(self):
        df_site_clearsky = pd.read_csv(self.clearsky_data_path)
        # select the concerned time peirod
        df_site_clearsky = df_site_clearsky[(df_site_clearsky['date'] >= self.time_start) &
                                            (df_site_clearsky['date'] < self.time_end)]
        df_site_expected = pd.read_csv(self.expected_data_path)
        df_site_expected = df_site_expected[(df_site_expected['date'] >= self.time_start) &
                                            (df_site_expected['date'] < self.time_end)]

        return df_site_clearsky, df_site_expected

    def calculate_cloudiness(self, df_site_clearsky, df_site_expected):
        df_cloudiness = df_site_clearsky.copy()
        df_cloudiness.iloc[:, 1:] = df_site_expected.iloc[:, 1:] / df_site_clearsky.iloc[:, 1:]
        df_cloudiness.iloc[:, 1:] = df_cloudiness.iloc[:, 1:].astype(float)
        df_cloudiness.dropna(how='all', axis=1, inplace=True)
        df_cloudiness.iloc[:, 1:].fillna(axis=1, method='ffill', inplace=True)

        return df_cloudiness

    def identify_clearsky_day(self):
        df_site_clearsky, df_site_expected = self.read_raw_data()
        df_cloudiness = self.calculate_cloudiness(df_site_clearsky=df_site_clearsky,
                                                  df_site_expected=df_site_expected)
        df_cloudiness.iloc[:, 1:] = df_cloudiness.iloc[:, 1:].ge(self.threshold_low_cloudiness)
        clearsky_date_list = df_cloudiness.loc[df_cloudiness[self.siteid] == True, 'date'].values.tolist()
        return clearsky_date_list

