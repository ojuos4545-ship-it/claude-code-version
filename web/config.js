// 배포할 때 API 서버 주소로 바꾼다. 서버의 APP_CORS_ORIGINS에 이 웹의 출처가 있어야 한다.
export const config = {
  apiBase: "http://localhost:8000",
  // true면 서버 없이 브라우저 저장소로만 동작하는 체험 모드(demo-api.js). 화면 확인용.
  demo: false,
};
