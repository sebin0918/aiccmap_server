const nodemailer = require('nodemailer');

use_mail = 'add your email'
use_pass = 'add your password'

const smtpTransport = nodemailer.createTransport({
    pool: true,                     // 여러 이메일을 한 번에 보내기 위해 재사용 옵션
    maxConnections: 10,             // 동시 최대 10개 전송
    service: 'gmail',               // google gmail 서비스 사용
    host: 'smtp.gmail.com',         // gmail SMTP 주소
    port: 587,                      // SSL은 포트 465 사용. TLS(보안 연결) 포트 587 사용
    secure: false,                  // 보안 소켓 사용 X
    requireTLS: true,               // TLS (전송계층보안) 사용 X
    auth: {
        user: use_mail,
        pass: use_pass
    },
    tls: {
        rejectUnauthorized: false   // 인증되지 않은 SSL 인증서 허용
    },
    logger: true,  // 로깅 활성화
    debug: true    // 디버그 모드 활성화
});


// SMTP 서버 연결 상태 확인
smtpTransport.verify(function(error, success) {
    if (error) {
        console.error('SMTP connection error:', error);
    } else {
        console.log('SMTP server is ready to take messages:', success);
    }
});


// export default smtpTransport;  // ES 모듈 시스템 문법
module.exports = smtpTransport;  // CommonJS 환경 문법
