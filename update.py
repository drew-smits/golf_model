import config
import time
import logging
from golfsim import dg_tools as dg, pga_tools, db_tools

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

api = dg.API()
db = db_tools.DB_Interface(config.db_filename)

t = time.perf_counter()
log.info('Updating tournament info...')
tourn = api.get_next_event(tour=config.tsg_tour)
purse = pga_tools.get_purse_breakdown(config.pga_purse_url)
db.update_sim_tournaments(db.simTournaments.get_df([
    tourn['event_name'],
    int(tourn['start_date'].replace('-', '')),
    config.tsg_tour,
    int(tourn['event_id']),
    config.cut_line,
    config.cut_round,
    str(purse)
]))
log.info(f'Updating tournament info complete. ({time.perf_counter() - t}s)')

t = time.perf_counter()
log.info('Updating DataGolf Pred...')
db.update_dg_pred(api)
log.info(f'Updating DataGolf Pred complete. ({time.perf_counter() - t}s)')

log.info('Updating Player Names...')
t = time.perf_counter()
db.update_player_names(api)
log.info(f'Updating Players Table complete ({time.perf_counter() - t})s')

log.info('Updating Round History...')
t = time.perf_counter()
players = db.get_dg_pred()
df_player_names = db.get_player_names()
idx = 0
for plr in players['dg_id']:
    idx += 1
    name = df_player_names.loc[df_player_names['dg_id'] == plr]['player_name'].values[0]
    log.info(f'Updating Round history for {name}. {len(players) - idx} remaining.')
    num_rounds = db.update_player_rounds(api, plr)
    log.info(f'Updated {num_rounds} rounds for {name}.')
    time.sleep(config.updateWaitTime)
log.info(f'Updating Round History Table complete. ({time.perf_counter() -t }s)')

