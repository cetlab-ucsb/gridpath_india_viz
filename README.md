# GridPath-India Visualization Toolkit

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

Jupyter notebooks for exploratory analysis, diagnostics, publication figures, and manuscript tables.

#### System-Level Analysis

- `overview-electricity_system.ipynb`: High-level overview of currect electricity system.
- `system-summary.ipynb`: Emission, costs and clean energy summary aggregated at the system level.
- `system-capacity_summary.ipynb`: Installed capacity, emission and cost summaries by technology and scenario.
- `system-capacity_generation.ipynb`: Analysis of installed capacity and electricity generation.
- `system-retirements.ipynb`: Generator retirement trajectories across planning horizons.
- `system-technology_costs.ipynb`: Evolution of technology costs and investment assumptions.
- `system-land_used.ipynb`: Land-use implications of energy infrastructure deployment.
- `system_zone-energy_dispatch.ipynb`: Temporal and spatial dispatch analysis by load zone.

#### Load Zone-Level Analysis

- `zone-capacity_generation.ipynb`: Capacity and generation breakdowns at the load zones.
- `zone-demand_profiles.ipynb`: Load zone demand profiles and temporal load characteristics.
- `zone-capacity_factors-inertia-installation_rates.ipynb`: Capacity factors, system inertia metrics, and installation rate analysis.

#### Transmission Analysis

- `summary-transmission.ipynb`: Transmission expansion and interregional transfer analysis.

#### Technology Cost Analysis

- `overview-technology_costs.ipynb`:  India-specific new projects technology cost projections.
- `specified_costs.ipynb`: India-specific existing technology costs.

#### Diagnostics and Validation

- `diagnostic_plots.ipynb`: Diagnostic visualizations and quality-control checks for model outputs.

#### Manuscript Preparation

- `tables.ipynb`: Automated generation of manuscript-ready tables.
- `paper.ipynb`: Central notebook used for producing results included in manuscript.

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
