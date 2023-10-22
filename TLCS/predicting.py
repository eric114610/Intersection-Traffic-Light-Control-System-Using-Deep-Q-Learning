from __future__ import absolute_import
from __future__ import print_function

import os
from shutil import copyfile
import time

from predicting_simulation import Simulation
from generator import TrafficGenerator
from model import PredictModel
from visualization import Visualization
from utils import import_predict_configuration, set_sumo, set_predict_path

from firebase_get import firebase_Get

class CarDistribute:
    def __init__(self, l):
        self._car = l[0]
        self._bus = l[1]
        self._truck = l[2]
        self._total = l[0] + l[1] + l[2]

class CarQueue:
    def __init__(self, car_q):
        self.N_Straight = self._buildDirection(car_q[0:3])
        self.S_Straight = self._buildDirection(car_q[6:9])
        self.W_Straight = self._buildDirection(car_q[12:15])
        self.E_Straight = self._buildDirection(car_q[18:21])
        self.N_Turn = self._buildDirection(car_q[3:6])
        self.S_Turn = self._buildDirection(car_q[9:12])
        self.W_Turn = self._buildDirection(car_q[15:18])
        self.E_Turn = self._buildDirection(car_q[21:])

    def _buildDirection(self, l):
        return CarDistribute(l)



if __name__ == "__main__":

    config = import_predict_configuration(config_file='predicting_settings.ini')
    #sumo_cmd = set_sumo(config['gui'], config['sumocfg_file_name'], config['max_steps'])
    #print(config['model_to_load'])

    model_path, plot_path = set_predict_path(config['models_path_name'], config['model_to_load'], 'predicts')
    #print(model_path, plot_path)

    Models = []

    for i,v in enumerate(model_path):
        Model = PredictModel(
            input_dim=config['num_states'],
            model_path=model_path[i]
        )
        Models.append(Model)

    TrafficGen = TrafficGenerator(
        config['max_steps'], 
        config['n_cars_generated']
    )

    Visualization = Visualization(
        plot_path, 
        dpi=96
    )

    Simulations = []

    for i,v in enumerate(Models):
        
        TmpSimulation = Simulation(
            v,
            config['max_steps'],
            config['green_duration'],
            config['yellow_duration'],
            config['num_states'],
            config['num_actions'],
            3
        )
        Simulations.append(TmpSimulation)

    firebase_db = firebase_Get()

    predict = True
    first = True
    while predict:
        start_time = time.perf_counter()

        car_queue = firebase_db.get()
        #print(car_queue)
        if car_queue == "Stop":
            predict = False
            continue
        #car_q = list(int(i) for i in car_queue.split(","))
        #car_q = list(int(i) for i in car_queue.split(","))
        if type(car_queue) != list:
            print("End")
            predict = False
            continue
        #print(car_q)
        car_queue = CarQueue(car_queue)
        Simulations[1].run(car_queue)
        print("1 step")
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        #print(elapsed_time)
        if not first:
            time.sleep(max(1-elapsed_time, 0))
        
        first = False
