from typing import Any
from collections import OrderedDict

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import (
	AutoModelForSequenceClassification,
	AutoTokenizer,
	DataCollatorWithPadding,
)
from evaluate import load as load_metric
from datasets.utils.logging import disable_progress_bar
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner

import os
import sys
from torch_geometric.transforms import RandomLinkSplit, ToUndirected
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
from swigg_db_local import SWGDatasetLocal
from swigg_ml import SWG
import torch.nn.functional as F
import numpy as np

disable_progress_bar()
#fds = None

def load_data(partition_id: int, num_partitions: int, model_name: str) -> tuple[DataLoader[Any], DataLoader[Any]]:
	
	#global fds
	#if fds is None:

	path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')
	dataset = SWGDatasetLocal(path, partition_id, force_reload=True)
	fds = dataset.data 

	transform = RandomLinkSplit(
		num_val=0.1,
		num_test=0.2,
		neg_sampling_ratio=0.0,
        edge_types=[('restaurant', 'to', 'restaurant'),
                    ('restaurant', 'to', 'area'),
                    ('restaurant', 'to', 'customer'),
                    ('customer', 'to', 'restaurant')
                    ]
	)

	trainloader, valloader, testloader = transform(fds)

	return fds, trainloader, testloader

def get_model(model_name, metadata):
	return SWG(hidden_channels=64, out_channels=2, num_heads=2, num_layers=1,
			node_types=['restaurant', 'area', 'customer'], metadata=metadata)

def get_params(model):
	return [val.cpu().numpy() for _, val in model.state_dict().items()]

def set_params(model, parameters) -> None:
	params_dict = zip(model.state_dict().keys(), parameters)
	state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
	model.load_state_dict(state_dict, strict=True)

def train(net, trainloader, epochs, device) -> None:
	optimizer = torch.optim.Adam(net.parameters(), lr=0.005, weight_decay=0.001)		
	for epoch in range(1, epochs):
		net.train()
		optimizer.zero_grad()
		outputs = net(trainloader.x_dict, trainloader.edge_index_dict)
		loss = F.cross_entropy(outputs, trainloader['restaurant'].y)
		print(f"l={loss}")
		loss.backward()
		optimizer.step()

def test(net, testloader, device) -> tuple[Any | float, Any]:
	loss = 0
	net.eval()
	with torch.no_grad():
		outputs = net(testloader.x_dict, testloader.edge_index_dict)
		preds = outputs.argmax(dim=-1)

	accuracy = (preds == testloader['restaurant'].y).sum() / len(testloader['restaurant'].y)
	loss = 1.0 - accuracy 
	return loss, accuracy