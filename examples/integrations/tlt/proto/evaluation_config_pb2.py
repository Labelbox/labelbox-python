# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/evaluation_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 12796 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/evaluation_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n.iva/detectnet_v2/proto/evaluation_config.proto"ð\x06\n\x10EvaluationConfig\x12I\n!validation_period_during_training\x18\x01 \x01(\rR\x1evalidationPeriodDuringTraining\x124\n\x16first_validation_epoch\x18\x02 \x01(\rR\x14firstValidationEpoch\x12\x8d\x01\n&minimum_detection_ground_truth_overlap\x18\x03 \x03(\x0b29.EvaluationConfig.MinimumDetectionGroundTruthOverlapEntryR"minimumDetectionGroundTruthOverlap\x12^\n\x15evaluation_box_config\x18\x04 \x03(\x0b2*.EvaluationConfig.EvaluationBoxConfigEntryR\x13evaluationBoxConfig\x12O\n\x16average_precision_mode\x18\x05 \x01(\x0e2\x19.EvaluationConfig.AP_MODER\x14averagePrecisionMode\x1aU\n\'MinimumDetectionGroundTruthOverlapEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12\x14\n\x05value\x18\x02 \x01(\x02R\x05value:\x028\x01\x1a\xad\x01\n\x13EvaluationBoxConfig\x12%\n\x0eminimum_height\x18\x01 \x01(\x05R\rminimumHeight\x12%\n\x0emaximum_height\x18\x02 \x01(\x05R\rmaximumHeight\x12#\n\rminimum_width\x18\x03 \x01(\x05R\x0cminimumWidth\x12#\n\rmaximum_width\x18\x04 \x01(\x05R\x0cmaximumWidth\x1am\n\x18EvaluationBoxConfigEntry\x12\x10\n\x03key\x18\x01 \x01(\tR\x03key\x12;\n\x05value\x18\x02 \x01(\x0b2%.EvaluationConfig.EvaluationBoxConfigR\x05value:\x028\x01"$\n\x07AP_MODE\x12\n\n\x06SAMPLE\x10\x00\x12\r\n\tINTEGRATE\x10\x01b\x06proto3'
    )))
_EVALUATIONCONFIG_AP_MODE = _descriptor.EnumDescriptor(
    name='AP_MODE',
    full_name='EvaluationConfig.AP_MODE',
    filename=None,
    file=DESCRIPTOR,
    values=[
        _descriptor.EnumValueDescriptor(name='SAMPLE',
                                        index=0,
                                        number=0,
                                        serialized_options=None,
                                        type=None),
        _descriptor.EnumValueDescriptor(name='INTEGRATE',
                                        index=1,
                                        number=1,
                                        serialized_options=None,
                                        type=None)
    ],
    containing_type=None,
    serialized_options=None,
    serialized_start=895,
    serialized_end=931)
_sym_db.RegisterEnumDescriptor(_EVALUATIONCONFIG_AP_MODE)
_EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY = _descriptor.Descriptor(
    name='MinimumDetectionGroundTruthOverlapEntry',
    full_name='EvaluationConfig.MinimumDetectionGroundTruthOverlapEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='key',
            full_name=
            'EvaluationConfig.MinimumDetectionGroundTruthOverlapEntry.key',
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
            full_name=
            'EvaluationConfig.MinimumDetectionGroundTruthOverlapEntry.value',
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
    serialized_start=521,
    serialized_end=606)
_EVALUATIONCONFIG_EVALUATIONBOXCONFIG = _descriptor.Descriptor(
    name='EvaluationBoxConfig',
    full_name='EvaluationConfig.EvaluationBoxConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='minimum_height',
            full_name='EvaluationConfig.EvaluationBoxConfig.minimum_height',
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
            json_name='minimumHeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='maximum_height',
            full_name='EvaluationConfig.EvaluationBoxConfig.maximum_height',
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
            json_name='maximumHeight',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='minimum_width',
            full_name='EvaluationConfig.EvaluationBoxConfig.minimum_width',
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
            json_name='minimumWidth',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='maximum_width',
            full_name='EvaluationConfig.EvaluationBoxConfig.maximum_width',
            index=3,
            number=4,
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
            json_name='maximumWidth',
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
    serialized_start=609,
    serialized_end=782)
_EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY = _descriptor.Descriptor(
    name='EvaluationBoxConfigEntry',
    full_name='EvaluationConfig.EvaluationBoxConfigEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='key',
            full_name='EvaluationConfig.EvaluationBoxConfigEntry.key',
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
            full_name='EvaluationConfig.EvaluationBoxConfigEntry.value',
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
    serialized_start=784,
    serialized_end=893)
_EVALUATIONCONFIG = _descriptor.Descriptor(
    name='EvaluationConfig',
    full_name='EvaluationConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='validation_period_during_training',
            full_name='EvaluationConfig.validation_period_during_training',
            index=0,
            number=1,
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
            json_name='validationPeriodDuringTraining',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='first_validation_epoch',
            full_name='EvaluationConfig.first_validation_epoch',
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
            json_name='firstValidationEpoch',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='minimum_detection_ground_truth_overlap',
            full_name='EvaluationConfig.minimum_detection_ground_truth_overlap',
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
            json_name='minimumDetectionGroundTruthOverlap',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='evaluation_box_config',
            full_name='EvaluationConfig.evaluation_box_config',
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
            json_name='evaluationBoxConfig',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='average_precision_mode',
            full_name='EvaluationConfig.average_precision_mode',
            index=4,
            number=5,
            type=14,
            cpp_type=8,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            json_name='averagePrecisionMode',
            file=DESCRIPTOR)
    ],
    extensions=[],
    nested_types=[
        _EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY,
        _EVALUATIONCONFIG_EVALUATIONBOXCONFIG,
        _EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY
    ],
    enum_types=[_EVALUATIONCONFIG_AP_MODE],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[],
    serialized_start=51,
    serialized_end=931)
_EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY.containing_type = _EVALUATIONCONFIG
_EVALUATIONCONFIG_EVALUATIONBOXCONFIG.containing_type = _EVALUATIONCONFIG
_EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY.fields_by_name[
    'value'].message_type = _EVALUATIONCONFIG_EVALUATIONBOXCONFIG
_EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY.containing_type = _EVALUATIONCONFIG
_EVALUATIONCONFIG.fields_by_name[
    'minimum_detection_ground_truth_overlap'].message_type = _EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY
_EVALUATIONCONFIG.fields_by_name[
    'evaluation_box_config'].message_type = _EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY
_EVALUATIONCONFIG.fields_by_name[
    'average_precision_mode'].enum_type = _EVALUATIONCONFIG_AP_MODE
_EVALUATIONCONFIG_AP_MODE.containing_type = _EVALUATIONCONFIG
DESCRIPTOR.message_types_by_name['EvaluationConfig'] = _EVALUATIONCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
EvaluationConfig = _reflection.GeneratedProtocolMessageType(
    'EvaluationConfig', (_message.Message,),
    dict(MinimumDetectionGroundTruthOverlapEntry=(
        _reflection.GeneratedProtocolMessageType(
            'MinimumDetectionGroundTruthOverlapEntry', (_message.Message,),
            dict(DESCRIPTOR=
                 _EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY,
                 __module__='iva.detectnet_v2.proto.evaluation_config_pb2'))),
         EvaluationBoxConfig=(_reflection.GeneratedProtocolMessageType(
             'EvaluationBoxConfig', (_message.Message,),
             dict(DESCRIPTOR=_EVALUATIONCONFIG_EVALUATIONBOXCONFIG,
                  __module__='iva.detectnet_v2.proto.evaluation_config_pb2'))),
         EvaluationBoxConfigEntry=(_reflection.GeneratedProtocolMessageType(
             'EvaluationBoxConfigEntry', (_message.Message,),
             dict(DESCRIPTOR=_EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY,
                  __module__='iva.detectnet_v2.proto.evaluation_config_pb2'))),
         DESCRIPTOR=_EVALUATIONCONFIG,
         __module__='iva.detectnet_v2.proto.evaluation_config_pb2'))
_sym_db.RegisterMessage(EvaluationConfig)
_sym_db.RegisterMessage(
    EvaluationConfig.MinimumDetectionGroundTruthOverlapEntry)
_sym_db.RegisterMessage(EvaluationConfig.EvaluationBoxConfig)
_sym_db.RegisterMessage(EvaluationConfig.EvaluationBoxConfigEntry)
_EVALUATIONCONFIG_MINIMUMDETECTIONGROUNDTRUTHOVERLAPENTRY._options = None
_EVALUATIONCONFIG_EVALUATIONBOXCONFIGENTRY._options = None
# okay decompiling evaluation_config_pb2.pyc
