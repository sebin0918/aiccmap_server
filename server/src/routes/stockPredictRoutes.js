const express = require('express');
const { getStockPredictData } = require('../controllers/stockPredictController');
const router = express.Router();

router.get('/stock-predict', getStockPredictData);

module.exports = router;
