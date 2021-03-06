import copy
import os
import pickle
import random
import time
import datetime
import shutil
import json
import numpy as np
from gym.envs.toy_text.taxi import TaxiEnv
from UCRL.envs.wrappers import GymDiscreteEnvWrapperTaxi
from UCRL.envs.toys import ResourceCollection
import UCRL.Ucrl as Ucrl
import UCRL.span_algorithms as spalg
import UCRL.logging as ucrl_logger
from optparse import OptionParser, OptionGroup

import matplotlib
# 'DISPLAY' will be something like this ':0'
# on your local machine, and None otherwise
# if os.environ.get('DISPLAY') is None:
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class UCRLforRC(Ucrl.UcrlMdp):

    def set_parameters(self, log_file_prefix,
                       save_policy_every_episodes=50,
                       save_state_every_times=100):
        self.log_file_prefix = log_file_prefix
        self.every_policy = save_policy_every_episodes
        self.every_state = save_state_every_times
        self.state_log = '{}_states.txt'.format(self.log_file_prefix)
        try:
            os.remove(self.state_log)
        except OSError:
            pass

    def solve_optimistic_model(self):
        if self.episode == 2 or (self.episode > 1 and (self.episode-1) % 50 == 0):
            output_dict = {
                'policy': self.policy.tolist(),
                'state_tk': self.old_state,
                'episode_start': self.old_time,
                'episode_end': self.iteration,
                'episode': self.episode-1
            }
            import json
            fname = "{}_policy_ep_{}.json".format(self.log_file_prefix, self.episode-1)
            with open(fname, 'w') as ff:
                json.dump(output_dict, ff, sort_keys=True)

        self.old_time = self.iteration
        self.old_state = self.environment.state

        span_value = super(UCRLforRC, self).solve_optimistic_model()
        return span_value

    def update(self, curr_state, curr_act_idx, curr_act):
        if self.iteration % self.every_state == 0:
            self.statefp = open(self.state_log, 'a+')
            self.statefp.write('{}\n'.format(curr_state))
            self.statefp.close()
        super(UCRLforRC, self).update(curr_state, curr_act_idx, curr_act)

    def clear_before_pickle(self):
        super(UCRLforRC, self).clear_before_pickle()
        del self.statefp
        del self.old_state
        del self.old_time


class SCALforRC(spalg.SCAL):

    def set_parameters(self, log_file_prefix,
                       save_policy_every_episodes=50,
                       save_state_every_times=100):
        self.log_file_prefix = log_file_prefix
        self.every_policy = save_policy_every_episodes
        self.every_state = save_state_every_times
        self.state_log = '{}_states.txt'.format(self.log_file_prefix)
        try:
            os.remove(self.state_log)
        except OSError:
            pass

    def solve_optimistic_model(self):
        if self.episode == 2 or (self.episode > 1 and (self.episode - 1) % 50 == 0):
            output_dict = {
                'policy': self.policy.tolist(),
                'policy_indices': self.policy_indices.tolist(),
                'state_tk': self.old_state,
                'episode_start': self.old_time,
                'episode_end': self.iteration,
                'episode': self.episode-1
            }
            import json
            fname = "{}_policy_ep_{}.json".format(self.log_file_prefix, self.episode-1)
            with open(fname, 'w') as ff:
                json.dump(output_dict, ff, sort_keys=True)

        self.old_time = self.iteration
        self.old_state = self.environment.state

        span_value = super(SCALforRC, self).solve_optimistic_model()
        return span_value

    def update(self, curr_state, curr_act_idx, curr_act):
        if self.iteration % self.every_state == 0:
            self.statefp = open(self.state_log, 'a+')
            self.statefp.write('{}\n'.format(curr_state))
            self.statefp.close()
        super(SCALforRC, self).update(curr_state, curr_act_idx, curr_act)

    def clear_before_pickle(self):
        super(SCALforRC, self).clear_before_pickle()
        del self.statefp
        del self.old_state
        del self.old_time



