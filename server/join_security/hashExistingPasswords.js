const pool = require('../src/config/database');
const bcrypt = require('bcryptjs');
const saltRounds = 10;

const updatePasswords = async () => {
    let conn;
    try {
        conn = await pool.getConnection();
        
        // 데이터베이스에서 모든 사용자의 ID와 비밀번호를 가져옴
        const users = await conn.query('SELECT user_id, uk_email, uk_password FROM tb_user_key');

        for (let user of users) {
            // 비밀번호가 이미 해시된 상태인지 확인 (bcrypt 해시의 길이는 60)
            if (user.uk_password.length !== 60) {
                console.log(`Updating password for user ID: ${user.user_id}`);

                // 비밀번호를 해시로 변환
                const hashedPassword = await bcrypt.hash(user.uk_password, saltRounds);

                // 데이터베이스에 업데이트
                await conn.query('UPDATE tb_user_key SET uk_password = ? WHERE user_id = ?', [hashedPassword, user.user_id]);

                console.log(`Password updated for user ID: ${user.user_id}`);
            } else {
                console.log(`Password for user ID: ${user.user_id} is already hashed.`);
            }
        }

        console.log('모든 비밀번호가 안전하게 해시되었습니다.');
    } catch (err) {
        console.error('오류 발생:', err.message);
    } finally {
        if (conn) conn.release();
    }
};

// 스크립트 실행
updatePasswords();
