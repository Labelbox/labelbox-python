# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/soft_start_annealing_schedule_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 3817 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/soft_start_annealing_schedule_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\nAiva/detectnet_v2/proto/soft_start_annealing_schedule_config.proto"·\x01\n SoftStartAnnealingScheduleConfig\x12*\n\x11min_learning_rate\x18\x01 \x01(\x02R\x0fminLearningRate\x12*\n\x11max_learning_rate\x18\x02 \x01(\x02R\x0fmaxLearningRate\x12\x1d\n\nsoft_start\x18\x03 \x01(\x02R\tsoftStart\x12\x1c\n\tannealing\x18\x04 \x01(\x02R\tannealingb\x06proto3'
    )))
_SOFTSTARTANNEALINGSCHEDULECONFIG = _descriptor.Descriptor(
    name='SoftStartAnnealingScheduleConfig',
    full_name='SoftStartAnnealingScheduleConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='min_learning_rate',
            full_name='SoftStartAnnealingScheduleConfig.min_learning_rate',
            index=0,
            number=1,
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
            json_name='minLearningRate',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='max_learning_rate',
            full_name='SoftStartAnnealingScheduleConfig.max_learning_rate',
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
            json_name='maxLearningRate',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='soft_start',
            full_name='SoftStartAnnealingScheduleConfig.soft_start',
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
            json_name='softStart',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='annealing',
            full_name='SoftStartAnnealingScheduleConfig.annealing',
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
            json_name='annealing',
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
    serialized_start=70,
    serialized_end=253)
DESCRIPTOR.message_types_by_name[
    'SoftStartAnnealingScheduleConfig'] = _SOFTSTARTANNEALINGSCHEDULECONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
SoftStartAnnealingScheduleConfig = _reflection.GeneratedProtocolMessageType(
    'SoftStartAnnealingScheduleConfig', (_message.Message,),
    dict(DESCRIPTOR=_SOFTSTARTANNEALINGSCHEDULECONFIG,
         __module__=
         'iva.detectnet_v2.proto.soft_start_annealing_schedule_config_pb2'))
_sym_db.RegisterMessage(SoftStartAnnealingScheduleConfig)
# okay decompiling soft_start_annealing_schedule_config_pb2.pyc
