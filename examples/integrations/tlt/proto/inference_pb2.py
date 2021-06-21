# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/inference_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 14338 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
from proto import inferencer_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_inferencer__config__pb2
from proto import postprocessing_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_postprocessing__config__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/inference.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n&iva/detectnet_v2/proto/inference.proto\x1a.iva/detectnet_v2/proto/inferencer_config.proto\x1a2iva/detectnet_v2/proto/postprocessing_config.proto"£\x02\n\x1aClasswiseBboxHandlerConfig\x12>\n\x11clustering_config\x18\x01 \x01(\x0b2\x11.ClusteringConfigR\x10clusteringConfig\x12)\n\x10confidence_model\x18\x02 \x01(\tR\x0fconfidenceModel\x12\x1d\n\noutput_map\x18\x03 \x01(\tR\toutputMap\x12D\n\nbbox_color\x18\x07 \x01(\x0b2%.ClasswiseBboxHandlerConfig.BboxColorR\tbboxColor\x1a5\n\tBboxColor\x12\x0c\n\x01R\x18\x01 \x01(\x05R\x01R\x12\x0c\n\x01G\x18\x02 \x01(\x05R\x01G\x12\x0c\n\x01B\x18\x03 \x01(\x05R\x01B"\x96\x03\n\x11BboxHandlerConfig\x12\x1d\n\nkitti_dump\x18\x01 \x01(\x08R\tkittiDump\x12\'\n\x0fdisable_overlay\x18\x02 \x01(\x08R\x0edisableOverlay\x12+\n\x11overlay_linewidth\x18\x03 \x01(\x05R\x10overlayLinewidth\x12u\n\x1dclasswise_bbox_handler_config\x18\x04 \x03(\x0b22.BboxHandlerConfig.ClasswiseBboxHandlerConfigEntryR\x1aclasswiseBboxHandlerConfig\x12)\n\x10postproc_classes\x18\x05 \x03(\tR\x0fpostprocClasses\x1aj\n\x1fClasswiseBboxHandlerConfigEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x121\n\x05value\x18\x02 \x01(\x0b2\x1b.ClasswiseBboxHandlerConfigR\x05value:\x028\x01"\x8f\x01\n\tInference\x12>\n\x11inferencer_config\x18\x01 \x01(\x0b2\x11.InferencerConfigR\x10inferencerConfig\x12B\n\x13bbox_handler_config\x18\x02 \x01(\x0b2\x12.BboxHandlerConfigR\x11bboxHandlerConfigb\x06proto3'
    )),
    dependencies=[
        iva_dot_detectnet__v2_dot_proto_dot_inferencer__config__pb2.DESCRIPTOR,
        iva_dot_detectnet__v2_dot_proto_dot_postprocessing__config__pb2.
        DESCRIPTOR
    ])
_CLASSWISEBBOXHANDLERCONFIG_BBOXCOLOR = _descriptor.Descriptor(
    name='BboxColor',
    full_name='ClasswiseBboxHandlerConfig.BboxColor',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='R',
            full_name='ClasswiseBboxHandlerConfig.BboxColor.R',
            index=0,
            number=1,
            type=5,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='R',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='G',
            full_name='ClasswiseBboxHandlerConfig.BboxColor.G',
            index=1,
            number=2,
            type=5,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='G',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='B',
            full_name='ClasswiseBboxHandlerConfig.BboxColor.B',
            index=2,
            number=3,
            type=5,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='B',
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
    serialized_start=381,
    serialized_end=434)
_CLASSWISEBBOXHANDLERCONFIG = _descriptor.Descriptor(
    name='ClasswiseBboxHandlerConfig',
    full_name='ClasswiseBboxHandlerConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='clustering_config',
            full_name='ClasswiseBboxHandlerConfig.clustering_config',
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
            json_name='clusteringConfig',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='confidence_model',
            full_name='ClasswiseBboxHandlerConfig.confidence_model',
            index=1,
            number=2,
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
            json_name='confidenceModel',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='output_map',
            full_name='ClasswiseBboxHandlerConfig.output_map',
            index=2,
            number=3,
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
            json_name='outputMap',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='bbox_color',
            full_name='ClasswiseBboxHandlerConfig.bbox_color',
            index=3,
            number=7,
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
            json_name='bboxColor',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[_CLASSWISEBBOXHANDLERCONFIG_BBOXCOLOR],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=143,
    serialized_end=434)
_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY = _descriptor.Descriptor(
    name='ClasswiseBboxHandlerConfigEntry',
    full_name='BboxHandlerConfig.ClasswiseBboxHandlerConfigEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='key',
            full_name='BboxHandlerConfig.ClasswiseBboxHandlerConfigEntry.key',
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
            full_name='BboxHandlerConfig.ClasswiseBboxHandlerConfigEntry.value',
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
    serialized_start=737,
    serialized_end=843)
