import gym
import holdem
import agent
import time
import logging
import numpy as np
import keyboard
import traceback

logger = logging.getLogger('TexasHoldemEnv')

def episode(env, n_seats, model_list):
    while True:
        cur_state = env.new_cycle()
        env.render(mode='machine')
        cycle_terminal = False
        try:
            logger.info("reseting all reset state")
            for m in model_list:
                m.reset_state()
        except:
            pass
        
        # (cur_state)
        if env.episode_end:
            break

        while not cycle_terminal:
            # play safe actions, check when no one else has raised, call when raised.
            # print(">>> Debug Information ")
            # print("state(t)")
            # for p in cur_state.player_states:
            #     print(p)
            # print(cur_state.community_state)

            actions = holdem.model_list_action(cur_state, n_seats=n_seats, model_list=model_list)
            cur_state, rews, cycle_terminal, info = env.step(actions)

            # print("action(t), (CALL=1, RAISE=2, FOLD=3 , CHECK=0, [action, amount])")
            # print(actions)

            # print("reward(t+1)")
            # print(rews)
            # print("<<< Debug Information ")
            env.render(mode="machine")
        # print("final state")
        # print(cur_state)

        # total_stack = sum([p.stack for p in env._seats])
        # if total_stack != 10000:
        #     return
    try:
        for p in env.winning_players:
            model_list[p.player_id].estimateReward(p.stack)
    except:
        pass
        
    logger.info("Episode End!!!")
    return np.array([p.stack for p in cur_state.player_states])
    
def new_env():
    env = gym.make('TexasHoldem-v2') # holdem.TexasHoldemEnv(2)
    
    for i in range(10):
        env.add_player(i, stack=1000) # add a player to seat 0 with 1000 "chips"
    return env
    
if __name__ == "__main__":
    env = new_env()
    model_list = list()
    model_list.append(agent.idiotModel()) #0
    model_list.append(agent.allFoldModel()) #1
    model_list.append(agent.allFoldModel()) #2
    model_list.append(agent.allFoldModel()) #3
    model_list.append(agent.allFoldModel()) #4
    model_list.append(agent.sarsa2Model()) #5
    model_list.append(agent.allCallModel()) #6
    model_list.append(agent.allFoldModel()) #7
    model_list.append(agent.allRaiseModel()) #8
    model_list.append(agent.sarsaModel()) #9
    
    model_list[5].loadModel("sarsa5.npy")
    model_list[9].loadModel("sarsa9.npy")

    logger.setLevel(logging.INFO)
    stacks = np.zeros(10)
    n_episode = 0
    start_time = time.time()
    
    try:
        while True:
            stacks += episode(env, env.n_seats, model_list)
            n_episode += 1
            if keyboard.is_pressed('q'):
                print("Interrupt by key. n_episode = {}".format(n_episode))
                break
            env.reset()
    except:
        traceback.print_exc()
    
    etime = (time.time()-start_time)
    print("Elapsed time: {}, per episode {}".format(etime, float(etime)/n_episode))
    print(stacks/n_episode)

    model_list[5].saveModel("sarsa5.npy")
    model_list[9].saveModel("sarsa9.npy")
