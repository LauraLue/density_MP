import argparse
def parse_args():
    parser = argparse.ArgumentParser()

    # simulation parameter
    parser.add_argument('--N_sim', type=int, default=100)
    parser.add_argument('--N_sim_min', type=int, default=10) # for data generation at random simulation time
    parser.add_argument('--N_sim_max', type=int, default=1000) # for data generation at random simulation time
    parser.add_argument('--N_u', type=int, default=10)
    parser.add_argument('--dt_sim', type=int, default=0.01)
    parser.add_argument('--random_seed', type=int, default=3)

    # data paths
    #parser.add_argument('--path_data', type=str, default="data/density_data/") # directory for the density data
    parser.add_argument('--path_rawdata', type=str, default="data/rawdata/")  # directory for the density data
    parser.add_argument('--path_dataset', type=str, default="data/dataset/")  # directory for the density data
    parser.add_argument('--path_nn', type=str, default="data/trained_nn/")  # directory for saving and loading the trained NN
    parser.add_argument('--path_plot_loss', type=str, default="plots/losscurves/")

    parser.add_argument('--nameend_rawdata', type=str, default="CAR_dt10ms_Nsim100_Nu10_iter1000.pickle")# ending of the file used for creating the data set / dataloader
    parser.add_argument('--nameend_dataset', type=str, default="CAR_dt10ms_Nsim100_Nu10_iter1000.pickle")
    parser.add_argument('--nameend_nn', type=str, default="CAR_dt10ms_Nsim100_Nu10_iter1000.pickle")
    parser.add_argument('--name_pretrained_nn', type=str, default="data/trained_nn/2022-04-18-20-30-22_NN_huge_CAR_dt10ms_Nsim100_Nu10_iter1000.pt") # location and name for the pretrained NN which is supposed to be loaded
    parser.add_argument('--load_pretrained_nn', type=bool, default=False)
    parser.add_argument('--load_dataset', type=bool, default=True) #"middle_all_CAR_dt10ms_Nsim100_Nu10_iter1000.pickle")

    # NN parameter
    parser.add_argument('--device', type=str, default="cpu")
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--epochs', type=int, default=500)
    parser.add_argument('--train_len', type=float, default=0.7) #val_len = 1-train_len
    parser.add_argument('--activation', type=str, default="relu")
    parser.add_argument('--size_hidden', type=int, nargs="+", default=[64, 64, 64])
    parser.add_argument('--rho_loss_weight', type=float, default=0.01)
    parser.add_argument('--optimizer', type=str, default="Adam")
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--weight_decay', type=float, default=0) #L2 regularization
    parser.add_argument('--patience', type=int, default=20)

    return parser.parse_args()