# 사다리타기 (Client / Server 버전)

브라우저 클라이언트 1개 + 동일 API를 제공하는 서버 2종(Node.js / Python).
서버가 **세션 상태(참여자·Goal·확정 여부)** 를 저장하고, '사다리 시작' 시 서버가
사다리를 난수 생성하여 결과까지 계산해 반환합니다. 클라이언트는 받은 데이터로
**왼쪽 참여자부터 한 명씩** 경로를 색칠하며 Goal을 오픈합니다.

```
cs-version/
├── public/index.html      공용 클라이언트 (두 서버가 함께 사용)
├── node-server/           Node.js + Express
│   ├── server.js
│   └── package.json
└── python-server/         Python + Flask
    ├── app.py
    └── requirements.txt
```

## 실행 방법

### Node.js
```bash
cd cs-version/node-server
npm install
npm start
# → http://localhost:3000
```

### Python
```bash
cd cs-version/python-server
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

두 서버 중 아무거나 실행한 뒤 브라우저로 해당 주소에 접속하면 됩니다.
(상단의 "서버 세션"에 node / python 중 어느 서버에 붙었는지 표시됩니다.)

## REST API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/session` | 새 세션 생성 → `sessionId` 반환 |
| POST | `/api/session/:id/add` | `{kind:"participant"\|"goal", value}` 추가 |
| POST | `/api/session/:id/remove` | `{kind, index}` 삭제 (확정 전만) |
| POST | `/api/session/:id/lock` | `{kind}` 확정('완료') |
| POST | `/api/session/:id/start` | 사다리 생성 + 결과 계산, `ladder` 반환 |
| POST | `/api/session/:id/reset` | 세션 초기화 |

## 규칙
- 참여자: 무한 입력, 최소 2명, '완료'로 확정
- Goal(점심값): 개수 자유, 최소 1개, '완료'로 확정 (참여자보다 적으면 순환 배정되어 중복 당첨 가능)
- 시작 시 왼쪽부터 한 명씩 순차 애니메이션, 전원 도착 시 결과 표시 후 종료
