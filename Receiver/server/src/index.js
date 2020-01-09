const express = require('express');
const {spawn} = require("child_process");


const app = express();
const port = 80;

const subprocess = spawn("python3 -m temperature -r");
let last_json = "";
subprocess.stdout.on("data", (data) => {
  last_json = data;
});

app.get('/', (req, res) => {
  res.send(last_json);
});

app.listen(port, () => console.log(`listening on port ${port}!`));