const pool = require('../config/database');

const checkAdmin = async (req, res, next) => {
  const userId = req.session.userId;  
  if (!userId) {
    return res.status(401).json({ error: '로그인이 필요합니다.' });  
  }
  try {
    // 데이터베이스에서 해당 사용자의 uk_permission 값을 조회
    const rows = await pool.query(`
      SELECT uk_permission 
      FROM tb_user_key 
      WHERE user_id = ?
      `, [userId]);
    console.log(`userId: ${userId}, uk_permission: ${rows[0]?.uk_permission}`);
    if (rows.length > 0 && rows[0].uk_permission === 0) {
      next();  
    } else {
      res.status(403).json({ error: '접근 권한이 없습니다.' });  
    }
  } catch (error) {
    console.error('Error checking admin permission:', error);
    res.status(500).json({ error: '서버 오류가 발생했습니다.' });`  `
  }
};

// 사용자 권한 확인 미들웨어 (관리자 권한 필요 없음)
const checkUser = async (req, res, next) => {
  const userId = req.session.userId;
  if (!userId) {
    return res.status(401).json({ 
      error: '로그인이 필요합니다.' 
    });
  }
  next();
};
// 경고 횟수 조회 함수
const getUserWarningCount = async (req, res) => {
  const userId = req.session.userId; 
  if (!userId) {
    return res.status(401).json({ error: '로그인이 필요합니다.' });
  }
  try {
    const result = await pool.query('SELECT ui_caution FROM tb_user_information WHERE user_id = ?', [userId]);
    if (result.length === 0) {
      return res.status(404).json({ error: '사용자 정보를 찾을 수 없습니다.' });
    }
    res.json({ warningCount: result[0].ui_caution });
  } catch (error) {
    console.error('Error fetching user warning count:', error);
    res.status(500).json({ error: '서버 오류가 발생했습니다.' });
  }
};

const getAdminData = async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
          uk.user_id AS "user_id",
          ui.ui_name AS "이름",
          uk.uk_email AS "Email",
          TO_CHAR(ui.ui_birth_date, 'YYYY-MM-DD') AS "생년월일",
          CASE 
              WHEN ui.ui_sex = 0 THEN '남자'
              WHEN ui.ui_sex = 1 THEN '여자'
              ELSE '알 수 없음'
          END AS "성별",
          CASE 
              WHEN uk.uk_permission = 0 THEN '관리자'
              WHEN uk.uk_permission = 1 THEN '유저'
              ELSE '알 수 없음'
          END AS "사용자권한",
          ui.ui_phone_number AS "모바일",
          ui.ui_caution AS "경고 횟수" 
      FROM 
          tb_user_key uk
      JOIN 
          tb_user_information ui
      ON 
          uk.user_id = ui.user_id
      WHERE 
          uk.user_id != 1
      ORDER BY 
          uk.uk_permission ASC, uk.user_id ASC;
    `);
    if (result.length === 0) {
      return res.status(404).json({ error: 'Admin data not found' });
    }
    // sessionId를 각 유저 데이터에 추가
    const adminDataWithSessionId = result.map(user => ({
      ...user,
      sessionId: req.sessionID 
    }));

    res.json({ data: adminDataWithSessionId });
  } catch (error) {
    console.log('Error fetching Admin data : ', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

const updateWarning = async (req, res) => {
  try {
    const { user_id, warningCount } = req.body;
    console.log(`User ID: ${user_id}, New Warning Count: ${warningCount}`);
    const result = await pool.query(`
      UPDATE tb_user_information
      SET ui_caution = ? 
      WHERE user_id = ? 
    `, [warningCount, user_id]);
    console.log(`경고 횟수가 성공적으로 업데이트되었습니다. User ID: ${user_id}, Warning Count: ${warningCount}`);
    res.status(200).json({ message: 'Warning count updated successfully' });
  } catch (error) {
    console.log('Error updating warning:', error);
    res.status(500).json({ error: 'Failed to update warning count' });
  }
};

const deleteUser = async (req, res) => {
  try {
    const { id } = req.params;
    console.log(`삭제: User ID ${id}`);
    const result = await pool.query(`
      DELETE FROM tb_user_information
      WHERE user_id = ?;
    `, [id]);
    console.log(`User ID ${id} 삭제 완료`);
    res.status(200).json({ message: `User ID ${id} deleted successfully` });
  } catch (error) {
    console.log('Error deleting user:', error);
    res.status(500).json({ error: 'Failed to delete user' });
  }
};

module.exports = {
  getAdminData,
  updateWarning,
  deleteUser,  
  checkAdmin,  
  getUserWarningCount, // 경고 횟수 조회 함수 추가
  checkUser,
};
