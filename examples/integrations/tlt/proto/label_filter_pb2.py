# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/label_filter_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 11639 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/label_filter.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n)iva/detectnet_v2/proto/label_filter.proto"¸\x05\n\x0bLabelFilter\x12i\n\x1cbbox_dimensions_label_filter\x18\x01 \x01(\x0b2&.LabelFilter.BboxDimensionsLabelFilterH\x00R\x19bboxDimensionsLabelFilter\x12W\n\x16bbox_crop_label_filter\x18\x02 \x01(\x0b2 .LabelFilter.BboxCropLabelFilterH\x00R\x13bboxCropLabelFilter\x12`\n\x19source_class_label_filter\x18\x03 \x01(\x0b2#.LabelFilter.SourceClassLabelFilterH\x00R\x16sourceClassLabelFilter\x1a\x93\x01\n\x19BboxDimensionsLabelFilter\x12\x1b\n\tmin_width\x18\x01 \x01(\x02R\x08minWidth\x12\x1d\n\nmin_height\x18\x02 \x01(\x02R\tminHeight\x12\x1b\n\tmax_width\x18\x03 \x01(\x02R\x08maxWidth\x12\x1d\n\nmax_height\x18\x04 \x01(\x02R\tmaxHeight\x1a\x8d\x01\n\x13BboxCropLabelFilter\x12\x1b\n\tcrop_left\x18\x01 \x01(\x02R\x08cropLeft\x12\x1d\n\ncrop_right\x18\x02 \x01(\x02R\tcropRight\x12\x19\n\x08crop_top\x18\x03 \x01(\x02R\x07cropTop\x12\x1f\n\x0bcrop_bottom\x18\x04 \x01(\x02R\ncropBottom\x1aF\n\x16SourceClassLabelFilter\x12,\n\x12source_class_names\x18\x04 \x03(\tR\x10sourceClassNamesB\x15\n\x13label_filter_paramsb\x06proto3'
    )))
_LABELFILTER_BBOXDIMENSIONSLABELFILTER = _descriptor.Descriptor(
    name='BboxDimensionsLabelFilter',
    full_name='LabelFilter.BboxDimensionsLabelFilter',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='min_width',
            full_name='LabelFilter.BboxDimensionsLabelFilter.min_width',
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
            json_name='minWidth',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='min_height',
            full_name='LabelFilter.BboxDimensionsLabelFilter.min_height',
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
            json_name='minHeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='max_width',
            full_name='LabelFilter.BboxDimensionsLabelFilter.max_width',
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
            json_name='maxWidth',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='max_height',
            full_name='LabelFilter.BboxDimensionsLabelFilter.max_height',
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
            json_name='maxHeight',
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
    serialized_start=356,
    serialized_end=503)
_LABELFILTER_BBOXCROPLABELFILTER = _descriptor.Descriptor(
    name='BboxCropLabelFilter',
    full_name='LabelFilter.BboxCropLabelFilter',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='crop_left',
            full_name='LabelFilter.BboxCropLabelFilter.crop_left',
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
            json_name='cropLeft',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='crop_right',
            full_name='LabelFilter.BboxCropLabelFilter.crop_right',
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
            json_name='cropRight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='crop_top',
            full_name='LabelFilter.BboxCropLabelFilter.crop_top',
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
            json_name='cropTop',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='crop_bottom',
            full_name='LabelFilter.BboxCropLabelFilter.crop_bottom',
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
            json_name='cropBottom',
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
    serialized_start=506,
    serialized_end=647)
_LABELFILTER_SOURCECLASSLABELFILTER = _descriptor.Descriptor(
    name='SourceClassLabelFilter',
    full_name='LabelFilter.SourceClassLabelFilter',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='source_class_names',
            full_name='LabelFilter.SourceClassLabelFilter.source_class_names',
            index=0,
            number=4,
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
            json_name='sourceClassNames',
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
    serialized_start=649,
    serialized_end=719)
