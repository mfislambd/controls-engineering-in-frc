#!/usr/bin/env python3

# Avoid needing display if plots aren't being shown
import sys

if "--noninteractive" in sys.argv:
    import matplotlib as mpl

    mpl.use("svg")
    import utils.latex as latex

import frccontrol as fct
import math
import matplotlib.pyplot as plt
import numpy as np

plt.rc("text", usetex=True)


class Flywheel(fct.System):
    def __init__(self, dt):
        """Flywheel subsystem.

        Keyword arguments:
        dt -- time between model/controller updates
        """
        state_labels = [("Angular velocity", "rad/s")]
        u_labels = [("Voltage", "V")]
        self.set_plot_labels(state_labels, u_labels)
        self.integrator = 0.0
        self.Ki = 0.2

        fct.System.__init__(
            self,
            np.array([[-12.0]]),
            np.array([[12.0]]),
            dt,
            np.zeros((1, 1)),
            np.zeros((1, 1)),
        )

    def create_model(self, states, inputs):
        # Number of motors
        num_motors = 1.0
        # Flywheel moment of inertia in kg-m^2
        J = 0.00032
        # Gear ratio
        G = 12.0 / 18.0

        return fct.models.flywheel(fct.models.MOTOR_775PRO, num_motors, J, G)

    def design_controller_observer(self):
        q = [200.0]
        r = [12.0]
        self.design_lqr(q, r)

        q_vel = 1.0
        r_vel = 0.01
        self.design_kalman_filter([q_vel], [r_vel])

    def update_controller(self, next_r):
        """Advance the controller by one timestep.

        Keyword arguments:
        next_r -- next controller reference (default: current reference)
        """
        e = (self.r - self.x_hat)[0, 0]
        self.integrator = np.clip(
            self.integrator + e * self.dt, self.u_min / self.Ki, self.u_max / self.Ki
        )
        u = self.K @ (self.r - self.x_hat) + self.Ki * self.integrator
        self.r = next_r
        self.u = np.clip(u, self.u_min, self.u_max)


def main():
    dt = 0.00505
    flywheel = Flywheel(dt)

    # Set up graphing
    l0 = 0.1
    l1 = l0 + 5.0
    l2 = l1 + 0.1
    t = np.arange(0, l2 + 5.0, dt)

    refs = []

    # Generate references for simulation
    for i in range(len(t)):
        if t[i] < l0:
            r = np.array([[0]])
        elif t[i] < l1:
            r = np.array([[9000 / 60 * 2 * math.pi]])
        else:
            r = np.array([[0]])
        refs.append(r)

    plt.figure(1)
    x_rec, ref_rec, u_rec, y_rec = flywheel.generate_time_responses(t, refs)

    plt.ylabel(flywheel.state_labels[0])
    plt.plot(t, flywheel.extract_row(x_rec, 0), label="Output")
    plt.plot(t, flywheel.extract_row(ref_rec, 0), label="Setpoint")
    plt.legend()
    plt.xlabel("Time (s)")

    if "--noninteractive" in sys.argv:
        latex.savefig("pi_controller_ss_error_overshoot")
    else:
        plt.show()


if __name__ == "__main__":
    main()
