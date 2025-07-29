# ATJ

This package provides an open-source modular framework for Sustainable Aviation Fuel (SAF) production via the  Alcohol-to-Jet (ATJ) pathway.


## Installation
Clone the repository

git clone https://github.com/H-Wadgama/ATJ.git
cd atj_saf

## Create a venv
conda create -n pyfuel python=3.10
conda activate pyfuel

## Install required packages 
pip install -r requirements.txt
If you want to develop the package, install in editable mode:
pip install -e .

## Simulate the baseline biorefinery
python -m atj_saf.main
This simulates a stream summmary, and the MJSP


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

## Questions
Feel free to reach out on LinkedIn!





```bash
git clone https://github.com/H-Wadgama/ATJ.git
cd atj_saf
pip install -e .
