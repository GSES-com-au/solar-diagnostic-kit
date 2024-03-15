# -*- coding: utf-8 -*-
"""
Created at 16/5/2023

@author: Yinyan Liu, The University of New South Wales (UNSW)
"""

import pandas as pd
import pvlib
import numpy as np
from pvlib import irradiance
from pvlib import location


# ======================================================================================
# = calculate the sunrise and sunset time based on the latitude and longitude
# ======================================================================================
def find_sunrise_set(df, time_index5min_local, latitude, longitude, offset_minute=60):
    """
    find the sunrise and sunset time with pvlib
    :param time_index5min_local:
    :param latitude:
    :param longitude:
    :return:
    """
    # calculate the sunrise and sunset time
    df_sunrise_set = pvlib.solarposition.sun_rise_set_transit_spa(times=time_index5min_local,
                                                                  latitude=latitude,
                                                                  longitude=longitude)
    df_sunrise_set['sunrise_hour'] = df_sunrise_set['sunrise'] + pd.Timedelta(minutes=offset_minute)
    df_sunrise_set['sunrise_hour'] = df_sunrise_set['sunrise_hour'].dt.tz_localize(None)
    df_sunrise_set['sunset_hour'] = df_sunrise_set['sunset'] - pd.Timedelta(minutes=offset_minute)  # df_sunrise_set['sunset'].dt.hour
    df_sunrise_set['sunset_hour'] = df_sunrise_set['sunset_hour'].dt.tz_localize(None)
    df_sunrise_set['time'] = time_index5min_local
    comparison_column = np.where(
        (df_sunrise_set["time"] >= df_sunrise_set['sunrise']) & (df_sunrise_set["time"] <= df_sunrise_set['sunset']),
        True, False)
    df['sunrise_time_after'] = df_sunrise_set['sunrise_hour'].values
    df['sunset_time_before'] = df_sunrise_set['sunset_hour'].values
    df['during_sunrise_set'] = comparison_column
    return df

# ======================================================================================
# = Preprocessing the outlier & missing data
# ======================================================================================
def preprocess_data(df, thred_missing_data, pv_size, measure_name_list):
    """
    drop the date with too many missing data & process the outlier & fill up the missing data
    :param df:
    :param thred_missing_data:
    :param pv_size:
    :param measure_name_list:
    :return:
    """
    # ========================================================
    # = Drop dates with too many missing data
    # ========================================================

    # count the nan/missing number in each day
    df_countnan = df['DC Current'].isna().groupby([df['date']]).sum().astype(int).reset_index(
        name='count')
    remove_date_list = df_countnan[df_countnan['count']>thred_missing_data]['date'].values.tolist()
    # remove the dates with too many missing data
    df = df[~(df['date'].isin(remove_date_list))]
    df.index = np.arange(len(df))

    # ========================================================
    # = Processing outliers based on the PV size
    # ========================================================
    df.loc[df['Inv.DC.P.W'] > 1.2 * pv_size, measure_name_list] = np.NaN
    # ========================================================
    # = Filling up the missing data
    # ========================================================
    df.fillna(method='ffill', inplace=True)

    return df

# ======================================================================================
# = Calculate the theoretical generation of a cleark-sky day
# ======================================================================================
def get_irradiance(time_index5min_local, time_zone, tilt, surface_azimuth,latitude, longitude, pv_size, loss_factor):
    """
    meta data of the monitor
    :param tilt:
    :param surface_azimuth:
    :param latitude:
    :param longitude:
    :param pv_size:
    :param loss_factor:
    :return:
    """
    loc = location.Location(latitude, longitude, tz=time_zone)
    # Generate clearsky data using the Ineichen model, which is the default
    # The get_clearsky method returns a dataframe with values for GHI, DNI,
    # and DHI
    clearsky = loc.get_clearsky(time_index5min_local)
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = loc.get_solarposition(times=time_index5min_local)
    # Use the get_total_irradiance function to transpose the GHI to POA
    POA_irradiance = irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=surface_azimuth,
        dni=clearsky['dni'],
        ghi=clearsky['ghi'],
        dhi=clearsky['dhi'],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'])
    # Return DataFrame with only GHI and POA
    df_pvlib = pd.DataFrame({'GHI': clearsky['ghi'],
                         'POA': POA_irradiance['poa_global']})
    df_pvlib = df_pvlib*pv_size*loss_factor/1000
    return df_pvlib


