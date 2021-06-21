# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/cost_scaling_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 3484 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/cost_scaling_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n0iva/detectnet_v2/proto/cost_scaling_config.proto"\x94\x01\n\x11CostScalingConfig\x12\x18\n\x07enabled\x18\x01 \x01(\x08R\x07enabled\x12)\n\x10initial_exponent\x18\x02 \x01(\x01R\x0finitialExponent\x12\x1c\n\tincrement\x18\x03 \x01(\x01R\tincrement\x12\x1c\n\tdecrement\x18\x04 \x01(\x01R\tdecrementb\x06proto3'
    )))
_COSTSCALINGCONFIG = _descriptor.Descriptor(
    name='CostScalingConfig',
    full_name='CostScalingConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(name='enabled',
                                    full_name='CostScalingConfig.enabled',
                                    index=0,
                                    number=1,
                                    type=8,
                                    cpp_type=7,
                                    label=1,
                                    has_default_value=False,
                                    default_value=False,
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='enabled',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='initial_exponent',
            full_name='CostScalingConfig.initial_exponent',
            index=1,
            number=2,
            type=1,
            cpp_type=5,
            label=1,
            has_default_value=False,
            default_value=(float(0)),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='initialExponent',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='increment',
                                    full_name='CostScalingConfig.increment',
                                    index=2,
                                    number=3,
                                    type=1,
                                    cpp_type=5,
                                    label=1,
                                    has_default_value=False,
                                    default_value=(float(0)),
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='increment',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='decrement',
                                    full_name='CostScalingConfig.decrement',
                                    index=3,
                                    number=4,
                                    type=1,
                                    cpp_type=5,
                                    label=1,
                                    has_default_value=False,
                                    default_value=(float(0)),
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='decrement',
                                    file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=53,
    serialized_end=201)
DESCRIPTOR.message_types_by_name['CostScalingConfig'] = _COSTSCALINGCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
CostScalingConfig = _reflection.GeneratedProtocolMessageType(
    'CostScalingConfig', (_message.Message,),
    dict(DESCRIPTOR=_COSTSCALINGCONFIG,
         __module__='iva.detectnet_v2.proto.cost_scaling_config_pb2'))
_sym_db.RegisterMessage(CostScalingConfig)
# okay decompiling cost_scaling_config_pb2.pyc
