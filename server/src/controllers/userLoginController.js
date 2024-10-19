const pool = require('../config/database');
const bcrypt = require('bcryptjs');
require('dotenv').config(); // .env 파일 로드

//유저 확인함수
const getUserByEmail = async (conn, email) => {
  const users = await conn.query('SELECT * FROM tb_user_key WHERE uk_email = ?', [email.trim()]);

  // users 배열이 있는지와 첫 번째 요소가 존재하는지 확인
  if (users && users.length > 0) {
    return users[0];  // 첫 번째 사용자를 반환
  } else {
    return null;  // 사용자 없음
  }
};


exports.login = async (req, res) => {
  const { user_email, user_password } = req.body;

  if (!user_email || !user_password) {
    return res.status(400).json({ message: '이메일과 비밀번호를 제공해주세요.' });
  }

  let conn;
  try {
    conn = await pool.getConnection();
    const user = await getUserByEmail(conn, user_email);

    if (user) {
      const passwordMatch = await bcrypt.compare(user_password, user.uk_password);  // `uk_password`로 사용

      if (passwordMatch) {
        req.session.userId = user.user_id; // 세션에 user_id 저장
        req.session.save((err) => {
          if (err) {
            return res.status(500).json({ message: '세션 저장 중 오류가 발생했습니다.' });
          }
          res.status(200).json({ message: '로그인 성공', userId: user.user_id });
        });
      } else {
        res.status(401).json({ message: '비밀번호가 일치하지 않습니다.' });
      }
    } else {
      res.status(401).json({ message: '등록된 이메일이 없습니다.' });
    }
  } catch (err) {
    console.error('로그인 중 오류 발생:', err);
    res.status(500).json({ message: '서버 오류 발생', error: err.message });
  } finally {
    if (conn) conn.release();
  }
};

// 프로필 확인 (세션 기반)
exports.getProfile = async (req, res) => {
  if (!req.session.userId) { 
    console.warn('No active session. Redirecting to login.');  // 세션이 없을 경우 로그
    return res.status(401).json({ message: '로그인이 필요합니다.' });
  }

  let conn;
  try {
    conn = await pool.getConnection();

    // tb_user_key와 tb_user_information을 조인하여 데이터 가져오기
    const [users] = await conn.query(
      `SELECT tb_user_key.user_id, tb_user_key.uk_email, tb_user_information.ui_name 
       FROM tb_user_key 
       LEFT JOIN tb_user_information ON tb_user_key.user_id = tb_user_information.user_id 
       WHERE tb_user_key.user_id = ?`, 
      [req.session.userId]
    );

    // 쿼리 결과가 배열로 처리되도록 수정
    const userArray = Array.isArray(users) ? users : [users];

    if (userArray.length > 0) {
      const user = userArray[0];
      res.json({ id: user.user_id, username: user.ui_name, email: user.uk_email });
    } else {
      console.warn("No user found with the provided session ID.");  // 사용자 정보를 찾을 수 없을 때
      res.status(404).json({ message: '사용자 정보를 찾을 수 없습니다.' });
    }
  } catch (err) {
    console.error("Error during profile retrieval:", err);  // 오류 발생 시
    res.status(500).json({ message: '서버 오류 발생' });
  } finally {
    if (conn) conn.release();
  }
};

// 로그아웃 기능 , 세션과 쿠키를 모두 삭제하도록 작성
exports.logout = (req, res) => {
  req.session.destroy((err) => { // 세션 삭제
    if (err) {
      return res.status(500).json({ message: '로그아웃 중 오류가 발생했습니다.' });
    }
    res.clearCookie('connect.sid'); // 세션 쿠키 삭제, 클라이언트의 세션 쿠키를 삭제한다.
    return res.status(200).json({ message: '로그아웃 성공' });
  });
};

// 세션 상태 확인 기능 
exports.checkSession = (req, res) => {
  if (req.session && req.session.userId) {
    res.status(200).json({ message: 'Session is valid.', userId: req.session.userId });
  } else {
    console.warn('Invalid session access attempt detected. No active session.');
    res.status(401).json({ message: 'No active session. Please log in first.' });
  }
};
