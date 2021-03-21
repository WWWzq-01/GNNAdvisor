
import argparse
import time
import os
import numpy as np
from tqdm import *

import torch
import torch.nn as nn
import torch.nn.functional as F
import dgl
from dgl.data import register_data_args

from dataset import *

run_GCN = False
if run_GCN:
    from gcn import GCN
else:
    from gin import GIN

def main(args):
    path = os.path.join("/home/yuke/.graphs/osdi-ae-graphs", args.dataset+".npz")
    data = custom_dataset(path, args.dim, args.classes, load_from_txt=False)
    g = data.g

    if args.gpu < 0:
        cuda = False
    else:
        cuda = True

    g = g.int().to(args.gpu)

    features = data.x
    labels = data.y
    in_feats = features.size(1)
    n_classes = data.num_classes
    n_edges = data.num_edges

    # normalization
    degs = g.in_degrees().float()
    norm = torch.pow(degs, -0.5)
    norm[torch.isinf(norm)] = 0
    if cuda:
        norm = norm.cuda()
    g.ndata['norm'] = norm.unsqueeze(1)

    if run_GCN:    
        model = GCN(g,
                    in_feats=in_feats,
                    n_hidden=args.hidden,
                    n_classes=n_classes,
                    n_layers=2)
    else:
        model = GIN(g,
                    input_dim=in_feats,
                    hidden_dim=64,
                    output_dim=n_classes,
                    num_layers=5)

    if cuda: model.cuda()

    loss_fcn = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(),
                                 lr=1e-2,
                                 weight_decay=5e-4)

    dur = []
    for epoch in tqdm(range(args.n_epochs)):
        model.train()
        t0 = time.time()

        logits = model(features)
        loss = loss_fcn(logits[:], labels[:])

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        dur.append(time.time() - t0)
    
    print("DGL Time: (ms) {:.3f}". format(np.mean(dur)*1e3))
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GCN')
    register_data_args(parser)
    parser.add_argument("--gpu", type=int, default=0,
                        help="gpu")
    parser.add_argument("--n-epochs", type=int, default=200,
                        help="number of training epochs")
    parser.add_argument("--dim", type=int, default=96, 
                        help="input embedding dimension")
    parser.add_argument("--hidden", type=int, default=16,
                        help="number of hidden gcn units")
    parser.add_argument("--classes", type=int, default=10,
                        help="number of output classes")
    args = parser.parse_args()
    print(args)

    main(args)
