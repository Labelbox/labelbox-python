# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/bbox_rasterizer_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 8471 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/bbox_rasterizer_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n3iva/detectnet_v2/proto/bbox_rasterizer_config.proto"Ò\x03\n\x14BboxRasterizerConfig\x12\\\n\x13target_class_config\x18\x01 \x03(\x0b2,.BboxRasterizerConfig.TargetClassConfigEntryR\x11targetClassConfig\x12\'\n\x0fdeadzone_radius\x18\x02 \x01(\x02R\x0edeadzoneRadius\x1aÃ\x01\n\x11TargetClassConfig\x12 \n\x0ccov_center_x\x18\x01 \x01(\x02R\ncovCenterX\x12 \n\x0ccov_center_y\x18\x02 \x01(\x02R\ncovCenterY\x12 \n\x0ccov_radius_x\x18\x03 \x01(\x02R\ncovRadiusX\x12 \n\x0ccov_radius_y\x18\x04 \x01(\x02R\ncovRadiusY\x12&\n\x0fbbox_min_radius\x18\x05 \x01(\x02R\rbboxMinRadius\x1am\n\x16TargetClassConfigEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12=\n\x05value\x18\x02 \x01(\x0b2\'.BboxRasterizerConfig.TargetClassConfigR\x05value:\x028\x01b\x06proto3'
    )))
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIG = _descriptor.Descriptor(
    name='TargetClassConfig',
    full_name='BboxRasterizerConfig.TargetClassConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='cov_center_x',
            full_name='BboxRasterizerConfig.TargetClassConfig.cov_center_x',
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
            json_name='covCenterX',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='cov_center_y',
            full_name='BboxRasterizerConfig.TargetClassConfig.cov_center_y',
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
            json_name='covCenterY',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='cov_radius_x',
            full_name='BboxRasterizerConfig.TargetClassConfig.cov_radius_x',
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
            json_name='covRadiusX',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='cov_radius_y',
            full_name='BboxRasterizerConfig.TargetClassConfig.cov_radius_y',
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
            json_name='covRadiusY',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='bbox_min_radius',
            full_name='BboxRasterizerConfig.TargetClassConfig.bbox_min_radius',
            index=4,
            number=5,
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
            json_name='bboxMinRadius',
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
    serialized_start=216,
    serialized_end=411)
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY = _descriptor.Descriptor(
    name='TargetClassConfigEntry',
    full_name='BboxRasterizerConfig.TargetClassConfigEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='key',
            full_name='BboxRasterizerConfig.TargetClassConfigEntry.key',
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
            json_name='key',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='value',
            full_name='BboxRasterizerConfig.TargetClassConfigEntry.value',
            index=1,
            number=2,
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
            json_name='value',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=(_b('8\x01')),
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=413,
    serialized_end=522)
_BBOXRASTERIZERCONFIG = _descriptor.Descriptor(
    name='BboxRasterizerConfig',
    full_name='BboxRasterizerConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='target_class_config',
            full_name='BboxRasterizerConfig.target_class_config',
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
            json_name='targetClassConfig',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='deadzone_radius',
            full_name='BboxRasterizerConfig.deadzone_radius',
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
            json_name='deadzoneRadius',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[
        _BBOXRASTERIZERCONFIG_TARGETCLASSCONFIG,
        _BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=56,
    serialized_end=522)
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIG.containing_type = _BBOXRASTERIZERCONFIG
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY.fields_by_name[
    'value'].message_type = _BBOXRASTERIZERCONFIG_TARGETCLASSCONFIG
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY.containing_type = _BBOXRASTERIZERCONFIG
_BBOXRASTERIZERCONFIG.fields_by_name[
    'target_class_config'].message_type = _BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY
DESCRIPTOR.message_types_by_name['BboxRasterizerConfig'] = _BBOXRASTERIZERCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
BboxRasterizerConfig = _reflection.GeneratedProtocolMessageType(
    'BboxRasterizerConfig', (_message.Message,),
    dict(TargetClassConfig=(_reflection.GeneratedProtocolMessageType(
        'TargetClassConfig', (_message.Message,),
        dict(DESCRIPTOR=_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIG,
             __module__='iva.detectnet_v2.proto.bbox_rasterizer_config_pb2'))),
         TargetClassConfigEntry=(_reflection.GeneratedProtocolMessageType(
             'TargetClassConfigEntry', (_message.Message,),
             dict(DESCRIPTOR=_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY,
                  __module__='iva.detectnet_v2.proto.bbox_rasterizer_config_pb2'
                 ))),
         DESCRIPTOR=_BBOXRASTERIZERCONFIG,
         __module__='iva.detectnet_v2.proto.bbox_rasterizer_config_pb2'))
_sym_db.RegisterMessage(BboxRasterizerConfig)
_sym_db.RegisterMessage(BboxRasterizerConfig.TargetClassConfig)
_sym_db.RegisterMessage(BboxRasterizerConfig.TargetClassConfigEntry)
_BBOXRASTERIZERCONFIG_TARGETCLASSCONFIGENTRY._options = None
# okay decompiling bbox_rasterizer_config_pb2.pyc
