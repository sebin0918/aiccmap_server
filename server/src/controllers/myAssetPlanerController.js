const pool = require('../config/database');

// 계좌 번호 확인 API
const checkUserBankAccount = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT ui_bank_num 
      FROM tb_user_information
      WHERE user_id = ?
      LIMIT 1
    `, [userId]);

    // 조회 결과 없으면 404 에러 반환
    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // 계좌 번호 확인 및 결과 반환
    const hasBankAccount = !!result[0].ui_bank_num; // 계좌번호가 있으면 true, 없으면 false
    res.json({ hasBankAccount });
  } catch (error) {
    // 에러 발생 시 로그 출력 및 500 에러 반환
    console.error('Error checking user bank account:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 사용자의 총 입금 및 출금 합계 조회 
const getUserTotalReceivedandPaid = async (req, res) => {
  try{
    const userId = req.user.id; // 로그인한 사용자의 id 가져오기 

    // 입금 합계 계산 (rp_part가 0일 경우)
    const receivedResult = await pool.query( `
      SELECT SUM(rp_amount) AS total_received 
      FROM tb_received_paid 
      WHERE user_id = ? AND rp_part = 0
    `, [userId]);

    // 출금 합계 계산 (rp_part가 1일 경우)
    const paidResult = await pool.query(`
      SELECT SUM(rp_amount) AS total_paid 
      FROM tb_received_paid 
      WHERE user_id = ? AND rp_part = 1
    `, [userId]);

    // 입금 및 출금 합계 초기화
    const totalReceived = receivedResult[0].total_received || 0;
    const totalPaid = paidResult[0].total_paid || 0;

    // JSON 형식으로 응답 반환
    res.json({
      totalReceived,
      totalPaid
    });
  } catch (error) {
    // 에러 발생 시 로그 출력 및 500 에러 반환
    console.error('Error fetching total received and paid:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// [userId]
// 총 자산 (초기자산) 불러오기
const getUserCapital = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT uf_capital
      FROM tb_user_finance
      WHERE user_id = ?
      LIMIT 1
      `, [userId]);

    // 조회 결과 없으면 404 에러 반환
    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    // 조회된 사용자 자산이 없으면 0으로 초기화
    const userCapital = result[0].uf_capital || 0;
    // 조회 자산 JSON 형식 반환
    res.json({ userCapital });
  } catch (error) {

    // 에러 발생시 로그 출력 및 500 에러 반환
    console.error('Error fetching user capital:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 목표 예산 불러오기
const getUserTargetBudget = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT uf_target_budget 
      FROM tb_user_finance
      WHERE user_id = ?
      LIMIT 1
    `, [userId]);
    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // 조회 목표 예산없으면 0으로 초기화
    const targetBudget = result[0].uf_target_budget || 0;
    // 조회 목표 예산 JSON 형식 반환
    res.json({ targetBudget });
  } catch (error) {
    console.error('Error fetching target budget:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 목표 예산 업데이트
const updateUserTargetBudget = async (req, res) => {
  const { targetBudget } = req.body;
  if (typeof targetBudget !== 'number' || targetBudget < 0) {
    return res.status(400).json({ error: 'Invalid target budget' });
  }
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      UPDATE tb_user_finance 
      SET uf_target_budget = ? 
      WHERE user_id = ?
    `, [targetBudget, userId]);
    
    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    res.json({ message: 'Target budget updated successfully' });
  } catch (error) {
    console.error('Error updating target budget:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 정기 예금 불러오기 
const getUserDeposit = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT uf_deposit 
      FROM tb_user_finance
      WHERE user_id = ?
      LIMIT 1
      `, [userId]);

    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    const userDeposit = result[0].uf_deposit || 0;
    res.json({ userDeposit });
  } catch (error) {
    console.error('Error fetching user deposit:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

// 적금 불러오기
const getUserInstallmentSaving = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT uf_installment_saving 
      FROM tb_user_finance
      WHERE user_id = ?
      LIMIT 1
      `, [userId]);
    // console.log(result); // 쿼리 결과를 출력해 확인
    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    const userInstallmentSaving = result[0].uf_installment_saving || 0;
    res.json({ userInstallmentSaving });
  } catch (error) {
    console.error('Error fetching user installment saving:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

// 정기 예금과 적금 업데이트
const updateUserSavings = async (req, res) => {
  const { deposit, installmentSaving } = req.body; // 클라이언트에서 보낸 정기 예금 및 적금 값

  // 입력 값 검증
  if (typeof deposit !== 'number' || deposit < 0) {
    return res.status(400).json({ error: 'Invalid deposit value' });
  }
  if (typeof installmentSaving !== 'number' || installmentSaving < 0) {
    return res.status(400).json({ error: 'Invalid installment saving value' });
  }

  try {
    const userId = req.user.id; // 로그인한 사용자 ID 가져오기

    // 정기 예금 업데이트
    const depositResult = await pool.query(`
      UPDATE tb_user_finance 
      SET uf_deposit = ? 
      WHERE user_id = ?
    `, [deposit, userId]);

    if (depositResult.affectedRows === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // 적금 업데이트
    const installmentResult = await pool.query(`
      UPDATE tb_user_finance 
      SET uf_installment_saving = ? 
      WHERE user_id = ?
    `, [installmentSaving, userId]);

    if (installmentResult.affectedRows === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ message: 'Savings updated successfully' });
  } catch (error) {
    console.error('Error updating savings:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 대출 불러오기 (대출한 총 금액)
const getUserLoan = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT uf_loan 
      FROM tb_user_finance 
      WHERE user_id = ?
      LIMIT 1
      `, [userId]);

    if (result.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }
    const userLoan = result[0].uf_loan || 0;
    res.json({ userLoan });
  } catch (error) {
    console.error('Error fetching user loan:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

// 대출 업데이트
const updateUserLoan = async (req, res) => {
  const { loan } = req.body; // 클라이언트에서 보낸 대출 값

  // 입력 값 검증
  if (typeof loan !== 'number' || loan < 0) {
    return res.status(400).json({ error: 'Invalid loan value' });
  }

  try {
    const userId = req.user.id; // 로그인한 사용자 ID 가져오기

    // 대출 업데이트
    const result = await pool.query(`
      UPDATE tb_user_finance 
      SET uf_loan = ? 
      WHERE user_id = ?
    `, [loan, userId]);

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ message: 'Loan updated successfully' });
  } catch (error) {
    console.error('Error updating loan:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 정기 예금 월 고정 지출 불러오기
const getMonthlyFixedDeposit = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT rp_amount
      FROM tb_received_paid
      WHERE user_id = ? AND rp_detail LIKE '%정기 예금%'
      ORDER BY rp_date DESC
      LIMIT 1
    `, [userId]);
    
    if (result.length === 0) {
      return res.status(404).json({ error: '월 고정 정기예금값을 못찾음' });
    }

    const monthlyFixedDeposit = result[0].rp_amount || 0;
    res.json({ monthlyFixedDeposit });
  } catch (error) {
    console.error('Error fetching monthly fixed deposit:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 적금 월 고정 지출 불러오기
const getMonthlyFixedInstallmentSaving = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT rp_amount
      FROM tb_received_paid
      WHERE user_id = ? AND rp_detail LIKE '%적금%'
      ORDER BY rp_date DESC
      LIMIT 1
    `, [userId]);

    if (result.length === 0) {
      return res.status(404).json({ error: '월 고정 적금 지출값 못찾음' });
    }

    const monthlyFixedInstallmentSavings = result[0].rp_amount || 0;
    res.json({ monthlyFixedInstallmentSavings });
  } catch (error) {
    console.error('Error fetching monthly fixed installment savings:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 대출 상환 총 금액 불러오기
const getTotalLoanRepayment = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    const result = await pool.query(`
      SELECT SUM(rp_amount) AS totalLoanRepayment
      FROM tb_received_paid
      WHERE user_id = ? AND rp_detail LIKE '%대출 상환%'
    `, [userId]);

    if (!result[0].totalLoanRepayment) {
      return res.status(404).json({ error: '대출 상환 내역을 찾을 수 없습니다.' });
    }

    const totalLoanRepayment = result[0].totalLoanRepayment || 0;
    res.json({ totalLoanRepayment });
  } catch (error) {
    console.error('Error fetching total loan repayment:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};


// 주식 및 코인 정보 조회 및 순수익과 수익률 계산
const getUserStockInfo = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기

    // 1. 유저의 모든 삼성, 애플 주식 및 비트코인 수량을 날짜별로 조회
    const sharesResult = await pool.query(`
      SELECT sh.sh_ss_count, sh.sh_ap_count, sh.sh_bit_count, sh.sh_date 
      FROM tb_shares_held sh 
      WHERE sh.user_id = ?
    `, [userId]);

    // 데이터가 없을 때 빈 데이터를 반환
    if (sharesResult.length === 0) {
      return res.json({
        samsung: {
          initialValue: 0,
          currentValue: 0,
          profit: 0,
          returnOfEquity: 0,
          amount: 0
        },
        apple: {
          initialValue: 0,
          currentValue: 0,
          profit: 0,
          returnOfEquity: 0,
          amount: 0
        },
        coin: {
          initialValue: 0,
          currentValue: 0,
          profit: 0,
          returnOfEquity: 0,
          amount: 0
        },
        total: {
          totalInitialValue: 0,
          totalCurrentValue: 0,
          totalProfit: 0,
          totalROE: 0
        }
      });
    }

    // 주식 수량과 구매 가격 정보 합산
    let totalSamsungCount = 0;
    let totalAppleCount = 0;
    let totalBitcoinCount = 0;
    let totalInitialSamsungValue = 0;
    let totalInitialAppleValue = 0;
    let totalInitialCoinValue = 0;

    // 최신 주식 가격 조회를 위해 마지막 구매 날짜 추적
    let lastPurchaseDate = null;

    // 2. 각 거래 날짜별로 가격을 조회하고 초기 자산 계산
    for (const record of sharesResult) {
      const { sh_ss_count, sh_ap_count, sh_bit_count, sh_date } = record;
      
      // 주식을 구매한 날짜 추적
      if (!lastPurchaseDate || new Date(sh_date) > new Date(lastPurchaseDate)) {
        lastPurchaseDate = sh_date;
      }

      const purchaseStockResult = await pool.query(`
        SELECT ts.sc_ss_stock, ts.sc_ap_stock, ts.sc_coin 
        FROM tb_finance_date fd
        JOIN tb_stock ts ON fd.fd_date = ts.fd_date
        WHERE fd.fd_date = ? 
        LIMIT 1
      `, [sh_date]);

      if (purchaseStockResult.length > 0) {
        const { 
          sc_ss_stock: purchaseSamsungPrice, 
          sc_ap_stock: purchaseApplePrice, 
          sc_coin: purchaseCoinPrice 
        } = purchaseStockResult[0];

        // 누적 수량 및 초기 자산 계산
        totalSamsungCount += sh_ss_count;
        totalAppleCount += sh_ap_count;
        totalBitcoinCount += sh_bit_count;

        totalInitialSamsungValue += sh_ss_count * purchaseSamsungPrice;
        totalInitialAppleValue += sh_ap_count * purchaseApplePrice;
        totalInitialCoinValue += sh_bit_count * purchaseCoinPrice;
      }
    }

    // 3. 최신 삼성, 애플 주식 및 비트코인 가격 조회
    const latestStockResult = await pool.query(`
      SELECT sc_ss_stock, sc_ap_stock, sc_coin 
      FROM tb_stock 
      ORDER BY fd_date DESC 
      LIMIT 1
    `);

    if (latestStockResult.length === 0) {
      return res.status(404).json({ error: 'No latest stock data found' });
    }

    const { 
      sc_ss_stock: latestSamsungPrice, 
      sc_ap_stock: latestApplePrice, 
      sc_coin: latestCoinPrice 
    } = latestStockResult[0];

    // 4. 최신 환율 조회
    const latestExchangeRateResult = await pool.query(`
      SELECT mei.mei_ex_rate 
      FROM tb_main_economic_index mei
      JOIN tb_finance_date fd ON mei.fd_date = fd.fd_date
      ORDER BY fd.fd_date DESC 
      LIMIT 1
    `);

    if (latestExchangeRateResult.length === 0) {
      return res.status(404).json({ error: 'No exchange rate data found' });
    }

    const latestExchangeRate = latestExchangeRateResult[0].mei_ex_rate;

    // 5. 현재 자산 계산 (최신 가격 기준)
    const currentSamsungValue = totalSamsungCount * latestSamsungPrice;
    const currentAppleValue = totalAppleCount * latestApplePrice * latestExchangeRate;
    const currentCoinValue = totalBitcoinCount * latestCoinPrice * latestExchangeRate;

    // 6. 순수익 계산
    const samsungProfit = currentSamsungValue - totalInitialSamsungValue;
    const appleProfit = currentAppleValue - (totalInitialAppleValue * latestExchangeRate);
    const coinProfit = currentCoinValue - (totalInitialCoinValue * latestExchangeRate);

    // 7. 전체 순수익 계산
    const totalProfit = samsungProfit + appleProfit + coinProfit;

    // 8. 전체 초기 자산 및 현재 자산 계산
    const totalInitialValue = totalInitialSamsungValue + (totalInitialAppleValue * latestExchangeRate) + (totalInitialCoinValue * latestExchangeRate);
    const totalCurrentValue = currentSamsungValue + currentAppleValue + currentCoinValue;

    // 9. 전체 수익률 계산
    const totalROE = ((totalProfit / totalInitialValue) * 100).toFixed(2);

    // 계산된 자산 정보, 수익률을 JSON 형식으로 client에 반환
    res.json({
      samsung: {
        initialValue: totalInitialSamsungValue,
        currentValue: currentSamsungValue,
        profit: samsungProfit,
        returnOfEquity: ((samsungProfit / totalInitialSamsungValue) * 100).toFixed(2),
        amount: totalSamsungCount
      },
      apple: {
        initialValue: totalInitialAppleValue * latestExchangeRate,
        currentValue: currentAppleValue,
        profit: appleProfit,
        returnOfEquity: ((appleProfit / (totalInitialAppleValue * latestExchangeRate)) * 100).toFixed(2),
        amount: totalAppleCount
      },
      coin: {
        initialValue: totalInitialCoinValue * latestExchangeRate,
        currentValue: currentCoinValue,
        profit: coinProfit,
        returnOfEquity: ((coinProfit / (totalInitialCoinValue * latestExchangeRate)) * 100).toFixed(2),
        amount: totalBitcoinCount
      },
      total: {
        totalInitialValue,
        totalCurrentValue,
        totalProfit,
        totalROE
      }
    });
  } catch (error) {
    console.error('Error fetching asset info:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};


// 사용자의 총 자산 계산함수
const getUserTotalAsset = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 ID 가져오기

    // 1. 사용자 자본 조회
    const capitalResult = await pool.query(`
      SELECT uf_capital FROM tb_user_finance WHERE user_id = ? LIMIT 1
    `, [userId]);
    const userCapital = capitalResult.length > 0 && capitalResult[0].uf_capital !== null ? parseFloat(capitalResult[0].uf_capital) : 0;

    // 2. 정기 예금 조회
    const depositResult = await pool.query(`
      SELECT uf_deposit FROM tb_user_finance WHERE user_id = ? LIMIT 1
    `, [userId]);
    const userDeposit = depositResult.length > 0 && depositResult[0].uf_deposit !== null ? parseFloat(depositResult[0].uf_deposit) : 0;

    // 3. 적금 조회
    const installmentSavingResult = await pool.query(`
      SELECT uf_installment_saving FROM tb_user_finance WHERE user_id = ? LIMIT 1
    `, [userId]);
    const userInstallmentSaving = installmentSavingResult.length > 0 && installmentSavingResult[0].uf_installment_saving !== null ? parseFloat(installmentSavingResult[0].uf_installment_saving) : 0;

    // 4. 대출 조회
    const loanResult = await pool.query(`
      SELECT uf_loan FROM tb_user_finance WHERE user_id = ? LIMIT 1
    `, [userId]);
    const userLoan = loanResult.length > 0 && loanResult[0].uf_loan !== null ? parseFloat(loanResult[0].uf_loan) : 0;

    // 5. 총 입금 조회
    const totalReceivedResult = await pool.query(`
      SELECT SUM(rp_amount) AS total_received FROM tb_received_paid WHERE user_id = ? AND rp_part = 0
    `, [userId]);
    const totalReceived = totalReceivedResult.length > 0 && totalReceivedResult[0].total_received !== null ? parseFloat(totalReceivedResult[0].total_received) : 0;

    // 6. 총 출금 조회
    const totalPaidResult = await pool.query(`
      SELECT SUM(rp_amount) AS total_paid FROM tb_received_paid WHERE user_id = ? AND rp_part = 1
    `, [userId]);
    const totalPaid = totalPaidResult.length > 0 && totalPaidResult[0].total_paid !== null ? parseFloat(totalPaidResult[0].total_paid) : 0;

    // 7. 주식 및 코인 현재 자산 계산
    // 7.1. 유저의 모든 삼성, 애플 주식 및 비트코인 수량을 합산
    const sharesResult = await pool.query(`
      SELECT sh.sh_ss_count, sh.sh_ap_count, sh.sh_bit_count 
      FROM tb_shares_held sh 
      WHERE sh.user_id = ?
    `, [userId]);

    // 주식 수량 합산
    let totalSamsungCount = 0;
    let totalAppleCount = 0;
    let totalBitcoinCount = 0;

    if (sharesResult.length > 0) {
      for (const record of sharesResult) {
        totalSamsungCount += record.sh_ss_count || 0;
        totalAppleCount += record.sh_ap_count || 0;
        totalBitcoinCount += record.sh_bit_count || 0;
      }
    }

    // 7.2. 최신 삼성, 애플 주식 및 비트코인 가격 조회
    const latestStockResult = await pool.query(`
      SELECT sc_ss_stock, sc_ap_stock, sc_coin 
      FROM tb_stock 
      ORDER BY fd_date DESC 
      LIMIT 1
    `);
    if (latestStockResult.length === 0) {
      return res.status(404).json({ error: 'No latest stock data found' });
    }

    const { 
      sc_ss_stock: latestSamsungPrice, 
      sc_ap_stock: latestApplePrice, 
      sc_coin: latestCoinPrice 
    } = latestStockResult[0];

    // 7.3. 최신 환율 조회
    const latestExchangeRateResult = await pool.query(`
      SELECT mei.mei_ex_rate 
      FROM tb_main_economic_index mei
      JOIN tb_finance_date fd ON mei.fd_date = fd.fd_date
      ORDER BY fd.fd_date DESC 
      LIMIT 1
    `);
    if (latestExchangeRateResult.length === 0) {
      return res.status(404).json({ error: 'No exchange rate data found' });
    }

    const latestExchangeRate = latestExchangeRateResult[0].mei_ex_rate;

    // 7.4. 현재 자산 계산 (최신 가격 기준)
    const currentSamsungValue = totalSamsungCount * latestSamsungPrice;
    const currentAppleValue = totalAppleCount * latestApplePrice * latestExchangeRate; // 애플 원화로 환산
    const currentCoinValue = totalBitcoinCount * latestCoinPrice * latestExchangeRate; // 비트코인 원화로 환산

    // 7.5. 주식 및 코인 총 자산 계산
    const totalStockAsset = currentSamsungValue + currentAppleValue + currentCoinValue;

    // 8. 총 자산 계산
    const totalAsset = userCapital + userDeposit + userInstallmentSaving - userLoan + totalReceived - totalPaid + totalStockAsset;

    // 9. 결과 JSON으로 반환
    res.json({
      totalAsset,
      userCapital,
      userDeposit,
      userInstallmentSaving,
      userLoan,
      totalReceived,
      totalPaid,
      totalStockAsset
    });
  } catch (error) {
    console.error('Error calculating total asset:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};


const getUserMonthlyExpenditures = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 ID 가져오기

    // 현재 날짜 기준으로 전월 및 금월의 시작 날짜와 종료 날짜 계산
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1; // JavaScript의 월은 0부터 시작하므로 +1
    const lastMonth = currentMonth === 1 ? 12 : currentMonth - 1;
    const lastMonthYear = currentMonth === 1 ? currentYear - 1 : currentYear;

    // 금월의 시작과 종료 날짜 계산
    const startOfCurrentMonth = new Date(currentYear, currentMonth - 1, 1).toISOString().split('T')[0];
    const endOfCurrentMonth = new Date(currentYear, currentMonth, 0).toISOString().split('T')[0];

    // 전월의 시작과 종료 날짜 계산
    const startOfLastMonth = new Date(lastMonthYear, lastMonth - 1, 1).toISOString().split('T')[0];
    const endOfLastMonth = new Date(lastMonthYear, lastMonth, 0).toISOString().split('T')[0];

    // 금월 지출 합계 조회
    const currentMonthExpenditureResult = await pool.query(`
      SELECT SUM(rp_amount) AS current_month_expenditure
      FROM tb_received_paid
      WHERE user_id = ? AND rp_part = 1 AND rp_date BETWEEN ? AND ?
    `, [userId, startOfCurrentMonth, endOfCurrentMonth]);
    
    const currentMonthExpenditure = currentMonthExpenditureResult[0]?.current_month_expenditure || 0;

    // 전월 지출 합계 조회
    const lastMonthExpenditureResult = await pool.query(`
      SELECT SUM(rp_amount) AS last_month_expenditure
      FROM tb_received_paid
      WHERE user_id = ? AND rp_part = 1 AND rp_date BETWEEN ? AND ?
    `, [userId, startOfLastMonth, endOfLastMonth]);

    const lastMonthExpenditure = lastMonthExpenditureResult[0]?.last_month_expenditure || 0;

    // 결과 JSON으로 반환
    res.json({
      currentMonthExpenditure,
      lastMonthExpenditure
    });

  } catch (error) {
    console.error('Error fetching monthly expenditures:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

// 금월 입금 합계 조회 
const getUserCurrentMonthReceived = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 ID 가져오기

    // 현재 날짜 기준으로 금월의 시작 날짜와 종료 날짜 계산
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1; // JavaScript의 월은 0부터 시작하므로 +1

    // 금월의 시작과 종료 날짜 계산
    const startOfCurrentMonth = new Date(currentYear, currentMonth - 1, 1).toISOString().split('T')[0];
    const endOfCurrentMonth = new Date(currentYear, currentMonth, 0).toISOString().split('T')[0];

    // 금월 입금 합계 조회
    const currentMonthReceivedResult = await pool.query(`
      SELECT SUM(rp_amount) AS current_month_received
      FROM tb_received_paid
      WHERE user_id = ? AND rp_part = 0 AND rp_date BETWEEN ? AND ?
    `, [userId, startOfCurrentMonth, endOfCurrentMonth]);
    
    const currentMonthReceived = currentMonthReceivedResult[0]?.current_month_received || 0;
    // 결과 JSON으로 반환
    res.json({
      currentMonthReceived
    });

  } catch (error) {
    console.error('Error fetching current month received:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

const saveInvestments = async (req, res) => {
  const investList = req.body; // 클라이언트에서 보낸 투자 리스트
  const userId = req.user.id; // 로그인한 사용자 ID 가져오기

  const connection = await pool.getConnection(); // 트랜잭션을 위한 커넥션 얻기
  try {
    await connection.beginTransaction(); // 트랜잭션 시작
    for (const invest of investList) {
      const { date, stock, action, quantity } = invest;
      
      // 수량이 숫자인지 체크
      if (isNaN(quantity) || quantity <= 0) {
        throw new Error("Invalid quantity"); // 오류 발생 시 트랜잭션 롤백을 위해 throw 사용
      }

      // 기본 값 설정 (구매: 양수, 판매: 음수는 rp_amount가 아니라 수량에서만 적용됨)
      const updatedQuantity = action === "buy" ? quantity : -quantity;
      let stockField = '';
      let stockPriceField = '';
      let isForeignCurrency = false; // 환율 적용 대상인지 여부

      // 주식 종류에 따른 필드 설정
      if (stock === "Samsung") {
        stockField = 'sh_ss_count';
        stockPriceField = 'sc_ss_stock'; // 삼성전자 가격 필드
      } else if (stock === "Apple") {
        stockField = 'sh_ap_count';
        stockPriceField = 'sc_ap_stock'; // 애플 가격 필드
        isForeignCurrency = true; // 애플은 외화로 계산
      } else if (stock === "Bitcoin") {
        stockField = 'sh_bit_count';
        stockPriceField = 'sc_coin'; // 비트코인 가격 필드
        isForeignCurrency = true; // 비트코인도 외화로 계산
      } else {
        return res.status(400).json({ error: "Invalid stock type" });
      }

      // 현재 사용자가 보유한 해당 주식의 총량을 확인하는 쿼리
      const totalStockRecord = await connection.query(`
        SELECT ${stockField} 
        FROM tb_shares_held 
        WHERE user_id = ? 
        LIMIT 1
      `, [userId]);

      let currentStockQuantity = 0;
      if (totalStockRecord.length > 0) {
        currentStockQuantity = totalStockRecord[0][stockField] || 0;

        // 주식을 매도할 때 보유량이 0보다 작아지면 오류 처리
        if (action === "sell" && currentStockQuantity + updatedQuantity < 0) {
          throw new Error(`투자 종목 ${stock}의 보유량이 부족합니다.`);
        }
      }

      // 동일 날짜의 기록을 확인
      const sameDateRecord = await connection.query(`
        SELECT sh_date, sh_ss_count, sh_ap_count, sh_bit_count 
        FROM tb_shares_held
        WHERE user_id = ? AND sh_date = ?
        LIMIT 1
      `, [userId, date]);

      if (sameDateRecord.length > 0) {
        const record = sameDateRecord[0];

        // 해당 주식 필드가 비어있다면 업데이트
        if (record[stockField] === null || record[stockField] === 0) {
          await connection.query(`
            UPDATE tb_shares_held 
            SET ${stockField} = ?
            WHERE user_id = ? AND sh_date = ?
          `, [updatedQuantity, userId, date]);
        } else {
          // 이미 해당 주식 필드에 값이 있는 경우, 새로운 기록을 삽입
          await connection.query(`
            INSERT INTO tb_shares_held (user_id, sh_date, ${stockField})
            VALUES (?, ?, ?)
          `, [userId, date, updatedQuantity]);
        }
      } else {
        // 동일 날짜에 기록이 없으면 새로 삽입
        await connection.query(`
          INSERT INTO tb_shares_held (user_id, sh_date, ${stockField}) 
          VALUES (?, ?, ?)
        `, [userId, date, updatedQuantity]);
      }

      // 해당 날짜의 주식 가격 조회
      const stockPriceResult = await connection.query(`
        SELECT ${stockPriceField} FROM tb_stock
        WHERE fd_date = ?
        LIMIT 1
      `, [date]);

      if (stockPriceResult.length === 0) {
        return res.status(404).json({ error: `No stock price found for date ${date}` });
      }

      const stockPrice = stockPriceResult[0][stockPriceField];
      let totalAmount = Math.abs(updatedQuantity * stockPrice); // 갯수와 가격을 곱한 값, **양수로 처리**

      // 비트코인이나 애플의 경우 환율 적용
      if (isForeignCurrency) {
        // 해당 날짜의 환율 가져오기
        const exchangeRateResult = await connection.query(`
          SELECT mei_ex_rate FROM tb_main_economic_index 
          WHERE fd_date = ?
          LIMIT 1
        `, [date]);

        if (exchangeRateResult.length === 0) {
          return res.status(404).json({ error: 'No exchange rate found for date' });
        }
        const exchangeRate = exchangeRateResult[0].mei_ex_rate;
        // 금액 계산 (외화를 환율로 원화 변환)
        totalAmount *= exchangeRate; // 주식 가격과 수량을 곱한 후 환율 적용
      }

      // 거래내역에 추가 (매도, 매수에 상관없이 rp_amount는 **양수 값**)
      const transactionDetail = `${stock} ${Math.abs(updatedQuantity)}개 ${action === 'buy' ? '매수' : '매도'}`;
      await connection.query(`
        INSERT INTO tb_received_paid (user_id, rp_date, rp_detail, rp_amount, rp_hold, rp_part)
        VALUES (?, ?, ?, ?, 1, ?)
      `, [userId, date, transactionDetail, totalAmount, action === 'buy' ? 1 : 0]);
    }
    await connection.commit(); // 트랜잭션 성공 시 커밋
    res.status(200).json({ message: "Investments saved successfully" });

  } catch (error) {
    await connection.rollback(); // 오류 발생 시 롤백
    console.error('Error saving investments:', error);
    res.status(500).json({ error: 'Failed to save investments', details: error.message });
  } finally {
    connection.release(); // 커넥션 해제
  }
};


// 기존 투자 내역 조회 API
const getUserInvestments = async (req, res) => {
  try {
    const userId = req.user.id; // 로그인한 사용자 id 가져오기
    // 사용자에 해당하는 투자 내역 조회
    const investmentsResult = await pool.query(`
      SELECT sh_date, sh_ss_count, sh_ap_count, sh_bit_count
      FROM tb_shares_held
      WHERE user_id = ?
      ORDER BY sh_date DESC
    `, [userId]);

    if (investmentsResult.length === 0) {
      console.log('No investments found for this user'); // 로그 추가
      return res.json([]);  // 빈 배열을 반환
    }
    // 투자 내역을 JSON 형식으로 클라이언트에 반환
    res.json(investmentsResult);
  } catch (error) {
    console.error('Error fetching investments:', error); // 에러 로그 추가
    res.status(500).json({ error: 'Internal server error' });
  }
};


module.exports = {
  getUserCapital,
  getUserTargetBudget,
  updateUserTargetBudget,
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
  getMonthlyFixedDeposit,
  getMonthlyFixedInstallmentSaving,
  getTotalLoanRepayment
};
