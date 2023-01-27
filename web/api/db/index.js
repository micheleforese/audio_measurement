const mysql = require("mysql2");

const pool = mysql.createPool({
  connectionLimit: 10,
  user: "audio",
  password: "acmesystemsaudio",
  host: "localhost",
  port: "3306",
  database: "audio",
});

let testdb = {};

testdb.get_all = function () {
  return new Promise(function (resolve, reject) {
    query = `SELECT * FROM test`;
    pool.query(query, function (err, results) {
      if (err) {
        return reject(err);
      }
      return resolve(results);
    });
  });
};

testdb.get_from_id = function (id) {
  return new Promise(function (resolve, reject) {
    query = `SELECT * FROM test WHERE id = ?`;
    pool.query(query, [id], function (err, results) {
      if (err) {
        return reject(err);
      }
      return resolve(results[0]);
    });
  });
};

testdb.create_user = function (name, date, comment) {
  return new Promise(function (resolve, reject) {
    query = `INSERT INTO test(name, date, comment) VALUES (?, ?, ?)`;
    pool.query(query, [name, date, comment], function (err, results) {
      if (err) {
        return reject(err);
      }
      return resolve({ response_type: "OK", id: results.insertId });
    });
  });
};

module.exports = testdb;
