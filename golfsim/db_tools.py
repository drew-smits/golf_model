import sqlite3
import pandas as pd
from . import utils

def list_to_query_string(items):
    s = ''
    for i in range(len(items)):
        s += str(items[i]) + ', '
    return s[:-2]


class Table:
    table_name = ''
    columns = []
    dtypes = []
    foreign_keys = []
    auto_incr_index = True
    index_name = 'index'

    def __init__(self):
        pass

    def _build_select_column_string(self, columns):
        return f'SELECT {list_to_query_string(columns)} FROM {self.table_name}'

    def _update_index(self, df, conn):
        idx = self.get_max_index(conn) or 1
        idx += 1
        df.index = [i for i in range(idx, idx + len(df))]

    def get_max_index(self, conn):
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX({self.index_name}) FROM {self.table_name}")
        return cursor.fetchone()[0]

    def get_df(self, data=None):
        if data is None:
            data = []
        if self.auto_incr_index:
            col = self.columns[1:]
        else:
            col = self.columns
        if len(data) > 0:
            df = pd.DataFrame(columns=col, data=[data])
        else:
            df = pd.DataFrame(columns=col)
        df.index.name = self.index_name
        return df

    def get_all(self, conn):
        return pd.read_sql_query(f'SELECT * FROM {self.table_name}', conn)

    def get_columns(self, columns, conn):
        s = self._build_select_column_string(columns)
        return pd.read_sql_query(s, conn)

    def append_df(self, df, conn):
        if self.auto_incr_index:
            self._update_index(df, conn)
        df.to_sql(self.table_name, conn, if_exists='append', index=self.auto_incr_index, index_label=self.index_name)

    def replace_df(self, df, conn):
        if self.auto_incr_index:
            self._update_index(df, conn)
        self.drop_table(conn)
        self.create_table(conn)
        df.to_sql(self.table_name, conn, if_exists='append', index=self.auto_incr_index, index_label=self.index_name)

    def drop_table(self, conn):
        cursor = conn.cursor()
        try:
            cursor.execute(f'DROP TABLE {self.table_name};')
        except sqlite3.OperationalError:
            pass

    def create_table(self, conn):
        cursor = conn.cursor()
        s = f'CREATE Table {self.table_name} ('
        if self.auto_incr_index:
            s += f'{self.index_name} INTEGER PRIMARY KEY AUTOINCREMENT, '
        else:
            s += f'{self.columns[0]} {self.dtypes[0]} PRIMARY KEY, '
        for i in range(1, len(self.columns)):
            s += f'{self.columns[i]} {self.dtypes[i]}, '
        s = s[:-2]
        if len(self.foreign_keys) > 0:
            s += ', '
            for key in self.foreign_keys:
                s += f'FOREIGN KEY({key}) REFERENCES {self.foreign_keys[key]}, '
        s = s[:-2] + ')'
        cursor.execute(s)


class SimTournaments(Table):
    table_name = 'Sim_Tournaments'
    columns = ['id', 'name', 'start_date', 'tour', 'dg_ekey', 'cut_line', 'cut_round', 'purse']
    dtypes = ['INTEGER', 'TEXT', 'INTEGER', 'TEXT', 'INTEGER', 'INTEGER', 'INTEGER', 'TEXT']
    index_name = 'id'


class RoundHistory(Table):
    table_name = 'Round_History'
    columns = ['id', 'dg_id', 'sg_total', 'sg_putt', 'sg_arg', 'sg_app', 'sg_ott', 'score', 'round_num', 'fin_numeric',
               'fin_text', 'tour', 'course_id', 'date', 'sim_tournament_id']
    dtypes = ['INTEGER', 'INTEGER', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'INTEGER', 'INTEGER', 'INTEGER', 'TEXT', 'TEXT',
              'INTEGER', 'INTEGER', 'INTEGER']
    index_name = 'id'
    dg_columns = ['dg_id', 'total', 'putt', 'arg', 'app', 'ott', 'round_score', 'round_num', 'fin_numeric',
                  'fin_text', 'tour', 'course_name', 'date', 'key']
    foreign_keys = {
        'dg_id': 'Players(dg_id)',
        'course_id': 'Courses(id)',
        'sim_tournament_id': 'Sim_Tournaments(id)'
    }


class Courses(Table):
    table_name = 'Courses'
    columns = ['id', 'name']
    dtypes = ['INTEGER', 'TEXT']
    index_name = 'id'


class Players(Table):
    table_name = 'Players'
    columns = ['dg_id', 'player_name', 'amateur', 'country', 'country_code']
    dtypes = ['INTEGER', 'TEXT', 'INTEGER', 'TEXT', 'TEXT']
    auto_incr_index = False
    index_name = 'dg_id'


class CurrentDGPred(Table):
    table_name = 'Current_DG_Pred'
    columns = ['dg_id', 'age', 'age_adjustment', 'am', 'baseline_pred', 'cf_approach_comp', 'cf_short_comp', 'country',
               'country_adjustment', 'course_experience_adjustment', 'course_history_adjustment',
               'driving_accuracy_adjustment', 'driving_distance_adjustment', 'final_pred', 'other_fit_adjustment',
               'player_name', 'sample_size', 'std_deviation', 'strokes_gained_category_adjustment', 'timing_adjustment',
               'total_course_history_adjustment', 'total_fit_adjustment', 'true_sg_adjustments']
    dtypes = ['INTEGER', 'INTEGER', 'FLOAT', 'INTEGER', 'FLOAT', 'FLOAT', 'FLOAT', 'TEXT', 'FLOAT', 'FLOAT', 'FLOAT',
              'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'TEXT', 'INTEGER', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT',
              'FLOAT']
    foreign_keys = {
        'dg_id': 'Players(dg_id)'
    }
    auto_incr_index = False
    index_name = 'dg_id'


