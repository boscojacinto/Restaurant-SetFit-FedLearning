# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import restaurant_pb2 as restaurant__pb2

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in restaurant_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class RestaurantNeighborStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Setup = channel.unary_unary(
                '/psi_proto.RestaurantNeighbor/Setup',
                request_serializer=restaurant__pb2.SetupRequest.SerializeToString,
                response_deserializer=restaurant__pb2.SetupReply.FromString,
                _registered_method=True)
        self.Fetch = channel.unary_unary(
                '/psi_proto.RestaurantNeighbor/Fetch',
                request_serializer=restaurant__pb2.CustomerRequest.SerializeToString,
                response_deserializer=restaurant__pb2.CustomerReply.FromString,
                _registered_method=True)


class RestaurantNeighborServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Setup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Fetch(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RestaurantNeighborServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Setup': grpc.unary_unary_rpc_method_handler(
                    servicer.Setup,
                    request_deserializer=restaurant__pb2.SetupRequest.FromString,
                    response_serializer=restaurant__pb2.SetupReply.SerializeToString,
            ),
            'Fetch': grpc.unary_unary_rpc_method_handler(
                    servicer.Fetch,
                    request_deserializer=restaurant__pb2.CustomerRequest.FromString,
                    response_serializer=restaurant__pb2.CustomerReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'psi_proto.RestaurantNeighbor', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('psi_proto.RestaurantNeighbor', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class RestaurantNeighbor(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Setup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/psi_proto.RestaurantNeighbor/Setup',
            restaurant__pb2.SetupRequest.SerializeToString,
            restaurant__pb2.SetupReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Fetch(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/psi_proto.RestaurantNeighbor/Fetch',
            restaurant__pb2.CustomerRequest.SerializeToString,
            restaurant__pb2.CustomerReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
