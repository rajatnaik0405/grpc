
import logging
import time
import unittest

import grpc
from grpc.framework.foundation import logging_pool
from tests.unit.framework.common import bound_socket, test_constants

_REQUEST = b"\x00\x00\x00"
_RESPONSE = b"\x00\x00\x01"

_SERVICE_NAME = "test"
_UNARY_UNARY = "UnaryUnary"

_NUM_OF_CALLS = 5
_CALL_TIMEOUT = 1 
_RETRY_SLEEP = 0.1  
_SERVER_DOWN_TIME_INTERVAL = 30
_RECOVERY_TIME_INTERVAL = 5


def _handle_unary_unary(unused_request, unused_servicer_context):
    return _RESPONSE


class ReconnectBehaviourTest(unittest.TestCase):
    def _wait_for_success_call(self, stub):
        deadline = time.time() + _RECOVERY_TIME_INTERVAL
        while time.time() < deadline:
            try:
                if stub(_REQUEST, timeout=_CALL_TIMEOUT) == _RESPONSE:
                    return True
            except grpc.RpcError:
                pass
            time.sleep(_RETRY_SLEEP)
        return False

    def test_channel_goes_transient_failure_and_recovers(self):
        pool = logging_pool.pool(test_constants.THREAD_CONCURRENCY)
        handler = grpc.method_handlers_generic_handler(
            _SERVICE_NAME,
            {_UNARY_UNARY: grpc.unary_unary_rpc_method_handler(_handle_unary_unary)},
        )
        options = (("grpc.so_reuseport", 1),)

        with bound_socket() as (host, port):
            addr = f"{host}:{port}"

            server = grpc.server(pool, (handler,), options=options)
            server.add_insecure_port(addr)
            server.start()

            channel = grpc.insecure_channel(addr)
            multi = channel.unary_unary(f"/{_SERVICE_NAME}/{_UNARY_UNARY}", _registered_method=True)

            # Send initial repeated calls and assert success
            for _ in range(_NUM_OF_CALLS):
                try:
                    response = multi(_REQUEST, timeout=_CALL_TIMEOUT)
                    self.assertEqual(_RESPONSE, response)
                except grpc.RpcError as e:
                    self.fail(f"Initial call : RPC failed with error: {e.code()}")
                time.sleep(_RETRY_SLEEP)

            #Stop server
            server.stop(None)
            server.wait_for_termination()

            #Send calls while server down, assert UNAVAILABLE
            with self.assertRaises(grpc.RpcError) as exc_context:
                multi(_REQUEST, timeout=_SERVER_DOWN_TIME_INTERVAL)
        
            self.assertEqual(
                grpc.StatusCode.UNAVAILABLE,
                exc_context.exception.code(),
                "Expected StatusCode.UNAVAILABLE when server is down"
            )
            
            #Restart server
            server = grpc.server(pool, (handler,), options=options)
            server.add_insecure_port(addr)
            server.start()

            # Wait for recovery and assert success
            recovered = self._wait_for_success_call(multi)
            self.assertTrue(
                recovered,
                "Expected calls to succeed after server restart"
            )

            server.stop(None)
            channel.close()


if __name__ == "__main__":
    logging.basicConfig()
    unittest.main(verbosity=2)
