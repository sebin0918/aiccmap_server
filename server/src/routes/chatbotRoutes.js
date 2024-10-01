const express = require('express');
const { postChatbotData, getChatList, getChatDetail } = require('../controllers/chatbotController');
const router = express.Router();

router.post('/chatbot', postChatbotData); // POST 요청
router.get('/chatList', getChatList);     // GET 요청
router.get('/chatDetail/:chatId', getChatDetail);

module.exports = router;
