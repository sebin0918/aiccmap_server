const express = require('express');
const {
    getComponentsUserInfo
} = require('../controllers/ComponentsController');

const sessionChecker = require('../middlewares/sessionChecker');
const router = express.Router();    

router.get('/user-info', sessionChecker, getComponentsUserInfo);

module.exports = router;