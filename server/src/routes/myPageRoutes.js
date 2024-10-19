const express = require('express');
const { getUserData, putUserChangeData, deleteId } = require('../controllers/MyPageController');
const router = express.Router();

router.get('/defaultdata', getUserData);
router.put('/datasubmit', putUserChangeData);
router.delete('/', deleteId)

module.exports = router;