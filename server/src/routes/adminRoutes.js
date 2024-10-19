const express = require('express');
const router = express.Router();

const { getAdminData, updateWarning, deleteUser, checkAdmin, getUserWarningCount, checkUser } = require('../controllers/AdminController');

// 관리자 데이터 가져오기 (관리자 권한 필요)
router.get('/admin', checkAdmin, getAdminData);
// 경고 업데이트 (관리자 권한 필요)
router.post('/warning', checkAdmin, updateWarning);
// 사용자 삭제 (관리자 권한 필요)
router.delete('/delete/:id', checkAdmin, deleteUser);
// 경고 횟수 조회 (일반 사용자도 가능)
router.get('/warning-count', checkUser, getUserWarningCount); // 일반 사용자도 접근 가능하도록 수정

module.exports = router;





