
# YouTube Content Search

[English](README.md) | [한국어](README.ko.md)

[변경 사항](CHANGELOG.md)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-v1.2.0-blue.svg?style=for-the-badge)
[![Ko-fi 후원](https://img.shields.io/badge/Ko--fi-Support%20Me-F16061?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/plplaaa2)

Home Assistant에서 YouTube 영상을 검색하고 TV에서 재생할 수 있는 통합입니다.
호환되는 LLM 대화 에이전트와 연동하면 음성 명령으로도 YouTube 재생을 제어할 수 있습니다.

## 주요 기능

- **YouTube 검색 및 재생** — 검색어로 영상을 찾아 첫 번째 검색 결과를 재생합니다.
- **직접 재생** — YouTube URL, 동영상 ID 또는 재생목록 URL로 재생합니다.
- **다양한 재생 방식** — 공식 YouTube 앱, SmartTube, Google Cast를 지원합니다.
- **음성 제어** — 호환되는 LLM 대화 에이전트에 재생 도구를 연결할 수 있습니다.
- **재생 방식 설정** — 통합 설정에서 재생 모드와 관련 옵션을 선택할 수 있습니다.

사이드바 패널과 HTTP 검색 엔드포인트는 현재 비활성화되어 있습니다.

## 요구 사항

- Home Assistant
- YouTube Data API v3 API 키
- 재생 방식에 맞는 기기 및 통합:
  - **공식 YouTube 앱 / SmartTube:** Android TV Remote 및 Google Cast 통합
  - **Google Cast 전용:** Google Cast `media_player` 엔티티
- 음성 제어 사용 시: LLM 도구 호출을 지원하는 대화 에이전트

## 설치

### HACS 설치 (권장)

[![Home Assistant에서 HACS 저장소 열기](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=plplaaa2&repository=https%3A%2F%2Fgithub.com%2Fplplaaa2%2Fyoutube_content_search&category=integration)

위 버튼을 눌러 HACS에서 통합을 설치합니다.

### 수동 설치

`custom_components/youtube_content_search` 폴더를 Home Assistant 설정 디렉터리의 다음 경로에 복사합니다.

`/config/custom_components/youtube_content_search`

### 초기 설정

1. Google Cloud에서 **YouTube Data API v3**를 활성화하고 API 키를 발급받습니다.
2. 필요한 Google Cast 및/또는 Android TV Remote 통합을 설정합니다.
3. Home Assistant를 재시작합니다.
4. **설정 → 기기 및 서비스 → 통합 추가**로 이동합니다.
5. **YouTube Content Search**를 검색하고 API 키와 재생 모드를 설정합니다.

설정을 변경하면 이후 실행되는 액션부터 적용됩니다.

## 재생 모드

| 모드 | 재생 방식 | 필요한 엔티티 |
| --- | --- | --- |
| 공식 YouTube 앱 → Cast 대체 재생 | TV의 YouTube 앱으로 영상을 열고, Remote 액션에서 오류가 반환되면 Cast 재생을 시도합니다. | Android TV Remote `remote` + Cast `media_player` |
| SmartTube → Cast 대체 재생 | SmartTube의 `vnd.youtube.launch` 링크로 영상을 열고, Remote 액션에서 오류가 반환되면 Cast 재생을 시도합니다. | Android TV Remote `remote` + Cast `media_player` |
| Google Cast 전용 | Cast 플레이어에 영상을 직접 전달합니다. | Cast `media_player` |

앱 실행 방식에서는 TV에 해당 앱이 설치되어 있어야 합니다. SmartTube를 사용할 경우 Android TV에서 YouTube 링크의 기본 앱으로 지정하라는 메시지가 표시되면 SmartTube를 선택합니다.

대체 재생은 Remote 액션이 오류를 반환할 때 시도됩니다. 앱이 오류 없이 실행에 실패하는 모든 경우를 감지할 수 있는 것은 아닙니다. 딥 링크 처리 방식은 TV 기기와 앱 버전에 따라 다를 수 있습니다.

## 사용 방법

**개발자 도구 → 액션**에서 `youtube_content_search.search_play`를 실행하거나 자동화 및 스크립트에서 호출할 수 있습니다.

### 검색해서 재생하기

```yaml
action: youtube_content_search.search_play
data:
  query: "아이유 라이브"
  entity_id: remote.living_room_tv
```

`entity_id`에는 선택한 재생 모드에 맞는 엔티티를 지정합니다.

- 앱 실행 모드: Android TV Remote의 `remote` 엔티티
- Google Cast 전용 모드: Cast의 `media_player` 엔티티

### URL로 직접 재생하기

검색 없이 재생하려면 `query` 대신 `video`를 사용합니다. YouTube URL, 11자리 동영상 ID 또는 재생목록 URL을 지정할 수 있습니다.

```yaml
action: youtube_content_search.search_play
data:
  video: "https://youtu.be/dQw4w9WgXcQ"
  entity_id: remote.living_room_tv
```

재생목록 URL을 전달하면 첫 번째로 재생 가능한 영상을 확인한 후 재생목록 ID를 YouTube에 전달하여 목록의 다음 영상도 이어서 재생할 수 있도록 합니다.

재생목록 조회에는 YouTube Data API가 필요합니다. API 키만으로는 비공개 재생목록에 접근하지 못할 수 있습니다.

`query`와 `video`는 둘 중 하나만 지정해야 합니다.

## Assist 음성 제어 연동

이 통합은 다음 LLM 도구를 제공합니다.

`youtube_content_search__search_play`

도구는 `query` 또는 `video`와 `entity_id`를 입력받습니다.

### 설정 방법

1. 통합을 설치하거나 업데이트한 후 Home Assistant를 재시작합니다.
2. **설정 → 음성 어시스턴트**에서 필요한 Android TV Remote 및/또는 Cast 플레이어 엔티티를 Assist에 노출합니다.
3. 사용 중인 대화 에이전트의 설정을 엽니다.
4. Home Assistant 버전과 에이전트에 따라 **도구 제공자(Tool providers)** 또는 **Control Home Assistant / LLM API**에서 **YouTube Content Search**를 선택합니다.
5. 해당 대화 에이전트를 사용해 음성 명령을 실행합니다.

예시:

> 거실 TV에서 아이유 라이브 틀어 줘.

이 도구는 기본 내장 Assist API에 자동으로 추가되지 않습니다. 기본 대화 에이전트는 이 LLM 도구를 직접 호출하지 않으므로, 도구 호출을 지원하는 호환 에이전트가 필요합니다.

도구는 선택한 재생 모드에 맞는 대상 엔티티인지 확인하고 액션을 실행하기 전에 해당 엔티티가 통합 소유인지 다시 확인합니다. 앱 실행 모드에서는 Android TV Remote와 Cast 플레이어가 모두 필요합니다.

도구가 성공을 반환하더라도 이는 재생 요청이 전송되었다는 의미이며, 실제 영상이나 오디오가 재생되기 시작했음을 보장하지는 않습니다. API 키와 원본 백엔드 오류는 LLM에 전달되지 않습니다.

도구 제공자가 표시되지 않는다면 통합이 설치되어 있고 Home Assistant 재시작 후 정상적으로 로드되었는지 확인한 다음, 대화 에이전트 설정을 다시 엽니다.

## 문제 해결

### 검색 오류 또는 검색 결과 없음

- Google Cloud에서 YouTube Data API v3가 활성화되어 있는지 확인합니다.
- API 키와 API 제한 설정을 확인합니다.
- API 할당량 사용량을 확인합니다.

API 오류와 검색 결과 없음은 액션 오류로 보고됩니다. 오류 메시지에는 HTTP 상태 코드와 허용 목록에 포함된 오류 코드가 표시되며, API 키·요청 URL·원본 응답 내용은 노출되지 않습니다.

주요 오류 예시:

- `SERVICE_DISABLED` — API가 활성화되어 있는지 확인합니다.
- `API_KEY_INVALID` — API 키를 확인합니다.
- `quotaExceeded` — API 할당량을 확인합니다.
- `invalidFilters` — 요청 필터를 확인합니다.

알 수 없는 오류 코드나 JSON이 아닌 응답은 `reason: UNKNOWN`으로 표시됩니다.

### 영상이 재생되지 않는 경우

- 선택한 재생 모드와 지정한 엔티티가 일치하는지 확인합니다.
- 앱 실행 모드에서는 Android TV Remote 연결과 TV 앱 설치 상태를 확인합니다.
- 대체 재생을 사용한다면 Google Cast 플레이어가 사용 가능한지 확인합니다.
- 액션 성공 응답만으로 실제 재생 여부를 판단할 수 없다는 점에 유의합니다.

### 업데이트 및 제거

통합 파일을 업데이트한 후 Home Assistant를 재시작합니다.

통합을 제거하려면 **설정 → 기기 및 서비스**에서 해당 통합 항목을 삭제합니다. 항목을 삭제하면 런타임 인증 정보가 제거됩니다.

그런 다음 HACS에서 통합을 제거하거나 수동 설치 폴더를 삭제하고 Home Assistant를 재시작합니다.

## 보안 및 개인정보 보호

API 키는 Home Assistant의 config entry에 저장됩니다. 이 통합은 별도의 암호화 기능을 제공하지 않으므로 Home Assistant 설정 파일과 백업을 안전하게 관리해야 합니다.

자동화 YAML에 실제 API 키를 직접 입력할 필요는 없습니다.

## 개발 및 테스트

테스트는 Home Assistant 인터페이스를 모의 객체로 대체하여 실행합니다. 도구 제공자 설정 및 재로드, API 도구 검색, 권한 확인, 오류 처리를 검증합니다.

실제 Home Assistant에서의 설정 로드, API 인증 및 TV 재생은 별도로 확인해야 합니다.

Windows 환경에서는 Python에 `aiohttp`와 `voluptuous`를 설치한 후 다음 명령을 실행합니다.

```powershell
python -B -m unittest discover -s tests -v
```

HACS 검증 GitHub Actions는 코드 푸시, Pull Request, 일일 실행 및 수동 실행 시 작동합니다.

## 공식 문서

- [Home Assistant LLM API 및 도구 제공](https://developers.home-assistant.io/docs/core/llm/)
- [Home Assistant 통합 manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant 사용자 정의 통합 번역](https://developers.home-assistant.io/docs/internationalization/custom_integration/)
- [Google Cast YouTube 재생](https://www.home-assistant.io/integrations/cast/#youtube)
- [YouTube 동영상 메타데이터 API](https://developers.google.com/youtube/v3/docs/videos/list)
- [HACS 게시 요구 사항](https://www.hacs.xyz/docs/publish/integration/)
