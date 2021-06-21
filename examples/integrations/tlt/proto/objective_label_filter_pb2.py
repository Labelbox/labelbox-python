# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/objective_label_filter_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 6436 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
from proto import label_filter_pb2 as iva_dot_detectnet__v2_dot_proto_dot_label__filter__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/objective_label_filter.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n3iva/detectnet_v2/proto/objective_label_filter.proto\x1a)iva/detectnet_v2/proto/label_filter.proto"\x91\x03\n\x14ObjectiveLabelFilter\x12u\n\x1eobjective_label_filter_configs\x18\x01 \x03(\x0b20.ObjectiveLabelFilter.ObjectiveLabelFilterConfigR\x1bobjectiveLabelFilterConfigs\x12\'\n\x0fmask_multiplier\x18\x02 \x01(\x02R\x0emaskMultiplier\x122\n\x15preserve_ground_truth\x18\x03 \x01(\x08R\x13preserveGroundTruth\x1a¤\x01\n\x1aObjectiveLabelFilterConfig\x12/\n\x0clabel_filter\x18\x01 \x01(\x0b2\x0c.LabelFilterR\x0blabelFilter\x12,\n\x12target_class_names\x18\x02 \x03(\tR\x10targetClassNames\x12\'\n\x0fobjective_names\x18\x03 \x03(\tR\x0eobjectiveNamesb\x06proto3'
    )),
    dependencies=[
        iva_dot_detectnet__v2_dot_proto_dot_label__filter__pb2.DESCRIPTOR
    ])
_OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG = _descriptor.Descriptor(
    name='ObjectiveLabelFilterConfig',
    full_name='ObjectiveLabelFilter.ObjectiveLabelFilterConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='label_filter',
            full_name=
            'ObjectiveLabelFilter.ObjectiveLabelFilterConfig.label_filter',
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
            json_name='labelFilter',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='target_class_names',
            full_name=
            'ObjectiveLabelFilter.ObjectiveLabelFilterConfig.target_class_names',
            index=1,
            number=2,
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
            json_name='targetClassNames',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='objective_names',
            full_name=
            'ObjectiveLabelFilter.ObjectiveLabelFilterConfig.objective_names',
            index=2,
            number=3,
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
            json_name='objectiveNames',
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
    serialized_start=336,
    serialized_end=500)
_OBJECTIVELABELFILTER = _descriptor.Descriptor(
    name='ObjectiveLabelFilter',
    full_name='ObjectiveLabelFilter',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='objective_label_filter_configs',
            full_name='ObjectiveLabelFilter.objective_label_filter_configs',
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
            json_name='objectiveLabelFilterConfigs',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='mask_multiplier',
            full_name='ObjectiveLabelFilter.mask_multiplier',
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
            json_name='maskMultiplier',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='preserve_ground_truth',
            full_name='ObjectiveLabelFilter.preserve_ground_truth',
            index=2,
            number=3,
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
            json_name='preserveGroundTruth',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[_OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=99,
    serialized_end=500)
_OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG.fields_by_name[
    'label_filter'].message_type = iva_dot_detectnet__v2_dot_proto_dot_label__filter__pb2._LABELFILTER
_OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG.containing_type = _OBJECTIVELABELFILTER
_OBJECTIVELABELFILTER.fields_by_name[
    'objective_label_filter_configs'].message_type = _OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG
DESCRIPTOR.message_types_by_name['ObjectiveLabelFilter'] = _OBJECTIVELABELFILTER
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
ObjectiveLabelFilter = _reflection.GeneratedProtocolMessageType(
    'ObjectiveLabelFilter', (_message.Message,),
    dict(ObjectiveLabelFilterConfig=(_reflection.GeneratedProtocolMessageType(
        'ObjectiveLabelFilterConfig', (_message.Message,),
        dict(DESCRIPTOR=_OBJECTIVELABELFILTER_OBJECTIVELABELFILTERCONFIG,
             __module__='iva.detectnet_v2.proto.objective_label_filter_pb2'))),
         DESCRIPTOR=_OBJECTIVELABELFILTER,
         __module__='iva.detectnet_v2.proto.objective_label_filter_pb2'))
_sym_db.RegisterMessage(ObjectiveLabelFilter)
_sym_db.RegisterMessage(ObjectiveLabelFilter.ObjectiveLabelFilterConfig)
# okay decompiling objective_label_filter_pb2.pyc
