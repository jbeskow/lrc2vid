import sys
import re
import datetime
import subprocess
import os
import glob
import shutil
import argparse
import pylrc
from tqdm import tqdm
from PIL import Image


parser = argparse.ArgumentParser('lyrics to video using VQGAN+CLIP')
parser.add_argument('-fps','--frames_per_second',type=float,default=10,dest='fps')
parser.add_argument('-ii','--init_image',type=str,default=None,dest='init_image')
parser.add_argument('-ip','--init_prompt',type=str,default='',dest='init_prompt')
parser.add_argument('-y','--style',type=str,default='A painting in the style of salvador Dali:0.2',dest='style')
parser.add_argument('-s','--size',nargs=2, type=int, help='Image size (width height)', default=[640,480], dest='size')
parser.add_argument('-l','--lyrics_file',type=str,default=None,dest='lrc')
parser.add_argument('-a','--audio_file',type=str,default=None,dest='audio')
parser.add_argument('-o','--output_dir',type=str,default='out',dest='outdir')
parser.add_argument('-hr','--high-resolution',action='store_true',dest='hires')
parser.add_argument('-v','--verbose',action='store_true',dest='verbose')

args, unknownargs = parser.parse_known_args()

print('extra args (will be passed to generate.py):',unknownargs)

fps = args.fps
initialimage  = args.init_image
initialprompt = args.init_prompt
lrcfile       = args.lrc
audiofile     = args.audio
outdir        = args.outdir
prompt     = initialprompt
currtime   = 0
segment    = 1
length     = -1

if args.verbose:
    outchan = None
else:
    outchan = subprocess.DEVNULL
    
def imresize(iimg,oimg,size):
    i1 = Image.open(iimg)
    i2 = i1.resize(size)
    i2.save(oimg)    

def list2cmd(cmdlst):
    cmd = ''
    for x in cmdlst:
        if ' ' in x:
            cmd += '\"{}\" '.format(x)
        else:
            cmd += x + ' '
    return cmd
    
if args.lrc:
    with open(lrcfile) as f:
        os.mkdir(outdir)
        if initialimage:
            os.mkdir(outdir+'/segment000')
            imresize(initialimage,outdir+'/segment000/000.png',args.size)
            
        with open(outdir+'/cmd.txt','w') as ff:
            ff.write(list2cmd(sys.argv))
                
        lyrics = pylrc.parse(''.join(f.readlines()))
        lines = []
                
        for line in lyrics:
            lines.append((line.time,line.text))
                    
        if lyrics.length != '':
            try:
                pt = datetime.datetime.strptime(lyrics.length, '%M:%S.%f')
            except:
                pt = datetime.datetime.strptime(lyrics.length.split('.')[0], '%M:%S')
            pt = datetime.datetime.strptime(lyrics.length.split('.')[0], '%M:%S')

            endtime = pt.minute*60+pt.second+pt.microsecond*1e-6
            
        else:
            endtime = lines[-1][0]+5.0
        lines.append((endtime,''))
        print('total length:',endtime)
    
        for (secs,txt) in lines:
            txt = txt.replace('\'','')

            seg = 'segment{}'.format(str(segment).zfill(3))
            nframes = int((secs - currtime)*fps)
            if nframes <= 0:
                prompt += ',' + txt
                continue
                

            shutil.rmtree('steps', ignore_errors=True)

            cmd = ['python','generate.py','-zse','10','-zsc','1.015','-opt','Adagrad','-lr','0.15','-zvid',
                   '-p','{}|{}'.format(prompt,args.style),'-i',str(nframes*10),'-ofps',str(fps),'-s']
            cmd += [str(x) for x in args.size]
            if initialimage:            
                cmd += ['-ii',initialimage]
            cmd += unknownargs
            
            print('{} ({:.2f} s - {:.2f} s), {} frames. cmd:'.format(seg,currtime,secs,nframes))
            print('\t',list2cmd(cmd))
            subprocess.call(cmd,stdout=outchan,stderr=outchan)
            segdir = os.path.join(outdir,seg)
            os.rename('steps',segdir)
            shutil.move('output.mp4',segdir)
            frames = sorted(glob.glob('{}/*.png'.format(segdir)),key=os.path.getctime)
            # delete extra frames
            for xframe in frames[nframes:]:
                os.remove(xframe)
            # get last file
            try:
                initialimage = frames[nframes-1]
            except:
                print('too few frames!')
            
            currtime = secs
            segment +=1
            prompt = txt
            
vidfile = outdir+'/vid.mp4'
outfile = outdir+'/out.mp4'

pngs = glob.glob(outdir+'/segment*/*.png')
# ensure numerical sort of segments and frames by finding all number sequences and zero-padding them
pngs.sort(key=lambda str: ''.join([x.zfill(5) for x in re.findall('\d+',str)]))

# optionally run esrgan on images to enhance resolution
if args.hires:
    print('enhancing...')
    hrpngs = [x.replace('segment','hires') for x in pngs]
    
    for png,hrpng in tqdm(zip(pngs,hrpngs)):
        hrdir = os.path.dirname(hrpng)
        if not os.path.isdir(hrdir):
            os.mkdir(hrdir)
        if not os.path.exists(hrpng):
            subprocess.call(['./realesrgan-ncnn-vulkan','-i',png,'-o',hrpng],stdout=outchan,stderr=outchan)
    images = hrpngs
else:
    images = pngs
            

# 480 x 270
# generate video
print('making video -> {}'.format(vidfile))
p = subprocess.Popen(['ffmpeg','-y','-f','image2pipe','-vcodec','png',
    '-r',str(fps),'-i','-','-b:v','10M','-vcodec','h264_nvenc',
    '-pix_fmt','yuv420p','-strict','-2',vidfile],
                     stdin=subprocess.PIPE,stdout=outchan,stderr=outchan)

for img in images:
    with open(img,'rb') as ff:
        data = ff.read()
        p.stdin.write(data)

p.stdin.close()
p.wait()

if audiofile:
    # add the audio
    print('adding audio -> {}'.format(outfile))
    cmd = ['ffmpeg','-i',vidfile,'-i',audiofile,'-map','0:v','-map','1:a','-c:v','copy','-shortest',outfile]
    subprocess.call(cmd,stdout=outchan,stderr=outchan)

        

    
        

