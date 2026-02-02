# GridPath-India Plotting Companion

**Visualization toolkit for GridPath-India Capacity Expansion Model (CEM) and Production Cost Model (PCM)**  

This repository contains Python plotting functionality designed to support visualization of outputs from the GridPath-India national energy model (CEM and PCM).

##  Repository Structure

`data/`: Holds reference (lookup tables) and spatial (shapefiles for Indian states) data that do not change across scenarios.

`csvs/`: Path to scenario result outputs from GridPath-India. Technology colors and groups (`technology_labels.csv`).

`templates/`: Original plotting functions for Python and R.

`software/`: All Python code that actually makes the figures: functions to load CSVs, and data processing routines, and plotting functions (time series, stacked bars, maps, etc.)

This project is licensed under the Apache License 2.0.
