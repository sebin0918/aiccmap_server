const nodemailer = require('nodemailer');

const smtpTransport = nodemailer.createTransport({
    pool: true,
    maxConnections: 10,
    service: 'gmail', // google
    host: 'smtp.gmail.com',
    port: 587,  // For SSL, enter 465. For TLS, enter 587.
    secure: false,
    requireTLS: true,
    auth: {
        user: 'lolanhani@gmail.com',
        pass: 'ayfbaxldefgphghe'
    },
    tls: {
        rejectUnauthorized: false
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
