const pool = require('../config/database');

const getNewsData = async (req, res) => {
  try {
    const news = await pool.query('\
      SELECT * \
      FROM tb_news \
      ');
    if (news.length === 0 ) {
      return res.status(404).json({ error : 'News data not found'});
    }

    res.json({ news })
  } catch {
    console.log('Error fetching news data : ', error);
    res.status(500).json({ error : 'Internal Server Error'})
  }
};

module.exports = {
  getNewsData
};