# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/regularizer_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 3623 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/regularizer_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n/iva/detectnet_v2/proto/regularizer_config.proto"\x98\x01\n\x11RegularizerConfig\x129\n\x04type\x18\x01 \x01(\x0e2%.RegularizerConfig.RegularizationTypeR\x04type\x12\x16\n\x06weight\x18\x02 \x01(\x02R\x06weight"0\n\x12RegularizationType\x12\n\n\x06NO_REG\x10\x00\x12\x06\n\x02L1\x10\x01\x12\x06\n\x02L2\x10\x02b\x06proto3'
    )))
_REGULARIZERCONFIG_REGULARIZATIONTYPE = _descriptor.EnumDescriptor(
    name='RegularizationType',
    full_name='RegularizerConfig.RegularizationType',
    filename=None,
    file=DESCRIPTOR,
    values=[
        _descriptor.EnumValueDescriptor(name='NO_REG',
                                        index=0,
                                        number=0,
                                        serialized_options=None,
                                        type=None),
        _descriptor.EnumValueDescriptor(name='L1',
                                        index=1,
                                        number=1,
                                        serialized_options=None,
                                        type=None),
        _descriptor.EnumValueDescriptor(name='L2',
                                        index=2,
                                        number=2,
                                        serialized_options=None,
                                        type=None)
    ],
    containing_type=None,
    serialized_options=None,
    serialized_start=156,
    serialized_end=204)
_sym_db.RegisterEnumDescriptor(_REGULARIZERCONFIG_REGULARIZATIONTYPE)
_REGULARIZERCONFIG = _descriptor.Descriptor(
    name='RegularizerConfig',
    full_name='RegularizerConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(name='type',
                                    full_name='RegularizerConfig.type',
                                    index=0,
                                    number=1,
                                    type=14,
                                    cpp_type=8,
                                    label=1,
                                    has_default_value=False,
                                    default_value=0,
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='type',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='weight',
                                    full_name='RegularizerConfig.weight',
                                    index=1,
                                    number=2,
                                    type=2,
                                    cpp_type=6,
                                    label=1,
                                    has_default_value=False,
                                    default_value=(float(0)),
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='weight',
                                    file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[],
    enum_types=[_REGULARIZERCONFIG_REGULARIZATIONTYPE],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=52,
    serialized_end=204)
_REGULARIZERCONFIG.fields_by_name[
    'type'].enum_type = _REGULARIZERCONFIG_REGULARIZATIONTYPE
_REGULARIZERCONFIG_REGULARIZATIONTYPE.containing_type = _REGULARIZERCONFIG
DESCRIPTOR.message_types_by_name['RegularizerConfig'] = _REGULARIZERCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
RegularizerConfig = _reflection.GeneratedProtocolMessageType(
    'RegularizerConfig', (_message.Message,),
    dict(DESCRIPTOR=_REGULARIZERCONFIG,
         __module__='iva.detectnet_v2.proto.regularizer_config_pb2'))
_sym_db.RegisterMessage(RegularizerConfig)
# okay decompiling regularizer_config_pb2.pyc
