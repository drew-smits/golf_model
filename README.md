# golf_model

## Initial Setup
Assumes python has already been installed. 

### Clone github repo
Using terminal (OSX/Linux) or Command Prompt (Windows), navigate to desired directory. Run "git clone https://github.com/drew-smits/golf_model"

### Create virtual environment
Move into the newly created directory with "cd golf_model". Create a python virtual environment with "python -m venv myvenv", where myvenv is whatever name you choose. Activate the venv with "source myenv/bin/activate" (OSX/Linux) or "myenv\Scripts\activate" (Windows)

### Install requirements
Run the command "pip install -r requirements.txt"

### Create database
TODO

### Build rust package
If you haven't already installed rust, follow the instructions at https://www.rust-lang.org/tools/install. Navigate to the directory golfsim in your terminal/command prompt. Run the command "maturin develop --release".

## Run a simulation

### Update config.py
Open the file config.py, update the address for the desired weeks pga tour event. This website can typically be found with a google search for "event_name purse site:pgatour.com".

### Update database
Run update.py

### Run simulation
Run pretournamnet.py