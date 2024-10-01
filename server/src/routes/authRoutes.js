const express = require('express');
const router = express.Router();
const userLoginController = require('../controllers/userLoginController');
const sessionChecker = require('../middlewares/sessionChecker');

// 로그인 라우트
router.post('/login', userLoginController.login);

// 로그아웃 라우트
router.post('/logout', userLoginController.logout);

// 세션 확인 라우트 (세션 유지 확인)
// sessionChecker에서 세션이 유효하다면, 이 라우트 핸들러로 넘어옴
router.get('/check-session', sessionChecker, userLoginController.checkSession);

// 프로필 확인 라우트 (세션 기반 보호)
router.get('/profile', sessionChecker, userLoginController.getProfile);

// 에러 처리 미들웨어
router.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: '서버 오류가 발생했습니다.' });
});

module.exports = router;
