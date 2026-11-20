"""Tiny audio bed builder: music (trimmed, faded) + one-shot SFX at times + optional voice, loudness-normalised."""
import subprocess

def build_mix(out_wav, T, music=None, music_gain_db=-3.0, fade_in=0.3, fade_out=1.5, sfx=(), voice=None, voice_delay=0.0,
              duck=True, lufs=-14.0):
    inputs, chains, labels = [], [], []
    n_in = [0]
    def add(path, loop=False):
        inputs.extend((["-stream_loop", "-1"] if loop else []) + ["-i", path]); n_in[0] += 1; return n_in[0] - 1
    if music:
        i = add(music, loop=True)
        chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{T},volume={music_gain_db}dB,"
                      f"afade=t=in:d={fade_in},afade=t=out:st={max(0, T - fade_out)}:d={fade_out},apad,atrim=0:{T}[mu]")
    if voice:
        i = add(voice); ms = int(voice_delay * 1000)
        chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},apad,atrim=0:{T}[vo]")
        if music and duck:
            chains.append("[vo]asplit=2[vo][key]"); chains.append("[mu][key]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=350[mu]")
        labels.append("[vo]")
    if music: labels.append("[mu]")
    for k, s in enumerate(sfx):
        i = add(s["path"]); ms = int(max(0, s["at"]) * 1000)
        chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={s.get('gain_db', -10)}dB,adelay={ms}|{ms},apad,atrim=0:{T}[s{k}]")
        labels.append(f"[s{k}]")
    if not labels: return None
    fc = ";".join(chains) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{T},loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample=48000[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-c:a", "pcm_s16le", out_wav], check=True)
    return out_wav
