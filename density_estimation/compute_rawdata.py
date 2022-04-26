import torch
from systems.sytem_CAR import Car
import hyperparams
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pickle
from plot_functions import plot_density_heatmap


def compute_data(iteration_number, samples_x, system, args,samples_t=None, save=True, plot=True):
    results_all = []
    for j in range(100):
        for i in range(iteration_number):
            # get random input trajectory and compute corresponding state trajectory
            valid = False
            while not valid:
                uref_traj, u_params = system.sample_uref_traj(args) # get random input trajectory
                xref0 = system.sample_xref0() # sample random xref
                xref_traj = system.compute_xref_traj(xref0, uref_traj, args) # compute corresponding xref trajectory
                xref_traj, uref_traj = system.cut_xref_traj(xref_traj, uref_traj) # cut trajectory where state limits are exceeded
                if xref_traj.shape[2] < 0.9 * args.N_sim: # start again if reference trajectory is shorter than 0.9 * N_sim
                    continue

                # compute corresponding  state and density trajectories
                x0 = system.sample_x0(xref0, samples_x) # get random initial states
                rho0 = torch.ones(x0.shape[0], 1, 1) # equal initial density
                x_traj, rho_traj = system.compute_density(x0, xref_traj, uref_traj, rho0, xref_traj.shape[2], args.dt_sim) # compute x and rho trajectories
                if rho_traj.dim() < 2 or x_traj.shape[2] < 0.9 * args.N_sim: # start again if x trajectories shorter than N_sim
                    continue
                valid = True

            # save the results
            xref_traj = xref_traj[[0],:, :x_traj.shape[2]]
            uref_traj = uref_traj[[0],:, :x_traj.shape[2]]
            xe_traj = x_traj - xref_traj
            t = args.dt_sim * torch.arange(0, x_traj.shape[2])

            if samples_t == 0:
                indizes = args.N_sim-1
            elif samples_t is not None:
                indizes = torch.randint(0, t.shape[0], (samples_t,))
            else:
                indizes = torch.arange(0, t.shape[0])
            results = {
                'uref_traj': uref_traj,
                'u_params': u_params,
                'x0': x_traj[:,:,0],
                #'rho0': rho_traj[:,:,0],
                't': t[indizes],
                'xref_traj': xref_traj[:,:,indizes],
                'xe_traj': xe_traj[:,:,indizes],
                'rho_traj': rho_traj[:,:,indizes]
                }
            results_all.append(results)

            if plot:
                name = "LE_time%.2fs_numSim%d_numStates%d)" % (
                    args.dt_sim * xe_traj.shape[2], xe_traj.shape[2], xe_traj.shape[0])
                plot_density_heatmap(xe_traj[:, 0, -1].numpy(), xe_traj[:, 1, -1].numpy(), rho_traj[:, 0, -1].numpy(), name, args)

        if save:
            path = args.path_rawdata
            data_name = path + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") +"_rawData_" + system.systemname +"_%s_Nsim%d_iter%d_xSamples%d_tSamples%d" % (args.input_type, args.N_sim, iteration_number, samples_x, samples_t) + ".pickle"
            print("save " + data_name)
            with open(data_name, "wb") as f:
                pickle.dump([results_all, args], f)
            results_all = []

    return results_all


if __name__ == "__main__":

    args = hyperparams.parse_args()

    samples_x = 20  # [15, 15, 5, 5] ' number of sampled initial conditions x0
    iteration_number = 500
    system = Car()
    random_seed = False
    if random_seed:
        torch.manual_seed(args.random_seed)
    else:
        args.random_seed = None

    compute_data(iteration_number, 100, system, args, samples_t=0, save=True,
                 plot=False) #samples_t=0... no sample times inbetween, just final value after N_sim-1 timesteps saved
    #compute_data(iteration_number, samples_x, system, args, samples_t=int(np.rint(0.1*args.N_sim)), save=True, plot=False)

    print("end")
