from datetime import date
import requests
import utils
import json
from local import keys


class API:
    feed_url = 'https://feeds.datagolf.com/'
    success_status_code = 200
    api_key = keys.dg_api_key
    default_params = {
        'tour': 'pga',
        'file_format': 'json',
        'key': api_key
    }

    def _get(self, endpoint, params=None, base_url=feed_url):
        if params is None:
            params = self.default_params
        url = base_url + endpoint
        res = requests.get(url=url, params=params)
        if res.status_code != self.success_status_code:
            raise utils.ResponseErrorHTTP(f'Invalid HTTP Status Code from {url}: {res.status_code}')
        return res.text

    def get_schedule(self, tour=None):
        endpoint = 'get-schedule'
        params = self.default_params
        if tour is not None:
            params['tour'] = tour
        return json.loads(self._get(endpoint, params))

    def get_next_event(self, tour=None, start_date=None):
        sched = self.get_schedule(tour)
        if start_date is None:
            start_date = date.today()
        for t in sched['schedule']:
            t_date = t['start_date'].split('-')
            if (date(int(t_date[0]), int(t_date[1]), int(t_date[2])) - start_date).days > 0:
                return t

    def get_event_key(self, event_name, tour=None):
        data = self.get_schedule(tour)
        for i in data['schedule']:
            if i['event_name'] == event_name:
                return i['event_id']

    def get_player_skill_decomp(self, tour=None):
        endpoint = 'preds/player-decompositions'
        params = self.default_params
        if tour is not None:
            params['tour'] = tour
        return json.loads(self._get(endpoint, params))

    def get_player_names(self):
        endpoint = 'get-player-list'
        return json.loads(self._get(endpoint))

    def get_player_profile(self, dg_id):
        json_start = 'reload_data = JSON.parse(\''
        json_end = '\');\n'
        url = 'https://datagolf.com/player-profiles'
        params = {
            'dg_id': dg_id
        }
        text = self._get('', params, url)
        data = utils.getSubstringFromIdentifiers(text, json_start, json_end)
        return json.loads(data)


# class PlayerList(utils.JsonFile):
#     baseURL = 'https://datagolf.com/true-sg-query'
#     jsonStart = 'JSON.parse(\''
#     jsonEnd = '\');\n'
#
#     def getPlayers(self, statTimePeriod):
#         players = {}
#
#         for i in self.data['current_data'][statTimePeriod]['data']:
#             plr = player.Player()
#             plr.name = i['player_name']
#             plr.tsgIndex = i['total']
#             plr.tsgSD = i['total_sd']
#             players[i['dg_id']] = plr
#
#         return players


# class PlayerProfile(utils.JsonFile):
#     baseURL = 'https://datagolf.com/player-profiles?dg_id='
#     jsonStart = 'reload_data = JSON.parse(\''
#     jsonEnd = '\');\n'
#
#     def parseJson(self, data):
#         l = len(config.playerProfileCache_path)
#         if str(data['data'][0]['dg_id']) != self.filename[l+1:-5]:
#             log.info(f'No profile for dg_id: {self.filename[l+1:-5]}')
#             return {}
#         else:
#             return data
#
#     def getTSGArr(self, maxRoundAge, tour=''):
#         tsg = np.zeros((len(self.data['data']), 2))
#         numSamples = 0
#
#         for i in range(len(self.data['data'])):
#             r = self.data['data'][i]
#             if (getRoundAge(r) < maxRoundAge or maxRoundAge < 0) and (tour == '' or tour == self.data['data'][i]['tour']):
#                 numSamples += 1
#                 tsg[i] = r['total'], getRoundAge(r)
#
#         return tsg[tsg.shape[0] - numSamples:]


# class LiveModel(utils.JsonFile):
#     if config.tsg_tour == 'opp':
#         baseURL = 'https://datagolf.com/live-model/pga-tour-opposite'
#     else:
#         baseURL = 'https://datagolf.com/live-model/pga-tour'
#     jsonStart = 'response = JSON.parse(\''
#     jsonEnd = '\'.replace(/'
#
#     def parse(self, text):
#         return json.loads(utils.getSubstringFromIdentifiers(text, self.jsonStart, self.jsonEnd).replace('NaN', "null"))


# allTime = 'All Time'
# last12Months = 'Last 12 Months'
# last2Years = 'Last 2 Years'
# last20Rounds = 'Last 20 Rounds'
# last3Months = 'Last 3 Months'
# last30Days = 'Last 30 Days'
# last50Rounds = 'Last 50 Rounds'
# last6Months = 'Last 6 Months'

