from typing import List, Tuple, Union, Optional, Dict, Callable
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from flwr.server.client_proxy import ClientProxy 
from flwr.common import (
	Context,
    EvaluateIns,
    EvaluateRes,
    FitIns,
    FitRes,
    MetricsAggregationFn,
    NDArrays,
    Parameters,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.common.logger import log

from restaurant_fl.task import get_params, get_model

class SwgStrategy(FedAvg):
	def aggregate_fit(
		self,
		server_round: int,
		results: List[Tuple[ClientProxy, FitRes]],
		failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
	) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
		weights_results = [
			parameters_to_ndarrays(fit_res.parameters)
			for _, fit_res in results
		]

		print(f"\nweights_results:\n{weights_results}")
		return {"feature1": 4}		

def server_fn(context: Context) -> ServerAppComponents:
	num_rounds = context.run_config["num-server-rounds"]
	config = ServerConfig(num_rounds=num_rounds)

	model_name = context.run_config["model-name"]
	# ndarrays = get_params(get_model(model_name, metadata=ds.metadata()))
	# print(f"\n\n:ndarrays\n{ndarrays}")
	# global_model_init = ndarrays_to_parameters(ndarrays)

	fraction_fit = context.run_config["fraction-fit"]
	fraction_evaluate = context.run_config["fraction-evaluate"]
	strategy = FedAvg(
		fraction_fit=fraction_fit,
		fraction_evaluate=fraction_evaluate,
		#initial_parameters=global_model_init,
	)

	return ServerAppComponents(config=config, strategy=strategy)

app = ServerApp(server_fn=server_fn)