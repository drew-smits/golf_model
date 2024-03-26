import time
import config
import logging
import db_tools
import utils
from datetime import date
import pandas as pd
import golfsim
import pga_tools


log = logging.getLogger(__name__)
if config.debug:
    level = logging.WARNING
    filename = ''
    if config.verbose:
        level = logging.INFO
    if config.to_file:
        filename = config.log_filename
    logging.basicConfig(filename=filename, level=level)

db = db_tools.DB_Interface(config.db_filename)
s = golfsim.Sim(config.num_sims, config.num_rounds, config.cut_round, config.cut_line)
s.set_purse(pga_tools.get_purse_breakdown(config.pga_purse_url))

log.info('Loading player list...')
t = time.perf_counter()
df_players = db.get_dg_pred()
log.info(f'Loading player list complete. ({time.perf_counter() - t}s)')

log.info('Loading player profiles...')
t = time.perf_counter()
for i in df_players['dg_id']:
    df_rounds = db.get_player_rounds([i])
    df_rounds = df_rounds[df_rounds['date'].astype('int64') >
                          utils.get_earliest_int_date(date.today(), config.max_round_age)]
    sg_index = df_players.loc[df_players['dg_id'] == i]['final_pred'].values[0]
    sg_sd = df_players.loc[df_players['dg_id'] == i]['std_deviation'].values[0]
    if len(df_rounds) > config.min_rounds:
        df_rounds['date'] = [utils.get_age_int_date(d, utils.date_to_int(date.today())) for d in df_rounds['date'].values]
        sg_index, sg_sd = utils.calcPlayerSkill(df_rounds['sg_total'].values,
                                                                    df_rounds['date'].astype('float64').values,
                                                                    config.decayFunction,
                                                                    config.decayExp, config.decayOffset, [1])
    else:
        log.info(f'Insufficient number of rounds for {i}, {len(df_rounds)}')

    s.add_player(i, sg_index, sg_sd)


log.info(f'Loading player profiles complete. ({time.perf_counter() - t}s)')

log.info(f'Simulating {config.num_sims * config.num_rounds * df_players.shape[0]} player rounds...')
t = time.perf_counter()
s.sim_rounds()
log.info(f'Simulating {config.num_sims * config.num_rounds * df_players.shape[0]} player rounds complete. ({time.perf_counter() - t}s)')

log.info(f'Simulating {config.num_sims} tournaments...')
t = time.perf_counter()
s.sim_tournaments()
log.info(f'Simulating {config.num_sims} tournaments complete ({time.perf_counter() - t}s)')

log.info(f'Calculating results...')
t = time.perf_counter()
s.calculate_results()
log.info(f'Calculating results complete. ({time.perf_counter() - t}s)')

df = None
df_names = db.get_player_names()
tournament_id = db.get_max_sim_tournament_id()
players = s.get_players()
for player_id, player in players.items():
    new = db.tournamentPlayerPredictions.get_df({
                'sim_tournament_id': tournament_id,
                'dg_id': player_id,
                'x_earnings': player.avg_earnings,
                'sim_win': player.win,
                'sim_top5': player.top5,
                'sim_top10': player.top10,
                'sim_top20': player.top20,
                'sim_made_cut': player.made_cut,
                'x_finish': player.avg_finish,
                'sg_index': player.index,
                'sg_sd': player.std_dev,
                'sim_date': utils.date_to_int(date.today())
            })
    if df is None:
        df = new
    else:
        df = pd.concat((df, new))

df = df.sort_values(by='x_earnings', ascending=False)
print(df.head())

save = input('Save results? y/n: ')
if save == 'y':
    db.update_player_predictions(df)
