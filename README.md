# show-yourself

YAML 파일 몇 개만 고쳐서 만드는 아카데믹 프로필 사이트입니다.
HTML/CSS를 건드리지 않아도 이름, 소속, 이력, 논문, 사이드바 링크를 바꿀 수 있습니다.

## 빠르게 시작하기

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python build.py --serve   # 빌드 후 http://127.0.0.1:8000 에서 미리보기
```

`--serve` 없이 `build.py`만 실행하면 `dist/` 폴더에 정적 파일만 생성됩니다.
내용을 수정한 뒤에는 다시 빌드하세요.

## 내용 수정하기

모든 내용은 `content/` 폴더의 YAML 파일에 있습니다.

| 파일 | 내용 |
| --- | --- |
| `content/profile.yaml` | 이름, 소속, 사진, About 문단, 상단 탭 이름, 섹션 on/off, 포인트 색 |
| `content/links.yaml` | 사이드바 링크 목록 (LinkedIn, CV, Scholar, GitHub, 이메일 등). 한 항목이 한 줄 |
| `content/career.yaml` | 거쳐온 회사 · 랩실 · 학교 (최신이 위) |
| `content/publications.yaml` | 모든 논문. 홈에는 `selected: true`인 논문만, Publications 페이지에는 전체가 표시 |
| `content/teaching.yaml` | 강의 / 조교 경력. `profile.yaml`의 `sections.teaching: false`로 페이지와 탭을 숨길 수 있음 |

### 페이지 구성

| 페이지 | 내용 |
| --- | --- |
| `index.html` (About 탭) | About, Career, Selected Publications |
| `publications.html` | 모든 논문을 연도별로. Selected 논문은 하이라이트 |
| `teaching.html` | 강의 / 조교 경력. `sections.teaching: false`면 생성되지 않음 |

사이드바(사진, 소속, 링크)는 모든 페이지에 공통으로 표시됩니다.
상단 탭 오른쪽에 CV 같은 외부 링크를 더하려면 `profile.yaml`의 `nav_extra`에 항목을 추가하세요.

### 사이드바 링크 추가하기

`content/links.yaml`에 항목을 하나 추가하면 됩니다.

```yaml
- label: "ORCID"
  href: "https://orcid.org/0000-0000-0000-0000"
  icon: orcid
```

`icon`에 쓸 수 있는 이름: `linkedin`, `cv`, `scholar`, `github`, `email`, `orcid`,
`twitter`, `bluesky`, `website`, `semantic-scholar`, `dblp`, `youtube`, `link`.
모르는 이름을 쓰면 기본 링크 아이콘이 표시됩니다.

### 논문 추가하기

```yaml
- title: "Paper title"
  authors: ["Your Name", "Coauthor"]
  venue: "NeurIPS"
  year: 2026
  selected: true          # 생략하면 false
  note: "Oral"            # 선택
  links:
    PDF: "https://..."
    Code: "https://github.com/..."
    BibTeX: "bib/paper.bib"
```

저자 목록에서 `profile.yaml`의 `author_aliases`와 같은 이름은 자동으로 굵게 표시됩니다.
연도별 정렬은 자동이고, 같은 연도 안에서는 파일에 적은 순서를 따릅니다.
`selected`가 하나도 없으면 홈에는 최신 논문 `recent_count`개가 대신 표시됩니다.

### 사진과 CV 파일

`static/` 폴더에 넣은 파일은 그대로 사이트 루트에 복사됩니다.

- 사진: `static/photo.jpg`를 넣고 `profile.yaml`의 `photo: "photo.jpg"`로 지정
- CV: `static/cv.pdf`를 넣으면 `links.yaml`과 내비의 `cv.pdf` 링크가 동작

## 구조

```
content/       ← 여기만 고치면 됩니다
templates/     base.html(공통 뼈대) + index / publications / teaching (Jinja2)
static/        style.css, 사진, PDF 등 그대로 복사되는 파일
build.py       YAML + 템플릿 → dist/
dist/          빌드 결과 (git에 올리지 않음)
```

## 배포 (GitHub Pages)

`main`은 뼈대만 유지하고, 본인 내용은 별도 브랜치에 채워서 배포합니다.

1. 개인 브랜치를 만들고 `content/`와 `static/`(사진, CV)을 채웁니다.
2. `.github/workflows/deploy.yml`의 `branches:` 에 그 브랜치 이름을 적습니다.
3. 저장소 **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 한 번만 바꿉니다.
4. 개인 브랜치에 push하면 Actions가 `build.py`를 실행해 `dist/`를 배포합니다.
   주소는 `https://<user>.github.io/<repo>/` 입니다.

템플릿을 고친 뒤에는 `main`에 커밋하고 개인 브랜치에서 `git merge main`으로 가져옵니다.
내용 파일(`content/`, `static/`)과 코드 파일이 분리되어 있어 충돌이 거의 나지 않습니다.
모든 링크가 상대 경로라서 하위 경로(`/<repo>/`)에서도 별도 설정 없이 동작합니다.
