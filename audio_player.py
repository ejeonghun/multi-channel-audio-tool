# audio_player.py ─ 6-채널 PCM → 실시간 스테레오 믹스(볼륨 즉시 반영)
import queue, threading, subprocess, numpy as np, sounddevice as sd
from ffmpeg_utils import ffmpeg_bin

CH_ORDER = ["FL", "FR", "FC", "LFE", "SL", "SR"]  # DTS 5.1(side)

class FFmpegStreamPlayer:
    def __init__(self, video_path: str, vol_map: dict[str, float], stream_index=0):
        self.video_path = video_path
        self.vol_map = vol_map.copy()    # 현재 볼륨 테이블
        self._q = queue.Queue(maxsize=120)
        self._stop = threading.Event()
        self._reader_t = None
        self._proc = None
        self._stream = None
        self.played_frames = 0       # 누적 재생 프레임 수
        self.stream_index = stream_index



    # ───────── public ─────────
    def update_volume(self, vol_map: dict[str, float]):
        self.vol_map = vol_map.copy()

    def play_async(self):
        threading.Thread(target=self._play_loop, daemon=True).start()

    def stop(self):
        self._stop.set()
        if self._stream:
            try: self._stream.abort()
            except: pass
        if self._proc and self._proc.poll() is None:
            self._proc.kill()
        if self._reader_t and self._reader_t.is_alive():
            self._reader_t.join(timeout=1)
        while not self._q.empty():
            self._q.get_nowait()

    # ───────── internal ───────
    def _spawn_ffmpeg(self):
        cmd = [
            ffmpeg_bin, "-v", "quiet", "-threads", "0",
            "-i", self.video_path,
            "-map", f"0:a:{self.stream_index}",
            "-ac", "6", "-ar", "48000",
            "-f", "f32le", "-"
        ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)

    def _reader(self):
        bpf = 6 * 4                  # bytes per frame (6ch × float32)
        chunk_frames = 2048
        chunk_bytes = bpf * chunk_frames
        while not self._stop.is_set():
            data = self._proc.stdout.read(chunk_bytes)
            if not data:
                break
            self._q.put(np.frombuffer(data, np.float32), timeout=1)

    def _play_loop(self):
        self._stop.clear()
        self._proc = self._spawn_ffmpeg()
        self._reader_t = threading.Thread(target=self._reader, daemon=True)
        self._reader_t.start()

        def callback(outdata, frames, _time, status):
            if status: print(status)
            need = frames * 6
            try:
                blk = self._q.get(timeout=0.5)
            except queue.Empty:
                outdata.fill(0); return
            if blk.size < need:
                blk = np.pad(blk, (0, need - blk.size))
            blk = blk[:need].reshape(-1, 6)

            self.played_frames += frames   # ★ 재생된 프레임 합계

            vols = np.array([self.vol_map.get(ch, 0.0) for ch in CH_ORDER])
            l_mix = blk[:, [0,2,4,3]].dot(vols[[0,2,4,3]] * [1,.7,.7,.7])
            r_mix = blk[:, [1,2,5,3]].dot(vols[[1,2,5,3]] * [1,.7,.7,.7])
            outdata[:] = np.column_stack((l_mix, r_mix)).astype(np.float32)

        with sd.OutputStream(
            samplerate=48000, channels=2, dtype="float32",
            blocksize=2048, callback=callback
        ) as self._stream:
            while not self._stop.is_set():
                sd.sleep(100)

        self.stop()


    def current_time(self) -> float:
        """재생 위치(초)"""
        return self.played_frames / 48000.0    # 48 kHz 고정