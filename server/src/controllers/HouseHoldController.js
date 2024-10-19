const pool = require('../config/database');

const login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const result = await pool.query(`SELECT * FROM users WHERE email = ?`, [email]);
    const user = result[0];

    if (!user || user.password !== password) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    req.session.userId = user.id; 
    res.json({ message: 'Login successful', userId: user.id });
  } catch (error) {
    console.log('Error logging in:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 데이터를 가져오는 함수
const getHouseHoldData = async (req, res) => {
  try {
    const userId = req.session.userId;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized: No user session found' });
    }
    // 쿼리 실행 - rp_id 필드도 함께 가져오는지 확인
    const query = `
      SELECT rp.rp_id, 
             rp.user_id, 
             rp.rp_date, 
             rp.rp_amount, 
             rp.rp_detail, 
             rp.rp_part
      FROM tb_received_paid rp
      WHERE rp.user_id = ?
      AND rp.rp_date >= DATE_SUB(CURDATE(), 
                                 INTERVAL 2 MONTH)
    `;
    const result = await pool.query(query, [userId]);
    if (result.length === 0) {
      return res.status(404).json({ error: 'HouseHold data not found' });
    }

    res.json({ data: result });
  } catch (error) {
    console.log('Error fetching HouseHold data:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 검색을 위한 함수 추가
const searchHouseHoldData = async (req, res) => {
  try {
    const userId = req.session.userId;
    const searchQuery = req.body.searchQuery;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized: No user session found' });
    }
    if (!searchQuery) {
      return res.status(400).json({ error: 'Search query is required' });
    }

    // 쿼리 실행
    const result = await pool.query(`
      SELECT rp.rp_date, rp.rp_detail, 
            CASE WHEN rp.rp_part = 0 
            THEN '입금' 
            ELSE '지출' 
            END as rp_part, 
                   rp.rp_amount
      FROM tb_received_paid rp
      WHERE rp.user_id = ? 
      AND rp.rp_detail LIKE ?
      ORDER BY rp.rp_date DESC;
    `, [userId, `%${searchQuery}%`]);

    if (result.length === 0) {
      return res.status(404).json({ error: 'No matching records found' });
    }
    res.json({ data: result });
  } catch (error) {
    console.log('Error searching HouseHold data: ', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 새로운 데이터를 저장하는 함수
const addHouseHoldData = async (req, res) => {
  try {
    const userId = req.session.userId;
    console.log('Session user_id:', userId); // 세션에 저장된 user_id 확인
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized: No user session found' });
    }
    const { rp_date, rp_amount, rp_detail, rp_hold, rp_part } = req.body;
    // 필수 필드가 존재하는지 확인
    if (!rp_date || !rp_amount || !rp_detail) {
      return res.status(400).json({ message: 'Required fields are missing' });
    }
    // rp_amount가 숫자인지 확인
    if (typeof rp_amount !== 'number' || isNaN(rp_amount)) {
      return res.status(400).json({ error: 'Invalid amount, please enter a valid number.' });
    }
    if (rp_amount < 0) {
      return res.status(400).json({ error: 'Amount cannot be less than zero.' });
    }
    const localDate = new Date(rp_date).toISOString().split('T')[0];

    const result = await pool.query(`
      INSERT INTO tb_received_paid (rp_date, 
                                    rp_amount, 
                                    rp_detail, 
                                    rp_hold, 
                                    rp_part, 
                                    user_id)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [localDate, rp_amount, rp_detail, rp_hold, rp_part, userId]);
    const insertId = result.insertId.toString();  // BigInt 값을 문자열로 변환
    res.json({ message: 'Data inserted successfully', insertId });
  } catch (error) {
    console.error('Error adding data: ', error);
    res.status(500).json({ error: 'Internal server error', details: error.message });
  }
};
// 메모 저장/업데이트 함수 추가
const saveOrUpdateMemo = async (req, res) => {
  try {
    const userId = req.session.userId;
    const { selectedDate, fm_memo } = req.body;
    if (!userId || !selectedDate || !fm_memo) {
      return res.status(400).json({ message: 'All fields are required' });
    }
    // user_id와 fm_date 조합으로 메모 존재 여부 확인
    const existingMemo = await pool.query(`
      SELECT * 
      FROM tb_finance_memo 
      WHERE user_id = ? 
      AND fm_date = ?
    `, [userId, selectedDate]);
    if (existingMemo.length > 0) {
      // 기존 메모가 있으면 업데이트
      await pool.query(`
        UPDATE tb_finance_memo 
        SET fm_memo = ? 
        WHERE user_id = ? 
        AND fm_date = ?
      `, [fm_memo, userId, selectedDate]);
      return res.status(200).json({ message: 'Memo updated successfully' });
    } else {
      // 메모가 없으면 삽입
      await pool.query(`
        INSERT INTO tb_finance_memo (user_id, 
                                    fm_date, 
                                    fm_memo)
        VALUES (?, ?, ?)
      `, [userId, selectedDate, fm_memo]);
      return res.status(201).json({ message: 'Memo saved successfully' });
    }
  } catch (error) {
    console.error('Error saving/updating memo:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
};

const getMemo = async (req, res) => {
  const userId = req.session.userId;  // userId 확인
  const { date } = req.query;
  if (!userId) {
    return res.status(401).json({ message: 'Unauthorized: No user session found' });
  }
  try {
    const [memo] = await pool.query(`
      SELECT fm_memo 
      FROM tb_finance_memo 
      WHERE fm_date = ? 
      AND user_id = ?
    `, [date, userId]);  // userId도 추가하여 메모를 가져옴
    if (memo.fm_memo.length > 0) {
      return res.status(200).json({ memo: memo.fm_memo });
    } else {
      return res.status(404).json({ message: 'Memo not found for this date' });
    }
  } catch (error) {
    console.error('Error fetching memo:', error);
    return res.status(500).json({ message: 'Server error' });
  }
};

// 가계부 데이터를 삭제하는 함수
const deleteHouseHoldData = async (req, res) => {
  try {
    const userId = req.session.userId;  
    const { rp_id } = req.query;       

    // userId와 rp_id가 없는 경우 에러 반환
    if (!rp_id || !userId) {
      return res.status(400).json({ message: "Record ID (rp_id) and user ID must be provided" });
    }

    // 데이터베이스에서 해당 user_id와 rp_id에 맞는 데이터를 삭제
    const result = await pool.query(`
      DELETE 
      FROM tb_received_paid
      WHERE user_id = ? 
      AND rp_id = ?;
    `, [userId, rp_id]);

    // affectedRows로 삭제된 행이 있는지 확인
    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Record not found or unauthorized' });
    }

    // 성공적으로 삭제된 경우
    res.json({ message: 'Record deleted successfully' });
  } catch (error) {
    console.error('Error deleting record:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

module.exports = {
  login, // 로그인 함수 추가
  getHouseHoldData,
  searchHouseHoldData, // 검색 함수 추가
  addHouseHoldData,
  saveOrUpdateMemo, // 메모 저장/업데이트 함수 추가
  deleteHouseHoldData, // 삭제 함수 추가
  getMemo,
};