_BBOXHANDLERCONFIG = _descriptor.Descriptor(
    name='BboxHandlerConfig',
    full_name='BboxHandlerConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(name='kitti_dump',
                                    full_name='BboxHandlerConfig.kitti_dump',
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
                                    json_name='kittiDump',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='disable_overlay',
            full_name='BboxHandlerConfig.disable_overlay',
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
            json_name='disableOverlay',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='overlay_linewidth',
            full_name='BboxHandlerConfig.overlay_linewidth',
            index=2,
            number=3,
            type=5,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='overlayLinewidth',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='classwise_bbox_handler_config',
            full_name='BboxHandlerConfig.classwise_bbox_handler_config',
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
            json_name='classwiseBboxHandlerConfig',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='postproc_classes',
            full_name='BboxHandlerConfig.postproc_classes',
            index=4,
            number=5,
            type=9,
            cpp_type=9,
            label=3,
            has_default_value=False,
            default_value=[],
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='postprocClasses',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=437,
    serialized_end=843)
_INFERENCE = _descriptor.Descriptor(
    name='Inference',
    full_name='Inference',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(name='inferencer_config',
                                    full_name='Inference.inferencer_config',
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
                                    json_name='inferencerConfig',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='bbox_handler_config',
                                    full_name='Inference.bbox_handler_config',
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
                                    json_name='bboxHandlerConfig',
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
    serialized_start=846,
    serialized_end=989)
_CLASSWISEBBOXHANDLERCONFIG_BBOXCOLOR.containing_type = _CLASSWISEBBOXHANDLERCONFIG
_CLASSWISEBBOXHANDLERCONFIG.fields_by_name[
    'clustering_config'].message_type = iva_dot_detectnet__v2_dot_proto_dot_postprocessing__config__pb2._CLUSTERINGCONFIG
_CLASSWISEBBOXHANDLERCONFIG.fields_by_name[
    'bbox_color'].message_type = _CLASSWISEBBOXHANDLERCONFIG_BBOXCOLOR
_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY.fields_by_name[
    'value'].message_type = _CLASSWISEBBOXHANDLERCONFIG
_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY.containing_type = _BBOXHANDLERCONFIG
_BBOXHANDLERCONFIG.fields_by_name[
    'classwise_bbox_handler_config'].message_type = _BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY
_INFERENCE.fields_by_name[
    'inferencer_config'].message_type = iva_dot_detectnet__v2_dot_proto_dot_inferencer__config__pb2._INFERENCERCONFIG
_INFERENCE.fields_by_name[
    'bbox_handler_config'].message_type = _BBOXHANDLERCONFIG
DESCRIPTOR.message_types_by_name[
    'ClasswiseBboxHandlerConfig'] = _CLASSWISEBBOXHANDLERCONFIG
DESCRIPTOR.message_types_by_name['BboxHandlerConfig'] = _BBOXHANDLERCONFIG
DESCRIPTOR.message_types_by_name['Inference'] = _INFERENCE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
ClasswiseBboxHandlerConfig = _reflection.GeneratedProtocolMessageType(
    'ClasswiseBboxHandlerConfig', (_message.Message,),
    dict(BboxColor=(_reflection.GeneratedProtocolMessageType(
        'BboxColor', (_message.Message,),
        dict(DESCRIPTOR=_CLASSWISEBBOXHANDLERCONFIG_BBOXCOLOR,
             __module__='iva.detectnet_v2.proto.inference_pb2'))),
         DESCRIPTOR=_CLASSWISEBBOXHANDLERCONFIG,
         __module__='iva.detectnet_v2.proto.inference_pb2'))
_sym_db.RegisterMessage(ClasswiseBboxHandlerConfig)
_sym_db.RegisterMessage(ClasswiseBboxHandlerConfig.BboxColor)
BboxHandlerConfig = _reflection.GeneratedProtocolMessageType(
    'BboxHandlerConfig', (_message.Message,),
    dict(ClasswiseBboxHandlerConfigEntry=(
        _reflection.GeneratedProtocolMessageType(
            'ClasswiseBboxHandlerConfigEntry', (_message.Message,),
            dict(DESCRIPTOR=_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY,
                 __module__='iva.detectnet_v2.proto.inference_pb2'))),
         DESCRIPTOR=_BBOXHANDLERCONFIG,
         __module__='iva.detectnet_v2.proto.inference_pb2'))
_sym_db.RegisterMessage(BboxHandlerConfig)
_sym_db.RegisterMessage(BboxHandlerConfig.ClasswiseBboxHandlerConfigEntry)
Inference = _reflection.GeneratedProtocolMessageType(
    'Inference', (_message.Message,),
    dict(DESCRIPTOR=_INFERENCE,
         __module__='iva.detectnet_v2.proto.inference_pb2'))
_sym_db.RegisterMessage(Inference)
_BBOXHANDLERCONFIG_CLASSWISEBBOXHANDLERCONFIGENTRY._options = None
# okay decompiling inference_pb2.pyc
