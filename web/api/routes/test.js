const express = require("express");
const db = require("../db");

const router = express.Router();

router.get("/", async function (req, res, next) {
  try {
    let results = await db.get_all();
    res.json(results);
  } catch (error) {
    console.log(error);
    res.sendStatus(500);
  }
});

router.get("/:id", async function (req, res, next) {
  try {
    let results = await db.get_from_id(req.params.id);
    res.json(results);
  } catch (error) {
    console.log(error);
    res.sendStatus(500);
  }
});

router.post("/", async function (req, res, next) {
  try {
    let results = await db.create_user(
      req.body.name,
      req.body.date,
      req.body.date,
      req.body.comment
    );
    res.status(200).json(results);
  } catch (error) {
    console.log(error);
    res.sendStatus(500);
  }
});
module.exports = router;
