# Data Discrepancy: Gridded (TIFF) vs. Station Data

This document explains why rainfall values in the gridded TileDB database (derived from TIFF files) may differ from raw station observations found on the HCDP website or in station JSON files.

## Summary of Differences

It is normal and expected for gridded (raster) data to deviate from point (station) measurements in meteorological datasets.

### 1. Interpolation (Point vs. Grid)
*   **Station Data**: Represents a **Point** measurement at a specific rain gauge.
*   **Gridded Data**: Represents an **estimate** across a continuous spatial grid. Each pixel (250m x 250m) is calculated by interpolating between many nearby stations using geostatistical methods (e.g., Kriging).

### 2. Spatial Averaging
A pixel value represents the **average rainfall** over a 62,500 square meter area. A single rain gauge within that area might catch more or less rain than the average for the entire grid cell, especially in areas with microclimates.

### 3. Gap Filling (Infilling)
Gridded products are designed to provide complete spatial coverage. If a specific station was offline, returned poor-quality data, or had missing days in a month, the gridded model "fills in" the value based on the surrounding stations and environmental predictors.
*   **Example**: SKN 705.9 reported **0mm** for August 2021 in raw records, but the gridded model estimated **~50mm** at that location based on the broader regional trend.

### 4. Topographical Adjustments
The HCDP gridded products account for Hawaii's complex topography, including elevation, slope, aspect, and "rain shadow" effects. The model may adjust a pixel's value to reflect these physical factors, even if it is very close to a station.

### 5. Production Versions
HCDP occasionally releases updated "Production" versions of their data (e.g., "New" vs. "Legacy"). Discrepancies can occur if the TIff files were downloaded from one production version while the website displays another.

---
*Reference: [Hawaiʻi Climate Data Portal (HCDP)](https://www.hawaii.edu/climate-data-portal/)*
