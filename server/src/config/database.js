const mariadb = require('mariadb');
const dotenv = require('dotenv');
require('dotenv').config();

const pool = mariadb.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_DATABASE,
  port: process.env.DB_PORT || 3306,
  charset: process.env.DB_CHARSET,
  connectionLimit: 10,
  charset: 'utf8mb4'
});

module.exports = pool;
