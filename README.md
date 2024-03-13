# Trigger Monitoring Dashboard for Anticipated Action  Guide

Author - Nitin Magima

Date - March 2024

Version - 1.0

This is a README file created for the Trigger Monitoring Dashboard for Anticipated Action Programs for WFP in various 
countries. The dashboard has been built in python using "Shiny for Python". The struture is similar to the Python 
maproom created for AA Design. The code base has been designed in such a way that only the YAML file needs to be 
updated to create a new Trigger Monitoring Dashboard. The Trigger Monitoring Dashboard takes advantage of the map rooms 
already created for respective countries and pulls  the data from there.The code has been divided  into four files: 

1. eos_madagascar_v1.ipynb - creates the front end of the dashboard. Creates filterable tables for admin 0 and admin 1 levels.  
2. utils.py - contains functions to use the maproom API
3. config.yaml - contains the data for the functions to work in utils.py 
4. get_admin1data.py - help manually update the config.yaml file of admin1_list. 


### Purpose
The Jupyter Notebook aims to do a post-assessment of drought in Madagascar during the relevant seasons such as October-November-December (OND) and December-January-February (DJF).

### Audience
Tailored for Madagascar government officials in agriculture, water resources, and disaster management sectors.

### Objectives
To provide an in-depth analysis of drought conditions during OND and DJF, historical drought patterns in these months, and predictive insights for future OND seasons.

### Summary
The jupyter notebook uses VIIRS product #13, Gridded Vegetation Indices (VNP13 Level 3 suite). The level 3 gridded vegetation indices are standard products designed to extend the significant VI time series derived from AVHRR and MODIS (Huete et al. 2002). The level 3 spatial and temporal gridded vegetation index products are composites of daily surface reflectances. They are generated at 500m, 1km, and 0.05o (~5.6km) every 8 days (quasi), 16 days, and calendar month. 

The standard Normalized Difference Vegetation Index (NDVI), is referred to as the “continuity index” to the existing NOAA-AVHRR and MODIS-derived NDVI. At the time of S-NPP launch S-NPP VIIRS VI User Guide-V2.1.1 8  (2011), there was nearly a 30-year NDVI record from AVHRR and MODIS (1981- and 2000-). VIIRS NDVI will extend this long-term data record for use in operational monitoring studies.

The Enhanced Vegetation Index (EVI) was developed to optimize the vegetation signal with improved sensitivity in high biomass regions and improved vegetation monitoring through a de-coupling of the canopy background signal and a reduction in atmosphere influences (Huete et al. 1997; Huete et al. 2002). 

The Standardized Precipitation Index (SPI) developed by McKee et al. (1993) describes the probability of variation from the normal precipitation over multiple years of data, on a monthly (or multiple months) time step. The SPI is calculated by taking the precipitation of the pixel i during timeframe j of year k minus the mean of pixel i during timeframe j over n years, divided by the standard deviation of pixel i during timeframe j over n years.

The jupyter notebook creates a standardized precipitation index (SPI) timeline based on daily CHIRPS data (since 1981). The SPI is used as it highlights the difference to the mean precipitation during a given time and therefore provides information about drought-like conditions. The script will be executed within Google Earth Engine and will work on two independent SPI calculations. 

The first calculation deals with the "common" SPI, which is calculated on an n-months basis. A SPI, which is calculated for one month usually refers to the description of "SPI-1", for six months "SPI-6" and so on. The second SPI calculation is based on MODIS capture dates. As MODIS (MOD13Q1.006) provides information about the vegetation, it might be useful to compare its vegetation indices with the SPI. Therefore a 16-day SPI is calculated, whose start date matches with MODIS's start date (if the user does not apply a 'shift').

As precipitation data is usually not normally distributed, especially when it comes to timeframes of 12 months or less, a transformation should be applied. The data is typically fitted to a gamma function, but not supported in the script. The resulting SPI values can therefore just be used as an estimator.

