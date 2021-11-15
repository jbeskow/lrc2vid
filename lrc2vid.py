import sys
import re
import datetime
import subprocess
import os
import glob
import shutil
import argparse
import pylrc

cmdline = ' '.join(sys.argv)

parser = argparse.ArgumentParser('lyrics to video using VQGAN+CLIP')

parser.add_argument('-fps','--frames_per_second',type=float,default=10,dest='fps')
parser.add_argument('-ii','--init_image',type=str,default=None,dest='init_image')
parser.add_argument('-ip','--init_prompt',type=str,default=None,dest='init_prompt')
parser.add_argument('-y','--style',type=str,default='A painting in the style of salvador Dali:0.2',dest='style')
parser.add_argument('-s','--size',nargs=2, type=int, help='Image size (width height)', default=[640,480], dest='size')
parser.add_argument('-l','--lyrics_file',type=str,default='in.lrc',dest='lrc')
parser.add_argument('-a','--audio_file',type=str,default=None,dest='audio')
parser.add_argument('-o','--output_dir',type=str,default='out',dest='outdir')

args = parser.parse_args()

fps = args.fps
initialimage  = args.init_image
initialprompt = args.init_prompt
lrcfile       = args.lrc
audiofile     = args.audio
outdir        = args.outdir

prompt = initialprompt
currtime = 0
segment = 0
length = -1

with open(lrcfile) as f:

    os.mkdir(outdir)
    with open(outdir+'/cmd.txt','w') as ff:
        ff.write(cmdline)
    lyrics = pylrc.parse(''.join(f.readlines()))
    lines = []
    for line in lyrics:
        lines.append((line.time,line.text))
    if lyrics.length != '':
        pt = datetime.datetime.strptime(lyrics.length.split('.')[0], '%M:%S')
        endtime = pt.minute*60+pt.second
    else:
        endtime = lines[-1][0]+5.0
    lines.append((endtime,''))
    
    for (secs,txt) in lines:
        seg = 'segment{}'.format(str(segment).zfill(3))
        nframes = int((secs - currtime)*fps)
        print('seg:',seg,', init:',initialimage,', prompt:',prompt,', nframes:',nframes)
        cmd = ['python','generate.py']
        if prompt:
            cmd.append('-p')
            cmd.append('{}|{}'.format(prompt,args.style))
        cmd.append('-i')
        cmd.append(str(nframes*10))
        cmd.append('-ofps')
        cmd.append(str(fps))
        cmd.append('-s')
        cmd.extend(str(x) for x in args.size)
        cmd.extend(['-zse','10','-zsc','1.015','-opt','Adagrad','-lr','0.15','-zvid'])
        if initialimage:            
            cmd.append('-ii')
            cmd.append(initialimage)
        print('cmd=',cmd)
        shutil.rmtree('steps', ignore_errors=True)
        subprocess.call(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
            
        prompt = txt.replace('\'','')
        currtime = secs
        segment +=1

    vidfile = outdir+'/vid.mp4'
    outfile = outdir+'/out.mp4'

    # generate video
    print('making video')
    p = subprocess.Popen(['ffmpeg','-y','-f','image2pipe','-vcodec','png',
                          '-r',str(fps),'-i','-','-b:v','10M','-vcodec','h264_nvenc',
                          '-pix_fmt','yuv420p','-strict','-2',vidfile],
                         stdin=subprocess.PIPE)
    # pipe PNGs to ffmpeg
    for file in sorted(glob.glob(outdir+'/segment*/*.png'),key=os.path.getctime):
        with open(file,'rb') as ff:
            data = ff.read()
            p.stdin.write(data)
    p.stdin.close()
    p.wait()

    if audiofile:
        # add the audio
        print('adding audio')
        cmd = ['ffmpeg','-i',vidfile,'-i',audiofile,'-map','0:v','-map','1:a','-c:v','copy','-shortest',outfile]
        print(cmd)
        subprocess.call(cmd)

        

    
        

