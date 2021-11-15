# lrc2vid

Generate music video from lyrics (`.lrc`) file using VQGAN-CLIP

## Install

1. Clone [`VQGAN-CLIP`](https://github.com/nerdyrodent/VQGAN-CLIP) and follow the set-up instructions
2. Clone `lrc2vid` (this repo) as a subfolder of `VQGAN-CLIP`
3. Install dependency `pip install pylrc`

## Example

[![sample video](https://img.youtube.com/vi/11Oevt0quuo/0.jpg)](https://www.youtube.com/watch?v=11Oevt0quuo)

The above video in the style of Edward Hopper was generated using the command

`python lrc2vid/lrc2vid.py -ii lrc2vid/sampledata/julie.png -l lrc2vid/sampledata/my_favourite_things.lrc -a lrc2vid/sampledata/my_favourite_things.wav -y "by Edward Hopper:0.6" -o my_favourite_things_hopper`

Output will be in `my_favourite_things_hopper/out.mp4`. GPU recommended.
