const pool = require('../config/database');

const getStockData = async (req, res) => {
  try {
    const stock_info = await pool.query('\
      SELECT fd.fd_date fd_date, ts.sc_ss_stock sc_ss_stock, ts.sc_ap_stock sc_ap_stock, ts.sc_coin sc_coin\
      FROM tb_finance_date fd \
      JOIN (SELECT fd_date, sc_ss_stock, sc_ap_stock, sc_coin \
      FROM tb_stock) ts ON fd.fd_date = ts.fd_date;');
    if (stock_info.length === 0) {
      return res.status(404).json({ error: 'Stock data not found' });
    }

    const ko_ec_indi = await pool.query('\
      SELECT kei_gdp, kei_m2_end, kei_m2_avg, kei_fed_rate, kei_ppi, kei_ipi, kei_cpi, kei_imp, kei_exp, kei_cs, kei_bsi \
      FROM tb_korea_economic_indicator');
    if (ko_ec_indi.length === 0) {
      return res.status(404).json({ error: 'Korea economic indicator data not found' });
    }
    
    const us_ec_indi = await pool.query('\
      SELECT uei_gdp, uei_fed_rate, uei_ipi, uei_ppi, uei_cpi, uei_cpi_m, uei_trade, uei_cb_cc, uei_ps_m, uei_rs_m, uei_umich_cs \
      FROM tb_us_economic_indicator');
    if (us_ec_indi.length === 0) {
      return res.status(404).json({ error: 'US economic indicator data not found' });
    }
    
    const mainIndex = await pool.query('\
      SELECT mei_nasdaq, mei_sp500, mei_dow, mei_kospi, mei_gold, mei_oil, mei_ex_rate \
      FROM tb_main_economic_index');
    if (mainIndex.length === 0) {
      return res.status(404).json({ error: 'Main economic index data not found' });
    }

    const transformedData = {
      stockData: stock_info.map(stock => ({
        x : stock.fd_date, 
        Samsung_KRW : stock.sc_ss_stock, 
        Apple_USD : stock.sc_ap_stock, 
        Bitcoin_USD : stock.sc_coin,
      })),
      koreaIndicatorData: ko_ec_indi.map(indicator => ({
        GDP_한국 : indicator.kei_gdp,
        M2_통화공급_말잔_한국 : indicator.kei_m2_end,
        M2_통화공급_평잔_한국 : indicator.kei_m2_avg,
        기준금리_한국 : indicator.kei_fed_rate,
        생산자물가지수_한국 : indicator.kei_ppi,
        수입물가지수_한국 : indicator.kei_ipi,
        소비자물가지수_한국 : indicator.kei_cpi,
        수입지수_한국 : indicator.kei_imp,
        수출지수_한국 : indicator.kei_exp,
        경상수지_한국 : indicator.kei_cs,
        소비자심리지수_한국 : indicator.kei_bsi,
      })),
      usIndicatorData: us_ec_indi.map(indicator => ({
        GDP_미국 : indicator.uei_gdp,
        기준금리_미국 : indicator.uei_fed_rate,
        수입물가지수_미국 : indicator.uei_ipi,
        생산자물가지수_미국 : indicator.uei_ppi,
        소비자물가지수_전년대비_미국 : indicator.uei_cpi,
        소비자물가지수_전월대비_미국 : indicator.uei_cpi_m,
        무역수지_미국 : indicator.uei_trade,
        소비자신뢰지수_미국 : indicator.uei_cb_cc,
        개인지출_미국 : indicator.uei_ps_m,
        소매판매_미국 : indicator.uei_rs_m,
        소비자심리지수_미국 : indicator.uei_umich_cs,
      })),
      mainIndexData: mainIndex.map(index => ({
        NASDAQ : index.mei_nasdaq,
        SnP500 : index.mei_sp500,
        다우존스 : index.mei_dow,
        KOSPI : index.mei_kospi,
        금 : index.mei_gold,
        유가 : index.mei_oil,
        환율 : index.mei_ex_rate,
      })),
    };
    
    const per_pbr_roe = await pool.query('\
      SELECT sc_ss_per, sc_ss_pbr, sc_ss_roe, sc_ap_per, sc_ap_pbr, sc_ap_roe \
      FROM tb_stock \
      ORDER BY fd_date DESC \
      LIMIT 1;\
      ')
    if (per_pbr_roe.length === 0) {
      return res.status(404).json({ error : 'PER AND PBR Data not found' })
    }
    
    const merged = transformedData.stockData.map((stock, index) => ({
      ...stock,
      ...(transformedData.koreaIndicatorData[index] || {}),
      ...(transformedData.usIndicatorData[index] || {}),
      ...(transformedData.mainIndexData[index] || {})
    }));
    
    res.json({ merged, per_pbr_roe });
  } catch (error) {
    console.log('Error fetching stock data : ', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};

module.exports = {
  getStockData,
};