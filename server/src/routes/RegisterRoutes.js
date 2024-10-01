const express = require('express');
const { postUserRegister, postEmailCode, postCheckEmail, postConfirmCode } = require('../controllers/RegisterController');
const router = express.Router();

// 회원가입 관련 라우트 설정
router.post('/userdata', postUserRegister);   // 회원가입 처리
router.post('/useremail', postCheckEmail);    // 이메일 중복 확인
router.post('/usercheckcode', postEmailCode); // 이메일 인증 코드 발송
router.post('/userconfirmcode', postConfirmCode); // 인증 코드 확인

module.exports = router;
