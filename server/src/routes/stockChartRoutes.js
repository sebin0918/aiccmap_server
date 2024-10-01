const express = require('express');
const { getStockData } = require('../controllers/stockChartController');
const router = express.Router();

router.get('/stock', getStockData);

module.exports = router;