parser = OptionParser()
parser.add_option("-n", "--duration", dest="duration", type="int",
                  help="duration of the experiment", default=10000)
parser.add_option("-b", "--boundtype", type="str", dest="bound_type",
                  help="Selects the bound type", default="bernstein")
parser.add_option("-c", "--span_constraint", type="float", dest="span_constraint",
                  help="Uppper bound to the bias span", default=1000000)
parser.add_option("--operatortype", type="str", dest="operator_type",
                  help="Select the operator to use for SC-EVI", default="T")
parser.add_option("--armor_collect_prob", dest="armor_collect_prob", type="float",
                  help="probability of mining gold with an armor", default=0.01)
parser.add_option("--p_alpha", dest="alpha_p", type="float",
                  help="range of transition matrix", default=0.05)
parser.add_option("--r_alpha", dest="alpha_r", type="float",
                  help="range of reward", default=0.05)
parser.add_option("--regret_steps", dest="regret_time_steps", type="int",
                  help="regret time steps", default=5000)
parser.add_option("-r", "--repetitions", dest="nb_simulations", type="int",
                  help="Number of repetitions", default=1)
parser.add_option("--no_aug_rew", dest="augmented_reward", action="store_false", default="True")
parser.add_option("--stochrew", dest="stochastic_reward", action="store_true", default="False")
parser.add_option("--rep_offset", dest="nb_sim_offset", type="int",
                  help="Repetitions starts at the given number", default=0)
parser.add_option("--id", dest="id", type="str",
                  help="Identifier of the script", default=None)
parser.add_option("--path", dest="path", type="str",
                  help="Path to the folder where to store results", default=None)
parser.add_option("-q", "--quiet",
                  action="store_true", dest="quiet", default=False,
                  help="don't print status messages to stdout")
parser.add_option("--seed", dest="seed_0", type=int, default=1011005946, #random.getrandbits(16),
                  help="Seed used to generate the random seed sequence")

alg_desc = """Here the description of the algorithms                                
|- UCRL                                                                       
|- SCAL                                                                                                                                            
"""
group1 = OptionGroup(parser, title='Algorithms', description=alg_desc)
group1.add_option("-a", "--alg", dest="algorithm", type="str",
                  help="Name of the algorith to execute"
                       "[UCRL, SCAL]",
                  default="SCAL")
parser.add_option_group(group1)

(in_options, in_args) = parser.parse_args()

if in_options.id and in_options.path:
    parser.error("options --id and --path are mutually exclusive")

assert in_options.algorithm in ["UCRL", "SCAL"]
assert in_options.nb_sim_offset >= 0
assert in_options.operator_type in ['T', 'N']

if in_options.id is None:
    in_options.id = '{:%Y%m%d_%H%M%S}'.format(datetime.datetime.now())

config = vars(in_options)

# ------------------------------------------------------------------------------
# Relevant code
# ------------------------------------------------------------------------------
r_max = 1  # should always be equal to 1 if we rescale

env = ResourceCollection(armor_collect_prob=in_options.armor_collect_prob)


# fps = 2
# s = env.state
# env.reset()
# env.render(mode='human')
# for i in range(1000):
#     a = env.optimal_policy_indices[s]
#     env.execute(a)
#     print("{} {:.3f}".format(a, env.reward))
#     env.render(mode='human')
#     time.sleep(1.0 / fps)
#     s = env.state
# exit(10)

if in_options.path is None:
    folder_results = os.path.abspath('{}_{}_{}'.format(in_options.algorithm, type(env).__name__,
                                                           in_options.id))
    if os.path.exists(folder_results):
        shutil.rmtree(folder_results)
    os.makedirs(folder_results)
else:
    folder_results = os.path.abspath(in_options.path)
    if not os.path.exists(folder_results):
        os.makedirs(folder_results)


