import os
from golfsim import utils


# Tournament specific config
tsg_tour = 'pga'
pga_purse_url = 'https://www.pgatour.com/article/news/latest/2024/03/25/prize-money-purse-breakdown-texas-childrens-houston-open-memorial-park'
cut_line = 65
cut_round = 2

# Sim config
max_round_age = 730
num_sims = 100000
num_rounds = 4
decayFunction = utils.inverseAgeDecay
decayExp = 1/1.01
decayOffset = 100
min_rounds = 25

# File paths
db_filename = os.path.join('local', 'golfmodel.db')

# Update config
updateWaitTime = 5

# Debug config
debug = True
verbose = True
to_file = False
log_filename = 'logs/debug.txt'