const pool = require('../config/database');
const smtpTransport = require('../config/email');
const bcrypt = require('bcryptjs');


// 이메일 중복 확인
const postCheckEmail = async (req, res) => {
  const checkingEmail = req.body.email;

  let connection;
  try {
    connection = await pool.getConnection();
    const query = 'SELECT uk_email FROM tb_user_key'
    const result = await connection.execute(query);
    const emailList = result.map(item => item.uk_email);
    if (emailList.includes(checkingEmail)) {
      res.status(200).json({ message: 'email impossible' });
    } else {
      res.status(200).json({ message: 'email possible' });
    }
  } catch (err) {
    console.error('Email 쿼리 실행 에러:', err);
    res.status(500).send('서버 에러');
  } finally {
    if (connection) connection.release();  // 연결 반환. 풀로 되돌리기
  }
}


// 인증코드 생성 및 발송
let vcode = '';
var returnEmail = '';
const postEmailCode = async (req, res) => {
  const email = req.body.email;
  const vcode = Math.random().toString(36).substring(2, 6); // 4자리 인증 코드 생성

  // 세션에 이메일과 인증 코드 저장 (세션 만료 시간 설정: 10분)
  req.session.emailVerification = { email, code: vcode };
  req.session.cookie.maxAge = 10 * 60 * 1000; // 10분

  const emailInfo = {
    from: 'lolanhani@gmail.com',
    to: email,
    subject: 'MAP 회원가입 인증코드',
    html: `<p>인증코드: <strong>${vcode}</strong></p>`
  };

  smtpTransport.sendMail(emailInfo, (err, response) => {
    if (err) {
      console.error('인증 코드 이메일 전송 실패:', err);
      res.json({ ok: false, msg: '인증코드 메일전송 실패', error: err.message });
    } else {
      res.json({ ok: true, msg: '인증코드 메일전송 성공' });
    }
  });
};

// 인증 코드 확인
const postConfirmCode = async (req, res) => {
  const userCode = req.body.userconfirm;
  const sessionData = req.session.emailVerification || {};

  if (sessionData.code && sessionData.code === userCode) {
    res.status(200).json({ message: 'code possible' });
  } else {
    console.error('인증 코드 불일치');
    res.status(400).json({ message: 'code impossible' });
  }
};


// 회원가입 처리
const postUserRegister = async (req, res) => {
  const {
    user_email, user_password, user_name, user_birth_date,
    user_sex, user_bank_num, user_capital, user_permission, user_mobile
  } = req.body;

  const sessionData = req.session.emailVerification || {};

  // 세션에 저장된 이메일과 입력된 이메일이 일치하는지 확인
  if (user_email === sessionData.email) {
    const hashedPassword = await bcrypt.hash(user_password, 10); // 비밀번호 해싱

    let connection;
    try {
      connection = await pool.getConnection();
      await connection.beginTransaction();  // 트랜잭션 시작

      const uk_query = 'INSERT INTO tb_user_key (uk_email, uk_password, uk_permission) VALUES (?, ?, ?)';
      const uk_result = await connection.execute(uk_query, [
        user_email,
        hashedPassword, // 해싱된 비밀번호로 저장
        user_permission || 1
      ]);

      const user_id = uk_result.insertId;
      const ui_query = 'INSERT INTO tb_user_information (user_id, ui_name, ui_birth_date, ui_sex, ui_bank_num, ui_caution, ui_phone_number) VALUES (?, ?, ?, ?, ?, ?, ?)';
      const ui_result = await connection.execute(ui_query, [
        user_id,
        user_name,
        user_birth_date,
        user_sex,
        user_bank_num || null,
        0,
        user_mobile
      ]);

      const uf_query = 'INSERT INTO tb_user_finance (user_id, uf_capital) VALUES (?, ?)';
      const uf_result = await connection.execute(uf_query, [
        user_id,
        user_capital || null
      ])

      await connection.commit();  // 모든쿼리가 성공했을때, 커밋
      res.status(200).json({ message: 'User registered successfully!', id: uk_result.insertId.toString() });
    } catch (err) {
        if (connection) { await connection.rollback() };
        console.error('회원가입 쿼리실행 에러:', err);
        res.status(500).send('서버 에러');
    } finally {
      if (connection) connection.release();  // 연결 반환. 풀로 되돌리기
    }
  } else {
    res.status(400).json({ message: 'Email does not match the verified email' });
  }
};

module.exports = {
  postUserRegister,
  postCheckEmail,
  postEmailCode,
  postConfirmCode
};
