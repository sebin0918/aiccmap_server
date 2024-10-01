const pool = require('../config/database');

// 데이터를 가져오는 함수
const getHouseHoldData = async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT rp.rp_date, rp.rp_amount, rp.rp_detail, rp.rp_part
      FROM tb_received_paid rp
      WHERE rp.user_id = 1;
    `);

    if (result.length === 0) {
      return res.status(404).json({ error: 'HouseHold data not found' });
    }

    res.json({ data: result });
  } catch (error) {
    console.log('Error fetching HouseHold data : ', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 새로운 데이터를 저장하는 함수
const addHouseHoldData = async (req, res) => {
  try {
    const { rp_date, rp_amount, rp_detail, rp_hold } = req.body;


    // 입력 값 검증
    if (!rp_date || !rp_amount || !rp_detail) {
      return res.status(400).json({ message: "Required fields are missing" });
    }

    // 날짜를 로컬 시간으로 변환
    const localDate = new Date(rp_date).toLocaleString('en-US', { timeZone: 'Asia/Seoul' });

    const result = await pool.query(`
      INSERT INTO tb_received_paid (rp_date, rp_amount, rp_detail, rp_hold, user_id)
      VALUES (?, ?, ?, ?, 1)
    `, [localDate, rp_amount, rp_detail, rp_hold]);

    res.json({ message: 'Data inserted successfully', data: result });
  } catch (error) {
    console.log('Error adding data: ', error);
    res.status(500).json({ error: 'Internal server error', details: error.message });
  }
};


module.exports = {
  getHouseHoldData,
  addHouseHoldData,
};
