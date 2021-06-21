# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/visualizer_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 6773 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/visualizer_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n.iva/detectnet_v2/proto/visualizer_config.proto"Ô\x02\n\x10VisualizerConfig\x12\x18\n\x07enabled\x18\x01 \x01(\x08R\x07enabled\x12\x1d\n\nnum_images\x18\x02 \x01(\rR\tnumImages\x12X\n\x13target_class_config\x18\x03 \x03(\x0b2(.VisualizerConfig.TargetClassConfigEntryR\x11targetClassConfig\x1aB\n\x11TargetClassConfig\x12-\n\x12coverage_threshold\x18\x01 \x01(\x02R\x11coverageThreshold\x1ai\n\x16TargetClassConfigEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x129\n\x05value\x18\x02 \x01(\x0b2#.VisualizerConfig.TargetClassConfigR\x05value:\x028\x01b\x06proto3'
    )))
_VISUALIZERCONFIG_TARGETCLASSCONFIG = _descriptor.Descriptor(
    name='TargetClassConfig',
    full_name='VisualizerConfig.TargetClassConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='coverage_threshold',
            full_name='VisualizerConfig.TargetClassConfig.coverage_threshold',
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
            json_name='coverageThreshold',
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
    serialized_start=218,
    serialized_end=284)
_VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY = _descriptor.Descriptor(
    name='TargetClassConfigEntry',
    full_name='VisualizerConfig.TargetClassConfigEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='key',
            full_name='VisualizerConfig.TargetClassConfigEntry.key',
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
            full_name='VisualizerConfig.TargetClassConfigEntry.value',
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
    serialized_start=286,
    serialized_end=391)
_VISUALIZERCONFIG = _descriptor.Descriptor(
    name='VisualizerConfig',
    full_name='VisualizerConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(name='enabled',
                                    full_name='VisualizerConfig.enabled',
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
        _descriptor.FieldDescriptor(name='num_images',
                                    full_name='VisualizerConfig.num_images',
                                    index=1,
                                    number=2,
                                    type=13,
                                    cpp_type=3,
                                    label=1,
                                    has_default_value=False,
                                    default_value=0,
                                    message_type=None,
                                    enum_type=None,
                                    containing_type=None,
                                    is_extension=False,
                                    extension_scope=None,
                                    serialized_options=None,
                                    json_name='numImages',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='target_class_config',
            full_name='VisualizerConfig.target_class_config',
            index=2,
            number=3,
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
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[
        _VISUALIZERCONFIG_TARGETCLASSCONFIG,
        _VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=51,
    serialized_end=391)
_VISUALIZERCONFIG_TARGETCLASSCONFIG.containing_type = _VISUALIZERCONFIG
_VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY.fields_by_name[
    'value'].message_type = _VISUALIZERCONFIG_TARGETCLASSCONFIG
_VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY.containing_type = _VISUALIZERCONFIG
_VISUALIZERCONFIG.fields_by_name[
    'target_class_config'].message_type = _VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY
DESCRIPTOR.message_types_by_name['VisualizerConfig'] = _VISUALIZERCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
VisualizerConfig = _reflection.GeneratedProtocolMessageType(
    'VisualizerConfig', (_message.Message,),
    dict(TargetClassConfig=(_reflection.GeneratedProtocolMessageType(
        'TargetClassConfig', (_message.Message,),
        dict(DESCRIPTOR=_VISUALIZERCONFIG_TARGETCLASSCONFIG,
             __module__='iva.detectnet_v2.proto.visualizer_config_pb2'))),
         TargetClassConfigEntry=(_reflection.GeneratedProtocolMessageType(
             'TargetClassConfigEntry', (_message.Message,),
             dict(DESCRIPTOR=_VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY,
                  __module__='iva.detectnet_v2.proto.visualizer_config_pb2'))),
         DESCRIPTOR=_VISUALIZERCONFIG,
         __module__='iva.detectnet_v2.proto.visualizer_config_pb2'))
_sym_db.RegisterMessage(VisualizerConfig)
_sym_db.RegisterMessage(VisualizerConfig.TargetClassConfig)
_sym_db.RegisterMessage(VisualizerConfig.TargetClassConfigEntry)
_VISUALIZERCONFIG_TARGETCLASSCONFIGENTRY._options = None
# okay decompiling visualizer_config_pb2.pyc
