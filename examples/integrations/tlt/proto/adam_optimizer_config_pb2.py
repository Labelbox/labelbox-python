# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54) 
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/adam_optimizer_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 3039 bytes
import sys
_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(name='iva/detectnet_v2/proto/adam_optimizer_config.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=(_b('\n2iva/detectnet_v2/proto/adam_optimizer_config.proto"[\n\x13AdamOptimizerConfig\x12\x18\n\x07epsilon\x18\x01 \x01(\x02R\x07epsilon\x12\x14\n\x05beta1\x18\x02 \x01(\x02R\x05beta1\x12\x14\n\x05beta2\x18\x03 \x01(\x02R\x05beta2b\x06proto3')))
_ADAMOPTIMIZERCONFIG = _descriptor.Descriptor(name='AdamOptimizerConfig',
  full_name='AdamOptimizerConfig',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
 _descriptor.FieldDescriptor(name='epsilon',
   full_name='AdamOptimizerConfig.epsilon',
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
   json_name='epsilon',
   file=DESCRIPTOR),
 _descriptor.FieldDescriptor(name='beta1',
   full_name='AdamOptimizerConfig.beta1',
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
   json_name='beta1',
   file=DESCRIPTOR),
 _descriptor.FieldDescriptor(name='beta2',
   full_name='AdamOptimizerConfig.beta2',
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
   json_name='beta2',
   file=DESCRIPTOR)],
  extensions=[],
  nested_types=[],
  enum_types=[],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[],
  serialized_start=54,
  serialized_end=145)
DESCRIPTOR.message_types_by_name['AdamOptimizerConfig'] = _ADAMOPTIMIZERCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
AdamOptimizerConfig = _reflection.GeneratedProtocolMessageType('AdamOptimizerConfig', (_message.Message,), dict(DESCRIPTOR=_ADAMOPTIMIZERCONFIG,
  __module__='iva.detectnet_v2.proto.adam_optimizer_config_pb2'))
_sym_db.RegisterMessage(AdamOptimizerConfig)
# okay decompiling adam_optimizer_config_pb2.pyc
