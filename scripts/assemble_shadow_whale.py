#!/usr/bin/env python3
"""Assemble Telemon Shadow Whale trailer using the client's own voice and SFX assets."""
import os, re, sys, json, math, subprocess, pathlib, glob
from PIL import Image, ImageOps, ImageDraw
BASE=pathlib.Path(".")
OUT=pathlib.Path("output")
OUT.mkdir(exist_ok=True)
FRAMES=pathlib.Path("frames")
FRAMES.mkdir(exist_ok=True)
FPS=30
DURATION=536/30
# Same temporal rhythm, output format, and narrator-card approach as Chronarch v5.
CUTS=[0,2.75,3.66,5.31,7.66,9.76,12.16,14.00,16.60,DURATION]
SCENES=[
  "ЕСЛИ КАМЕНЬ ПОД НОГАМИ\nПОШЁЛ ВОЛНАМИ...",
  "БЕГИ.",
  "ТЕНЕВОЙ КИТ СПИТ",
  "ПОД ВИДОМ КАМЕННОГО\nПЕРЕВАЛА.",
  "ПРОСНУВШИСЬ, ОН НЫРЯЕТ...",
  "В СКАЛУ. СО ВСЕМ,\nЧТО ОСТАЛОСЬ НА СПИНЕ.",
  "ПУТНИК УСПЕЛ СПРЫГНУТЬ.",
  "ЕГО КОСТЁР ДО СИХ ПОР\nГОРИТ ВНУТРИ ГОРЫ.",
  "ТЕНЕВОЙ КИТ\nTELEMON"
]
def run(cmd):
    print("RUN", " ".join(map(str,cmd))[:650], flush=True)
    subprocess.run([str(x) for x in cmd],check=True)
def fname(prefix,folder):
    p=list(pathlib.Path(folder).glob(f"speechkit_{prefix}*.mp3"))
    if not p:raise RuntimeError(f"Voice track not found {prefix}")
    return str(p[0])
def ffmpeg_text(txt):
    return txt.replace("\\","\\\\").replace(":",r"\:").replace("'","\\'")
def stamp(sec):
    cs=int(round(sec*100));return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"
# Real narration speechkit lines (recognised from supplied speech clips).
VOICES=[
    (0.00,"d4ab1dd4"),
    (2.85,"6b9591f0"),
    (3.80,"ed4e25ea"),
    (5.34,"0b0371da"),
    (7.80,"78e0c52e"),
    (12.14,"d099848c"),
    (13.83,"0f316326"),
]
# Keep voice separate from sound design; no artificial TTS added.
SOUNDS=[
    (0.0,"creatorshome-mountain-wind-371074.mp3",0.13,1),
    (0.0,"coghezzi-holy-aura-resonance-magical-energy-loop-533856.mp3",0.11,1),
    (0.2,"dragon-studio-footsteps-on-gravel-2-397986.mp3",0.18,1),
    (2.0,"lordsonny-rock-cinematic-161648.mp3",0.25,1),
    (3.75,"pwlpl-underwater-rumble-sound-effect-521068.mp3",0.35,1),
    (7.65,"dragon-studio-whale-song-382729.mp3",0.42,1),
    (9.85,"dragon-studio-creepy-whale-song-323612.mp3",0.28,1),
    (11.7,"dragon-studio-whoosh-cinematic-5-376880.mp3",0.26,1),
    (13.55,"dragon-studio-fire-crackling-sounds-427410 (1).mp3",0.23,1),
]
# Nine animated camera moves, one for each dark-fantasy 3D shot.
segments=[]
for i in range(9):
    infile=FRAMES/f"shot_{i:02d}.png"
    if not infile.exists():raise RuntimeError(f"Missing 3D scene {infile}")
    n=round((CUTS[i+1]-CUTS[i])*FPS)
    # 1.05–1.09x extremely gentle push-in / lateral drift, as in Chronarch.
    direction=1 if i%2==0 else -1
    z=f"min(zoom+0.00014,1.09)"
    x="iw/2-(iw/zoom/2)" if direction>0 else "iw/2-(iw/zoom/2)+10*sin(on/26)"
    y="ih/2-(ih/zoom/2)"
    vf=f"zoompan=z='{z}':d={n}:x='{x}':y='{y}':s=1080x1920:fps=30,format=yuv420p"
    path=OUT/f"shot_{i:02d}.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",infile,"-vf",vf,"-frames:v",n,
         "-c:v","libx264","-crf","21","-preset","veryfast","-pix_fmt","yuv420p","-an",path])
    segments.append(path)
