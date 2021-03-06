"""Author: Brandon Trabucco, Copyright 2019, MIT License"""


from multiarchy.launch import launch_local
from multiarchy.baselines.sac import sac, sac_variant
from gym.envs.mujoco.half_cheetah import HalfCheetahEnv


if __name__ == "__main__":

    # parameters for the learning experiment
    variant = dict(
        max_num_steps=1000000,
        logging_dir="half_cheetah/sac/",
        hidden_size=256,
        num_hidden_layers=2,
        reward_scale=1.0,
        discount=0.99,
        initial_alpha=1.0,
        policy_learning_rate=0.0003,
        qf_learning_rate=0.0003,
        tau=0.005,
        batch_size=256,
        max_path_length=1000,
        num_workers=10,
        num_warm_up_steps=100000,
        num_steps_per_epoch=1000,
        num_steps_per_eval=50000,
        num_steps_per_gradient=1,
        num_epochs_per_eval=10,
        num_epochs=10000)

    # make sure that all the right parameters are here
    assert all([x in variant.keys() for x in sac_variant.keys()])

    # launch the experiment using ray
    launch_local(
        sac,
        variant,
        HalfCheetahEnv,
        num_seeds=3)
