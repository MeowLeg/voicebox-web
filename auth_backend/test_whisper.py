"""Quick test: WhisperX model loading + transcription on a tiny audio."""
import sys, os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["DYLD_LIBRARY_PATH"] = os.path.join(
    os.path.dirname(__file__),
    "venv/lib/python3.13/site-packages/av/.dylibs",
)

print("Step 1: import whisperx...", flush=True)
import whisperx

print("Step 2: load model medium/cpu/int8/zh...", flush=True)
model = whisperx.load_model("medium", device="cpu", compute_type="int8", language="zh")
print("Step 3: model loaded OK", flush=True)

print("Step 4: generate tiny test audio...", flush=True)
import wave, struct, math
sr = 16000
duration = 5.0
n_samples = int(sr * duration)
tmp_wav = "/tmp/test_whisper.wav"
with wave.open(tmp_wav, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    for i in range(n_samples):
        val = int(16000 * math.sin(2 * math.pi * 440 * i / sr))
        wf.writeframes(struct.pack("<h", val))

print("Step 5: transcribe...", flush=True)
import torch
import numpy as np
with wave.open(tmp_wav, "rb") as wf:
    n_frames = wf.getnframes()
    raw = wf.readframes(n_frames)
pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
waveform = torch.from_numpy(pcm).unsqueeze(0)
audio = {"waveform": waveform, "sample_rate": sr}

result = model.transcribe(audio, batch_size=8)
print(f"Step 6: transcription done, {len(result.get('segments', []))} segments", flush=True)

print("Step 7: load align model...", flush=True)
model_a, metadata = whisperx.load_align_model(language_code="zh", device="cpu")
print("Step 8: aligning...", flush=True)
result_aligned = whisperx.align(
    result["segments"], model_a, metadata, audio, "cpu",
    return_char_alignments=False,
)
print(f"Step 9: alignment done, words={len(result_aligned.get('word_segments', []))}", flush=True)
print("ALL OK!", flush=True)
