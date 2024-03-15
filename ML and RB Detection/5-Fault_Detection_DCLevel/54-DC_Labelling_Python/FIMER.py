# -*- coding: utf-8 -*-
"""
Created at 16/5/2023

@author: Yinyan Liu, The University of New South Wales (UNSW)
"""

## ==========================================================
## = Labelling the faults for FIMER monitor
## ==========================================================
'''
# set measure name we concern
AC-Metrics:  'Gen.W', 'Inv.AC.U.V', 'Inv.AC.I.A', 'Inv.AC.Freq.Hz'
DC-Metrics: 'Inv.DC.P.W', 'Inv.DC.U.V', 'Inv.DC.I.A'
There is no DC current from the database. It can be calculated by DC Power/DC Voltage
'''

## ======================================================
## = IMPORT PACKAGES
## ======================================================
import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt
from read_preprocess_data import read_metric, build_dataframe, find_sunrise_set, preprocess_data, get_irradiance
from clearsky_day import ClearSkyDay
from Labelling_FIMER import find_clipping, DC0_generation, Inverter_Tripping, grid_overvoltage, blackout, \
    undersize_mppt_InVol, DCside_issue_gen0, volt_watt, volt_var, inverter_clipping, DCside_issue_flat_generation

import warnings
warnings.filterwarnings('ignore')
## ======================================================
## = SET GLOBAL PARAMETERS
## ======================================================

# ======== Global parameters for fonts & sizes ==========
FONT_SIZE = 14
rc={'font.size': FONT_SIZE, 'axes.labelsize': FONT_SIZE, 'legend.fontsize': FONT_SIZE,
    'axes.titlesize': FONT_SIZE, 'xtick.labelsize': FONT_SIZE, 'ytick.labelsize': FONT_SIZE}
plt.rcParams.update(**rc)
plt.rc('font', weight='bold')

style = 'ggplot' # choose a style from the above options
plt.style.use(style)

# ======== Global parameters for measurement metrics ==========
measure_name_list = ['Inv.DC.P.W', 'Inv.DC.U.V', 'DC Current', 'Gen.W', 'Inv.AC.U.V', 'Inv.AC.I.A', 'Inv.AC.Freq.Hz']
name_list = ['DC Power (Watt)', 'DC Voltage(V)', 'DC Current(A)', 'AC Power (Watt)', 'AC Voltage(V)',
             'AC Current(A)', 'AC Frequency (Hz)']

# for clear-sky and data preprocessing
threshold_low_cloudiness = 0.9
threshold_missing_data = 12

# for theoretical clear-sky generation
tilt = 10
azimuth = 0
loss_factor = 0.85
offset_time = 120 # minutes

# for fault labelling
ac_overvoltage_threshold = 255 # V
ac_blackout_vol_threshold = 216 # V
acvoltage_volt_watt_threshold = 250 # V
acvoltage_volt_var_threshold = 248 # V


