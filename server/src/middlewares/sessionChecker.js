const sessionChecker = (req, res, next) => {
    try {
      console.log(`[세션 검사] 현재 세션: ${JSON.stringify(req.session)}`); // 세션 정보를 로그에 출력
      
      if (req.session.userId) {  // 세션에 userId가 있는지 확인
        console.log(`[${new Date().toISOString()}] 세션이 유효합니다. userId: ${req.session.userId}`);

        // 세션이 유효하므로 req.user에 사용자 정보를 설정
        req.user = { id: req.session.userId };  // 이 부분을 추가
        
        // 세션이 유효하므로 다음 미들웨어 또는 라우트로 진행
        next();  
      } else { // 세션에 userId가 없는 경우
        console.warn(`[${new Date().toISOString()}] U                                 nauthorized access attempt detected. Request URL: ${req.originalUrl}, Method: ${req.method}`);
        // 세션이 존재할 때만 무효화 시도
        if (req.session) {  
            // 세션 무효화
            req.session.destroy((err) => { 
              // 세션 무효화 중 오류 발생 시
              if (err) { 
                console.error('세션 무효화 중 오류 발생:', err);
              }
            }); 
          }
        res.status(401).json({ message: '로그인이 필요합니다. 다시 로그인해주세요.' });
      }
    } catch (error) {
      console.error(`[${new Date().toISOString()}] Error during session check:`, error);
      res.status(500).json({ message: '서버 오류가 발생했습니다.' });
    }
  };
  
  module.exports = sessionChecker; 
  