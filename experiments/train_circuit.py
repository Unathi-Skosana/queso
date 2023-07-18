import time
import tqdm
import matplotlib.pyplot as plt

import jax
import jax.numpy as jnp
import optax

from queso.sensors.tc.sensor import Sensor
from queso.io import IO
import h5py


def train_circuit(
    io: IO,
    n: int,
    k: int,
    key: jax.random.PRNGKey,
    phi_range: tuple,
    n_phis: int = 10,
    n_shots: int = 500,
    lr: float = 1e-2,
    n_steps: int = 100,
    plot: bool = False,
    progress: bool = True,
):
    print(f"Initializing sensor n={n}, k={k}")
    sensor = Sensor(n, k)

    optimizer = optax.adam(learning_rate=lr)

    def loss_cfi(params):
        return -sensor.cfi(params["theta"], phi, params["mu"])

    def loss_qfi(params):
        return -sensor.qfi(params["theta"], phi)

    # %%
    @jax.jit
    def step(params, opt_state):
        val, grads = loss_val_grad(params)
        updates, opt_state = optimizer.update(grads, opt_state)
        params = optax.apply_updates(params, updates)
        return val, params, updates, opt_state

    # %%
    # key = jax.random.PRNGKey(time.time_ns())

    phi = jnp.array(0.0)
    theta = jax.random.uniform(key, shape=[n, k, 2])
    mu = jax.random.uniform(key, shape=[n, 3])

    loss = loss_cfi
    params = {"theta": theta, "mu": mu}

    # loss = loss_qfi
    # params = {'theta': theta}

    loss_val_grad = jax.value_and_grad(loss)

    opt_state = optimizer.init(params)
    val, grads = loss_val_grad(params)

    # %%
    losses, vn_ent = [], []
    for i in (pbar := tqdm.tqdm(range(n_steps), disable=(not progress))):
        val, params, updates, opt_state = step(params, opt_state)
        losses.append(-val)
        vn_ent.append(sensor.entanglement(params["theta"], phi))
        if progress:
            pbar.set_description(f"Step {i} | FI: {-val:.10f}")

    losses = jnp.array(losses)
    fi = losses  # set FI to the losses
    theta = params["theta"]
    mu = params["mu"]

    if plot:
        # %% visualize
        fig, axs = plt.subplots(ncols=1, nrows=2, sharex=True)
        axs[0].plot(losses)
        axs[0].axhline(n**2, ls="--", alpha=0.5)
        axs[0].set(ylabel="Fisher Information")
        axs[1].plot(vn_ent)
        axs[1].set(ylabel="Entropy of entanglement", xlabel="Optimization Step")
        io.save_figure(fig, filename="fi-entropy-optimization")

        # sensor.circuit(theta, phi, mu).draw(output="text")

    # %%
    print(f"Sampling {n_shots} shots for {n_phis} phase value between 0 and pi.")
    phis = jnp.linspace(*phi_range, n_phis, endpoint=False)
    t0 = time.time()
    shots, probs = sensor.sample_over_phases(theta, phis, mu, n_shots=n_shots, verbose=True)
    t1 = time.time()
    print(f"Sampling took {t1 - t0} seconds.")

    # %%
    metadata = dict(n=n, k=k, lr=lr)
    io.save_json(metadata, filename="circ-metadata.json")

    hf = h5py.File(io.path.joinpath("circ.h5"), "w")
    hf.create_dataset("theta", data=theta)
    hf.create_dataset("mu", data=mu)
    hf.create_dataset("phis", data=phis)
    hf.create_dataset("shots", data=shots)
    hf.create_dataset("probs", data=probs)
    hf.create_dataset("fi", data=fi)
    hf.create_dataset("vn_ent", data=vn_ent)
    hf.close()

    return


if __name__ == "__main__":
    n = 1
    k = 1

    io = IO(folder=f"nn-estimator-n{n}-k{k}", include_date=True)
    io.path.mkdir(parents=True, exist_ok=True)

    # %%
    key = jax.random.PRNGKey(time.time_ns())
    plot = True
    train_circuit(
        io=io,
        n=n,
        k=k,
        key=key,
        n_steps=100,
        lr=1e-1,
        n_phis=200,
        n_shots=1000,
        plot=plot,
    )
    time.sleep(0.1)