_base_ = '../../_base_/default_runtime.py'

url = ('https://download.openmmlab.com/mmaction/recognition/slowfast/'
       'slowfast_r50_8x8x1_256e_kinetics400_rgb/'
       'slowfast_r50_8x8x1_256e_kinetics400_rgb_20200716-73547d2b.pth')
# url = ('https://download.openmmlab.com/mmaction/v1.0/detection/acrn/slowfast-acrn_kinetics400-pretrained-r50_8xb8-8x8x1-cosine-10e_ava21-rgb/slowfast-acrn_kinetics400-pretrained-r50_8xb8-8x8x1-cosine-10e_ava21-rgb_20220906-0dae1a90.pth')
#class
model = dict(
    type='FastRCNN',
    _scope_='mmdet',
    init_cfg=dict(type='Pretrained', checkpoint=url),
    # init_cfg = None,
    backbone=dict(
        type='mmaction.ResNet3dSlowFast',
        pretrained=None,
        resample_rate=4,
        speed_ratio=4,
        channel_ratio=8,
        slow_pathway=dict(
            type='resnet3d',
            depth=50,
            pretrained=None,
            lateral=True,
            fusion_kernel=7,
            conv1_kernel=(1, 7, 7),
            dilations=(1, 1, 1, 1),
            conv1_stride_t=1,
            pool1_stride_t=1,
            inflate=(0, 0, 1, 1),
            spatial_strides=(1, 2, 2, 1)),
        fast_pathway=dict(
            type='resnet3d',
            depth=50,
            pretrained=None,
            lateral=False,
            base_channels=8,
            conv1_kernel=(5, 7, 7),
            conv1_stride_t=1,
            pool1_stride_t=1,
            spatial_strides=(1, 2, 2, 1))),
    roi_head=dict(
        type='AVARoIHead',
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor3D',
            roi_layer_type='RoIAlign',
            output_size=8,
            with_temporal_pool=True),
        shared_head=dict(type='ACRNHead', in_channels=4608, out_channels=2304),
        bbox_head=dict(
            type='BBoxHeadAVA',
            background_class=True,
            in_channels=2304,
            num_classes=6,
            multilabel=True,
            dropout_ratio=0.5)),
    data_preprocessor=dict(
        type='mmaction.ActionDataPreprocessor',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        format_shape='NCTHW'),
    train_cfg=dict(
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssignerAVA',
                pos_iou_thr=0.9,
                neg_iou_thr=0.9,
                min_pos_iou=0.9),
            sampler=dict(
                type='RandomSampler',
                num=32,
                pos_fraction=1,
                neg_pos_ub=-1,
                add_gt_as_proposals=True),
            pos_weight=1.0)),
    test_cfg=dict(rcnn=None))

# dataset_type = 'AVADataset'
# data_root = 'data/ava/rawframes'
# anno_root = 'data/ava/annotations'
#
# ann_file_train = f'{anno_root}/ava_train_v2.1.csv'
# ann_file_val = f'{anno_root}/ava_val_v2.1.csv'
#
# exclude_file_train = f'{anno_root}/ava_train_excluded_timestamps_v2.1.csv'
# exclude_file_val = f'{anno_root}/ava_val_excluded_timestamps_v2.1.csv'
#
# label_file = f'{anno_root}/ava_action_list_v2.1_for_activitynet_2018.pbtxt'
#
# proposal_file_train = (f'{anno_root}/ava_dense_proposals_train.FAIR.'
#                        'recall_93.9.pkl')
# proposal_file_val = f'{anno_root}/ava_dense_proposals_val.FAIR.recall_93.9.pkl'

dataset_type = 'AVADataset'
data_root = '/media/zhong/1.0T/zhong_work/archive/rawframes_mini'
anno_root = '/media/zhong/1.0T/zhong_work/archive/miniannotations'

ann_file_train = f'{anno_root}/ava_mini_train_v2.1.csv'
ann_file_val = f'{anno_root}/ava_mini_val_v2.1.csv'

exclude_file_train = None
exclude_file_val = None

label_file = f'{anno_root}/ava_mini_action_list_v2.1.pbtxt'

proposal_file_train = (f'{anno_root}/ava_mini_dense_proposals_train.FAIR.recall_93.9.pkl')
proposal_file_val = f'{anno_root}/ava_mini_dense_proposals_val.FAIR.recall_93.9.pkl'

file_client_args = dict(io_backend='disk')
train_pipeline = [
    dict(type='SampleAVAFrames', clip_len=32, frame_interval=2),
    dict(type='RawFrameDecode', **file_client_args),
    dict(type='RandomRescale', scale_range=(256, 320)),
    dict(type='RandomCrop', size=256),
    dict(type='Flip', flip_ratio=0.5),
    dict(type='FormatShape', input_format='NCTHW', collapse=True),
    dict(type='PackActionInputs')
]
# The testing is w/o. any cropping / flipping
val_pipeline = [
    dict(
        type='SampleAVAFrames', clip_len=32, frame_interval=2, test_mode=True),
    dict(type='RawFrameDecode', **file_client_args),
    dict(type='Resize', scale=(-1, 256)),
    dict(type='FormatShape', input_format='NCTHW', collapse=True),
    dict(type='PackActionInputs')
]

train_dataloader = dict(
    batch_size=8,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type=dataset_type,
        ann_file=ann_file_train,
        exclude_file=exclude_file_train,
        pipeline=train_pipeline,
        label_file=label_file,
        proposal_file=proposal_file_train,
        data_prefix=dict(img=data_root)))
val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type=dataset_type,
        ann_file=ann_file_val,
        exclude_file=exclude_file_val,
        pipeline=val_pipeline,
        label_file=label_file,
        proposal_file=proposal_file_val,
        data_prefix=dict(img=data_root),
        test_mode=True))
test_dataloader = val_dataloader

val_evaluator = dict(
    type='AVAMetric',
    ann_file=ann_file_val,
    label_file=label_file,
    exclude_file=exclude_file_val)
test_evaluator = val_evaluator

train_cfg = dict(
    type='EpochBasedTrainLoop', max_epochs=30, val_begin=1, val_interval=1)
val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')

# param_scheduler = [
#     dict(
#         type='LinearLR',
#         start_factor=0.01,
#         by_epoch=True,
#         begin=0,
#         end=1,
#         convert_to_iter_based=True),
#     dict(
#         type='CosineAnnealingLR',       #ConstantLR  CosineAnnealingLR multistep
#         T_max=5,
#         eta_min=0,
#         by_epoch=True,
#         begin=0,
#         end=20,
#         convert_to_iter_based=False)
# ]

# param_scheduler = [
#     dict(
#         type='MultiStepLR',
#         begin=0,
#         end=30,
#         by_epoch=True,
#         milestones=[10, 20],
#         gamma=0.1)
# ]

param_scheduler = [
#     dict(
#         type='CosineAnnealingLR',
#         eta_min=0,
#         T_max=20,
#         by_epoch=True,
#         convert_to_iter_based=True)
dict(type='MultiStepLR',  # 达到一个里程碑时衰减学习率
     begin=0,  # 开始更新学习率的步骤
     end=20,  # 结束更新学习率的步骤
     by_epoch=True,  # 是否按 epoch 更新学习率
     milestones=[5, 12],  # 衰减学习率的步骤
     gamma=0.1)]  # 学习率衰减的乘法因子
# ]

optim_wrapper = dict(
    optimizer=dict(type='SGD', lr=0.01, momentum=0.9, weight_decay=0.001),
    clip_grad=dict(max_norm=40, norm_type=2))
# auto_scale_lr = dict(enable=True, base_batch_size=8)