# concat exact consecutive shots
concat=OUT/"concat.txt"
concat.write_text("".join("file '"+p.name+"'\n" for p in segments),encoding="utf-8")
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",concat,
     "-c","copy",OUT/"video_silent.mp4"])
# ASS with bold white captions at lower third and dark contrast outline.
ass=OUT/"captions.ass"
header="""[Script Info]
Title: TELEMON - Теневой кит
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narrator,DejaVu Sans,69,&H00F7F6F1,&H0000E5FF,&H00101417,&H85000000,-1,0,0,0,100,100,-1,0,1,5,2,2,80,80,330,1
Style: Title,DejaVu Sans,85,&H00FCF8F2,&H0000E5FF,&H00101417,&H85000000,-1,0,0,0,100,100,1,0,1,6,3,2,80,80,400,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines=[]
for i,(start,end,txt) in enumerate(zip(CUTS[:-1],CUTS[1:],SCENES)):
    styled=txt.replace("\n",r"\N")
    sty="Title" if i==8 else "Narrator"
    lines.append(f"Dialogue: 0,{stamp(start)},{stamp(end)},{sty},,0,0,0,,{styled}\n")
ass.write_text(header+''.join(lines),encoding="utf-8")
# Mix voice and acoustic landscape to one stereo track.
inputs=[]
layers=[]
for start,prefix in VOICES:
    path=fname(prefix,BASE/"original/kits")
    ix=len(inputs)//2
    inputs+=["-i",path]
    delay=round(start*1000)
    layers.append(f"[{ix}:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.28,adelay={delay}|{delay}[s{ix}]")
for start,name,vol,once in SOUNDS:
    path=BASE/"original/sounds"/name
    if not path.exists():raise RuntimeError(f"Missing sound file {path}")
    ix=len(inputs)//2
    inputs+=["-i",path]
    delay=round(start*1000)
    layers.append(f"[{ix}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={delay}|{delay}[s{ix}]")
all_labels="".join(f"[s{i}]" for i in range(len(VOICES)+len(SOUNDS)))
fc=";".join(layers)+f";{all_labels}amix=inputs={len(VOICES)+len(SOUNDS)}:duration=longest:dropout_transition=0,atrim=0:{DURATION:.6f},alimiter=limit=0.93[outa]"
run(["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,"-filter_complex",fc,"-map","[outa]",
     "-c:a","aac","-b:a","192k",OUT/"soundtrack.m4a"])
# Save final H264/AAC, original Chronarch framing (1080x1920, 30fps, 17.867s)
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",OUT/"video_silent.mp4",
     "-i",OUT/"soundtrack.m4a","-vf",f"ass={ass.as_posix()}",
     "-c:v","libx264","-preset","medium","-crf","19","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-t",f"{DURATION:.6f}","-movflags","+faststart",
     OUT/"Telemon_Shadow_Whale_v1.mp4"])
# Save a clear nine-frame review sheet for user
previews=[]
for i in range(9):
    pic=Image.open(FRAMES/f"shot_{i:02d}.png").convert("RGB")
    pic.thumbnail((270,480))
    canvas=Image.new("RGB",(300,510),"#0b121b")
    canvas.paste(pic,((300-pic.width)//2,0))
    ImageDraw.Draw(canvas).text((15,482),f"{i+1}. {CUTS[i]:.2f} s",fill="white")
    previews.append(canvas)
contact=Image.new("RGB",(900,1530),"#0b121b")
for i,pic in enumerate(previews): contact.paste(pic,((i%3)*300,(i//3)*510))
contact.save(OUT/"Shadow_Whale_preview.jpg",quality=85)
info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate","-of","json",str(OUT/"Telemon_Shadow_Whale_v1.mp4")]))
(OUT/"render_info.json").write_text(json.dumps(info,indent=2,ensure_ascii=False))
print("SUCCESS",str(OUT/"Telemon_Shadow_Whale_v1.mp4"),info,flush=True)