_LABELFILTER = _descriptor.Descriptor(
    name='LabelFilter',
    full_name='LabelFilter',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='bbox_dimensions_label_filter',
            full_name='LabelFilter.bbox_dimensions_label_filter',
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
            json_name='bboxDimensionsLabelFilter',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='bbox_crop_label_filter',
            full_name='LabelFilter.bbox_crop_label_filter',
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
            json_name='bboxCropLabelFilter',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='source_class_label_filter',
            full_name='LabelFilter.source_class_label_filter',
            index=2,
            number=3,
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
            json_name='sourceClassLabelFilter',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[
        _LABELFILTER_BBOXDIMENSIONSLABELFILTER,
        _LABELFILTER_BBOXCROPLABELFILTER, _LABELFILTER_SOURCECLASSLABELFILTER
    ],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
        _descriptor.OneofDescriptor(name='label_filter_params',
                                    full_name='LabelFilter.label_filter_params',
                                    index=0,
                                    containing_type=None,
                                    fields=[])
    ],
    serialized_start=46,
    serialized_end=742)
_LABELFILTER_BBOXDIMENSIONSLABELFILTER.containing_type = _LABELFILTER
_LABELFILTER_BBOXCROPLABELFILTER.containing_type = _LABELFILTER
_LABELFILTER_SOURCECLASSLABELFILTER.containing_type = _LABELFILTER
_LABELFILTER.fields_by_name[
    'bbox_dimensions_label_filter'].message_type = _LABELFILTER_BBOXDIMENSIONSLABELFILTER
_LABELFILTER.fields_by_name[
    'bbox_crop_label_filter'].message_type = _LABELFILTER_BBOXCROPLABELFILTER
_LABELFILTER.fields_by_name[
    'source_class_label_filter'].message_type = _LABELFILTER_SOURCECLASSLABELFILTER
_LABELFILTER.oneofs_by_name['label_filter_params'].fields.append(
    _LABELFILTER.fields_by_name['bbox_dimensions_label_filter'])
_LABELFILTER.fields_by_name[
    'bbox_dimensions_label_filter'].containing_oneof = _LABELFILTER.oneofs_by_name[
        'label_filter_params']
_LABELFILTER.oneofs_by_name['label_filter_params'].fields.append(
    _LABELFILTER.fields_by_name['bbox_crop_label_filter'])
_LABELFILTER.fields_by_name[
    'bbox_crop_label_filter'].containing_oneof = _LABELFILTER.oneofs_by_name[
        'label_filter_params']
_LABELFILTER.oneofs_by_name['label_filter_params'].fields.append(
    _LABELFILTER.fields_by_name['source_class_label_filter'])
_LABELFILTER.fields_by_name[
    'source_class_label_filter'].containing_oneof = _LABELFILTER.oneofs_by_name[
        'label_filter_params']
DESCRIPTOR.message_types_by_name['LabelFilter'] = _LABELFILTER
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
LabelFilter = _reflection.GeneratedProtocolMessageType(
    'LabelFilter', (_message.Message,),
    dict(BboxDimensionsLabelFilter=(_reflection.GeneratedProtocolMessageType(
        'BboxDimensionsLabelFilter', (_message.Message,),
        dict(DESCRIPTOR=_LABELFILTER_BBOXDIMENSIONSLABELFILTER,
             __module__='iva.detectnet_v2.proto.label_filter_pb2'))),
         BboxCropLabelFilter=(_reflection.GeneratedProtocolMessageType(
             'BboxCropLabelFilter', (_message.Message,),
             dict(DESCRIPTOR=_LABELFILTER_BBOXCROPLABELFILTER,
                  __module__='iva.detectnet_v2.proto.label_filter_pb2'))),
         SourceClassLabelFilter=(_reflection.GeneratedProtocolMessageType(
             'SourceClassLabelFilter', (_message.Message,),
             dict(DESCRIPTOR=_LABELFILTER_SOURCECLASSLABELFILTER,
                  __module__='iva.detectnet_v2.proto.label_filter_pb2'))),
         DESCRIPTOR=_LABELFILTER,
         __module__='iva.detectnet_v2.proto.label_filter_pb2'))
_sym_db.RegisterMessage(LabelFilter)
_sym_db.RegisterMessage(LabelFilter.BboxDimensionsLabelFilter)
_sym_db.RegisterMessage(LabelFilter.BboxCropLabelFilter)
_sym_db.RegisterMessage(LabelFilter.SourceClassLabelFilter)
# okay decompiling label_filter_pb2.pyc
