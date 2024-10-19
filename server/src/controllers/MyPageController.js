const pool = require('../config/database');
const bcrypt = require('bcryptjs');

// 유저 데이터 조회 함수
const getUserData = async (req, res) => {
  const userId = req.session.userId;  // 세션에 저장된 userId 사용
  console.log(userId);
    
  let connection;
  try {
    connection = await pool.getConnection();
    const query = "SELECT * FROM tb_user_key WHERE user_id = ?";
    const [result] = await connection.execute(query, [userId]);

    // result가 배열이 아니라 객체일 경우 바로 사용
    const userData = Array.isArray(result) ? result[0] : result;
    if (!userData) {  // result가 비어 있는지 확인
      console.error('사용자를 찾을 수 없습니다.');
      return res.status(404).json({ message: '사용자를 찾을 수 없습니다.' });
    }

    const user_id = userData.user_id;  // 첫 번째 결과의 user_id
    const ui_query = "SELECT * FROM tb_user_information WHERE user_id = ?";
    const [ui_result] = await connection.execute(ui_query, [user_id]);

    // 사용자 정보가 객체로 반환될 경우 바로 사용
    const userInfo = Array.isArray(ui_result) ? ui_result[0] : ui_result;
    if (!userInfo) {  // 배열이 비어 있는지 확인
      console.error('사용자 정보가 없습니다.');
      return res.status(404).json({ message: '사용자 정보를 찾을 수 없습니다.' });
    }

    const uf_query = "SELECT * FROM tb_user_finance WHERE user_id = ?";
    const [uf_result] = await connection.execute(uf_query, [user_id]);
    uf_result.uf_capital = uf_result.uf_capital.toString();

    // 사용자 금융 정보가 객체로 반환될 경우 바로 사용
    const userFinance = Array.isArray(uf_result) ? uf_result[0] : uf_result;
    if (!userFinance) {  // 배열이 비어 있는지 확인
      console.error('사용자 금융 정보가 없습니다.');
      return res.status(404).json({ message: '사용자 금융 정보를 찾을 수 없습니다.' });
    }

    // 클라이언트에서 기대하는 형식으로 데이터 변환
    const data = {
      name: userInfo.ui_name || '',
      email: userData.uk_email || '',
      gender: userInfo.ui_sex === 0 ? 'Male' : 'Female',
      birthdate: userInfo.ui_birth_date || '',
      mobile: userInfo.ui_phone_number || '',
      accountNo: userInfo.ui_bank_num || '',
      holdingAsset: userFinance.uf_capital || '',
    };

    res.status(200).json(data);
  } catch (err) {
    console.error('UserData 쿼리 실행 에러:', err);
    res.status(500).json({ message: '서버 에러', error: err.message });
  } finally {
    if (connection) connection.release();
  }
};


// 유저 정보 변경 함수
const putUserChangeData = async (req, res) => {
  const receiveData = req.body;
  receiveData.gender = receiveData.gender === 'Male' ? 0 : 1;

  let connection;
  try {

    if (receiveData.password) {  // 패스워드가 존재하는 경우에만 해시 처리
      receiveData.password = await bcrypt.hash(receiveData.password, 10);
    }

    connection = await pool.getConnection();
    await connection.beginTransaction();  // 트랜잭션 시작
    
    const query = "UPDATE tb_user_key SET uk_password=? WHERE uk_email = ?";
    const value = [receiveData.password, receiveData.email];
    const result = await connection.execute(query, value);
    
    const [return_id] = await connection.execute("SELECT user_id FROM tb_user_key WHERE uk_email = ?", [receiveData.email]);
    const user_id = return_id.user_id;  // 배열에서 user_id 가져오기

    const ui_query = "UPDATE tb_user_information SET ui_name=?, ui_birth_date=?, ui_sex=?, ui_bank_num=? WHERE user_id = ?";
    const ui_value = [receiveData.name, receiveData.birthdate, receiveData.gender, receiveData.accountNo, user_id];
    const ui_result = await connection.execute(ui_query, ui_value);

    const uf_query = "UPDATE tb_user_finance SET uf_capital=? WHERE user_id = ?";
    const uf_value = [receiveData.holdingAsset, user_id];
    const uf_result = await connection.execute(uf_query, uf_value);

    await connection.commit();  // 모든쿼리가 성공했을때, 커밋처리

    res.status(200).json({ message: '회원정보가 성공적으로 업데이트되었습니다.' });
  } catch (err) {
    if (connection) { await connection.rollback() };
    console.error('User 제출 쿼리 실행 에러:', err);
    res.status(500).json({ message: '서버 에러', error: err.message });
  } finally {
    if (connection) connection.release();
  }
};

const deleteId = async (req, res) => {
  const userId = req.session.userId;  // 세션에 저장된 userId 사용

    let connection;
    try {
      connection = await pool.getConnection();
      const query = "DELETE FROM tb_user_key WHERE user_id = ?";
      const result = await connection.execute(query, [userId]);

      // 결과 확인 후 로그아웃 처리
      if (result.affectedRows > 0) { // 탈퇴 성공 확인
        req.session.destroy((err) => {  // 세션 삭제 시 에러 처리
          if (err) {
            console.error('세션 삭제 에러:', err);
            return res.status(500).json({ message: '회원 탈퇴 중 오류가 발생했습니다.' });
          }

          res.clearCookie('connect.sid');  // 쿠키 삭제
          res.status(200).json({ message: '회원 탈퇴가 정상적으로 처리되었습니다.' });
        }); 
      } else {
        console.error('회원 탈퇴 실패, 삭제된 행이 없습니다.');
        res.status(500).json({ message: '회원 탈퇴 중 오류가 발생했습니다.' });
      }
    } catch (err) {
      console.error('회원 탈퇴 쿼리 실행 에러:', err);
      res.status(500).json({ message: '서버 에러', error: err.message });
    } finally {
      if (connection) await connection.release();
      console.log('데이터베이스 연결 해제 완료');
    }
};



module.exports = {
  getUserData,
  putUserChangeData,
  deleteId
};
