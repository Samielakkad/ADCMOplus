"""
hedge_regret.py — runnable empirical check of ADCMOplus Theorem 1.

ADCMOplus reacts to each environmental change by mixing three response arms
(predict / guided-reinit / repair) with a Hedge (multiplicative-weights)
meta-policy. Theorem 1 states that with learning rate

    eta = sqrt(8 * ln(K) / T)

the cumulative regret of Hedge against the best single arm in hindsight is
bounded by

    R_T <= sqrt((T / 2) * ln(K)).

This script simulates the meta-policy over T rounds and shows the realised
regret staying under that theoretical bound — no external data needed.

Run:  python demo/hedge_regret.py    (writes figures/hedge_regret_demo.png)
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Deterministic — a portfolio demo should reproduce identically every run.
RNG = np.random.default_rng(0)

K = 3            # response arms
T = 200          # environmental changes (horizon)
ETA = np.sqrt(8.0 * np.log(K) / T)   # Theorem-1 learning rate

# Each arm has a hidden mean loss in [0, 1]; the realised per-round loss is the
# mean plus bounded sub-Gaussian noise (this is the Lemma-1 noise model).
ARM_MEANS = np.array([0.45, 0.62, 0.30])   # arm 2 is best in hindsight


def simulate():
    weights = np.ones(K) / K
    cum_hedge = 0.0
    cum_arms = np.zeros(K)
    realised_regret, bound = [], []

    for t in range(1, T + 1):
        # Bounded noise in [-0.15, 0.15], losses clipped to [0, 1].
        losses = np.clip(ARM_MEANS + RNG.uniform(-0.15, 0.15, K), 0.0, 1.0)

        # Hedge pays the weighted (expected) loss of its mixture this round.
        cum_hedge += float(weights @ losses)
        cum_arms += losses

        # Multiplicative-weights update, then renormalise.
        weights *= np.exp(-ETA * losses)
        weights /= weights.sum()

        # Regret = Hedge loss - best fixed arm so far; vs the proven bound.
        realised_regret.append(cum_hedge - cum_arms.min())
        bound.append(np.sqrt((t / 2.0) * np.log(K)))

    return np.array(realised_regret), np.array(bound)


def main():
    regret, bound = simulate()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "figures")
    os.makedirs(out_dir, exist_ok=True)

    horizon = np.arange(1, T + 1)
    plt.figure(figsize=(8, 5))
    plt.plot(horizon, bound, "--", color="#BF616A",
             label=r"theoretical bound  $\sqrt{(T/2)\ln K}$")
    plt.plot(horizon, regret, color="#5E81AC", linewidth=2,
             label="realised Hedge regret")
    plt.fill_between(horizon, regret, bound, color="#A3BE8C", alpha=0.25)
    plt.xlabel("environmental change t")
    plt.ylabel("cumulative regret")
    plt.title("ADCMOplus Theorem 1 — Hedge regret stays under the bound (K=3)")
    plt.legend(loc="upper left")
    plt.tight_layout()
    out = os.path.join(out_dir, "hedge_regret_demo.png")
    plt.savefig(out, dpi=160)

    ratio = regret[-1] / bound[-1]
    print(f"final realised regret = {regret[-1]:.3f}")
    print(f"theoretical bound     = {bound[-1]:.3f}")
    print(f"regret / bound        = {ratio:.2%}  (must be <= 100%)")
    assert regret[-1] <= bound[-1], "regret exceeded the proven bound!"
    print(f"OK — bound holds. Figure written to {os.path.normpath(out)}")


if __name__ == "__main__":
    main()
