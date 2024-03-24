# Intersection-Traffic-Light-Control-System-Using-Deep-Q-Learning

Aim to automaticly decide traffic signal using computer vision and Deep Q-learning with camera footage at the intersection.


Run the file training_main.py to start training.
Run simulation.py to start simulating.

## Deep Q-learning
Deep Q-learning related code is in "TLCS" folder. 

We use SUMO simulator to simulate traffic situation and use it as input to train our model.
Once we fetched the data from SUMO, we derive current state of the envirnment based on waiting queue and traffic flow.

### State
To get the current state of the envirnment and since we were limited by the camera angle, we assume that the maximum depth that the camera can see is 35 meters (or max. 5 cars) from the Stop bar at the intersection.
We use waiting queue at the lanes of red light and traffic flow of the lanes with green light to derive state.

### Environment
There are 5 kinds of intersections.
- Environment1: 4-way intersection with 4 incoming lanes and 4 outgoing lanes per arm. Left-most lane dedicated to left-turn only. Right-most lane dedicated to right-turn and straight. Left-most lane will only move when the Left-turn signal is green.
- Environment2: 3-way intersection with 3 incoming lanes and 3 outgoing lanes per arm. Left-most lane dedicated to left-turn only. Right-most lane dedicated to right-turn and straight
- Environment3: 3-way intersection with 3 incoming lanes and 3 outgoing lanes per arm. Left-most lane dedicated to left-turn and straight. Right-most lane dedicated to right-turn and straight
- Environment4: 4-way intersection with 4 incoming lanes and 4 outgoing lanes per arm. Left-most lane dedicated to left-turn only. Right-most lane dedicated to right-turn and straight
- Environment5: 4-way intersection with 4 incoming lanes and 4 outgoing lanes per arm. Left-most lane dedicated to left-turn and straight. Right-most lane dedicated to right-turn and straight

### Action
There are 4 actions the agent can choose from
- North-South Straight: green for lanes in the north and south arm dedicated to turning right or going straight.
- North-South Left Turn: green for lanes in the north and south arm dedicated to turning left.
- East-West Straight: green for lanes in the east and west arm dedicated to turning right or going straight.
- East-West Left Turn: green for lanes in the east and west arm dedicated to turning left.
If the action agent selected is different from the original action, there will be a yellow light for 4 seconds insert between two green lights.

### Reward
Change in *cumulative waiting time* for all the cars in incoming lanes between actions.
The *cunulative waiting time* for each car isn't linear.
Suppose that a car spent t seconds with speed=0 since the spawn, its *cumulative waiting time* will be int(log(t+1)*10)

### Learning Machanism
We implemented Deep Q-learning to train the model. 
We make use of the Q-learning equation Q(s,a) = Q(s,a) + gamma * (reward + gamma • max Q'(s',a') - Q(s,a)) to update the action values and a deep neural network to learn the state-action function.
The neural network is fully connected with 12 neurons as input (the state), 4 hidden layers of 400 neurons each, and the output layers with 4 neurons representing the 4 possible actions.
For training, experience replay is implemented, the experiences are stored at memory.
For each episode, their will be 100 epochs, for each epoch, a small batch of 400 experiences will be fed to train the neural network.
