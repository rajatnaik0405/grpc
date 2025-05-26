import logging
import time
import unittest
import grpc

from grpc.framework.foundation import logging_pool
from tests.unit.framework.common import test_constants

# Constants
_REQUEST = b"\x00\x00\x00"
_RESPONSE = b"\x00\x00\x01"

_SERVICE_NAME = "test"
_UNARY_UNARY = "UnaryUnary"

_NUM_OF_CALLS = 5
_CALL_TIMEOUT = 1  # seconds
_RETRY_SLEEP = 0.1  # seconds
_SERVER_DOWN_TIME_INTERVAL = 30  # seconds
_RECOVERY_TIME_INTERVAL = 5  # seconds


def _handle_unary_unary(unused_request, unused_servicer_context):
    return _RESPONSE


def start_server(pool):
    """Creates and starts a gRPC server on a dynamic port."""
    handler = grpc.method_handlers_generic_handler(
        _SERVICE_NAME,
        {_UNARY_UNARY: grpc.unary_unary_rpc_method_handler(_handle_unary_unary)},
    )
    options = (("grpc.so_reuseport", 1),)
    server = grpc.server(pool, (handler,), options=options)
    port = server.add_insecure_port("localhost:0")  
    addr = f"localhost:{port}"
    server.start()
    logging.info(f"Server started at {addr}")
    return server, addr


class ReconnectBehaviourTest(unittest.TestCase):
    def _wait_for_success_call(self, stub):
        deadline = time.time() + _RECOVERY_TIME_INTERVAL
        while time.time() < deadline:
            try:
                response = stub(_REQUEST, timeout=_CALL_TIMEOUT)
                if response == _RESPONSE:
                    return True
            except grpc.RpcError as e:
                print(f"Waiting for recovery... Got error: {e.code()}")
                pass
        return False

    def test_channel_goes_transient_failure_and_recovers(self):
        pool = logging_pool.pool(test_constants.THREAD_CONCURRENCY)

        # Start server
        server, addr = start_server(pool)

        # Create client stub
        channel = grpc.insecure_channel(addr)
        stub = channel.unary_unary(
            f"/{_SERVICE_NAME}/{_UNARY_UNARY}",
            request_serializer=None,
            response_deserializer=None,
            _registered_method=True,
        )

        # Send initial repeated calls and assert success
        for i in range(_NUM_OF_CALLS):
            self.assertEqual(_RESPONSE, stub(_REQUEST))

        # Stop server
        server.stop(None)
        server.wait_for_termination()

        # Send call while server is down, expect UNAVAILABLE
        with self.assertRaises(grpc.RpcError) as ctx:
            stub(_REQUEST, timeout=_SERVER_DOWN_TIME_INTERVAL)

        self.assertEqual(
            grpc.StatusCode.UNAVAILABLE,
            ctx.exception.code(),
            "Expected UNAVAILABLE status while server is down"
        )

        # Restart server
        server, _ = start_server(pool)

        # Wait and assert recovery
        recovered = self._wait_for_success_call(stub)
        self.assertTrue(recovered, "Expected calls to succeed after server restart")

        # Cleanup
        server.stop(None)
        channel.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main(verbosity=2)