# GridPath-India visualization toolkit

**Visualization toolkit for GridPath-India Capacity Expansion Model (CEM) and Production Cost Model (PCM)**  

This repository contains Python plotting functionality designed to support visualization of outputs from the GridPath-India national energy model (CEM and PCM).

##  Repository Structure

`csvs/`: Path to scenario result outputs from GridPath-India. Technology colors and groups (`technology_labels.csv`).

## Repository Structure

### `notebooks/`
Interactive Jupyter notebooks for exploratory analysis, diagnostics, figure generation, and manuscript preparation.

Key notebooks include:

- `overview-electricity_system.ipynb`
- `system-capacity_generation.ipynb`
- `system-summary.ipynb`
- `summary-transmission.ipynb`
- `system_zone-energy_dispatch.ipynb`
- `paper.ipynb`

### `src/`
Reusable Python modules for loading, processing, and visualizing GridPath outputs.

- `loading.py` — database and CSV loading utilities
- `processing.py` — post-processing and aggregation functions
- `visualization.py` / `viz.py` — plotting utilities
- `utils.py` — helper functions

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

conda create -n india_viz python=3.11
conda activate india_viz

pip install -r requirements.txt
