import config
from golfsim import db_tools
import os


db = db_tools.DB_Interface(os.path.join('local', 'golfmodel2.db'))
db.tournamentPlayerPredictions.drop_table(db.conn)
db.tournamentPlayerPredictions.create_table(db.conn)
# db.initialize_tables()