class FIMER_DCAC_Labelling():
    def __init__(self, time_start, time_end, df_monitors, df_sites):
        self.fimer_list = df_monitors.loc[df_monitors['manufacturerApi']=='FIMER', 'source'].str.split('|').str[1].values
        self.time_start = time_start
        self.time_end = time_end
        self.df_monitors = df_monitors
        self.df_sites = df_sites

        time_index5min = pd.date_range(start=pd.to_datetime(self.time_start),
                                       end=pd.to_datetime(self.time_end),
                                       freq='5min').tz_localize(None)
        # dataframe for saving the results
        # DC zero generation
        self.df_DC0 = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_DC0['time'] = time_index5min

        # Inverter Tripping
        self.df_GridOverVol = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_GridOverVol['time'] = time_index5min

        # blackout
        self.df_Blackout = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_Blackout['time'] = time_index5min

        # undersized MPPT input voltage
        self.df_Undersize_MPPT = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_Undersize_MPPT['time'] = time_index5min

        # DC side issue with zero generation
        self.df_DCissue_Gen0 = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_DCissue_Gen0['time'] = time_index5min

        # Volt-Watt
        self.df_Volt_Watt = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_Volt_Watt['time'] = time_index5min

        # Volt-Var
        self.df_Volt_Var = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_Volt_Var['time'] = time_index5min

        # Inverter Clipping
        self.df_Inverter_Clipping = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_Inverter_Clipping['time'] = time_index5min

        # DC side issue with flat generation
        self.df_DCissue_FlatGen = pd.DataFrame(index=np.arange(len(time_index5min)))
        self.df_DCissue_FlatGen['time'] = time_index5min

    def fetch_data_fromAWS(self):
        # merge all monitors data together
        # to check the missing data
        time_index5min = pd.date_range(start=pd.to_datetime(self.time_start),
                                       end=pd.to_datetime(self.time_end),
                                       freq='5min').tz_localize(None)
        for m, measure_name in enumerate(measure_name_list):
            save_name = name_list[m]
            df_5min = pd.DataFrame(index=np.arange(len(time_index5min)))
            df_5min['time'] = time_index5min
            for MID in self.fimer_list:
                site_id = self.df_monitors.loc[self.df_monitors['source'] == str('MNTR|' + MID), 'siteId'].iloc[0]
                timezone_value = self.df_sites[self.df_sites['source'] == site_id].iloc[0]['timezone']
                timeid, data_values = read_metric(self.time_start, self.time_end, measure_name, MID)
                if len(timeid) != 0:
                    df_measure = build_dataframe(timeid=timeid, measure_name=measure_name, data_values=data_values,
                                                 timezone_value=timezone_value)
                    df_measure['time'] = df_measure['time'].dt.tz_localize(None)
                    df_measure.sort_values('time', inplace=True)
                    df_measure.rename(columns={measure_name: str('MNTR|' + MID)}, inplace=True)
                    df_5min = pd.merge_asof(df_5min, df_measure, on="time", tolerance=pd.Timedelta("1 minute"))
            df_5min.to_csv('../preprocessed_data/monitors_DCdata/{}.csv'.format(save_name), index=None)


    def read_all_rawdata(self):
        if not os.path.exists('../preprocessed_data/monitors_DCdata/AC Current(A).csv'):
            self.fetch_data_fromAWS()
        # read AC data
        self.df_ac_current = pd.read_csv('../preprocessed_data/monitors_DCdata/AC Current(A).csv')
        self.df_ac_power = pd.read_csv('../preprocessed_data/monitors_DCdata/AC Power (Watt).csv')
        self.df_ac_freq = pd.read_csv('../preprocessed_data/monitors_DCdata/AC Frequency (Hz).csv')
        self.df_ac_voltage = pd.read_csv('../preprocessed_data/monitors_DCdata/AC Voltage(V).csv')

        # read DC data
        self.df_dc_current = pd.read_csv('../preprocessed_data/monitors_DCdata/DC Current(A).csv')
        self.df_dc_power = pd.read_csv('../preprocessed_data/monitors_DCdata/DC Power (Watt).csv')
        self.df_dc_voltage = pd.read_csv('../preprocessed_data/monitors_DCdata/DC Voltage(V).csv')

    ## ==================== for each monitor ====================================
    def select_date_time(self, time_index5min_local, df, site_id, latitude, longitude):
        # select sunrise and sunset time
        df = find_sunrise_set(df=df, time_index5min_local=time_index5min_local,
                              latitude=latitude, longitude=longitude, offset_minute=offset_time)
        df = df[df['during_sunrise_set'] == True]
        df.index = np.arange(len(df))
        df.drop('during_sunrise_set', axis=1, inplace=True)
        # select clear-sky day
        select_clearsky_days = ClearSkyDay(threshold_low_cloudiness=threshold_low_cloudiness,
                                           clearsky_data_path='../preprocessed_data/PVsites_Clearsky_Production.csv',
                                           expected_data_path='../preprocessed_data/PVsites_Expected_Production.csv',
                                           site_id=site_id, time_start=self.time_start, time_end=self.time_end)
        clearsky_date_list = select_clearsky_days.identify_clearsky_day()

        df = df[df['date'].isin(clearsky_date_list)]
        df.index = np.arange(len(df))
        return df

    def processing_monitor(self, df, pv_size):
        df = preprocess_data(df=df, thred_missing_data=threshold_missing_data,
                             pv_size=pv_size, measure_name_list=measure_name_list)
        return df

    def DC0_Labelling(self, df):
        # # DC power =  0
        # # AC power = 0
        # # not at the begining and end of a day
        df = DC0_generation(df=df)
        return df

    def Flat_Generation(self, df, pv_size, diff_name, metric_name):
        # metric_name = 'Inv.DC.P.W' | 'Gen.W'
        df['{}_Pdiff'.format(diff_name)] = df[metric_name].diff() / pv_size
        df = find_clipping(df=df, diff_name=diff_name, metric_name=metric_name)
        return df

    def grid_overvoltage_labelling(self, df):
        # inverter tripping
        df = grid_overvoltage(df=df, ac_overvol_threshold=ac_overvoltage_threshold)
        return df

    def blackout_labelling(self, df):
        # ac power = 0 & V_ac <216 V
        df = blackout(df=df, ac_vol_threshold=ac_blackout_vol_threshold)
        return df

    def undersize_mpptVol_labelling(self, df):
        df = undersize_mppt_InVol(df=df, ac_overvol_threshold=ac_overvoltage_threshold,
                                  ac_blackout_vol_threshold=ac_blackout_vol_threshold)
        return df

    def dcside_gen0_issue_labelling(self, df):
        df = DCside_issue_gen0(df=df, ac_overvol_threshold=ac_overvoltage_threshold,
                               ac_blackout_vol_threshold=ac_blackout_vol_threshold)
        return df

    def volt_watt_labelling(self, df, diff_name):
        df = volt_watt(df=df, acvol_vw_threshold=acvoltage_volt_watt_threshold, diff_name=diff_name)
        return df

    def volt_var_labelling(self, df, diff_name):
        df = volt_var(df=df, acvol_vw_threshold=acvoltage_volt_watt_threshold,
                      acvol_vv_threshold=acvoltage_volt_var_threshold, diff_name=diff_name)
        return df

    def inverter_clipping_labelling(self, df, diff_name):
        df = inverter_clipping(df=df, acvol_vv_threshold=acvoltage_volt_var_threshold,
                               diff_name=diff_name)
        return df

    def DCside_flatGen_issue_labelling(self, df, diff_name):
        df = DCside_issue_flat_generation(df=df, acvol_vv_threshold=acvoltage_volt_var_threshold,
                                          diff_name=diff_name)
        return df

    def plot_results(self, df, site_id, MID, metric_name):
        date_list = df.loc[df[metric_name] == True, 'date'].unique()
        if not os.path.exists('results/plots/{}'.format(metric_name)):
            os.makedirs('results/plots/{}'.format(metric_name))
        for date_id in date_list:
            df_plot = df[df['date']==date_id]
            fig, axe = plt.subplots(nrows=5, figsize=(20, 10))
            # # === plot generation
            sns.lineplot(df_plot, x='time', y='theoretical_P.W',
                         legend='brief', label='Theoretical Power', ax=axe[0], linestyle='dashed', color='green')
            sns.lineplot(df_plot, x='time', y='Gen.W', legend='brief', label='AC Power', ax=axe[0])
            sns.lineplot(df_plot, x='time', y='Inv.DC.P.W', legend='brief', label='DC Power', ax=axe[0])
            sns.scatterplot(df_plot, x='time', y='Inv.DC.P.W', hue=metric_name,
                            palette={True: 'red', False: 'gray'}, markers='o', s=50, ax=axe[0])
            axe[0].set_title(str('MNTR|' + MID) + '   ' + site_id)
            # # ===  plot voltage
            sns.lineplot(df_plot, x='time', y='Inv.AC.U.V', legend='brief', label='AC Voltage',
                         ax=axe[1], color='darkorange', marker='o')
            axev = axe[1].twinx()
            sns.lineplot(df_plot, x='time', y='Inv.DC.U.V', legend='brief', label='DC Voltage',
                         ax=axev, color='blue', marker='o')
            # sns.scatterplot(df_plot, x='time', y='Inv.AC.U.V', hue=metric_name,
            #                 palette={True: 'red', False: 'gray'}, markers='o', s=50, ax=axe[1])
            # # === plot zoom out voltage
            sns.lineplot(df_plot, x='time', y='Inv.AC.U.V', legend='brief', label='AC Voltage',
                         ax=axe[2], color='darkorange', marker='o')
            if df_plot['Inv.AC.U.V'].max()>300:
                axe[2].set_ylim(420, 450)
            else:
                axe[2].set_ylim(240, 260)
            axevt = axe[2].twinx()
            sns.lineplot(df_plot, x='time', y='Inv.DC.U.V', legend='brief', label='DC Voltage',
                         ax=axevt, color='blue', marker='o')
            # sns.scatterplot(df_plot, x='time', y='Inv.AC.U.V', hue=metric_name,
            #                 palette={True: 'red', False: 'gray'}, markers='o', s=50, ax=axe[2])
            # # === plot current
            sns.lineplot(df_plot, x='time', y='Inv.AC.I.A', legend='brief', label='AC Current', marker='o', ax=axe[3])
            sns.lineplot(df_plot, x='time', y='DC Current', legend='brief', label='DC Current', marker='o', ax=axe[3])
            # sns.scatterplot(df_plot, x='time', y='Inv.AC.I.A', hue=metric_name,
            #                 palette={True: 'red', False: 'gray'}, markers='o', s=50, ax=axe[3])

            # # === plot the frequency
            sns.lineplot(df_plot, x='time', y='Inv.AC.Freq.Hz', legend='brief', label='AC Frequency', marker='o', ax=axe[4])

            plt.savefig('results/plots/{}/{}_{}.png'.format(metric_name, MID, date_id))
            plt.close()
    def plot_simple_results(self, df, MID, metric_name):
        date_list = df.loc[df[metric_name] == True, 'date'].unique()
        if not os.path.exists('results/plots_simple/{}'.format(metric_name)):
            os.makedirs('results/plots_simple/{}'.format(metric_name))
        for date_id in date_list:
            df_plot = df[df['date'] == date_id]
            fig, axe = plt.subplots(nrows=2, figsize=(20, 5.5))
            # #==== plot AC power
            sns.lineplot(df_plot, x='time', y='theoretical_P.W', legend='brief', label='Theoretical Power',
                         ax=axe[0], linestyle='dashed', color='gray')
            sns.lineplot(df_plot, x='time', y='Gen.W', legend='brief', label='AC Power',
                         ax=axe[0], color='blue', linewidth=2)
            sns.scatterplot(df_plot, x='time', y='Gen.W', hue=metric_name,
                            palette={True: 'red', False: 'gray'}, markers='o', s=50, ax=axe[0])
            axe[0].set_ylabel('Power (W)')
            # axes[0].legend(loc=2, fontsize=font_size_value)
            axe[0].set_xlabel('Time')
            axe[0].grid(axis='y')

            # # === plot zoom-in AC voltage
            sns.lineplot(df_plot, x='time', y='Inv.AC.U.V', legend='brief', label='AC Voltage',
                         ax=axe[1], linewidth=2, marker='o')
            if df_plot['Inv.AC.U.V'].max() > 300:
                axe[1].set_ylim(420, 450)
            else:
                axe[1].set_ylim(240, 260)

            # # # === plot the frequency
            # sns.lineplot(df_plot, x='time', y='Inv.AC.Freq.Hz', legend='brief', label='AC Frequency', marker='o',
            #              ax=axe[2], linewidth=2, color='black')
            axe[1].set_xlabel('Time (5-minute resolution)', fontsize=18)
            plt.savefig('results/plots_simple/{}/{}_{}.png'.format(metric_name, MID, date_id))
            plt.close()

    def Labelling_Process(self):
        # #========== read raw data of all fimer monitors =======
        self.read_all_rawdata()
        # #==================== each monitor  ===================
        for MID in self.fimer_list:
            # #==================== Meta data  ==================
            MID_full = str('MNTR|' + MID)
            site_id = self.df_monitors.loc[self.df_monitors['source'] == MID_full, 'siteId'].iloc[0]
            time_zone = self.df_sites.loc[self.df_sites['source'] == site_id, 'timezone'].values[0]

            latitude = self.df_monitors.loc[self.df_monitors['source'] == MID_full, 'latitude'].values[0][1:]
            latitude = float(latitude)
            longitude = self.df_monitors.loc[self.df_monitors['source'] == MID_full, 'longitude'].values[0]
            longitude = float(longitude)

            pv_size = self.df_monitors.loc[self.df_monitors['source'] == MID_full, 'pvSizeWatt'].values[0]

            # #============ raw data for each monitor ============
            df = self.df_ac_power[['time', MID_full]].copy()
            df.rename(columns={MID_full: 'Gen.W'}, inplace=True)
            df['Inv.AC.U.V'] = self.df_ac_voltage[MID_full].values
            df['Inv.AC.I.A'] = self.df_ac_current[MID_full].values
            df['Inv.AC.Freq.Hz'] = self.df_ac_freq[MID_full].values
            df['Inv.DC.P.W'] = self.df_dc_power[MID_full].values
            df['Inv.DC.U.V'] = self.df_dc_voltage[MID_full].values
            df['DC Current'] = df['Inv.DC.P.W'].div(df['Inv.DC.U.V']).replace(np.inf, 0)

            # #====== Calculate the theoretical generation ==========
            time_index5min_local = pd.date_range(start=pd.to_datetime(self.time_start).tz_localize(time_zone),
                                                 end=pd.to_datetime(self.time_end).tz_localize(time_zone),
                                                 freq='5min')
            df_theoretical = get_irradiance(time_index5min_local=time_index5min_local, time_zone=time_zone,
                                            tilt=tilt, surface_azimuth=azimuth, latitude=latitude,
                                            longitude=longitude, pv_size=pv_size, loss_factor=loss_factor)
            df['theoretical_P.W'] = df_theoretical['POA'].values
            # #=========== time converter ================
            df['time'] = pd.to_datetime(df['time'].values)
            df['minute'] = df['time'].dt.minute
            df['hour'] = df['time'].dt.hour
            df['date'] = df['time'].dt.date
            df['date'] = df['date'].astype(pd.StringDtype())

            # #====== clear-sky days & sunrise sunset time =============
            df = self.select_date_time(time_index5min_local=time_index5min_local, df=df, site_id=site_id,
                                       latitude=latitude, longitude=longitude)

            # #====== Preprocessing data: outlier & missing data =============
            df = self.processing_monitor(df=df, pv_size=pv_size)

            # # #===============================================================
            # # #  Start Labelling: AC generation is zero
            # # #===============================================================
            # # #====== DC zero Generation =============
            # df = self.DC0_Labelling(df=df)
            # self.df_DC0[MID_full] = self.df_DC0['time'].map(df.set_index('time')['DC Zero Generation']).values
            # # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='DC Zero Generation')
            # self.plot_simple_results(df=df, MID=MID, metric_name='DC Zero Generation')
            #
            # # #====== Grid Overvoltage & Inverter tripping =========
            # df = self.grid_overvoltage_labelling(df=df)
            # self.df_GridOverVol[MID] = self.df_GridOverVol['time'].map(df.set_index('time')['grid_overVol']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='grid_overVol')
            # self.plot_simple_results(df=df, MID=MID, metric_name='grid_overVol')
            #
            # # #====== AC Voltage sensor malfuncttion (or blackout) =============
            # df = self.blackout_labelling(df=df)
            # self.df_Blackout[MID] = self.df_Blackout['time'].map(df.set_index('time')['blakout']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='blakout')
            # self.plot_simple_results(df=df, MID=MID, metric_name='blakout')
            #
            # # #====== Undersized MPPT input Voltage =============
            # df = self.undersize_mpptVol_labelling(df=df)
            # self.df_Undersize_MPPT[MID] = self.df_Undersize_MPPT['time'].map(df.set_index('time')['undersize_mppt_InVol']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='undersize_mppt_InVol')
            # self.plot_simple_results(df=df, MID=MID, metric_name='undersize_mppt_InVol')
            #
            # # #====== DC-side Issues with zero AC generation =============
            # df = self.dcside_gen0_issue_labelling(df=df)
            # self.df_DCissue_Gen0[MID] = self.df_DCissue_Gen0['time'].map(df.set_index('time')['DC_issue_Gen0']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='DC_issue_Gen0')
            # self.plot_simple_results(df=df, MID=MID, metric_name='DC_issue_Gen0')
            #
            # # #====== DC-side Issues with zero AC generation =============
            # df = self.dcside_gen0_issue_labelling(df=df)
            # self.df_DCissue_Gen0[MID] = self.df_DCissue_Gen0['time'].map(df.set_index('time')['DC_issue_Gen0']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='DC_issue_Gen0')
            # self.plot_simple_results(df=df, MID=MID, metric_name='DC_issue_Gen0')
            # # #===============================================================
            # # #  Labelling: AC generation is Flat
            # # #===============================================================
            diff_name, metric_name = 'AC', 'Gen.W'
            df = self.Flat_Generation(df=df, pv_size=pv_size, diff_name=diff_name, metric_name=metric_name)
            # # #====== Volt-Watt =============
            # df = self.volt_watt_labelling(df=df, diff_name=diff_name)
            # self.df_Volt_Watt[MID] = self.df_Volt_Watt['time'].map(df.set_index('time')['volt_watt']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='volt_watt')
            # self.plot_simple_results(df=df, MID=MID, metric_name='volt_watt')
            #
            # # #====== Volt-Var =============
            # df = self.volt_var_labelling(df=df, diff_name=diff_name)
            # self.df_Volt_Var[MID] = self.df_Volt_Var['time'].map(df.set_index('time')['volt_var']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='volt_var')
            # self.plot_simple_results(df=df, MID=MID, metric_name='volt_var')

            # #====== Inverter Clipping =============
            df = self.inverter_clipping_labelling(df=df, diff_name=diff_name)
            self.df_Inverter_Clipping[MID] = self.df_Inverter_Clipping['time'].map(df.set_index('time')['inverter_clipping']).values
            self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='inverter_clipping')
            self.plot_simple_results(df=df, MID=MID, metric_name='inverter_clipping')

            # # #====== DC-side issue with flat generation =============
            # df = self.DCside_flatGen_issue_labelling(df=df, diff_name=diff_name)
            # self.df_DCissue_FlatGen[MID] = self.df_DCissue_FlatGen['time'].map(
            #     df.set_index('time')['DCside_issue_flat']).values
            # self.plot_results(df=df, site_id=site_id, MID=MID, metric_name='DCside_issue_flat')
            # self.plot_simple_results(df=df, MID=MID, metric_name='DCside_issue_flat')


        # # save final labelling results
        # self.df_DC0.to_csv('results/df_DC_zero_generation.csv')
        # self.df_GridOverVol.to_csv('results/df_grid_OverVoltage.csv')
        # self.df_Blackout.to_csv('results/df_blackout.csv')
        # self.df_Undersize_MPPT.to_csv('results/df_undersized_MPPT.csv')
        # self.df_DCissue_Gen0.to_csv('results/df_dcissue_gen0.csv')
        # self.df_Volt_Watt.to_csv('results/df_volt_watt.csv')
        # self.df_Volt_Var.to_csv('results/df_volt_var.csv')
        # self.df_Inverter_Clipping.to_csv('results/df_inverter_clipping.csv')
        # self.df_DCissue_FlatGen.to_csv('results/df_dcissue_flatGen.csv')

time_start = '2022-09-06'
time_end = '2023-04-30'
df_sites = pd.read_csv('../input_data/SITE_nodeType_20230321.csv')
df_monitors = pd.read_csv('../input_data/MNTR_ddb_20230419.csv')
fimer_labelling = FIMER_DCAC_Labelling(time_start, time_end, df_monitors, df_sites)

fimer_labelling.Labelling_Process()
