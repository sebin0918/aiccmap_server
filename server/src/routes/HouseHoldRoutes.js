const express = require('express');
const router = express.Router();

const { 
    addHouseHoldData, 
    getHouseHoldData, 
    searchHouseHoldData, 
    deleteHouseHoldData, 
    saveOrUpdateMemo,
    getMemo,
} = require('../controllers/HouseHoldController');

// 사용자 가계부 데이터를 가져오는 라우트
router.get('/HouseHold', getHouseHoldData);

// router.get('/HouseHoldByRange', getHouseHoldDataByRange);

// 가계부 데이터를 입출금 내역을 추가할 때 사용 추가하는 라우트
router.post('/addHouseHoldData', addHouseHoldData);

// 가계부 데이터를  검색어를 기반으로 데이터를 조회 검색하는 라우트
router.post('/searchHouseHoldData', searchHouseHoldData);

// 가계부  특정 입출금 내역을 삭제할 때 데이터를 삭제하는 라우트
router.delete('/deleteHouseHoldData', deleteHouseHoldData);

// 메모를 저장 또는 업데이트하는 라우트
router.post('/saveOrUpdateMemo', saveOrUpdateMemo);

// 날짜별 메모를 가져오는 라우트
router.get('/getMemo', getMemo);

module.exports = router;
