import torch
from data_generation.create_dataset import densityDataset
from density_training.train_density import NeuralNetwork


def loss_function(xe_nn, xe_true, rho_nn, rho_true, args):
    loss_xe = ((xe_nn - xe_true) ** 2).mean()
    mask = torch.logical_or(rho_true < 1e-5, rho_nn < 1e-5)
    loss_rho = 0
    if mask.any():
        loss_rho = ((rho_nn[mask] - rho_true[mask]) ** 2).mean()
        rho_nn = rho_nn[torch.logical_not(mask)]
        rho_true = rho_true[torch.logical_not(mask)]
    if not mask.all():
        loss_rho += ((torch.log(rho_nn) - torch.log(rho_true)) ** 2).mean()

    return loss_xe, args.rho_loss_weight * loss_rho


def load_dataloader(args):
    train_data = densityDataset(args, mode="Train")
    train_dataloader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_data = densityDataset(args, mode="Val")
    validation_dataloader = DataLoader(val_data, batch_size=args.batch_size, shuffle=True)
    # train_set_size = int(len(density_data) * args.train_len)
    # val_set_size = len(density_data) - train_set_size
    # train_data, validation_data = random_split(density_data, [train_set_size, val_set_size])
    # train_dataloader = DataLoader(train_data.dataset, batch_size=args.batch_size, shuffle=True)
    # validation_dataloader = DataLoader(validation_data.dataset, batch_size=args.batch_size, shuffle=True)
    return train_dataloader, validation_dataloader


def create_configs(learning_rate=None, num_hidden=None, size_hidden=None, weight_decay=None, optimizer=None, rho_loss_weight=None, args=None):
    if learning_rate is None:
        learning_rate = [args.learning_rate]
    if num_hidden is None:
        num_hidden = [len(args.size_hidden)]
    if size_hidden is None:
        size_hidden = [args.size_hidden[0]]
    if weight_decay is None:
        weight_decay = [args.weight_decay]
    if optimizer is None:
        optimizer = [args.optimizer]
    if rho_loss_weight is None:
        rho_loss_weight = [args.rho_loss_weight]

    configs = []
    for lr in learning_rate:
        for nh in num_hidden:
            for sh in size_hidden:
                for wd in weight_decay:
                    for opt in optimizer:
                        for rw in rho_loss_weight:
                            configs.append({"learning_rate": lr,
                                            "num_hidden": nh,
                                            "size_hidden": sh,
                                            "weight_decay": wd,
                                            "optimizer": opt,
                                            "rho_loss_weight": rw})
    return configs


def load_args(config, args):
    args.learning_rate = config["learning_rate"]
    args.size_hidden = [config["size_hidden"]] * config["num_hidden"]
    args.weight_decay = config["weight_decay"]
    args.optimizer = config["optimizer"]
    args.rho_loss_weight = config["rho_loss_weight"]
    return args


def load_nn(num_inputs, num_outputs, args, load_pretrained=False):
    model = NeuralNetwork(num_inputs, num_outputs, args).to(args.device)
    if load_pretrained:
        model_params, _, _ = torch.load(args.name_pretrained_nn, map_location=args.device)
        model.load_state_dict(model_params)
    if args.optimizer == "SGD":
        optimizer = torch.optim.SGD(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    elif args.optimizer == "Adam":
        optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    elif args.optimizer == "LBFGS":
        optimizer = torch.optim.LBFGS(model.parameters(), lr=args.learning_rate)
    else:
        raise NotImplemented('NotImplemented')

    return model, optimizer


def evaluate(dataloader, model, args, optimizer=None, mode="val"):

    if mode == "train" and optimizer is not None:
        model.train()
    elif mode == "val":
        model.eval()
    else:
        print("mode not defined")

    total_loss, total_loss_xe, total_loss_rho_w = 0, 0, 0
    max_loss_xe = torch.zeros(len(dataloader), 4)
    max_loss_rho_w = torch.zeros(len(dataloader))

    for batch, (input, target) in enumerate(dataloader):
        input, target = input.to(args.device), target.to(args.device)

        # Compute prediction error
        output = model(input)
        xe_nn, rho_nn = get_output_variables(output, dataloader.dataset.output_map, type='exp')
        xe_true, rho_true = get_output_variables(target, dataloader.dataset.output_map)

        loss_xe, loss_rho_w = loss_function(xe_nn, xe_true, rho_nn, rho_true, args)
        loss = loss_xe + loss_rho_w
        total_loss_xe += loss_xe.item()
        total_loss_rho_w += loss_rho_w.item()
        max_loss_xe[batch, :], _ = torch.max(torch.abs(xe_nn-xe_true), dim=0)
        max_loss_rho_w[batch] = args.rho_loss_weight * torch.log(torch.max(torch.abs(rho_nn-rho_true)))
        total_loss += loss.item()

        if mode == "train":
            # Backpropagation
            if args.optimizer == "LBFGS":
                def closure():
                    output = model(input)
                    xe_nn, rho_nn = get_output_variables(output, dataloader.dataset.output_map, type='exp')
                    xe_true, rho_true = get_output_variables(target, dataloader.dataset.output_map)
                    loss_xe, loss_rho_w = loss_function(xe_nn, xe_true, rho_nn, rho_true, args)
                    loss = loss_xe + loss_rho_w
                    loss.backward()
                    return loss

                optimizer.step(closure)
            else:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

    maxMax_loss_xe, _ = torch.max(max_loss_xe, dim=0)
    loss_all = {
        "loss": total_loss / len(dataloader),
        "loss_xe": total_loss_xe / len(dataloader),
        "loss_rho_w": total_loss_rho_w / len(dataloader),
        "max_error_xe": maxMax_loss_xe.detach().numpy(),
        "max_error_rho_w": (torch.max(max_loss_rho_w)).detach().numpy()
        }
    return loss_all

