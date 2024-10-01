const pool = require('../config/database');
const smtpTransport = require('../config/email');
const bcrypt = require('bcryptjs');

// 이메일 중복 확인
const postCheckEmail = async (req, res) => {
  const checkingEmail = req.body.email;
  console.log('확인할 이메일:', checkingEmail);

  let connection;
  try {
    connection = await pool.getConnection();
    const query = 'SELECT uk_email FROM tb_user_key'
    const result = await connection.execute(query);
    console.log('Email쿼리적용 데이터:', result);

    const emailList = result.map(item => item.uk_email);
    console.log(emailList);
    if (emailList.includes(checkingEmail)) {
      console.log('이미 가입된 이메일');
      res.status(200).json({ message: 'email impossible' });
    } else {
      console.log('가입 가능한 이메일');
      res.status(200).json({ message: 'email possible' });
    }
  } catch (err) {
    console.error('Email 쿼리 실행 에러:', err);
    res.status(500).send('서버 에러');
  } finally {
    if (connection) connection.release();  // 연결 반환. 풀로 되돌리기
  }
  
}


let vcode = '';
var returnEmail = '';
const postEmailCode = async (req, res) => {
  const email = req.body.email;
  console.log('인증코드를 보낼 이메일:', email);

  const vcode = Math.random().toString(36).substring(2, 6); // 4자리 인증 코드 생성
  console.log('생성된 인증 코드:', vcode);

  // 세션에 이메일과 인증 코드 저장 (세션 만료 시간 설정: 10분)
  req.session.emailVerification = { email, code: vcode };
  req.session.cookie.maxAge = 10 * 60 * 1000; // 10분

  // 세션 저장 확인 로그 추가
  console.log("세션에 저장된 인증 데이터:", req.session.emailVerification);

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
      console.log('인증 코드 이메일 전송 성공:', response);
      res.json({ ok: true, msg: '인증코드 메일전송 성공' });
    }
  });
};

// 인증 코드 확인
const postConfirmCode = async (req, res) => {
  const userCode = req.body.userconfirm;
  const sessionData = req.session.emailVerification || {};
  console.log('세션에 저장된 코드:', sessionData.code, '사용자가 입력한 코드:', userCode);

  if (sessionData.code && sessionData.code === userCode) {
    console.log('인증 코드 일치');
    res.status(200).json({ message: 'code possible' });
  } else {
    console.log('인증 코드 불일치');
    res.status(400).json({ message: 'code impossible' });
  }
};

// 회원가입 처리
const postUserRegister = async (req, res) => {
  const {
    user_email, user_password, user_name, user_birth_date,
    user_sex, user_bank_num, user_capital, user_permission, user_mobile
  } = req.body;  // user_mobile, user_loan, user_installment_saving, user_deposit

  console.log('회원가입 데이터:', req.body);
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

      // const ui_query = 'INSERT INTO tb_user_information (user_id, ui_name, ui_birth_date, ui_sex, ui_bank_num, ui_caution) VALUES ((SELECT user_id FROM tb_user_key WHERE user_id ORDER BY user_id DESC LIMIT 1), ?, ?, ?, ?, 0)';
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
  
      console.log('회원가입 적용쿼리:', uk_result, ui_result, uf_result);
      res.status(200).json({ message: 'User registered successfully!', id: uk_result.insertId.toString() });
    } catch (err) {
        if (connenction) { await connection.rollback()};
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
