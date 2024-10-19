const pool = require('../config/database');

const getStockPredictData = async (req, res) => {
  
  let connection;
  try {
    connection = await pool.getConnection();
    const predict_quary = "SELECT sp_date, sp_ss_predict, sp_ap_predict, sp_bit_predict FROM tb_stock_predict ORDER by sp_date asc"
    const predict_result = await connection.execute(predict_quary);
    
    const stock_quary = "SELECT fd_date, sc_ss_stock, sc_ap_stock, sc_coin FROM tb_stock ORDER by fd_date asc"
    const stock_result = await connection.execute(stock_quary);

    // stock_result 데이터를 data에 추가
    const data = [];
    for (let i = 0; i < stock_result.length; i++) {
      const stockItem = stock_result[i];

      // 날짜를 형식에 맞게 변환 (로컬 시간대 사용)
      const dateKey = stockItem.fd_date.toLocaleDateString('en-CA'); // 'YYYY-MM-DD' 형식의 날짜

      // 주식 데이터 구조 생성
      const dataItem = {
        x: dateKey,
        Samsung: stockItem.sc_ss_stock,
        Apple: stockItem.sc_ap_stock,
        Bitcoin: stockItem.sc_coin,
        predictSamsung: null,
        predictApple: null,
        predictBitcoin: null
      };
      
      data.push(dataItem);  // data 배열에 추가
    }

    // 예측 데이터를 data에 추가
    for (let j = 0; j < predict_result.length; j++) {
      const predictItem = predict_result[j];
      
      // 날짜를 형식에 맞게 변환 (로컬 시간대 사용)
      const predictDateKey = predictItem.sp_date.toLocaleDateString('en-CA'); // 'YYYY-MM-DD' 형식의 날짜

      // 예측 데이터 객체 생성
      const predictDataItem = {
        x: predictDateKey,
        Samsung: null,
        Apple: null,
        Bitcoin: null,
        predictSamsung: predictItem.sp_ss_predict,
        predictApple: predictItem.sp_ap_predict,
        predictBitcoin: predictItem.sp_bit_predict
      };

      data.push(predictDataItem);
    }
    
    res.status(200).json(data);
  } catch (err) {
    console.error('주식예측데이터 쿼리실행 에러:', err);
    res.status(500).json({ message: '서버에러', error: err.message });
  } finally {
    if (connection) connection.release();
  }
};

module.exports ={
  getStockPredictData,
};