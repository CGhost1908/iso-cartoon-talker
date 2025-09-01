import argparse
import torch
from inference import main

def run_sadtalker(
    audio_path,
    image_path,
    checkpoint_dir='checkpoints',
    result_dir='results',
    enhancer='gfpgan', #if you change this parameter you can get ValueError, default is 'gfpgan'
    preprocess='resize', # none, crop, full, resize, extfull, extcrop
    device=None,
):
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    args = argparse.Namespace(
        driven_audio=audio_path,
        source_image=image_path,
        checkpoint_dir=checkpoint_dir,
        result_dir=result_dir,
        enhancer=enhancer,
        preprocess=preprocess,
        still=True,
        pose_style=5,
        batch_size=1,
        size=512,
        expression_scale=1.2,
        use_last_fc=False,
        input_yaw=[0],
        input_pitch=[0],
        input_roll=[0],
        background_enhancer=None,
        cpu=(device == 'cpu'),
        face3dvis=False,
        verbose=False,
        old_version=False,
        net_recon='resnet50',
        init_path=None,
        bfm_folder='checkpoints',
        bfm_model='BFM_model_front.mat',
        ref_eyeblink=None,
        ref_pose=None,
        device=device,
    )

    main(args)
