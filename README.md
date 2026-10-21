# HUROM Electronics Weekly

매주 공개 RSS/기술자료를 수집해 `data/weekly.json`을 갱신하는 정적 사이트입니다.

## 자동 업데이트
- GitHub Actions: 매주 월요일 00:00 UTC (한국시간 월요일 09:00)
- 수동 실행: Actions > Weekly Electronics Update > Run workflow
- 데이터: `scripts/update_weekly.py`가 공개 RSS를 읽고 키워드 필터링 후 저장
- 배포: GitHub 저장소를 Vercel 프로젝트에 연결하면 push 시 자동 배포

## 중요
공급사 RSS URL은 사이트 개편에 따라 바뀔 수 있습니다. 실제 배포 전 `FEEDS` URL의 현재 유효성을 확인하세요. 이 패키지는 외부 기사를 복제하지 않고 제목/짧은 메타 설명/원문 링크만 저장하도록 구성했습니다.

## 확장 포인트
- ST/TI 외 Infineon, NXP, Renesas, onsemi 등 공식 Feed/API 추가
- AI 요약은 별도 API 키를 GitHub Secrets에 저장한 뒤 스크립트에 연결
- 키워드: BLDC, PMSM, Sensorless, inverter, MOSFET, current sensing, MCU 등
