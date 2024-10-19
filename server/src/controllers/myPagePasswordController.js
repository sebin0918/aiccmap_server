const pool = require('../config/database');
const bcrypt = require('bcryptjs');

const postCheckPassword = async (req, res) => {
  const receivePassword = req.body.userpassword;
  const sessionId = req.session.userId;

  let connection;
  try {
    connection = await pool.getConnection();
    
    // SQL 쿼리 실행 시 세션 ID 값을 전달
    const query = "SELECT * FROM tb_user_key WHERE user_id = ?";
    const [result] = await connection.execute(query, [sessionId]);  // 세션 ID를 사용하여 조건 값 전달

    // 결과가 배열인 경우만 length 확인
    if (Array.isArray(result) && result.length === 0) {
      console.error('사용자를 찾을 수 없습니다.');
      return res.status(404).json({ message: '사용자를 찾을 수 없습니다.' });
    }

    // 비밀번호 비교를 위한 첫 번째 결과 값 가져오기
    const user = Array.isArray(result) ? result[0] : result;  // 배열이면 첫 번째 요소를 가져오고, 아니면 그대로 사용

    // 사용자 정보가 없을 경우 에러 처리
    if (!user || !user.uk_password) {
      console.error('사용자 정보에 비밀번호가 없습니다.');
      return res.status(404).json({ message: '사용자 정보에 비밀번호가 없습니다.' });
    }

    const isMatch = await bcrypt.compare(receivePassword, user.uk_password);

    if (isMatch) {
      res.status(200).json({ message: 'checkOk', id: user.user_id });  // 올바른 id로 변경
    } else {
      res.status(200).json({ message: 'checkNot', id: user.user_id });  // 올바른 id로 변경
    }
  } catch (err) {
    console.error('Password쿼리실행 에러:', err);
    res.status(500).send('서버 에러');
  } finally {
    if (connection) connection.release();
  }
}

module.exports = {
  postCheckPassword,
};
