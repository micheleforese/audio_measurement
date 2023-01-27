const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
const apiRouter = require("./routes");

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

app.use("/api", apiRouter);

app.listen(PORT, () => {
  console.log(`Listening on port: ${PORT}.`);
});
