import argparse
from dataclasses import dataclass, field

import time
import jax
import jax.numpy as jnp

from queso.io import IO
from experiments.train_circuit import train_circuit
from experiments.sample_circuit import sample_circuit
from experiments.train_nn import train_nn
from experiments.benchmark_estimator import benchmark_estimator


#%%
if __name__ == "__main__":

    #%%
    @dataclass
    class Configuration:
        folder: str = None
        seed: int = None

        n: int = 2
        k: int = 2


    d = Configuration()


    # %%
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, default="nonlocal-det-single-int")
    parser.add_argument("--n", type=int, default=2)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    folder = args.folder
    n = args.n
    k = args.k
    seed = args.seed if args.seed is not None else time.time_ns()

    # %%
    io = IO(
        folder=f"{folder}-n{n}-k{k}",
        include_date=True,
        include_id=False,
    )
    io.path.mkdir(parents=True, exist_ok=True)

    key = jax.random.PRNGKey(seed)

    # %% train circuit settings
    circ_kwargs = dict(
        # preparation="brick_wall_cr", interaction="local_rx", detection="local_r"
        preparation="brick_wall_cr", interaction="single_rx", detection="brick_wall_cr"
        # preparation="local_r", interaction="local_rx", detection="local_r"
    )
    circ_kwargs.update(dict(backend="dm"))

    phi_range = (-jnp.pi / 12, jnp.pi / 12)
    n_phis = 100
    n_steps = 20000
    lr = 1e-3
    _, key = jax.random.split(key)
    progress = True
    plot = True

    # %%
    if True:
        train_circuit(
            io=io,
            n=n,
            k=k,
            key=key,
            phi_range=phi_range,
            n_phis=n_phis,
            n_steps=n_steps,
            lr=lr,
            progress=progress,
            plot=plot,
            **circ_kwargs,
        )

    # %% sample circuit settings
    n_shots = 5000
    n_shots_test = 1000
    _, key = jax.random.split(key)

    # %%
    if True:
        sample_circuit(
            io=io,
            n=n,
            k=k,
            key=key,
            phi_range=phi_range,
            n_phis=n_phis,
            n_shots=n_shots,
            n_shots_test=n_shots_test,
            plot=plot,
            **circ_kwargs,
        )

    # %% train estimator settings
    _, key = jax.random.split(key)
    n_epochs = 1000
    batch_size = 50
    n_grid = n_phis  # todo: make more general - not requiring matching training phis and grid
    nn_dims = [32, 32, n_grid]
    lr = 1e-3
    plot = True
    progress = True
    from_checkpoint = False

    # %%
    if True:
        train_nn(
            io=io,
            key=key,
            nn_dims=nn_dims,
            n_steps=n_steps,
            n_grid=n_grid,
            lr=lr,
            n_epochs=n_epochs,
            batch_size=batch_size,
            plot=plot,
            progress=progress,
            from_checkpoint=from_checkpoint,
        )

    # %% benchmark estimator
    _, key = jax.random.split(key)
    n_trials = 100
    phis_inds = jnp.arange(0, 100, 10)
    n_sequences = jnp.round(jnp.logspace(0, 4, 20)).astype("int")

    # %%
    if True:
        benchmark_estimator(
            io=io,
            key=key,
            n_trials=n_trials,
            phis_inds=phis_inds,
            n_sequences=n_sequences,
            plot=False,
        )

    # %%
