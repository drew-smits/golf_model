use pyo3::prelude::*;
use pyo3::types::PyDict;
use rand::prelude::*;
use rand_distr::{Distribution, Normal};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::thread;

#[pyclass]
struct Sim {
    players: HashMap<u32, Player>,
    data: HashMap<u32, Vec<f32>>,
    purse: HashMap<u32, u32>,
    num_sims: usize,
    num_rounds: usize,
    cut_round: usize,
    cut_line: usize,
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct Player {
    #[pyo3(get)]
    pub index: f32,
    #[pyo3(get)]
    pub std_dev: f32,
    #[pyo3(get)]
    pub avg_finish: f32,
    #[pyo3(get)]
    pub avg_earnings: f32,
    #[pyo3(get)]
    pub win: f32,
    #[pyo3(get)]
    pub top5: f32,
    #[pyo3(get)]
    pub top10: f32,
    #[pyo3(get)]
    pub top20: f32,
    #[pyo3(get)]
    pub made_cut: f32,
}

impl Player {
    fn update_stats(&mut self, finish_pos: f32, cut_line: f32, earnings: f32) {
        self.avg_finish += finish_pos;
        if finish_pos <= cut_line + 1.0 {
            self.avg_earnings += earnings;
            self.made_cut += 1.0;
            if finish_pos < 21.0 {
                self.top20 += 1.0;
                if finish_pos < 11.0 {
                    self.top10 += 1.0;
                    if finish_pos < 6.0 {
                        self.top5 += 1.0;
                        if finish_pos < 2.0 {
                            self.win += 1.0;
                        }
                    }
                }
            }
        }
    }
}

impl Sim {
    fn simulate_player_rounds(&self, player: &Player, size: usize, rng: &mut ThreadRng) -> Vec<f32> {
        let normal = Normal::new(player.index, player.std_dev).unwrap();
        (0..size).map(|_| normal.sample(rng)).collect()
    }

    fn simulate_tournament(&self, tournament_data: &[(u32, Vec<f32>)]) -> Vec<(u32, Vec<f32>)> {
        let mut tournament: Vec<(u32, Vec<f32>)> = tournament_data.to_vec();
    
        if self.cut_round > 0 {
            let mut cut: Vec<(u32, Vec<f32>)> = tournament_data
                .iter()
                .map(|&(id, ref scores)| (id, scores[..self.cut_round].to_vec()))
                .collect();
    
            cut.sort_by(|a, b| b.1.iter().sum::<f32>().partial_cmp(&a.1.iter().sum::<f32>()).unwrap());
    
            tournament.sort_by(|a, b| {
                let a_pos = cut.iter().position(|&(id, _)| id == a.0).unwrap();
                let b_pos = cut.iter().position(|&(id, _)| id == b.0).unwrap();
                a_pos.cmp(&b_pos)
            });
    
            let split_point = self.cut_line.min(tournament.len());
            let (made_cut, missed_cut) = tournament.split_at_mut(split_point);
            let mut made_cut_vec = made_cut.to_vec();
            made_cut_vec.sort_by(|a, b| b.1.iter().sum::<f32>().partial_cmp(&a.1.iter().sum::<f32>()).unwrap());
    
            tournament = [made_cut_vec, missed_cut.to_vec()].concat();
        } else {
            tournament.sort_by(|a, b| b.1.iter().sum::<f32>().partial_cmp(&a.1.iter().sum::<f32>()).unwrap());
        }
    
        tournament
    }

    fn update_player_stats(&self, tournament: &[(u32, Vec<f32>)], players: &mut HashMap<u32, Player>, purse: &HashMap<u32, u32>) {
        for (pos, &(id, _)) in tournament.iter().enumerate() {
            if let Some(player) = players.get_mut(&id) {
                let fin = pos as f32 + 1.0;
                let mut e: f32 = 0.0;
                if let Some(earnings) = purse.get(&(fin as u32)) {
                    e = *earnings as f32;
                }
                player.update_stats(fin, self.cut_line as f32, e);
            }
        }
    }

    fn update_player_stats_from_thread(&mut self, t_players: &Vec<HashMap<u32, Player>> ) {
        for t in t_players {
            for (id, player) in t {
                if let Some(p) = self.players.get_mut(&id) {
                    p.avg_finish += player.avg_finish;
                    p.made_cut += player.made_cut;
                    p.avg_earnings += player.avg_earnings;
                    p.top20 += player.top20;
                    p.top10 += player.top10;
                    p.top5 += player.top5;
                    p.win += player.win;
                }
            }
        }
    }

    fn normalize_results(&mut self) {
        let num_sims = self.num_sims as f32;
        for player in self.players.values_mut() {
            player.avg_finish /= num_sims;
            player.made_cut /= num_sims;
            player.avg_earnings /= num_sims;
            player.top20 /= num_sims;
            player.top10 /= num_sims;
            player.top5 /= num_sims;
            player.win /= num_sims;
        }
    }
}

#[pymethods]
impl Sim {
    #[new]
    fn new(num_sims: usize, num_rounds: usize, cut_round: usize, cut_line: usize) -> Self {
        Sim {
            players: HashMap::new(),
            data: HashMap::new(),
            purse: HashMap::new(),
            num_sims,
            num_rounds,
            cut_round,
            cut_line,
        }
    }

