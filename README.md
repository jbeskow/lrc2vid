# lrc2vid

Generate music video from lyrics (`.lrc`) file using VQGAN+CLIP

## Install

1. Clone repo from [VQGAN+CLIP](https://github.com/nerdyrodent/VQGAN-CLIP) and follow all instructions
2. Clone `lrc2vid` repo inside `VQGAN+CLIP`
3. Install dependency `pip install pylrc`


## Example

[![sample video](img/0.png)](https://www.youtube.com/watch?v=11Oevt0quuo)

To generate a video based on `my_favourite_things.lrc` in the style of Edward Hopper, use

`python lrc2vid/lrc2vid.py -ii julie.png -l my_favourite_things.lrc -a my_favourite_things.wav -y "by Edward Hopper:0.6" -o my_favourite_things_hopper`

Output will be placed in `my_favourite_things_hopper/out.mp4`. GPU recommended.
