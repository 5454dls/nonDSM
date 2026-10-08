# Chief problems and diagnostic groups — GitHub Pages 버전

기존 Python Gradio 연구용 도구를 HTML/CSS/JavaScript로 옮긴 버전입니다. **Render 등의 서버 없이 GitHub Pages에서 실행**됩니다.

## GitHub Pages에 올리는 방법

1. 이 ZIP 파일을 먼저 **압축 해제**합니다. ZIP 파일 자체를 GitHub에 올리면 실행되지 않습니다.
2. GitHub 저장소의 최상위 위치(루트)에 아래 **5개 파일**을 올립니다.
   - `index.html`
   - `style.css`
   - `script.js`
   - `model_all_groups.json`
   - `item_domains.json`
3. 저장소에서 **Settings → Pages**를 누릅니다.
4. **Build and deployment → Source**를 `Deploy from a branch`로 선택합니다.
5. **Branch:** `main`, **Folder:** `/(root)`을 선택하고 **Save**를 누릅니다.
6. 배포 후 안내되는 주소(`https://사용자이름.github.io/저장소이름/`)를 방문합니다.

원래 GitHub에 올려둔 `app.py`와 `requirements.txt`는 그대로 두어도 되지만, GitHub Pages에서는 사용하지 않습니다.

## 기존 프로그램과의 일치성

- 업로드하신 두 JSON 파일을 **바이트 단위로 변경 없이** 복사했습니다.
- 101개 선택 항목 및 20개 도메인, 3~10개 선택 제한, Compute 버튼을 눌렀을 때만 계산, Reset, 별도로 표시하는 잔여 범주 Other diagnoses 등을 유지했습니다.
- 기존 로지스틱 회귀 점수 계산 및 정규화, 그룹별 cut-off 비교(반올림 이전의 값 사용)를 유지했습니다.
- 학습 대상 수, 진단군별 성능(AUC), cut-off, Youden J 등은 모델 JSON에서 읽습니다.
- 증상 선택값은 브라우저 안에서만 계산합니다. 별도 데이터베이스나 예측 API로 전송하지 않습니다.

## 주의사항

- 이것은 임상 진단 도구가 아닌 **연구용 도구**입니다.
- `script.js`의 `CITATION = "[OO]"`는 원본 앱에 있던 추후 논문 인용 자리입니다. 논문 출판 후 수정할 수 있습니다.
- GitHub 저장소를 Public으로 운영하면 `model_all_groups.json`의 **모델 계수, 학습 데이터의 집계 수치 및 성능 지표도 공개**됩니다. 원본 환자별 기록은 포함하지 않습니다.
- `index.html`을 파일 탐색기에서 직접 열면 브라우저 보안 정책 때문에 JSON을 읽지 못할 수 있습니다. GitHub Pages에 올리면 정상 실행됩니다.

## PC에서 별도로 시험하기(선택)

이 폴더에서 `python -m http.server 8000`을 실행한 다음 브라우저에서 `http://localhost:8000/`을 엽니다. 웹사이트 운영에는 Python이 필요하지 않습니다.
