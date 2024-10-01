const express = require('express');
const { postUserData, putUserChangeData, deleteId } = require('../controllers/MyPageController');
const router = express.Router();

router.post('/defaultdata', postUserData);
router.put('/datasubmit', putUserChangeData);
router.delete('/', deleteId)

module.exports = router;