# payout = {
#     1: 0.18,
#     2: 0.109,
#     3: 0.069,
#     4: 0.049,
#     5: 0.041,
#     6: 0.03625,
#     7: 0.03375,
#     8: 0.03125,
#     9: 0.02925,
#     10:	0.02725,
#     11:	0.02525,
#     12:	0.02325,
#     13:	0.02125,
#     14:	0.01925,
#     15:	0.01825,
#     16:	0.01725,
#     17:	0.01625,
#     18:	0.01525,
#     19:	0.01425,
#     20:	0.01325,
#     21:	0.01225,
#     22:	0.01125,
#     23:	0.01045,
#     24:	0.00965,
#     25:	0.00885,
#     26:	0.00805,
#     27:	0.00775,
#     28:	0.00745,
#     29:	0.00715,
#     30:	0.00685,
#     31:	0.00655,
#     32:	0.00625,
#     33:	0.00595,
#     34:	0.00570,
#     35:	0.00545,
#     36:	0.00520,
#     37:	0.00495,
#     38:	0.00475,
#     39:	0.00455,
#     40:	0.00435,
#     41:	0.00415,
#     42:	0.00395,
#     43:	0.00375,
#     44:	0.00355,
#     45:	0.00335,
#     46:	0.00315,
#     47:	0.00295,
#     48:	0.00279,
#     49:	0.00265,
#     50:	0.00257,
#     51:	0.00251,
#     52:	0.00245,
#     53:	0.00241,
#     54:	0.00237,
#     55:	0.00235,
#     56:	0.00233,
#     57:	0.00231,
#     58:	0.00229,
#     59:	0.00227,
#     60:	0.00225,
#     61:	0.00223,
#     62:	0.00221,
#     63:	0.00219,
#     64:	0.00217,
#     65:	0.00215,
# }

# months = {
#     'Jan': 1,
#     'Feb': 2,
#     'Mar': 3,
#     'Apr': 4,
#     'May': 5,
#     'Jun': 6,
#     'Jul': 7,
#     'Aug': 8,
#     'Sep': 9,
#     'Oct': 10,
#     'Nov': 11,
#     'Dec': 12
# }


# def getRoundAge(round, compareDate=date.today()):
#     dateString = round['date']
#     roundMonth = months[dateString[:3]]
#     roundDay = int(dateString[4:dateString.index(',')])
#     roundYear = int(dateString[dateString.index(',') + 1:])
#     roundDate = date(roundYear, roundMonth, roundDay)
#     return (compareDate - roundDate).days










# def get_player_list(tsg_tour, tsg_timeframe=last12Months):
#     url = PlayerList.baseURL
#     cookie = {'tsg_tour': tsg_tour}
#     res = requests.get(url=url, cookies=cookie)
#     if res.status_code != 200:
#         raise utils.ResponseErrorHTTP(f'Invalid HTTP Status Code from {url}: {res.status_code}')
#     data = json.loads(utils.getSubstringFromIdentifiers(res.text, PlayerList.jsonStart, PlayerList.jsonEnd))
#     players = {}
#     for i in data['current_data'][tsg_timeframe]['data']:
#         plr = player.Player()
#         plr.name = i['player_name']
#         plr.tsgIndex = i['total']
#         plr.tsgSD = i['total_sd']
#         players[i['dg_id']] = plr
#
#     return players













#
# def getMoneyEarned(pos, purseSize):
#     try:
#         return payout[pos] * purseSize
#     except KeyError:
#         return 0










# def getRemainingStrokes(courseAvgs, round, thru, numRounds):
#     strokes = 0
#     for i in range(thru, len(courseAvgs)):
#         strokes += courseAvgs[i + 1]
#     for i in range(round, numRounds):
#         strokes += sum(courseAvgs)
#
#     return strokes
#
# def getCourseStats(course):
#     courseStats = {'avg': {}, 'par': {}}
#     for i in course:
#         avgs = {'1': i['avg_1'], '2': i['avg_2'], '3': i['avg_3'], '4': i['avg_4']}
#         courseStats['avg'][str(i['hole'])] = avgs
#         courseStats['par'][str(i['hole'])] = i['par']
#
#     return courseStats
#
#
# def getCurrentStrokes(coursePars, round, thru, currentScore):
#     strokes = currentScore
#     for i in range(round - 1):
#         strokes += sum(coursePars)
#     for i in range(thru):
#         strokes += coursePars[i + 1]
#
#     return strokes
#
#
# def getCurrentScores(playerScores, player_num,):
#     scores = {}
#     for i in playerScores[str(player_num)]:
#         try:
#             int(i)
#             scores[i] = (playerScores[str(player_num)][i])
#         except ValueError:
#             pass
#
#     return scores
#
#
# def getCurrentStrokesGained(courseAvgs, scores):
#     sg = 0
#     for i in scores:
#         for j in scores[i]:
#             try:
#                 sg += courseAvgs[j][i] - scores[i][j]
#             except TypeError:
#                 pass
#             except KeyError:
#                 pass
#
#     return sg
