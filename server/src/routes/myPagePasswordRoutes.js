const express = require('express');
const { postCheckPassword } = require('../controllers/myPagePasswordController');
const router = express.Router();

router.post('/checkpassword', postCheckPassword);

module.exports = router;