Google Earth Engine (GEE) is a web platform for cloud-based processing of remote sensing data on a large scale. The advantage lies in its remarkable computation speed as processing is outsourced to Google servers. The platform provides a variety of constantly updated datasets; no download of raw imagery is required. While it is free of charge, one still needs to activate access to Google Earth Engine with a valid Google account.


## YAML Description

In the config.yaml file, you will see that the structure of the YAML file is such that each country's map room has 
been listed, along with these variables.

1. maproom: to access the appropriate maproom
2. country: country name. The difference between the maproom variable and the country variable is that the maproom 
sometimes has the season hyphenated in it. This is why the maproom variable from the country variable has to be different
3. target_season: The target season is the season the maproom targetsmode: mode refers to the geographic level of the 
data. If you want the full country, it would be ‘0’, the next level (probably region) would be ‘1’, district (this case) 
would be ‘2’, and so on for as many levels are configured. Different admin levels are described in terms of both 
name and key, where the name is the admin level name and the key is the admin level in integer.
4. season:This field refers to the season you need data from, for now, all maptools have just one season, 
so this field will be always season1. This does not need to be changed. 
5. predictor=pnep: This refers to the variable that is predicting the season, in this case, ‘pnep’ refers to the IRI 
forecast result. It can change to total rainfall, average rainfall, or any other data set included in the tool. 
You can review all available predictors in the dropdown menu in the tool. To find the ID to use for a given variable, 
see the config file https://github.com/iridl/python-maprooms/blob/master/fbfmaproom/fbfmaproom-sample.yaml
6. predictand: This refers to the variable on which the forecast result will be compared and used to calculate 
the skill. It is usually labeled as bad years since we want to know how many of the known bad years are captured by 
the forecast. The available options are the same as for predictor (see above)
7. year: year of the season
8. issue_month0: the month you want the forecast result from. It is important to note that month counting starts at zero.
9. freq: This refers to the frequency of the event you want the forecast for. It corresponds to the ‘frequency of event’
slider in the tool
10. include_upcoming=false: This field states that the forecast for the upcoming season is not included in the 
historical statistics used to calculate the forecast or the skill. We usually include only past seasons in the 
historical data. 
11. design_tool: link to the design/maptool. Updates in the "Additional Resouces" tab in the front end
12. report: link to the AA reports.Updates in the "Additional Resouces" tab in the front end
13. username: use username if the maproom is behind a sign-in wall
14. password: use username if the maproom is behind a sign-in wall
15. threshold_protocol:The threshold protocol is decided during the respective country working groups to see if 
additional points are required to determine whether the forecast will be triggered or not
16. need_valid_keys: assign value True, without quotes (don't use "True"), if using admin1_list
17. admin1_list: this field refers to the list of keys or admin level 1 the AA project is focusing on. The admin1 list 
is there in case only certain admin1 units need to be shown in the trigger monitoring table, this list needs to be 
updated. To see the full list of keys, go to the data folder and see the respective maproom CSV file. If it's not there, 
you can use the get_admin1_data.py to create the CSV files in the data folder, and then open the CSV file that reflects 
your maproom name to update the admin1_list.

### DISCLAIMER

This is a set of scripts  shared for educational purposes only.  Anyone who uses this code or its
functionality or structure, assumes full liability and credits the author.

#### Map Disclaimer

The designations employed and the presentation of the material on this map do not imply the expression 
of any opinion whatsoever on the part of the author concerning the legal status of any country, territory, city or area or of its authorities, or concerning the delimitation of its 
frontiers or boundaries.

### Sources
- [LANDDATAOPERATIONALPRODUCTSEVALUATION MODIS/VIIRS LAND PRODUCT QUALITY ASSESSMENT](https://landweb.modaps.eosdis.nasa.gov/browse?sensor=VIIRS&sat=SNPP)
- [Vegetation Index Product Suite User Guide & Abridged Algorithm Theoretical Basis Document](https://lpdaac.usgs.gov/documents/1372/VNP13_User_Guide_ATBD_V2.1.2.pdf)
- [UN-SPIDER Knowledge Portal (SPI)](https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-drought-monitoring-spi)