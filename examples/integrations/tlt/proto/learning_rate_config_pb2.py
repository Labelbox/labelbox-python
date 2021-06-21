# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54) 
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/learning_rate_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 3285 bytes
import sys
_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
_sym_db = _symbol_database.Default()
from proto import soft_start_annealing_schedule_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_soft__start__annealing__schedule__config__pb2
DESCRIPTOR = _descriptor.FileDescriptor(name='iva/detectnet_v2/proto/learning_rate_config.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=(_b('\n1iva/detectnet_v2/proto/learning_rate_config.proto\x1aAiva/detectnet_v2/proto/soft_start_annealing_schedule_config.proto"\x8d\x01\n\x12LearningRateConfig\x12f\n\x1dsoft_start_annealing_schedule\x18\x01 \x01(\x0b2!.SoftStartAnnealingScheduleConfigH\x00R\x1asoftStartAnnealingScheduleB\x0f\n\rlearning_rateb\x06proto3')),
  dependencies=[
 iva_dot_detectnet__v2_dot_proto_dot_soft__start__annealing__schedule__config__pb2.DESCRIPTOR])
_LEARNINGRATECONFIG = _descriptor.Descriptor(name='LearningRateConfig',
  full_name='LearningRateConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
 _descriptor.FieldDescriptor(name='soft_start_annealing_schedule',
   full_name='LearningRateConfig.soft_start_annealing_schedule',
   index=0,
   number=1,
   type=11,
   cpp_type=10,
   label=1,
   has_default_value=False,
   default_value=None,
   message_type=None,
   enum_type=None,
   containing_type=None,
   is_extension=False,
   extension_scope=None,
   serialized_options=None,
   json_name='softStartAnnealingSchedule',
   file=DESCRIPTOR)],
  extensions=[],
  nested_types=[],
  enum_types=[],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
 _descriptor.OneofDescriptor(name='learning_rate',
   full_name='LearningRateConfig.learning_rate',
   index=0,
   containing_type=None,
   fields=[])],
  serialized_start=121,
  serialized_end=262)
_LEARNINGRATECONFIG.fields_by_name['soft_start_annealing_schedule'].message_type = iva_dot_detectnet__v2_dot_proto_dot_soft__start__annealing__schedule__config__pb2._SOFTSTARTANNEALINGSCHEDULECONFIG
_LEARNINGRATECONFIG.oneofs_by_name['learning_rate'].fields.append(_LEARNINGRATECONFIG.fields_by_name['soft_start_annealing_schedule'])
_LEARNINGRATECONFIG.fields_by_name['soft_start_annealing_schedule'].containing_oneof = _LEARNINGRATECONFIG.oneofs_by_name['learning_rate']
DESCRIPTOR.message_types_by_name['LearningRateConfig'] = _LEARNINGRATECONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
LearningRateConfig = _reflection.GeneratedProtocolMessageType('LearningRateConfig', (_message.Message,), dict(DESCRIPTOR=_LEARNINGRATECONFIG,
  __module__='iva.detectnet_v2.proto.learning_rate_config_pb2'))
_sym_db.RegisterMessage(LearningRateConfig)
# okay decompiling learning_rate_config_pb2.pyc