np.random.seed(in_options.seed_0)
random.seed(in_options.seed_0)
seed_sequence = [random.randint(0, 2**30) for _ in range(in_options.nb_simulations)]

config['seed_sequence'] = seed_sequence

with open(os.path.join(folder_results, 'settings{}.conf'.format(in_options.nb_sim_offset)),'w') as f:
    json.dump(config, f, indent=4, sort_keys=True)

# ------------------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------------------
start_sim = in_options.nb_sim_offset
end_sim = start_sim + in_options.nb_simulations
for rep in range(start_sim, end_sim):
    env.reset()
    env_desc = env.description()
    seed = seed_sequence[rep-start_sim]  # set seed
    np.random.seed(seed)
    random.seed(seed)
    print("rep: {}/{}".format(rep-start_sim, in_options.nb_simulations))

    name = "trace_{}".format(rep)
    ucrl_log = ucrl_logger.create_multilogger(logger_name=name,
                                              console=not in_options.quiet,
                                              filename=name,
                                              path=folder_results)
    ucrl_log.info("mdp desc: {}".format(env_desc))
    ucrl_log.info("optimal bias span: {}".format(env.span))
    ucrl_log.info("optimal gain: {}".format(env.max_gain))
    ofualg = None
    if in_options.algorithm == "UCRL":
        ofualg = UCRLforRC(
            env,
            r_max=r_max,
            alpha_r=in_options.alpha_r,
            alpha_p=in_options.alpha_p,
            verbose=1,
            logger=ucrl_log,
            bound_type_p=in_options.bound_type,
            bound_type_rew=in_options.bound_type,
            random_state=seed)  # learning algorithm
    elif in_options.algorithm == "SCAL":
        ucrl_log.info("Augmented Reward: {}".format(in_options.augmented_reward))
        ofualg = SCALforRC(
            environment=env,
            r_max=r_max,
            span_constraint=in_options.span_constraint,
            alpha_r=in_options.alpha_r,
            alpha_p=in_options.alpha_p,
            verbose=1,
            logger=ucrl_log,
            bound_type_p=in_options.bound_type,
            bound_type_rew=in_options.bound_type,
            random_state=seed,
            operator_type=in_options.operator_type,
            augment_reward=in_options.augmented_reward
        )
    ofualg.set_parameters(log_file_prefix=os.path.join(folder_results, "log".format(rep)))

    ucrl_log.info("[id: {}] {}".format(in_options.id, type(ofualg).__name__))
    ucrl_log.info("seed: {}".format(seed))
    ucrl_log.info("Config: {}".format(config))

    alg_desc = ofualg.description()
    ucrl_log.info("alg desc: {}".format(alg_desc))

    pickle_name = 'ucrl_{}.pickle'.format(rep)
    try:
        h = ofualg.learn(in_options.duration, in_options.regret_time_steps)  # learn task
    except Ucrl.EVIException as valerr:
        ucrl_log.info("EVI-EXCEPTION -> error_code: {}".format(valerr.error_value))
        pickle_name = 'exception_model_{}.pickle'.format(rep)
    except Exception as e:
        ucrl_log.error('EXCEPTION: '+ str(e))
        pickle_name = 'exception_model_{}.pickle'.format(rep)

    ofualg.clear_before_pickle()
    with open(os.path.join(folder_results, pickle_name), 'wb') as f:
        pickle.dump(ofualg, f)

    plt.figure()
    plt.plot(ofualg.span_values, '-')
    plt.xlabel("Points")
    plt.ylabel("Span")
    plt.savefig(os.path.join(folder_results, "span_{}.png".format(rep)))
    plt.figure()
    plt.plot(ofualg.regret, '-')
    plt.xlabel("Points")
    plt.ylabel("Regret")
    plt.savefig(os.path.join(folder_results, "regret_{}.png".format(rep)))
    plt.show()
    plt.close('all')
