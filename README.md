# GridPath-India visualization toolkit

**Visualization toolkit for GridPath-India Capacity Expansion Model (CEM) and Production Cost Model (PCM)**  

This repository contains Python plotting functionality designed to support visualization of outputs from the GridPath-India national energy model (CEM and PCM).

##  Repository Structure

### `csvs/`
Scenario metadata, technology mappings, and labeling tables used for post-processing and visualization.

These CSV files are used to define:
- scenario groupings
- visualization labels
- technology mappings
- zone mappings
- comparison sets for figures and tables

CVS files include:

- `technology_labels.csv`: standardized technology names and plotting labels.

- `zone_labels.csv`: mappings for load zones with labels and names.

- `cost-scenario_labels.csv`: scenario definitions used for technology cost comparisons.

- `demand-scenario_labels.csv`: bottom-up and linearly-scalled demand sensitivity scenarios.

- `prm-scenario_labels.csv`: planning reserve margin scenarios.

- `pier-scenario_labels.csv`: policy scenarios for bottom-up demand.

- `iced-scenario_labels.csv`: policy scenarios for linearly-scaled demand.

- `alternative-scenario_labels.csv`: alternative technologies scenarios.

- `pcm-scenario_labels.csv`: production cost model scenarios.

### `notebooks/`
Interactive Jupyter notebooks for exploratory analysis, diagnostics, figure generation, and manuscript preparation.

Notebooks to generate the figures in the manuscript:
- `overview-electricity_system.ipynb`
- `system-capacity_generation.ipynb`
- `system-summary.ipynb`
- `summary-transmission.ipynb`
- `system_zone-energy_dispatch.ipynb`

Notebooks to replicate the results reported in the manuscript.
- `paper.ipynb`
- `tables.ipynb`

### `src/`
Reusable Python modules for loading, processing, and visualizing GridPath outputs.

- `loading.py` — database and CSV loading utilities
- `processing.py` — post-processing and aggregation functions
- `visualization.py` — plotting utilities

### `templates/`
Reusable plotting templates and dashboard utilities for automated figure generation.

Includes:
- capacity expansion plots
- dispatch plots
- emissions and carbon plots
- curtailment heatmaps
- R-based visualization scripts
- shell scripts for batch plot generation
- dashboard utilities
## Installation

Clone the repository:

```bash
git clone https://github.com/cetlab-ucsb/gridpath_india_viz.git
cd gridpath_india_viz
```

Create conda environment:
```bash
conda create -n india_viz python=3.11
conda activate india_viz
```
Install package requirements
```bash
pip install -r requirements.txt
```
