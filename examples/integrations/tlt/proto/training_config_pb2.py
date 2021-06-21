# uncompyle6 version 3.7.4
# Python bytecode 3.6 (3379)
# Decompiled from: Python 3.8.6 (default, Dec 16 2020, 17:27:54)
# [GCC 9.3.0]
# Embedded file name: /home/vpraveen/.cache/dazel/_dazel_vpraveen/216c8b41e526c3295d3b802489ac2034/execroot/ai_infra/bazel-out/k8-fastbuild/bin/magnet/packages/iva/build_wheel.runfiles/ai_infra/iva/detectnet_v2/proto/training_config_pb2.py
# Compiled at: 2021-02-05 20:37:47
# Size of source mod 2**32: 6963 bytes
import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
from proto import cost_scaling_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_cost__scaling__config__pb2
from proto import learning_rate_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_learning__rate__config__pb2
from proto import optimizer_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_optimizer__config__pb2
from proto import regularizer_config_pb2 as iva_dot_detectnet__v2_dot_proto_dot_regularizer__config__pb2

DESCRIPTOR = _descriptor.FileDescriptor(
    name='iva/detectnet_v2/proto/training_config.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=(_b(
        '\n,iva/detectnet_v2/proto/training_config.proto\x1a0iva/detectnet_v2/proto/cost_scaling_config.proto\x1a1iva/detectnet_v2/proto/learning_rate_config.proto\x1a-iva/detectnet_v2/proto/optimizer_config.proto\x1a/iva/detectnet_v2/proto/regularizer_config.proto"\x83\x03\n\x0eTrainingConfig\x12+\n\x12batch_size_per_gpu\x18\x01 \x01(\rR\x0fbatchSizePerGpu\x12\x1d\n\nnum_epochs\x18\x02 \x01(\rR\tnumEpochs\x128\n\rlearning_rate\x18\x03 \x01(\x0b2\x13.LearningRateConfigR\x0clearningRate\x124\n\x0bregularizer\x18\x04 \x01(\x0b2\x12.RegularizerConfigR\x0bregularizer\x12.\n\toptimizer\x18\x05 \x01(\x0b2\x10.OptimizerConfigR\toptimizer\x125\n\x0ccost_scaling\x18\x06 \x01(\x0b2\x12.CostScalingConfigR\x0bcostScaling\x12/\n\x13checkpoint_interval\x18\x07 \x01(\rR\x12checkpointInterval\x12\x1d\n\nenable_qat\x18\x08 \x01(\x08R\tenableQatb\x06proto3'
    )),
    dependencies=[
        iva_dot_detectnet__v2_dot_proto_dot_cost__scaling__config__pb2.
        DESCRIPTOR,
        iva_dot_detectnet__v2_dot_proto_dot_learning__rate__config__pb2.
        DESCRIPTOR,
        iva_dot_detectnet__v2_dot_proto_dot_optimizer__config__pb2.DESCRIPTOR,
        iva_dot_detectnet__v2_dot_proto_dot_regularizer__config__pb2.DESCRIPTOR
    ])
_TRAININGCONFIG = _descriptor.Descriptor(
    name='TrainingConfig',
    full_name='TrainingConfig',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='batch_size_per_gpu',
            full_name='TrainingConfig.batch_size_per_gpu',
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
            json_name='batchSizePerGpu',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='num_epochs',
                                    full_name='TrainingConfig.num_epochs',
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
                                    json_name='numEpochs',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='learning_rate',
                                    full_name='TrainingConfig.learning_rate',
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
                                    json_name='learningRate',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='regularizer',
                                    full_name='TrainingConfig.regularizer',
                                    index=3,
                                    number=4,
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
                                    json_name='regularizer',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='optimizer',
                                    full_name='TrainingConfig.optimizer',
                                    index=4,
                                    number=5,
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
                                    json_name='optimizer',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='cost_scaling',
                                    full_name='TrainingConfig.cost_scaling',
                                    index=5,
                                    number=6,
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
                                    json_name='costScaling',
                                    file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='checkpoint_interval',
            full_name='TrainingConfig.checkpoint_interval',
            index=6,
            number=7,
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
            json_name='checkpointInterval',
            file=DESCRIPTOR),
        _descriptor.FieldDescriptor(name='enable_qat',
                                    full_name='TrainingConfig.enable_qat',
                                    index=7,
                                    number=8,
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
                                    json_name='enableQat',
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
    serialized_start=246,
    serialized_end=633)
_TRAININGCONFIG.fields_by_name[
    'learning_rate'].message_type = iva_dot_detectnet__v2_dot_proto_dot_learning__rate__config__pb2._LEARNINGRATECONFIG
_TRAININGCONFIG.fields_by_name[
    'regularizer'].message_type = iva_dot_detectnet__v2_dot_proto_dot_regularizer__config__pb2._REGULARIZERCONFIG
_TRAININGCONFIG.fields_by_name[
    'optimizer'].message_type = iva_dot_detectnet__v2_dot_proto_dot_optimizer__config__pb2._OPTIMIZERCONFIG
_TRAININGCONFIG.fields_by_name[
    'cost_scaling'].message_type = iva_dot_detectnet__v2_dot_proto_dot_cost__scaling__config__pb2._COSTSCALINGCONFIG
DESCRIPTOR.message_types_by_name['TrainingConfig'] = _TRAININGCONFIG
_sym_db.RegisterFileDescriptor(DESCRIPTOR)
TrainingConfig = _reflection.GeneratedProtocolMessageType(
    'TrainingConfig', (_message.Message,),
    dict(DESCRIPTOR=_TRAININGCONFIG,
         __module__='iva.detectnet_v2.proto.training_config_pb2'))
_sym_db.RegisterMessage(TrainingConfig)
# okay decompiling training_config_pb2.pyc
