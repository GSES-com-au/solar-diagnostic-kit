# Level 1 Faults - Description and Brief

- A Level 1 label is one that is applied from analysing AC Power Generation data (Gen.W from monitor data) and/or Performance data (using Production.kWh.Daily + Irrad.kWh.m2.Daily + EnergyYield.kWh.Daily from site data).
- Level 1 doesn’t consider any other metrics provided by an inverter (regardless of whether it’s available or not).
- While a lot of these faults can be detected using simple statistical methods, some may require more advanced techniques (e.g., maybe the Recurring Underperformance).
- The conditions required for triggering a label are sometimes provided (e.g., Generation Tripping). When the conditions are not provided, a best approach has to be defined (e.g., Weekend Underperformance).
- AC Power Generation is available for monitors whereas Performance is available for sites (not currently calculated for monitors). A site can have multiple monitors.
- If a fault is detected, a label will be applied to the site for the day it was detected.
- Faults can therefore be persistent and may apply over consecutive days. There can be multiple faults per site.
- **The code has to be designed such that it will be run on schedule once a day and will analyse the previous day.**
- **The code generates a daily report as a csv, where the file name includes date, each row is a site and the columns are: Site Name, Site Address, Site ID, Labels**
- **The values under the Labels column are stored in arrays (e.g., [L1F002, L1F009, L1F010])**

### Level 1 Faults Summary Table

| Code | Name | Metrics | Minimum Fault Duration | Minimum Label Duration | Requires Clearsky | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| L1F000 | No Data | Any | 1 hour | 1 day | No |  |
| L1F001 | Generation Tripping | Gen.W | 3 occurrences in a day | 1 day | No | Pick a minimum threshold to avoid false positives due to precision error: 1% of system size |
| L1F002 | Generation Clipping | Gen.W | 1 hour | 1 day | Yes | Pick a minimum threshold to avoid false negatives as clipping is never just one value: 1% of system size |
| L1F003 | Zero Generation | Gen.W | 1 hour | 1 day | No | Pick a minimum threshold to avoid false positives due to precision error: 1% of system size |
| L1F004 | Recurring Underperformance | Gen.W | 3 days in a row | 3 days | Yes |  |
| L1F005 | Major Underperformance | Perf | 3 days in a row | 3 days | Yes |  |
| L1F006 | Minor Underperformance | Perf | 7 days in a row | 7 days | Yes |  |
| L1F007 | Weekend Underperformance | Perf | Variable depending on weather | Exactly 2 days | Yes | Compare weekend day with average performance for previous 10 weekday entries. Flag if more than 20% under. |
| L1F008 | Weekdays Underperformance | Perf | Variable depending on weather | Exactly 5 days | Yes | Compare weekday with average performance for previous 4 weekend entries. Flag if more than 20% under. |
| L1F009 | Winter Underperformance | Perf | Compare with previous summer average | 1 day | Yes |  |
| L1F010 | Summer Underperformance | Perf | Compare with previous winter average | 1 day | Yes |  |
| L1F011 | Non-Zero Tripping | Gen.W | 3 occurrences in a day | 1 day | Yes |  |
| L1F012 | Night-Time Generation | Gen.W | 1 hour | 1 day | No |  |
| L1F013 | Negative Generation | Gen.W | 1 hour | 1 day | No | Pick a minimum threshold to avoid false positives due to precision error: 1% of system size |
| L1F014 | Excessive Generation | Gen.W | As soon as it occurs | 1 day | No | Pick a minimum threshold to avoid false positives: excessive 100% of system size |

- **No Data**: There’s just no data.

- **Generation Tripping**: During daytime, the AC generation intermittently goes to zero and then back to normal. Trigger if this happens more than 3 times in a day.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510789/NSSN%20GSES/gxlq5uonhwcwjoht9e69.png)

- **Generation Clipping**: During daytime, the AC generation clips at a specific value and doesn’t exceed it. Trigger if this occurs for longer than an hour. Note that the value won’t be exactly the same when clipping occurs but the profile will look flat.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/qsyxdjtdimrqvczpjn2g.png)

- **Zero Generation**: The AC generation is zero for an hour or more.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/zsjovizvtskiosamltth.png)

- **Recurring Underperformance:** There is a recurrent dent (i.e., it happens every day) in the generation profile at a particular time of the day. Note that the dent is more detectable on sunny days. On cloudy days, it might be diluted in the profile’s variation.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510787/NSSN%20GSES/jg0j9nbxprfdzwjwslwk.png)

- **Major Underperformance**: System is performing at less than 60 % for 3 days or more. Use the sudden and unresolved fault code for this.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/qw2xaopkmwpmkp4gesz7.png)

- **Minor Underperformance**: System is performing at less than 80 % for 7 days or more. Use the sudden and unresolved fault code for this.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/rpz37gzj8avyr8aaxua5.png)

- **Weekend Underperformance:** The performance is often lower on weekends.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/iezdaon36waarzjczyc6.png)

- **Weekdays Underperformance:** The performance is often lower on weekdays.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/dvw4tuch4sokqycjankf.png)

- **Winter Underperformance**: There is a seasonal underperformance in winter.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/v43cmtcq7ol0kanqa3j8.png)

- **Summer Underperformance**: There is a seasonal underperformance in summer.

![Untitled](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510789/NSSN%20GSES/qmai0heujgsjun0msuwb.png)

- **Non-Zero Tripping**: During daytime, the AC generation intermittently rapidly spikes down (decreases and increases back to normal). Trigger if this happens more than 3 times in a day.

![nonzeroTripping3.png](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510787/NSSN%20GSES/qrkdtxifxeqcvyetrjai.png)

- **Night-Time Generation**: There is AC generation at night time. Trigger as soon as that occurs.

![image (3).png](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510787/NSSN%20GSES/pfma2ybznkihbcv1gwer.png)

- **Negative Generation**: There is some negative generation. Trigger as soon as that occurs.
    
    ![image (4).png](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510788/NSSN%20GSES/g3nvj5ouvcd70mucu9ts.png)
    

- **Excessive Generation**: The generation is excessively higher than expected. Trigger as soon as that occurs.
    
    ![excessiveGeneration.png](https://res.cloudinary.com/dxbk4zeyc/image/upload/v1697510787/NSSN%20GSES/a8zkw7jjlqwlgmkqzedc.png)