from __future__ import absolute_import
from __future__ import print_function

import os
from shutil import copyfile
import numpy as np

from testing_simulation_4lanes_all_car import Simulation
from generator import TrafficGenerator
from model import TestModel
from visualization import Visualization
from utils import import_test_configuration, set_sumo, set_test_path
from testing_simulation_4lanes_fixed_light import Simulation as Simulation22


if __name__ == "__main__":

    config = import_test_configuration(config_file='testing_settings.ini')
    sumo_cmd = set_sumo(config['gui'], config['sumocfg_file_name'], config['max_steps'])
    model_path, plot_path, model_path2, plot_path2 = set_test_path(config['models_path_name'], config['model_to_test'])

    Model1 = TestModel(
        input_dim=config['num_states'],
        model_path=model_path
    )

    Model2 = TestModel(
        input_dim=80,
        model_path=model_path2
    )

    TrafficGen = TrafficGenerator(
        config['max_steps'], 
        config['n_cars_generated']
    )

    Visualization1 = Visualization(
        plot_path, 
        dpi=96
    )

    Visualization2 = Visualization(
        plot_path2, 
        dpi=96
    )
        
    Simulation1 = Simulation(
        Model1,
        TrafficGen,
        sumo_cmd,
        config['max_steps'],
        config['green_duration'],
        config['yellow_duration'],
        config['num_states'],
        config['num_actions']
    )

    Simulation2 = Simulation22(
        Model2,
        TrafficGen,
        sumo_cmd,
        config['max_steps'],
        config['green_duration'],
        config['yellow_duration'],
        80,
        config['num_actions']
    )

    f = open("testing_record.txt", "a")
    mo = config['model_to_test']
    f.write("Model%d:\n" %mo)

    for i in range(1):
        seed = 1000#np.random.randint(1,100000)
        f.write("testing seed %d" % seed)
        print('\n----- Test episode1 with model')
        simulation_time, total_waiting_time = Simulation1.run(seed)  # run the simulation
        print('Simulation time:', simulation_time, 's')

        print("----- Testing info saved at:", plot_path)

        copyfile(src='testing_settings.ini', dst=os.path.join(plot_path, 'testing_settings.ini'))

        Visualization1.save_data_and_plot(data=Simulation1._last_waiting, filename='waiting_time_for_car', xlabel='car', ylabel='seconds')
        Visualization1.save_data_and_plot(data=Simulation1.queue_length_episode, filename='accumulated_waiting_time_for_queue', xlabel='Step', ylabel='seconds')
        print("Model%d:" %mo)
        print("\nTotal waiting time for model", sum(Simulation1._last_waiting))
        print("\nAverage waiting time per car:", sum(Simulation1._last_waiting)/config['n_cars_generated'])
        print(total_waiting_time/config['n_cars_generated'])
        f.write("\nTotal waiting time for model " + str(sum(Simulation1._last_waiting)))
        f.write("\nAverage waiting time per car: " + str(sum(Simulation1._last_waiting)/config['n_cars_generated']))

        print('\n----- Test episode2 with fixed length traffic light')
        simulation_time, total_waiting_time = Simulation2.run(seed)  # run the simulation
        print('Simulation time:', simulation_time, 's')

        print("----- Testing info saved at:", plot_path2)

        copyfile(src='testing_settings.ini', dst=os.path.join(plot_path2, 'testing_settings.ini'))

        Visualization2.save_data_and_plot(data=Simulation2._last_waiting, filename='waiting_time_for_car', xlabel='car', ylabel='seconds')
        Visualization2.save_data_and_plot(data=Simulation2.queue_length_episode, filename='accumulated_waiting_time_for_queue', xlabel='Step', ylabel='seconds')
        print("\nTotal waiting time for fixed length traffic light", sum(Simulation2._last_waiting))
        print("\nAverage waiting time per car:", sum(Simulation2._last_waiting)/config['n_cars_generated'])
        print(total_waiting_time/config['n_cars_generated'])
        f.write("\nTotal waiting time for fixed length traffic light " + str(sum(Simulation2._last_waiting)))
        f.write("\nAverage waiting time per car: " + str(sum(Simulation2._last_waiting)/config['n_cars_generated']) + "\n\n")

        #Visualization1.save_data_and_plot2(data=Simulation1._last_waiting, data2=Simulation2._last_waiting, filename='waiting_time_for_car', xlabel='car', ylabel='seconds')
        #Visualization1.save_data_and_plot2(data=Simulation1.queue_length_episode, data2=Simulation2.queue_length_episode, filename='accumulated_waiting_time_for_queue', xlabel='Step', ylabel='seconds')