    fn add_player(&mut self, id: u32, sg_index: f32, std_dev: f32) {
        let player = Player {
            index: sg_index,
            std_dev,
            avg_finish: 0.0,
            avg_earnings: 0.0,
            win: 0.0,
            top5: 0.0,
            top10: 0.0,
            top20: 0.0,
            made_cut: 0.0
        };
        self.players.insert(id, player);
    }

    fn sim_rounds(&mut self) {
        let num_threads = thread::available_parallelism().unwrap().get();
        let size = self.num_sims * self.num_rounds;
        let players = Arc::new(self.players.clone());
        let data = Arc::new(Mutex::new(HashMap::new()));

        thread::scope(|s| {
            for t in 0..num_threads {
                let players = Arc::clone(&players);
                let data = Arc::clone(&data);
                let num_rounds = self.num_rounds;
                s.spawn(move || {
                    let mut rng = thread_rng();
                    for (id, player) in players.iter() {
                        if *id as usize % num_threads == t {
                            let random_data = Self::simulate_player_rounds(&Self::new(0, num_rounds, 0, 0), player, size, &mut rng);
                            data.lock().unwrap().insert(*id, random_data);
                        }
                    }
                });
            }
        });

        self.data = Arc::try_unwrap(data).unwrap().into_inner().unwrap();
    }

    fn sim_tournaments(&mut self) {
        let num_threads = thread::available_parallelism().unwrap().get();
        let original_players = Arc::new(self.players.clone());
        let data_chunks: Vec<Vec<(u32, Vec<f32>)>> = {
            let mut data_vec: Vec<(u32, Vec<f32>)> = self.data.clone().into_iter().collect();
            let total_sims = self.num_sims * self.num_rounds;
            let chunk_size = (total_sims + num_threads - 1) / num_threads;
            let mut chunks = Vec::new();
        
            for _ in 0..num_threads {
                let mut chunk = Vec::new();
                for (id, scores) in data_vec.iter_mut() {
                    let chunk_scores = scores.split_off(scores.len() - chunk_size);
                    chunk.push((*id, chunk_scores));
                }
                chunks.push(chunk);
            }
        
            chunks
        };
    
        let purse = self.purse.clone();
        let num_rounds = self.num_rounds;
        let num_thread_sims = self.num_sims * self.num_rounds / num_threads;
        let cut_round = self.cut_round;
        let cut_line = self.cut_line;

        let thread_players: Arc<Mutex<Vec<HashMap<u32, Player>>>> = Arc::new(Mutex::new(vec![HashMap::new(); num_threads]));
    
        thread::scope(|s| {
            for (t, data_chunk) in data_chunks.into_iter().enumerate() {
                let original_players = Arc::clone(&original_players);
                let purse = purse.clone();
                let mut players = original_players.iter().map(|(id, p)| (*id, p.clone())).collect();
                let thread_players = Arc::clone(&thread_players);
                let sim = Self::new(0, num_rounds, cut_round, cut_line);
                s.spawn(move || {
                    for i in (0..num_thread_sims).step_by(num_rounds) {
                        let tournament_data: Vec<(u32, Vec<f32>)> = data_chunk
                            .iter()
                            .map(|&(id, ref scores)| (id, scores[i..i + num_rounds].to_vec()))
                            .collect();
                        let tournament = sim.simulate_tournament(&tournament_data);
                        sim.update_player_stats(&tournament, &mut players, &purse);
                    }
                    thread_players.lock().unwrap()[t] = players;
                });
            }
        });
        self.update_player_stats_from_thread(&Arc::try_unwrap(thread_players).unwrap().into_inner().unwrap())
    }

    fn calculate_results(&mut self) {
        self.normalize_results();
    }

    fn run(&mut self) {
        self.sim_rounds();
        self.sim_tournaments();
        self.calculate_results();
    }

    fn get_players(&self) -> HashMap<u32, Player> {
        self.players.clone()
    }

    fn set_num_rounds(&mut self, num_rounds: usize) {
        self.num_rounds = num_rounds;
    }

    fn set_num_sims(&mut self, num_sims: usize) {
        self.num_sims = num_sims;
    }

    fn set_cut_round(&mut self, cut_round: usize) {
        self.cut_round = cut_round;
    }

    fn set_cut_line(&mut self, cut_line: usize) {
        self.cut_line = cut_line;
    }

    fn set_purse(&mut self, purse_dict: &PyDict) {
        for (pos, pay) in purse_dict.iter() {
            let pos = pos.extract().unwrap();
            let pay = pay.extract().unwrap();
            self.purse.insert(pos, pay);
        }
    }
}

#[pymodule]
fn golfsim(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Sim>()?;
    Ok(())
}