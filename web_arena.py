import holdem
import agent
import logging
import time

SERVER_URI = r"ws://allhands2018-beta.dev.spn.a1q7.net:3001" # beta
#SERVER_URI = r"ws://allhands2018-training.dev.spn.a1q7.net:3001" # training

logger = logging.getLogger('TexasHoldemEnv')
logger.setLevel(logging.INFO)

# name="Enter Your Name Here"
name="bob"
model = agent.sarsaModel()
model.loadModel("sarsa9.npy")



# while True: # Reconnect after Gameover
client_player = holdem.ClientPlayer(SERVER_URI, name, model, debug=True, playing_live=True)
while True:
    client_player.doListen()
    time.sleep(1)