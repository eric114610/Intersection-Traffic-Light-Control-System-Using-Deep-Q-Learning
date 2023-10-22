import traci
import numpy as np
import random
import timeit
import os

# phase codes based on environment.net.xml
PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7


class Simulation:
    def __init__(self, Model, TrafficGen, sumo_cmd, max_steps, green_duration, yellow_duration, num_states, num_actions):
        self._Model = Model
        self._TrafficGen = TrafficGen
        self._step = 0
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._num_states = num_states
        self._num_actions = num_actions
        self._reward_episode = []
        self._queue_length_episode = []
        self._last_waiting = []


    def run(self, episode):
        """
        Runs the testing simulation
        """
        start_time = timeit.default_timer()

        # first, generate the route file for this simulation and set up sumo
        self._TrafficGen.generate_routefile(seed=episode)
        traci.start(self._sumo_cmd)
        print("Simulating...")

        # inits
        self._step = 0
        self._waiting_times = {}
        old_total_wait = 0
        old_action = -1 # dummy init
        self._last_waiting = []
        self._queue_length_episode = []

        old_flow=0
        current_flow=0

        while self._step < self._max_steps:

            # get current state of the intersection
            current_state, current_flow = self._get_state(old_action)

            # calculate reward of previous action: (change in cumulative waiting time between actions)
            # waiting time = seconds waited by a car since the spawn in the environment, cumulated for every car in incoming lanes
            current_total_wait = self._collect_waiting_times()
            reward = old_total_wait - current_total_wait

            # choose the light phase to activate, based on the current state of the intersection
            action = self._choose_action(current_state, current_flow, old_flow, old_action)

            # if the chosen phase is different from the last phase, activate the yellow phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duration)

            # execute the phase selected before
            self._set_green_phase(action)
            self._simulate(self._green_duration)

            # saving variables for later & accumulate reward
            old_action = action
            old_total_wait = current_total_wait
            old_flow = current_flow

            self._reward_episode.append(reward)

        car_list = traci.vehicle.getIDList()
        total_waiting_time=0
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            total_waiting_time += wait_time
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)


        return simulation_time, total_waiting_time


    def _simulate(self, steps_todo):
        """
        Proceed with the simulation in sumo
        """
        if (self._step + steps_todo) >= self._max_steps:  # do not do more steps than the maximum allowed number of steps
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1 # update the step counter
            steps_todo -= 1
            #queue_length = self._get_queue_length() 
            queue_length = self._collect_waiting_times() 
            self._queue_length_episode.append(queue_length)


    def _collect_waiting_times(self):
        """
        Retrieve the waiting time of every car in the incoming roads
        """
        incoming_roads = ["E2TL", "N2TL", "W2TL", "S2TL"]
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)  # get the road id where the car is located
            if road_id in incoming_roads:  # consider only the waiting times of cars in incoming roads
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times: # a car that was tracked has cleared the intersection
                    del self._waiting_times[car_id] 
                    self._last_waiting.append(wait_time)
        total_waiting_time = sum(self._waiting_times.values())
        return total_waiting_time


    def _choose_action(self, state, current_flow, old_flow, old_action):
        """
        Pick the best action known based on the current state of the env
        """

        NS_turn_queue= traci.lane.getLastStepHaltingNumber("N2TL_2") + traci.lane.getLastStepHaltingNumber("S2TL_2")
        WE_turn_queue= traci.lane.getLastStepHaltingNumber("W2TL_2") + traci.lane.getLastStepHaltingNumber("E2TL_2")
        NS_straight_queue= traci.edge.getLastStepHaltingNumber("N2TL") + traci.edge.getLastStepHaltingNumber("S2TL") - NS_turn_queue
        WE_straight_queue= traci.edge.getLastStepHaltingNumber("E2TL") + traci.edge.getLastStepHaltingNumber("W2TL") - WE_turn_queue

        if current_flow < 3 and old_flow < 3:
            if old_action == 1 or old_action == 3:
                if current_flow < 1 and old_flow < 1 and self._get_queue_length() < 5 and self._get_queue_length() > 0:
                    if old_action == 1:
                        if NS_straight_queue > WE_straight_queue + WE_turn_queue:
                            return 0
                        else:
                            if WE_straight_queue > WE_turn_queue:
                                return 2
                            else:
                                return 3
                    else:
                        if WE_straight_queue > NS_straight_queue + NS_turn_queue:
                            return 2
                        else:
                            if NS_straight_queue > NS_turn_queue:
                                return 0
                            else:
                                return 1
                else:
                    return np.argmax(self._Model.predict_one(state))
            else:
                if self._get_queue_length() < 5 and self._get_queue_length() > 0:
                    if old_action == 0:
                        return 2
                    else:
                        return 0
                else:
                    return np.argmax(self._Model.predict_one(state))
        else:
            return np.argmax(self._Model.predict_one(state))


    def _set_yellow_phase(self, old_action):
        """
        Activate the correct yellow light combination in sumo
        """
        yellow_phase_code = old_action * 2 + 1 # obtain the yellow phase code, based on the old action (ref on environment.net.xml)
        traci.trafficlight.setPhase("TL", yellow_phase_code)


    def _set_green_phase(self, action_number):
        """
        Activate the correct green light combination in sumo
        """


        if action_number == 0:
            traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
        elif action_number == 1:
            traci.trafficlight.setPhase("TL", PHASE_NSL_GREEN)
        elif action_number == 2:
            traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
        elif action_number == 3:
            traci.trafficlight.setPhase("TL", PHASE_EWL_GREEN)


    def _get_queue_length(self):
        """
        Retrieve the number of cars with speed = 0 in every incoming lane
        """
        halt_N = traci.edge.getLastStepHaltingNumber("N2TL")
        halt_S = traci.edge.getLastStepHaltingNumber("S2TL")
        halt_E = traci.edge.getLastStepHaltingNumber("E2TL")
        halt_W = traci.edge.getLastStepHaltingNumber("W2TL")
        queue_length = halt_N + halt_S + halt_E + halt_W
        return queue_length


    def _get_state(self,old_action):
        """
        Retrieve the state of the intersection from sumo, in the form of cell occupancy
        """
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()
        lane_car = np.zeros(16)

        for car_id in car_list:
            lane_pos = traci.vehicle.getLanePosition(car_id)
            lane_id = traci.vehicle.getLaneID(car_id)
            lane_pos = 750 - lane_pos  # inversion of lane pos, so if the car is close to the traffic light -> lane_pos = 0 --- 750 = max len of a road

            
            if lane_pos < 0:
                lane_cell = 9
            elif lane_pos < 7:
                lane_cell = 0
            elif lane_pos < 14:
                lane_cell = 1
            elif lane_pos < 21:
                lane_cell = 2
            elif lane_pos < 28:
                lane_cell = 3
            elif lane_pos < 35:
                lane_cell = 4
            elif lane_pos < 45:
                lane_cell = 5
            elif lane_pos < 55:
                lane_cell = 6
            elif lane_pos < 65:
                lane_cell = 7
            elif lane_pos < 80:
                lane_cell = 8
            elif lane_pos <= 750:
                lane_cell = 9


            if lane_cell <= 4:
                if lane_id == "W2TL_0":
                    if lane_car[0] < 10:
                        lane_car[0] += 1
                elif lane_id == "W2TL_1":
                    if lane_car[0] < 10:
                        lane_car[0] += 1
                elif lane_id == "W2TL_2":
                    if lane_car[1] < 5:
                        lane_car[1] += 1
                elif lane_id == "N2TL_0":
                    if lane_car[2] < 10:
                        lane_car[2] += 1
                elif lane_id == "N2TL_1":
                    if lane_car[2] < 10:
                        lane_car[2] += 1
                elif lane_id == "N2TL_2":
                    if lane_car[3] < 5:
                        lane_car[3] += 1
                elif lane_id == "E2TL_0":
                    if lane_car[4] < 10:
                        lane_car[4] += 1
                elif lane_id == "E2TL_1":
                    if lane_car[4] < 10:
                        lane_car[4] += 1
                elif lane_id == "E2TL_2":
                    if lane_car[5] < 5:
                        lane_car[5] += 1
                elif lane_id == "S2TL_0":
                    if lane_car[6] < 10:
                        lane_car[6] += 1
                elif lane_id == "S2TL_1":
                    if lane_car[6] < 10:
                        lane_car[6] += 1
                elif lane_id == "S2TL_2":
                    if lane_car[7] < 5:
                        lane_car[7] += 1
        
        flow_count=0
        total_flow=0
        if old_action==0:
            flow_count = lane_car[2] + lane_car[6]
            lane_car[2]=0; lane_car[6] = 0
            state[8] = flow_count
            total_flow += flow_count
        if old_action==1:
            flow_count = lane_car[3] + lane_car[7]
            lane_car[3]=0; lane_car[7]=0
            state[9] = flow_count
            total_flow += flow_count
        if old_action==2:
            flow_count = lane_car[0] + lane_car[4]
            lane_car[0]=0; lane_car[4]=0
            state[10] = flow_count
            total_flow += flow_count
        if old_action==3:
            flow_count = lane_car[1] + lane_car[5]
            lane_car[1]=0; lane_car[5]=0
            state[11] = flow_count
            total_flow += flow_count

        for i in range(8):
            total_s = 0
            for j in range(int(lane_car[i])):
                total_s += -(j+1)*(j+1)*(j+1)*0.02 + 20
            state[i] = total_s

        return state, total_flow


    @property
    def queue_length_episode(self):
        return self._queue_length_episode


    @property
    def reward_episode(self):
        return self._reward_episode



