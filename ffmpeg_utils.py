# ffmpeg_utils.py ─ FFmpeg/FFprobe 래퍼 + 채널 유틸
import json, subprocess, shutil
from static_ffmpeg import run as sffmpeg_run

# ── FFmpeg/FFprobe 실행 파일 경로 ───────────────────────────
ffmpeg_bin, ffprobe_bin = sffmpeg_run.get_or_fetch_platform_executables_else_raise()

# ── 공통 실행 헬퍼 ────────────────────────────────────────────
def _run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, check=True
    )
    return result.stdout.strip()


# 모든 오디오 스트림 정보를 가져오는 함수
def list_audio_streams(video: str) -> list[dict]:
    """
    반환 [
      {'a_idx':0, 'global_idx':1, 'lang':'eng', ...},
      {'a_idx':1, 'global_idx':2, 'lang':'jpn', ...}
    ]
    """
    cmd = [
        ffprobe_bin, "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index:stream_tags=language",
        "-show_entries", "stream=codec_name,channel_layout",
        "-of", "json", video
    ]
    raw = json.loads(_run(cmd))["streams"]
    out = []
    for a_idx, s in enumerate(raw):      # ← 오디오 트랙 순서가 a_idx
        out.append({
            "a_idx": a_idx,
            "global_idx": s["index"],
            "lang": s.get("tags", {}).get("language", "und"),
            "codec": s["codec_name"],
            "layout": s.get("channel_layout", "")
        })
    return out


# ── 채널 레이아웃 탐색 ───────────────────────────────────────
def probe_channels(video: str, stream_index: int = 0) -> list[str]:
    """
    ① channel_layout 값이 있으면 그대로 매핑
    ② 없으면 channels 개수(1·2·6·8)로 추론
    """
    cmd = [
        ffprobe_bin, "-v", "error",
        "-select_streams", f"a:{stream_index}",
        "-show_entries", "stream=channel_layout,channels",
        "-of", "json", video
    ]
    info = json.loads(_run(cmd))["streams"][0]
    layout = info.get("channel_layout", "") or ""
    ch_count = info.get("channels", 0)

    std_map = {
        "mono":  ["FC"],
        "stereo":["FL","FR"],
        "5.1":   ["FL","FR","FC","LFE","SL","SR"],
        "5.1(side)":["FL","FR","FC","LFE","SL","SR"],
        "7.1":   ["FL","FR","FC","LFE","BL","BR","SL","SR"],
    }

    if layout and layout in std_map:
        return std_map[layout]
    if "+" in layout:                      # "FL+FR+FC+…"
        return layout.split("+")

    # ---- 레이아웃이 비어 있는 경우 ----
    if ch_count == 1:  return std_map["mono"]
    if ch_count == 2:  return std_map["stereo"]
    if ch_count == 6:  return std_map["5.1"]
    if ch_count == 8:  return std_map["7.1"]
    return std_map["stereo"]               # 안전 기본값




# ── 전체 오디오 추출 (스테레오·5.1) ───────────────────────────
def export_audio(video: str,
                 out_path: str,
                 vol: dict[str, float],
                 layout: str = "stereo",
                 start: float | None = None,
                 duration: float | None = None,
                 stream_index: int = 0):
    """
    vol: {'FL':0.0,'FR':0.0,'FC':1.0,'LFE':1.0,'SL':0.0,'SR':0.0} …
    layout:
        'stereo' → PotPlayer 같은 가중치 다운믹스
        '5.1'    → 채널별 볼륨만 곱해 그대로 5.1 출력
    stream_index: 사용할 오디오 트랙의 인덱스
    """

    def gain(ch: str, w: float = 1.0) -> str:
        # 볼륨×가중치(0.7 등) · 대문자 채널 코드
        return f"{vol.get(ch, 0)*w}*{ch}"

    if layout == "stereo":
        #   L = FL + 0.7·FC + 0.7·SL + 0.7·LFE
        #   R = FR + 0.7·FC + 0.7·SR + 0.7·LFE
        pan = (
            "stereo|"
            f"c0={gain('FL')}+{gain('FC',0.7)}+{gain('SL',0.7)}+{gain('LFE',0.7)}|"
            f"c1={gain('FR')}+{gain('FC',0.7)}+{gain('SR',0.7)}+{gain('LFE',0.7)}"
        )
        ac_opts = ["-ac", "2"]
    elif layout == "5.1":
        pan = (
            "5.1(side)|"
            f"c0={gain('FL')}|c1={gain('FR')}|c2={gain('FC')}|"
            f"c3={gain('LFE')}|c4={gain('SL')}|c5={gain('SR')}"
        )
        ac_opts = ["-ac", "6"]
    else:
        raise ValueError("layout must be 'stereo' or '5.1'")

    cmd = [ffmpeg_bin, "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", video]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]

    cmd += ["-map", f"0:a:{stream_index}", "-af", f"pan={pan}", *ac_opts,
            "-ar", "48000", "-c:a", "pcm_s16le", out_path]

    _run(cmd)



# ── 개별 채널만 모노 WAV 로 추출 ──────────────────────────────
def export_single_channel(video: str, channel: str, out_path: str):
    ch_idx = {"FL":"0.0","FR":"0.1","FC":"0.2","LFE":"0.3",
              "BL":"0.4","BR":"0.5","SL":"0.4","SR":"0.5"}[channel]
    cmd = [
        ffmpeg_bin, "-y", "-i", video,
        "-map_channel", f"0.0.{ch_idx}",
        "-c:a", "pcm_s16le", out_path
    ]
    _run(cmd)
