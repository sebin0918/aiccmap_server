const express = require('express');
const router = express.Router();

const { addHouseHoldData, getHouseHoldData } = require('../controllers/HouseHoldController');
//const houseHoldRoutes = require('./src/routes/HouseHold'); // 정확한 경로와 파일명으로 수정

router.get('/HouseHold', getHouseHoldData);
router.post('/addHouseHoldData', addHouseHoldData);



module.exports = router;