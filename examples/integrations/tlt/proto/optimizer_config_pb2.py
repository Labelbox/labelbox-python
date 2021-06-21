# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54) 
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/optimizer_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 2905 bytes
import sys
_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
_sym_db = _symbol_database.Default()
from proto import adam_optimizer_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_adam__optimizer__config__pb2
DESCRIPTOR = _descriptor.FileDescriptor(name='iva/detectnet_v2/proto/optimizer_config.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=(_b('\n-iva/detectnet_v2/proto/optimizer_config.proto\x1a2iva/detectnet_v2/proto/adam_optimizer_config.proto"J\n\x0fOptimizerConfig\x12*\n\x04adam\x18\x01 \x01(\x0b2\x14.AdamOptimizerConfigH\x00R\x04adamB\x0b\n\toptimizerb\x06proto3')),
  dependencies=[
 iva_dot_detectnet__v2_dot_proto_dot_adam__optimizer__config__pb2.DESCRIPTOR])
_OPTIMIZERCONFIG = _descriptor.Descriptor(name='OptimizerConfig',
  full_name='OptimizerConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
 _descriptor.FieldDescriptor(name='adam',
   full_name='OptimizerConfig.adam',
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
   json_name='adam',
   file=DESCRIPTOR)],
  extensions=[],
  nested_types=[],
  enum_types=[],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
 _descriptor.OneofDescriptor(name='optimizer',
   full_name='OptimizerConfig.optimizer',
   index=0,
   containing_type=None,
   fields=[])],
  serialized_start=101,
  serialized_end=175)
_OPTIMIZERCONFIG.fields_by_name['adam'].message_type = iva_dot_detectnet__v2_dot_proto_dot_adam__optimizer__config__pb2._ADAMOPTIMIZERCONFIG
_OPTIMIZERCONFIG.oneofs_by_name['optimizer'].fields.append(_OPTIMIZERCONFIG.fields_by_name['adam'])
_OPTIMIZERCONFIG.fields_by_name['adam'].containing_oneof = _OPTIMIZERCONFIG.oneofs_by_name['optimizer']
DESCRIPTOR.message_types_by_name['OptimizerConfig'] = _OPTIMIZERCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
OptimizerConfig = _reflection.GeneratedProtocolMessageType('OptimizerConfig', (_message.Message,), dict(DESCRIPTOR=_OPTIMIZERCONFIG,
  __module__='iva.detectnet_v2.proto.optimizer_config_pb2'))
_sym_db.RegisterMessage(OptimizerConfig)
# okay decompiling optimizer_config_pb2.pyc
