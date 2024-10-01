const pool = require('../config/database'); // db 대신 pool을 사용

const getComponentsUserInfo = async (req, res) => {
    const userId = req.session.userId; // 세션에서 사용자 ID 가져오기
    
    if (!userId) {
        console.warn('[WARN] Components No userId in session. 로그인이 필요합니다.');
        return res.status(401).json({ message: '로그인이 필요합니다.' });
    }
    
    const query = `
        SELECT uk_permission 
        FROM tb_user_key 
        WHERE user_id = ?
        `;

    try {
        // pool.query를 사용하여 데이터베이스 쿼리 실행
        const rows = await pool.query(query, [userId]);
        // 사용자가 있는지 확인
        if (rows.length > 0) {
        const isAdmin = rows[0].uk_permission === 0; // 관리자 여부 확인
        console.log('[LOG] User found. Admin status:', isAdmin); // 관리자 여부 로그 출력
        res.json({ isAdmin }); // 클라이언트로 권한 정보 전달
        } else {
        res.status(404).json({ message: 'User not found' }); // 사용자가 없는 경우 처리
        }
    } catch (err) {
        console.error(err); // 에러 로그 출력
        res.status(500).send('Error fetching user info'); // 에러 응답
    }
};

module.exports = { 
    getComponentsUserInfo 
};
