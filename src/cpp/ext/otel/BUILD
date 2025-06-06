# gRPC Bazel BUILD file.
#
# Copyright 2023 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

load(
    "//bazel:grpc_build_system.bzl",
    "grpc_cc_library",
)

licenses(["reciprocal"])

package(
    default_visibility = ["//visibility:public"],
    features = [
        "layering_check",
    ],
)

grpc_cc_library(
    name = "otel_plugin",
    srcs = [
        "otel_client_call_tracer.cc",
        "otel_plugin.cc",
        "otel_server_call_tracer.cc",
    ],
    hdrs = [
        "key_value_iterable.h",
        "otel_client_call_tracer.h",
        "otel_plugin.h",
        "otel_server_call_tracer.h",
        "//:include/grpcpp/ext/otel_plugin.h",
    ],
    external_deps = [
        "absl/base:core_headers",
        "absl/container:flat_hash_map",
        "absl/container:flat_hash_set",
        "absl/functional:any_invocable",
        "absl/log:check",
        "absl/status",
        "absl/status:statusor",
        "absl/strings",
        "absl/strings:str_format",
        "absl/time",
        "absl/types:span",
        "otel/api",
    ],
    tags = [
        # TODO(b/332369798): Remove after fixing bug
        "grpc:otel-namespace-calamity",
    ],
    visibility = ["//bazel:otel_plugin"],
    deps = [
        "//:call_tracer",
        "//:config",
        "//:exec_ctx",
        "//:gpr",
        "//:gpr_platform",
        "//:grpc++",
        "//:grpc_base",
        "//:grpc_client_channel",
        "//:grpc_public_hdrs",
        "//src/core:arena",
        "//src/core:arena_promise",
        "//src/core:channel_args",
        "//src/core:channel_fwd",
        "//src/core:channel_stack_type",
        "//src/core:context",
        "//src/core:down_cast",
        "//src/core:error",
        "//src/core:event_engine_utils",
        "//src/core:experiments",
        "//src/core:match",
        "//src/core:metadata_batch",
        "//src/core:metrics",
        "//src/core:slice",
        "//src/core:slice_buffer",
        "//src/core:sync",
        "//src/core:tcp_tracer",
    ],
)
