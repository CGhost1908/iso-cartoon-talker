wget https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar -O  SadTalker/checkpoints/mapping_00109-model.pth.tar
wget https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar -O  SadTalker/checkpoints/mapping_00229-model.pth.tar
wget https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors -O  SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors
wget https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors -O  SadTalker/checkpoints/SadTalker_V0.0.2_512.safetensors
mkdir -p ./gfpgan/weights
wget https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth -O SadTalker/gfpgan/weights/alignment_WFLW_4HG.pth 
wget https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth -O SadTalker/gfpgan/weights/detection_Resnet50_Final.pth 
wget https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth -O SadTalker/gfpgan/weights/GFPGANv1.4.pth 
wget https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth -O SadTalker/gfpgan/weights/parsing_parsenet.pth 