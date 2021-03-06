import torch
import hyperparams
from torch.utils.data import DataLoader, Dataset
import os
import pickle
from datetime import datetime
from systems.sytem_CAR import Car


def load_inputmap(dim_x, args):
    if args.input_type == "discr10":
        dim_u = 20
    elif args.input_type == "discr5":
        dim_u = 10
    elif args.input_type == "polyn3":
        dim_u = 8
    elif args.input_type == "sincos3":
        dim_u = 12
    elif args.input_type == "sincos4":
        dim_u = 16
    elif args.input_type == "sin":
        dim_u = 8
    elif args.input_type == "cust2":
        dim_u = 12
    elif args.input_type == "cust3":
        dim_u = 18
    else:
        raise NotImplementedError
    num_inputs = 2 * dim_x + 1 + dim_u
    input_map = {'xe0': torch.arange(0, dim_x),
                 'xref0': torch.arange(dim_x, 2 * dim_x),
                 't': 2 * dim_x,
                 'u_params': torch.arange(2 * dim_x + 1, num_inputs)}
    return input_map, num_inputs


def load_outputmap(dim_x=5, args=None):
    if args is None or args.equation == "LE":
        num_outputs = dim_x + 1
        output_map = {'xe': torch.arange(0, dim_x),
                      'rholog': dim_x}
    else:
        num_outputs = 1
        output_map = {'rho': 0}
    return output_map, num_outputs


def raw2nnData(results_all, args):
    data = []
    input_map = None
    #system = Car(args)

    for results in results_all:
        u_params = results['u_params']
        xref0 = results['xref0']
        t = results['t']
        if input_map is None:
            input_map, num_inputs = load_inputmap(xref0.flatten().shape[0], args)
            input_tensor = torch.zeros(num_inputs)
            output_map, num_outputs = load_outputmap(xref0.flatten().shape[0], args)
            output_tensor = torch.zeros(num_outputs)

        if args.equation == "LE":
            xe0 = results['xe0']
            xe_traj = results['xe_traj']
            rholog_traj = results['rholog_traj']
            # if 'u_params' not in results.keys():
            #     uref_traj = results['uref_traj']
            #     u_params = uref_traj[0, :, ::args.N_u]
            #     if u_params.shape[1] < 10:
            #         u_params = torch.cat((u_params[:, :], torch.zeros(u_params.shape[0], 10 - u_params.shape[1])), 1)
            # else:
                # t_traj = torch.arange(0, args.dt_sim * args.N_sim, args.dt_sim).reshape(1, 1, -1).repeat(1, system.DIM_U, 1)
                # uref_traj = u_params[:, :, :, 0] * torch.ones_like(t_traj) + u_params[:, :, :, 1] * t_traj + \
                #             u_params[:, :, :, 2] * t_traj ** 2 + u_params[:, :, :, 3] * t_traj ** 3

            #xref_traj = system.compute_xref_traj(xref0.reshape(1, -1, 1), uref_traj, args)

            #xref_traj = xref_traj[:, :, (t / args.dt_sim).round().int().tolist()]

            input_tensor[input_map['u_params']] = u_params.flatten()
            input_tensor[input_map['xref0']] = xref0
            for i_x in range(min(xe_traj.shape[0], 10)):
                input_tensor[input_map['xe0']] = xe0[i_x, :]
                for i_t in range(0, t.shape[0]):
                    input_tensor[input_map['t']] = t[i_t]
                    output_tensor[output_map['xe']] = xe_traj[i_x, :, i_t]
                    output_tensor[output_map['rholog']] = rholog_traj[i_x, 0, i_t]
                    data.append([input_tensor.numpy().copy(), output_tensor.numpy().copy()])
        else:
            density_map = results['density']
            xref_traj = results['xref_traj']
            uref_traj = results['uref_traj']
            data.append([u_params.flatten(), xref0, t, density_map, xref_traj, uref_traj])
    return data, input_map, output_map, num_inputs, num_outputs


def get_input_tensors(u_params, xref0, xe0, t, args):
    bs = xe0.shape[0]
    if xe0.dim() > 1:
        input_map, num_inputs = load_inputmap(xe0.shape[1], args)
        input_tensor = torch.zeros(bs, num_inputs)
        if xref0.shape[0] == 1:
            xref0 = xref0.flatten()
        else:
            xref0 = xref0.squeeze()
        xe0 = xe0.squeeze()
    else:
        input_map, num_inputs = load_inputmap(xe0.shape[0], args)
        input_tensor = torch.zeros(1, num_inputs)
    if u_params.shape[0] == bs:
        input_tensor[:, input_map['u_params']] = u_params
    else:
        input_tensor[:, input_map['u_params']] = u_params.flatten()
    input_tensor[:, input_map['xref0']] = xref0
    input_tensor[:, input_map['xe0']] = xe0
    input_tensor[:, input_map['t']] = t
    return input_tensor, input_map


def get_output_tensors(xe, rholog):
    output_map, num_outputs = load_outputmap(xe.shape[0])
    output_tensor = torch.zeros(num_outputs)
    output_tensor[output_map['xe']] = xe
    output_tensor[output_map['rholog']] = rholog
    return output_tensor, output_map


def get_input_variables(input, input_map):
    if input.dim() == 2:
        xref0 = input[:, input_map['xref0']]
        xe0 = input[:, input_map['xe0']]
        t = input[:, input_map['t']]
        u_params = input[:, input_map['u_params']]
    elif input.dim() == 1:
        xref0 = input[input_map['xref0']]
        xe0 = input[input_map['xe0']]
        t = input[input_map['t']]
        u_params = input[input_map['u_params']]
    return xref0, xe0, t, u_params


def get_output_variables(output, output_map, type='normal'):
    if output.dim() == 2:
        xe = output[:, output_map['xe']]
        if type == 'exp':
            rho = torch.exp(output[:, output_map['rholog']])
        elif type == 'normal':
            rho = (output[:, output_map['rholog']])
    elif output.dim() == 1:
        xe = output[output_map['xe']]
        if type == 'exp':
            rho = torch.exp(output[output_map['rholog']])
        elif type == 'normal':
            rho = (output[output_map['rholog']])
    return xe, rho


def nn2rawData(data, input_map, output_map, args):
    input, output = data
    xref0, xe0, t, u_params = get_input_variables(input, input_map)
    xe, rho = get_output_variables(output, output_map)
    results = {
        'xe0': xe0,
        'xref0': xref0,
        't': t,
        'u_params': u_params,
        'xe': xe,
        'rho': rho,
    }
    return results





