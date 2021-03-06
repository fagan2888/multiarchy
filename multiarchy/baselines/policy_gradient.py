"""Author: Brandon Trabucco, Copyright 2019, MIT License"""


from multiarchy import maybe_initialize_process
from multiarchy.envs.normalized_env import NormalizedEnv
from multiarchy.distributions.gaussian import Gaussian
from multiarchy.networks import dense
from multiarchy.agents.policy_agent import PolicyAgent
from multiarchy.replay_buffers.path_replay_buffer import PathReplayBuffer
from multiarchy.loggers.tensorboard_logger import TensorboardLogger
from multiarchy.samplers.parallel_sampler import ParallelSampler
from multiarchy.algorithms.policy_gradient import PolicyGradient
from multiarchy.savers.local_saver import LocalSaver
import numpy as np


policy_gradient_variant = dict(
    max_path_length=1000,
    max_num_paths=1000,
    logging_dir="./",
    hidden_size=400,
    num_hidden_layers=2,
    reward_scale=1.0,
    discount=0.99,
    policy_learning_rate=0.0003,
    exploration_noise_std=0.1,
    num_workers=2,
    num_steps_per_epoch=10000,
    num_steps_per_eval=10000,
    num_epochs_per_eval=10,
    num_epochs=1000)


def policy_gradient(
        variant,
        env_class,
        env_kwargs=None,
        observation_key="observation",
):
    # initialize tensorflow and the multiprocessing interface
    maybe_initialize_process()

    # run an experiment with multiple agents
    if env_kwargs is None:
        env_kwargs = {}

    # initialize the environment to track the cardinality of actions
    env = NormalizedEnv(env_class, **env_kwargs)
    action_dim = env.action_space.low.size
    observation_dim = env.observation_space.spaces[
        observation_key].low.size

    # create a replay buffer to store data
    replay_buffer = PathReplayBuffer(
        max_path_length=variant["max_path_length"],
        max_num_paths=variant["max_num_paths"])

    # create a logging instance
    logger = TensorboardLogger(
        replay_buffer, variant["logging_dir"])

    # create policies for each level in the hierarchy
    policy = Gaussian(
        dense(
            observation_dim,
            action_dim,
            hidden_size=variant["hidden_size"],
            num_hidden_layers=variant["num_hidden_layers"],
            output_activation="tanh"),
        optimizer_kwargs=dict(learning_rate=variant["policy_learning_rate"]),
        std=variant["exploration_noise_std"])

    # train the agent using soft actor critic
    algorithm = PolicyGradient(
        policy,
        replay_buffer,
        reward_scale=variant["reward_scale"],
        discount=variant["discount"],
        observation_key=observation_key,
        batch_size=-1,  # sample everything in the buffer
        logger=logger,
        logging_prefix="policy_gradient/")

    # create a single agent to manage the hierarchy
    agent = PolicyAgent(
        policy,
        algorithm=algorithm,
        observation_key=observation_key)

    # create a saver to record training progress to the disk
    saver = LocalSaver(
        replay_buffer,
        variant["logging_dir"],
        policy=policy)

    # load the networks if already trained
    saver.load()

    # make a sampler to collect data to warm up the hierarchy
    sampler = ParallelSampler(
        env,
        agent,
        max_path_length=variant["max_path_length"],
        num_workers=variant["num_workers"])

    #  train for a specified number of iterations
    for iteration in range(variant["num_epochs"]):

        # discard all previous samples for on policy learning
        replay_buffer.empty()

        if iteration % variant["num_epochs_per_eval"] == 0:

            # evaluate the policy at this step
            sampler.set_weights(agent.get_weights())
            paths, eval_returns, num_steps = sampler.collect(
                variant["num_steps_per_eval"],
                deterministic=True,
                keep_data=False,
                workers_to_use=variant["num_workers"])
            logger.record("eval_mean_return", np.mean(eval_returns))

            # save the replay buffer and the policies
            saver.save()

        # collect more training samples
        sampler.set_weights(agent.get_weights())
        paths, train_returns, num_steps = sampler.collect(
            variant["num_steps_per_epoch"],
            deterministic=False,
            keep_data=True,
            workers_to_use=variant["num_workers"])
        logger.record("train_mean_return", np.mean(train_returns))

        # insert the samples into the replay buffer
        for o, a, r in paths:
            replay_buffer.insert_path(o, a, r)

        # train once with the on policy data
        agent.train()
