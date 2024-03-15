# Smart Energy Asset Management Intelligence - Fault detection for level 1 faults

Documentation part of the NSSN Grand Challenge - Smart Energy Asset Management Intelligence Project

This repository contains the following projects:

1. **performance analysis**: Contains Jupyter Notebooks and data to perform a performance analysis in AC data at a site level
2. **labelling level 1**: Contains Jupyter Notebooks and data to perform level 1 labelling in AC data.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Subprojects](#subprojects)
  - [Performance Analysis](#performance-analysis)
  - [Level 1 Labelling](#level-1-labelling)
- [Acknowledgements](#acknowledgements)

## Prerequisites

What things you need to install and run this code:

- Python 3.9
- Jupyter Notebook
- Required Python libraries

## 1. Performance Analysis

Can be found under the folder ./performance analysis

#### Jupyter Notebooks

- `2_Performance_analysis_individual_site.ipynb`: Runs the performance analysis for 1 particular site. Necessary to provide SiteID
- `3_Performance_analysis_all_sites.ipynb`: Runs the performance analysis for all th sites. Reads from CSV exported from DynamoDB (e.g. Site_List_2023-04-28.csv).

#### Input Data

- `Monitors_List_2023-04-28.csv`: List of monitors as of 28th of April 2023.Exported from DynamoDB.
- `Site_List_2023-04-28.csv`: List of sites as of 28th of April 2023.Exported from DynamoDB.

## 2. Level 1 Labelling

Can be found under the folder ./labelling level 1 and can be categorised as such:

!['fault level 1'](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1691718695/jheb1fidagigkes718fr.png)

### 2.1. Performance-related faults
Performance-related faults are determined based on analysis of daily aggregate performance.

This data is queried from a site-level.

#### 2.1.1. Performance - Major Underperformance
System is performing at less than 60 % for 3 days or more

#### 2.1.2. Performance - Minor Underperformance
System is performing at less than 80 % for 7 days or more.

#### 2.1.3. Performance - Week-related Underperformance
System underperforms either during weekends or weekdays.
When this check is performed, all days of that week are labelled as such.

- Weekend Underperformance: The performance is often lower on weekends
- Weekdays Underperformance: The performance is often lower on weekdays.

#### 2.1.4. Performance - Seasonal Underperformance
System underperforms during a specific season.

### 2.2. Raw-signal-related faults
Raw-signal-related faults are determined based on analysis of AC generation data (W) in 5-minutes intervals.

This data is queried from a monitor-level.

#### 2.2.1. Raw-signal - No Data

There’s just no data.

#### 2.2.2. Raw-signal - Tripping

During daytime, the AC generation intermittently goes to zero and then back to normal. Trigger if this happens more than 3 times in a day.

#### 2.2.3. Raw-signal - Clipping

During daytime, the AC generation clips at a specific value and doesn’t exceed it. Trigger if this occurs for longer than an hour. Note that the value won’t be exactly the same when clipping occurs but the profile will look flat.

#### 2.2.4. Raw-signal - Zero-Generation

There is some negative generation. Trigger as soon as that occurs.

#### 2.2.5. Raw-signal - Recurring underperformance

There is a recurrent dent (i.e., it happens every day) in the generation profile at a particular time of the day. Note that the dent is more detectable on sunny days. On cloudy days, it might be diluted in the profile’s variation.

#### 2.2.6. Raw-signal - Non-Zero Tripping

During daytime, the AC generation intermittently rapidly spikes down (decreases and increases back to normal). Trigger if this happens more than 3 times in a day.

#### 2.2.7. Raw-signal - Night-Time Generation

There is AC generation at night time. 

#### 2.2.8. Raw-signal - Negative Generation

There is some negative generation. At least 1% of system size

#### 2.2.9. Raw-signal - Excessive Generation

The generation is excessively higher than expected. Excessive 100% of system size


#### Jupyter Notebooks

- `1A_labelling_site.ipynb.ipynb`: Analyse one site, taking into SiteID and labels every occurrence of any performance-related faults. (see section 2.1.)
- `1B_labelling_site_aggregate.ipynb`: Analyses a list of sites (e.g. Site_List_2023-04-28.csv) and outputs a CSV with every site that currently contains an occurence of any performance-related fault.
- `1C_validation_labelling_monitor.ipynb`: Takes into a list of manually labelled fault and runs an analysis of faults for all those sites.


- `2A_labelling_monitor.ipynb`: Analyse one monitor, taking into MonitorID and labels every occurrence of any raw-signal-related fault. (see section 2.2.)
- `2B_labelling_monitor_aggregate.ipynb`: Analyses a list of monitors (e.g. Monitor_List_2023-04-28.csv) and outputs a CSV with every monitor that currently contains an occurence of any raw-signal-related fault.
- `2C_validation_labelling_monitor.ipynb`: Takes into a list of manually labelled faults and runs an analysis of faults for all those monitors.

- `3_validation.ipynb`: Takes into the result of scripts 1C and 2C and compares the results with the manually labelled faults. Outputs a range of confusion matrices, and plots for false negatives.


#### Input Data

- `Monitors_List_2023-09-14.csv`: List of monitors as of 28th of April 2023. Exported from DynamoDB.
- `Site_List_2023-09-14.csv`: List of sites as of 28th of April 2023. Exported from DynamoDB.
- `Diagno_Labelling_2023-09-01.csv`: List of sites as of 28th of April 2023. Exported from DynamoDB.

#### Output

- level1_sites
   - individual_sites: Includes individual CSVs for every single site that had a fault identified
   - aggregate: Aggregate the most recent faults based on a time-window (e.g. faults in the last week)
- Level1_monitors
   - individual_monitors: Includes individual CSVs for every single monitor that had a fault identified
   - aggregate: Aggregate the most recent faults based on a time-window (e.g. faults in the last week)
- Validation
   - Confusion Matrices
   - Plots for false negatives

## 3. Acknowledgements

- NSSN Grand Challenge
- GSES
- UNSW
- UTS
