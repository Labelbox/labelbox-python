# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/cost_function_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 9196 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/cost_function_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n1iva/detectnet_v2/proto/cost_function_config.proto"°\x04\n\x12CostFunctionConfig\x12F\n\x0etarget_classes\x18\x01 \x03(\x0b2\x1f.CostFunctionConfig.TargetClassR\rtargetClasses\x121\n\x14enable_autoweighting\x18\x02 \x01(\x08R\x13enableAutoweighting\x120\n\x14max_objective_weight\x18\x03 \x01(\x02R\x12maxObjectiveWeight\x120\n\x14min_objective_weight\x18\x04 \x01(\x02R\x12minObjectiveWeight\x1aº\x02\n\x0bTargetClass\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12!\n\x0cclass_weight\x18\x02 \x01(\x02R\x0bclassWeight\x12<\n\x1acoverage_foreground_weight\x18\x03 \x01(\x02R\x18coverageForegroundWeight\x12I\n\nobjectives\x18\x04 \x03(\x0b2).CostFunctionConfig.TargetClass.ObjectiveR\nobjectives\x1ak\n\tObjective\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12%\n\x0einitial_weight\x18\x02 \x01(\x02R\rinitialWeight\x12#\n\rweight_target\x18\x03 \x01(\x02R\x0cweightTargetb\x06proto3'
    )))
_COSTFUNCTIONCONFIG_TARGETCLASS_OBJECTIVE = _descriptor.Descriptor(
    name='Objective',
    full_name='CostFunctionConfig.TargetClass.Objective',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='name',
            full_name='CostFunctionConfig.TargetClass.Objective.name',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=(_b('').decode('utf-8')),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='name',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='initial_weight',
            full_name='CostFunctionConfig.TargetClass.Objective.initial_weight',
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
            json_name='initialWeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='weight_target',
            full_name='CostFunctionConfig.TargetClass.Objective.weight_target',
            index=2,
            number=3,
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
            json_name='weightTarget',
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
    serialized_start=507,
    serialized_end=614)
_COSTFUNCTIONCONFIG_TARGETCLASS = _descriptor.Descriptor(
    name='TargetClass',
    full_name='CostFunctionConfig.TargetClass',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='name',
            full_name='CostFunctionConfig.TargetClass.name',
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=(_b('').decode('utf-8')),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='name',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='class_weight',
            full_name='CostFunctionConfig.TargetClass.class_weight',
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
            json_name='classWeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='coverage_foreground_weight',
            full_name=
            'CostFunctionConfig.TargetClass.coverage_foreground_weight',
            index=2,
            number=3,
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
            json_name='coverageForegroundWeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='objectives',
            full_name='CostFunctionConfig.TargetClass.objectives',
            index=3,
            number=4,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='objectives',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[_COSTFUNCTIONCONFIG_TARGETCLASS_OBJECTIVE],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=300,
    serialized_end=614)
_COSTFUNCTIONCONFIG = _descriptor.Descriptor(
    name='CostFunctionConfig',
    full_name='CostFunctionConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='target_classes',
            full_name='CostFunctionConfig.target_classes',
            index=0,
            number=1,
            type=11,
            cpp_type=10,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='targetClasses',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='enable_autoweighting',
            full_name='CostFunctionConfig.enable_autoweighting',
            index=1,
            number=2,
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
            json_name='enableAutoweighting',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='max_objective_weight',
            full_name='CostFunctionConfig.max_objective_weight',
            index=2,
            number=3,
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
            json_name='maxObjectiveWeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='min_objective_weight',
            full_name='CostFunctionConfig.min_objective_weight',
            index=3,
            number=4,
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
            json_name='minObjectiveWeight',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[_COSTFUNCTIONCONFIG_TARGETCLASS],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=54,
    serialized_end=614)
_COSTFUNCTIONCONFIG_TARGETCLASS_OBJECTIVE.containing_type = _COSTFUNCTIONCONFIG_TARGETCLASS
_COSTFUNCTIONCONFIG_TARGETCLASS.fields_by_name[
    'objectives'].message_type = _COSTFUNCTIONCONFIG_TARGETCLASS_OBJECTIVE
_COSTFUNCTIONCONFIG_TARGETCLASS.containing_type = _COSTFUNCTIONCONFIG
_COSTFUNCTIONCONFIG.fields_by_name[
    'target_classes'].message_type = _COSTFUNCTIONCONFIG_TARGETCLASS
DESCRIPTOR.message_types_by_name['CostFunctionConfig'] = _COSTFUNCTIONCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
CostFunctionConfig = _reflection.GeneratedProtocolMessageType(
    'CostFunctionConfig', (_message.Message,),
    dict(TargetClass=(_reflection.GeneratedProtocolMessageType(
        'TargetClass', (_message.Message,),
        dict(Objective=(_reflection.GeneratedProtocolMessageType(
            'Objective', (_message.Message,),
            dict(
                DESCRIPTOR=_COSTFUNCTIONCONFIG_TARGETCLASS_OBJECTIVE,
                __module__='iva.detectnet_v2.proto.cost_function_config_pb2'))),
             DESCRIPTOR=_COSTFUNCTIONCONFIG_TARGETCLASS,
             __module__='iva.detectnet_v2.proto.cost_function_config_pb2'))),
         DESCRIPTOR=_COSTFUNCTIONCONFIG,
         __module__='iva.detectnet_v2.proto.cost_function_config_pb2'))
_sym_db.RegisterMessage(CostFunctionConfig)
_sym_db.RegisterMessage(CostFunctionConfig.TargetClass)
_sym_db.RegisterMessage(CostFunctionConfig.TargetClass.Objective)
# okay decompiling cost_function_config_pb2.pyc