class TournamentPlayerPredictions(Table):
    table_name = 'Tournament_Player_Predictions'
    columns = ['id', 'sim_tournament_id', 'dg_id', 'x_earnings', 'sim_win', 'sim_top5', 'sim_top10', 'sim_top20',
               'sim_made_cut', 'x_finish', 'sg_index', 'sg_sd', 'sim_date']
    dtypes = ['INTEGER', 'INTEGER', 'INTEGER', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT', 'FLOAT',
              'INTEGER']
    foreign_keys = {
        'dg_id': 'Players(dg_id)',
        'sim_tournament_id': 'SimTournaments(id)'
    }
    index_name = 'id'


class DB_Interface:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.simTournaments = SimTournaments()
        self.roundHistory = RoundHistory()
        self.courses = Courses()
        self.players = Players()
        self.currentDGPred = CurrentDGPred()
        self.tournamentPlayerPredictions = TournamentPlayerPredictions()

    def initialize_tables(self):
        self.players.create_table(self.conn)
        self.simTournaments.create_table(self.conn)
        self.tournamentPlayerPredictions.create_table(self.conn)
        self.courses.create_table(self.conn)
        self.roundHistory.create_table(self.conn)
        self.currentDGPred.create_table(self.conn)

    # TODO:cleanup
    def get_player_rounds(self, dg_ids, columns=None):
        if columns is None:
            columns = ['*']
        s = f'''SELECT {list_to_query_string(columns)} FROM {RoundHistory.table_name} 
                WHERE dg_id in ({list_to_query_string(dg_ids)})'''

        return pd.read_sql_query(s, self.conn)

    def get_player_names(self):
        return self.players.get_all(self.conn)

    def get_courses(self):
        return self.courses.get_all(self.conn)

    # TODO:cleanup
    def get_course_id(self, course_name):
        return int(pd.read_sql_query(f'SELECT id FROM {Courses.table_name} WHERE name = \"{course_name}\"',
                                     self.conn).values[0])

    def get_dg_pred(self):
        return self.currentDGPred.get_all(self.conn)

    def get_sim_tournaments(self):
        return self.simTournaments.get_all(self.conn)

    def get_max_sim_tournament_id(self):
        return self.simTournaments.get_max_index(self.conn)

    # TODO:cleanup
    def get_sim_tournament_id(self, df):
        year = int(str(df['date'])[:4])
        key = str(df['sim_tournament_id'])
        if len(key) == 0:
            return
        res = pd.read_sql_query(f'''SELECT id FROM {SimTournaments.table_name} 
        WHERE dg_ekey = {key} AND start_date > {str(year * 10000)} AND start_date < {str((year + 1) * 10000)}''',
                                self.conn)
        if len(res) > 0:
            return int(res.values[0])

    def get_tournament_player_pred(self, id, date=None):
        if date is None:
            return pd.read_sql_query(f'''SELECT * FROM {self.tournamentPlayerPredictions.table_name}
                                        WHERE sim_tournament_id = {id};''', self.conn)
        else:
            return pd.read_sql_query(f'''SELECT * FROM {self.tournamentPlayerPredictions.table_name}
                                        WHERE sim_tournament_id = {id} AND sim_date = {date};''', self.conn)

    def add_sim_tournament(self, df):
        self.simTournaments.append_df(df, self.conn)

    def add_player_rounds(self, df):
        self.roundHistory.append_df(df, self.conn)

    def add_courses(self, df):
        self.courses.append_df(df, self.conn)

    def update_courses(self, df):
        df = df[~df['name'].isin(self.get_courses()['name'])]
        self.add_courses(df)

    def update_player_predictions(self, df):
        self.tournamentPlayerPredictions.append_df(df, self.conn)

    def update_sim_tournaments(self, df):
        df = df[~df['start_date'].isin(self.get_sim_tournaments()['start_date'])]
        self.simTournaments.append_df(df, self.conn)

    def update_dg_pred(self, api, tour=None):
        df = pd.DataFrame(api.get_player_skill_decomp(tour)['players'])
        
        # TODO: Keep? DG json data can contain new columns e.g. major_adjustment
        col = [i for i in df.columns if i not in CurrentDGPred.columns]
        df = df.drop(columns=col)

        self.currentDGPred.replace_df(df, self.conn)

    def update_player_names(self, api):
        df = pd.DataFrame(api.get_player_names())
        df = df[~df['dg_id'].isin(self.get_player_names()['dg_id'])]
        self.players.append_df(df, self.conn)

    def update_player_rounds(self, api, dg_id):
        player_profile = api.get_player_profile(dg_id)
        if player_profile['dg_id'] != dg_id:
            return 0
        df = pd.DataFrame(player_profile['data'])
        col = [i for i in df.columns if i not in RoundHistory.dg_columns]
        df = df.drop(columns=col)
        df['date'] = [utils.text_date_to_int(d) for d in df['date']]
        df = df[~df['date'].isin(self.get_player_rounds([dg_id], ['date']).astype('int64')['date'])]
        if df.empty:
            return 0
        # TODO: get rid of colums[1:] - id column
        df = df.rename(columns=dict(zip(RoundHistory.dg_columns, RoundHistory.columns[1:])))
        df_courses = self.courses.get_df()
        df_courses['name'] = df['course_id']
        self.update_courses(df_courses)
        df['course_id'] = [self.get_course_id(i) for i in df['course_id']]
        df['sim_tournament_id'] = [utils.getSubstringFromIdentifiers(i, 'pga_e_', ';') for i in df['sim_tournament_id']]
        df['sim_tournament_id'] = [self.get_sim_tournament_id(df.loc[i]) for i in df.index.values]
        self.roundHistory.append_df(df, self.conn)
        return len(df)
