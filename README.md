# 멀티채널 오디오 도구 (Multi-Channel Audio Tool)

[English](#multi-channel-audio-tool) | [한국어](#멀티채널-오디오-도구)

---
<div align="center">"><img src="https://github.com/user-attachments/assets/a414d079-3f17-4747-b996-172209d1bf47"></div>


## 멀티채널 오디오 도구

멀티채널 오디오 도구는 5.1, 7.1 등 멀티채널 오디오가 포함된 비디오 파일에서 특정 채널만 선택적으로 추출하거나 믹싱할 수 있는 도구입니다. 실시간으로 채널별 볼륨을 조절하면서 미리 들어볼 수 있고, 원하는 설정으로 WAV 파일로 추출할 수 있습니다.

### 주요 기능

- 비디오 파일의 다양한 오디오 트랙 선택 가능
- 각 채널별 볼륨 실시간 조절 및 미리듣기
- 스테레오 또는 5.1 포맷으로 오디오 추출
- 현재 재생 중인 구간의 마지막 10초 클립 저장 기능

### 설치 방법

1. 이 저장소를 클론합니다:
   ```
   git clone https://github.com/ejeonghun/multi-channel-audio-tool.git
   cd 채널분리_chatgpt
   ```

2. 필요한 패키지를 설치합니다:
   ```
   pip install -r requirements.txt
   ```

### 사용 방법

1. 프로그램 실행:
   ```
   python main.py
   ```

2. "📂 동영상 열기" 버튼을 클릭하여 멀티채널 오디오가 포함된 비디오 파일을 선택합니다.

3. 오디오 트랙을 선택합니다 (여러 개의 오디오 트랙이 있는 경우).

4. 출력 레이아웃을 선택합니다 (stereo 또는 5.1).

5. 각 채널별 슬라이더로 볼륨을 조절합니다:
   - FL: 전방 왼쪽 (Front Left)
   - FR: 전방 오른쪽 (Front Right)
   - FC: 중앙 (Front Center)
   - LFE: 저주파 효과 (Low-Frequency Effects)
   - SL/BL: 측면/후방 왼쪽 (Side/Back Left)
   - SR/BR: 측면/후방 오른쪽 (Side/Back Right)

6. "▶️ 재생" 버튼을 클릭하여 현재 설정으로 오디오를 미리 들어볼 수 있습니다.

7. "💾 추출" 버튼을 클릭하여 현재 설정대로 WAV 파일로 추출합니다.

### 활용 예시

- 영화에서 대사만 추출하기 (중앙 채널만 켜기)
- 콘서트 영상에서 보컬만 추출하거나 반주만 추출하기
- 멀티채널 오디오를 스테레오로 다운믹싱하면서 특정 채널 강조하기
- 특정 음향 효과만 분리하여 사용하기

### 시스템 요구사항

- Python 3.9 이상
- FFmpeg (패키지가 자동으로 다운로드해서 사용)
- Qt 그래픽 환경 지원 (Windows, macOS, Linux)

---

## Multi-Channel Audio Tool

Multi-Channel Audio Tool is a utility for selectively extracting or mixing channels from video files containing multi-channel audio such as 5.1 or 7.1 surround sound. You can adjust channel volumes in real-time for preview and export your settings to a WAV file.

### Key Features

- Select from multiple audio tracks in video files
- Real-time adjustment and preview of individual channel volumes
- Export audio in stereo or 5.1 format
- Save the last 10 seconds of currently playing segment as a clip

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/ejeonghun/multi-channel-audio-tool.git
   cd 채널분리_chatgpt
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Usage

1. Run the program:
   ```
   python main.py
   ```

2. Click the "📂 Open Video" button to select a video file with multi-channel audio.

3. Select an audio track (if multiple tracks are available).

4. Choose an output layout (stereo or 5.1).

5. Adjust the volume for each channel using the sliders:
   - FL: Front Left
   - FR: Front Right
   - FC: Front Center
   - LFE: Low-Frequency Effects
   - SL/BL: Side/Back Left
   - SR/BR: Side/Back Right

6. Click the "▶️ Play" button to preview the audio with your current settings.

7. Click the "💾 Export" button to extract the audio to a WAV file with your current settings.

### Use Cases

- Extract only dialogue from movies (isolate center channel)
- Extract vocals or instrumentals from concert videos
- Downmix multi-channel audio to stereo while emphasizing specific channels
- Isolate specific sound effects for use in other projects

### System Requirements

- Python 3.9 or higher
- FFmpeg (automatically downloaded by the package)
- Qt-compatible graphical environment (Windows, macOS, Linux)
