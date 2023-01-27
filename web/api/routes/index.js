const express = require("express");
const db = require("../db");
const apiTestRouter = require("./test.js");
const router = express.Router();

router.use("/tests", apiTestRouter);

module.exports = router;
