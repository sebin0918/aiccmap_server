const pool = require('../config/database');

const getNewsData = async (req, res) => {
  try {
    const news = await pool.query('SELECT * FROM tb_news');
    if (news.length === 0) {
      return res.status(404).json({ error: 'News data not found' });
    }

    // 뉴스 데이터를 처리하여 title을 나눕니다.
    const processedNews = news.map(item => {
      const [title, extra] = item.news_title.split('!eo$'); // !eo$를 기준으로 나눔
      return {
        news_id: item.news_id,
        news_title: title.trim(), // 앞부분을 news_title로 사용
        news_simple_text: item.news_simple_text,
        news_link: item.news_link,
        news_classification: item.news_classification,
        extra_info: extra ? extra.trim() : '' // 뒷부분을 extra_info로 사용
      };
    });
    res.json({ news: processedNews });
  } catch (error) {
    console.error('Error fetching news data:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
};

module.exports = {
  getNewsData
};
