# main.py ─ PySide6 GUI (트랙 선택 + 채널별 볼륨 + 실시간 재생/추출)
import sys, os, threading
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QListWidget, QLabel, QSlider, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt

from ffmpeg_utils import (
    list_audio_streams,
    probe_channels,
    export_audio,
)
from audio_player import FFmpegStreamPlayer


# ─────────────────────────────── 위젯 클래스 ──────────────────────────────
class ChannelControl(QWidget):
    def __init__(self, ch: str):
        super().__init__()
        self.ch = ch
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(100)
        lay = QHBoxLayout(self)
        lay.addWidget(QLabel(ch)); lay.addWidget(self.slider)

    @property
    def volume(self): return self.slider.value() / 100.0


# ─────────────────────────────── 메인 윈도우 ─────────────────────────────
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Channel Audio Tool")
        self.resize(560, 650)

        # 상태
        self.video_path: str | None = None
        self.current_stream_idx: int = 0
        self.controls: dict[str, ChannelControl] = {}
        self.player: FFmpegStreamPlayer | None = None

        # ── 위젯 ──
        self.btn_open   = QPushButton("📂 동영상 열기")
        self.track_box  = QComboBox()                 # 오디오 트랙 선택
        self.layout_box = QComboBox(); self.layout_box.addItems(["stereo", "5.1"])

        self.ch_list    = QListWidget()
        self.ctrl_layout= QVBoxLayout()

        self.btn_play   = QPushButton("▶️ 재생")
        self.btn_export = QPushButton("💾 추출")
        # self.btn_clip   = QPushButton("🔖 마지막 10초 저장")

        # ── 레이아웃 ──
        root = QVBoxLayout(self)
        root.addWidget(self.btn_open)
        root.addWidget(QLabel("오디오 트랙:"));   root.addWidget(self.track_box)
        root.addWidget(QLabel("출력 레이아웃:")); root.addWidget(self.layout_box)
        root.addWidget(QLabel("채널 목록:"));     root.addWidget(self.ch_list)
        root.addLayout(self.ctrl_layout)
        root.addWidget(self.btn_play)
        root.addWidget(self.btn_export)
        # root.addWidget(self.btn_clip)

        # ── 시그널 ──
        self.btn_open.clicked.connect(self.open_file)
        self.track_box.currentIndexChanged.connect(self.track_changed)
        self.btn_play.clicked.connect(self.play_clicked)
        self.btn_export.clicked.connect(self.export_clicked)
        # self.btn_clip.clicked.connect(self.export_clip)

    # ---------- 도우미 ----------
    def _vol_map(self): return {ch: ctrl.volume for ch, ctrl in self.controls.items()}

    def _volume_changed(self, _):
        if self.player:
            self.player.update_volume(self._vol_map())

    def _refresh_sliders(self, chs: list[str]):
        # 슬라이더 영역 비우기
        while self.ctrl_layout.count():
            w = self.ctrl_layout.takeAt(0).widget()
            if w: w.deleteLater()
        self.controls.clear(); self.ch_list.clear()

        for ch in chs:
            self.ch_list.addItem(ch)
            ctrl = ChannelControl(ch)
            ctrl.slider.valueChanged.connect(self._volume_changed)
            self.ctrl_layout.addWidget(ctrl)
            self.controls[ch] = ctrl

    # ---------- 슬롯 ----------
    def open_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "동영상 선택", "", "Video Files (*.mp4 *.mkv *.mov *.avi)"
        )
        if not f: return
        self.video_path = f

        # 재생 중이면 정리
        if self.player:
            self.player.stop(); self.player = None

        # 오디오 스트림 탐색
        streams = list_audio_streams(f)
        self.track_box.clear()
        for s in streams:
            text = f"[{s['a_idx']}] {s['lang']} • {s['codec']} • {s['layout'] or '??'}"
            self.track_box.addItem(text, userData=s["a_idx"])   # userData 도 a_idx
        self.current_stream_idx = streams[0]["a_idx"]   # ← 여기!
        
        # 채널 슬라이더 세팅
        chs = probe_channels(f, self.current_stream_idx)
        self._refresh_sliders(chs)

    def track_changed(self, _):
        if not self.video_path: return
        self.current_stream_idx = self.track_box.currentData()
        chs = probe_channels(self.video_path, self.current_stream_idx)
        self._refresh_sliders(chs)
        # 재생 중이었다면 즉시 갱신
        if self.player:
            self.player.stop(); self.player = None
            self.play_clicked()

    def play_clicked(self):
        if not self.video_path: return
        if self.player:              # 토글 동작
            self.player.stop(); self.player = None; return
        self.player = FFmpegStreamPlayer(
            self.video_path, self._vol_map(), stream_index=self.current_stream_idx
        )
        threading.Thread(target=self.player.play_async, daemon=True).start()

    def export_clicked(self):
        if not self.video_path: return
        out, _ = QFileDialog.getSaveFileName(
            self, "오디오 추출",
            str(Path(self.video_path).with_suffix(".wav")),
            "WAV (*.wav)"
        )
        if not out: return
        try:
            export_audio(
                self.video_path, out, self._vol_map(),
                layout=self.layout_box.currentText(),
                stream_index=self.current_stream_idx
            )
            QMessageBox.information(self, "완료", f"저장 성공:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # def export_clip(self):
    #     if not (self.video_path and self.player): return
    #     out, _ = QFileDialog.getSaveFileName(
    #         self, "현재 구간 WAV 저장",
    #         str(Path(self.video_path).with_suffix("_clip.wav")),
    #         "WAV (*.wav)"
    #     )
    #     if not out: return
    #     end = self.player.current_time()
    #     start = max(end - 10.0, 0.0)
    #     try:
    #         export_audio(
    #             self.video_path, out, self._vol_map(),
    #             layout=self.layout_box.currentText(),
    #             stream_index=self.current_stream_idx,
    #             start=start, duration=end - start
    #         )
    #         QMessageBox.information(
    #             self, "완료",
    #             f"{start:,.2f}s–{end:,.2f}s 구간 저장 성공"
    #         )
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", str(e))


# ──────────────────────────────── main ────────────────────────────────
if __name__ == "__main__":
    os.environ["QT_MAC_WANTS_LAYER"] = "1"
    app = QApplication(sys.argv)
    mw = MainWindow(); mw.show()
    sys.exit(app.exec())
