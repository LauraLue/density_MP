import torch
from systems.sytem_CAR import Car
import hyperparams
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pickle
from plot_functions import plot_density_heatmap


def compute_data(iteration_number, sample_size, system, args):
    results_all = []
    for i in range(iteration_number):

        # get random input trajectory and compute corresponding state trajectory
        uref_traj = system.sample_uref_traj(args.N_sim, args.N_u) # get random input trajectory
        xref0 = system.sample_xref0() # sample random xref
        xref_traj = system.compute_xref_traj(xref0, uref_traj, args.N_sim, args.dt_sim) # compute corresponding xref trajectory
        xref_traj, uref_traj = system.cut_xref_traj(xref_traj, uref_traj) # cut trajectory where state limits are exceeded
        if xref_traj.shape[2] < args.N_sim: # start again if reference trajectory is shorter than N_sim
            continue

        # compute corresponding  state and density trajectories
        x0 = system.sample_x0(xref0, sample_size) # get random initial states
        rho0 = 1 / (torch.prod(system.X_MAX-system.X_MIN)) * torch.ones(x0.shape[0], 1, 1) # equal initial density
        x_traj, rho_traj = system.compute_density(x0, xref_traj, uref_traj, rho0, xref_traj.shape[2], args.dt_sim) # compute x and rho trajectories
        if x_traj.shape[2] < args.N_sim: # start again if x trajectories shorter than N_sim
            continue

        # save the results
        xref_traj = xref_traj[[0],:, :x_traj.shape[2]]
        uref_traj = uref_traj[[0],:, :x_traj.shape[2]]
        xe_traj = x_traj - xref_traj
        t = args.dt_sim * torch.arange(0, x_traj.shape[2])
        results = {
            't': t,
            'uref_traj': uref_traj,
            'xref_traj': xref_traj,
            'xe_traj': xe_traj,
            'rho_traj': rho_traj
        }
        results_all.append(results)

        if args.plot_densityheat:
            plot_density_heatmap(xe_traj[:, 0, -1].numpy(), xe_traj[:, 1, -1].numpy(), rho_traj[:, 0, -1].numpy(), xe_traj.shape[2], args)

    path = args.path_rawdata
    data_name = path+datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+"_"+system.systemname+"_dt%d" % (args.dt_sim*1000)+"ms_Nsim%d_Nu%d_iter%d" % (args.N_sim, args.N_u, iteration_number)+".pickle" #+"_randomSeed"+str(args.random_seed)
    with open(data_name, "wb") as f:
        pickle.dump(results_all, f)


if __name__ == "__main__":

    args = hyperparams.parse_args()

    sample_size = 1000  # [15, 15, 5, 5] ' number of sampled initial conditions x0
    iteration_number = 3
    system = Car()
    random_seed = False
    if random_seed:
        torch.manual_seed(args.random_seed)
    else:
        args.random_seed = None

    compute_data(iteration_number, sample_size, system, args)

    print("end")
