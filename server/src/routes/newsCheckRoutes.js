const express = require('express');
const { getNewsData } = require('../controllers/newsCheckController');
const router = express.Router();

router.get('/newscheck', getNewsData);

module.exports = router;