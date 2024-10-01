const express = require('express');
const { 
    getUserTargetBudget, 
    updateUserTargetBudget, 
    getUserCapital, 
    getUserDeposit, 
    getUserInstallmentSaving, 
    getUserLoan, 
    getUserStockInfo,
    checkUserBankAccount,
    getUserTotalReceivedandPaid,
    getUserTotalAsset,
    getUserMonthlyExpenditures,
    getUserCurrentMonthReceived,
    updateUserSavings,
    updateUserLoan,
    saveInvestments,
    getUserInvestments,
} = require('../controllers/myAssetPlanerController');

// 미들웨어 불러오기 
const sessionChecker = require('../middlewares/sessionChecker');  // 세션 인증 미들웨어로 대체
const router = express.Router();

// 세션 미들웨어를 사용하여 각 라우트 보호
router.get('/capital', sessionChecker, getUserCapital);
router.get('/target', sessionChecker, getUserTargetBudget);
router.put('/target', sessionChecker, updateUserTargetBudget);
router.get('/deposit', sessionChecker, getUserDeposit);
router.put('/deposit', sessionChecker, updateUserSavings);
router.get('/installmentsaving', sessionChecker, getUserInstallmentSaving);
router.get('/loan', sessionChecker, getUserLoan);
router.put('/loan', sessionChecker, updateUserLoan);
router.get('/stock', sessionChecker, getUserStockInfo);
router.get('/check-bank-account', sessionChecker, checkUserBankAccount);
router.get('/total-received-paid', sessionChecker, getUserTotalReceivedandPaid);
router.get('/total-asset', sessionChecker, getUserTotalAsset);
router.get('/monthly-expenditures', sessionChecker, getUserMonthlyExpenditures);
router.get('/current-month-received', sessionChecker, getUserCurrentMonthReceived);
router.post('/save-investments', sessionChecker, saveInvestments);
router.get('/get-investments', sessionChecker, getUserInvestments);


module.exports = router;
