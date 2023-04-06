# Kattis / Canvas Helper

## Prerequisites
1. Python 3.8 or higher.
2. Install pip3 if not installed already.

## Setup

Clone the repo locally
1. Open a terminal and cd into the project directory
2. Run ```source setup.sh```
3. In the ```cache/honors_problems.in``` list the problems that should not be counted for honors students, each on a new
line. Each line should contain the kattis problem id (ex: onaveragetheyrepurple)

## Usage
- Start the program with ```python3 main.py```
- The program will prompt you for filepaths to a Canvas gradebook csv and a Kattis JSON Export.
  - If you want to avoid entering these manually, you can set a value for the constants ```KATTIS_JSON``` and ```CANVAS_CSV_PATH``` in ```main.py```
- On the first run, the program will ask for assistance in matching the Kattis users to the appropriate Canvas names.
- Once the program is complete, an updated gradebook will be exported into ```output.csv```