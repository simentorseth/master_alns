# Master's Thesis: [A Matheuristic Algorithm for an Offshore Multi-period Location Routing Problem]

## Overview
This thesis provides a solution approach for the multi-period location routing problem set in an offshore wind farm. The
proposed solution is a matheuristic algorithm. The algorithm utilises an adaptive large neighbourhood search to determine
routing variables of electric vessels, and pass these to an integer program which determines the optimal placement of
charging stations with respect to the routing variables. This repository contains only the matheuristic algorithm which
is implemented in Python.

## Installation
Instructions on setting up the project environment:
1. Clone the repository:
   ```bash
   git clone (https://github.com/simentorseth/master_alns)

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
## Usage
To run the matheuristic use the following command with the arguments `num` which is the number of runs to do on an instance
and `file` is the instance to solve:
```bash
python3 ./src/heuristic/main.py [num] [file]
```

## Dependencies
- Python 3.9+
- haversine
