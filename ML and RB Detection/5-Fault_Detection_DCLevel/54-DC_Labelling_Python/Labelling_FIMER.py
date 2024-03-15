# -*- coding: utf-8 -*-
"""
Created at 16/5/2023

@author: Yinyan Liu, The University of New South Wales (UNSW)
"""

##========== Global Parameter ====================
threshold_performance_clipp_upper = 0.001
threshold_performance_clipp_lower = -0.001
threshold_clipp_time = 12  # time slots # 1 hour
sun_thre_start = 10  # 10 am
sun_thred_end = 15  # 15 pm

def find_clipping(df, diff_name, metric_name):
    # identify the potential clipping
    # diff in a tiny range & hour during sunny time
    df['potential_clip'] = (df[diff_name + '_Pdiff'] <= threshold_performance_clipp_upper) & \
                            (df[diff_name + '_Pdiff'] >= threshold_performance_clipp_lower) & \
                            (df['hour'] >= sun_thre_start) & (df['hour'] <= sun_thred_end) & \
                           (df[metric_name]>50)
    # if same (True or False), the diff is zero, calculate the last period of the same value (True or False)
    df['clipping_period'] = df['potential_clip'].diff().ne(0).cumsum()
    df[diff_name + '_clipping_duration'] = df.groupby('clipping_period')['potential_clip'].transform('sum')
    df['is_' + diff_name + '_clipping'] = df['potential_clip'] & (df[diff_name + '_clipping_duration']>= threshold_clipp_time)
    df.drop(['potential_clip', 'clipping_period'], axis=1, inplace=True)
    return df

def DC0_generation(df):
    # # DC power =  0
    # # AC power = 0
    # # not at the begining and end of a day
    df['DC Zero Generation'] = (df['Inv.DC.P.W'] == 0) & (df['Gen.W'] == 0) & \
                               (df['time']>=df['sunrise_time_after']) & (df['time']<=df['sunset_time_before'])
    return df

def Inverter_Tripping(df):
    ## DC Power not zero
    ## AC Power zero
    df['Inverter_Tripping'] = (df['Inv.DC.P.W'] > 100) & (df['Gen.W'] == 0) & \
                              (df['time'] >= df['sunrise_time_after']) & (df['time'] <= df['sunset_time_before'])
    return df

# ========================================================
# = AC Generation == 0
# ========================================================
def grid_overvoltage(df, ac_overvol_threshold=255):
    """
    AC generation == 0 & V_ac > threshold value, e.g., 255 V
    :param df:
    :param ac_overvol_threshold:
    :return:
    """
    df['grid_overVol'] = (df['Inv.AC.U.V'] > ac_overvol_threshold) &(df['Inv.AC.U.V'].max() < 300) \
                         & (df['Gen.W'] == 0) & (df['time'] >= df['sunrise_time_after']) \
                         & (df['time'] <= df['sunset_time_before'])

    return df

def blackout(df, ac_vol_threshold=216):
    """
    if AC generation == 0 & AC voltage < threshold value, e.g., 216 V
    :param df:
    :param ac_vol_threshold:
    :return:
    """
    df['blakout'] = (df['Inv.AC.U.V'] < ac_vol_threshold) &(df['Inv.AC.U.V'].max() < 300) & (df['Gen.W'] == 0) & \
                    (df['time'] >= df['sunrise_time_after']) & (df['time'] <= df['sunset_time_before'])

    return df

def undersize_mppt_InVol(df, ac_overvol_threshold, ac_blackout_vol_threshold):
    """
    if AC generation == 0 & AC voltage <= ac_overvol_threshold & AC voltage >= ac_blackout_vol_threshold & V_DC > V_AC
    :param df:
    :return:
    """
    df['undersize_mppt_InVol'] = (df['Gen.W'] == 0) & (df['Inv.AC.U.V'] >= ac_blackout_vol_threshold) & \
                                 (df['Inv.AC.U.V'] <= ac_overvol_threshold) & (df['Inv.DC.U.V'] > df['Inv.AC.U.V']) \
                                 & (df['time'] >= df['sunrise_time_after']) \
                                 & (df['time'] <= df['sunset_time_before'])
    return df

def DCside_issue_gen0(df, ac_overvol_threshold, ac_blackout_vol_threshold):
    """
    AC generation == 0 & AC voltage <= ac_overvol_threshold & AC voltage >= ac_blackout_vol_threshold & V_DC <= V_AC
    :param df:
    :param ac_overvol_threshold:
    :param ac_blackout_vol_threshold:
    :return:
    """
    df['DC_issue_Gen0'] = (df['Gen.W'] == 0) & (df['Inv.AC.U.V'] >= ac_blackout_vol_threshold) & \
                          (df['Inv.AC.U.V'] <= ac_overvol_threshold) & \
                          (df['Inv.DC.U.V'] <= df['Inv.AC.U.V']) & (df['time'] >= df['sunrise_time_after']) & \
                          (df['time'] <= df['sunset_time_before'])
    return df

# ========================================================
# = AC flat Generation
# ========================================================

def volt_watt(df, acvol_vw_threshold, diff_name):
    """
    flat generation  -- > AC Voltage > 250 v
    :param df:
    :param acvol_vw_threshold:  ac voltage threshold for the Volt-Watt identification
    :return:
    """
    df['volt_watt'] = (df['is_' + diff_name + '_clipping'] == True) & (df['Inv.AC.U.V'] > acvol_vw_threshold) & \
                      (df['Inv.AC.U.V'].max() < 300)
    return df

def volt_var(df, acvol_vw_threshold, acvol_vv_threshold, diff_name):
    """
    flat generation  -- > AC Voltage <= 250 V & AC Voltage > 248 V
    :param df:
    :param acvol_vv_threshold:
    :param diff_name:
    :return:
    """
    df['volt_var'] = (df['is_' + diff_name + '_clipping'] == True) & (df['Inv.AC.U.V'] <= acvol_vw_threshold) & \
                     (df['Inv.AC.U.V'] > acvol_vv_threshold)
    return df

def inverter_clipping(df, acvol_vv_threshold, diff_name):
    """
    flat generation  -- > AC Voltage <= 248 V & P_dc > P_ac
    :param df:
    :param acvol_vv_threshold:
    :param diff_name:
    :return:
    """
    df['inverter_clipping'] = (df['is_' + diff_name + '_clipping'] == True) & \
                              (df['Inv.AC.U.V'] <= acvol_vv_threshold) &(df['Inv.AC.U.V'].max() < 300) & \
                              (df['Inv.DC.P.W'] > 1.1*df['Gen.W']) & (df['time'] >= df['sunrise_time_after']) & \
                              (df['time'] <= df['sunset_time_before'])
    return df

def DCside_issue_flat_generation(df, acvol_vv_threshold, diff_name):
    df['DCside_issue_flat'] = (df['is_' + diff_name + '_clipping'] == True) & \
                              (df['Inv.AC.U.V'] <= acvol_vv_threshold) & \
                              (df['Inv.DC.P.W'] <= df['Gen.W'])
    return df
