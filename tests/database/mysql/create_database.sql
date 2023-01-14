CREATE DATABASE audio;

CREATE TABLE audio.test(
  id INTEGER NOT NULL AUTO_INCREMENT,
  name TEXT NOT NULL,
  comment TEXT,
  date TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE audio.sweep(
  id INTEGER NOT NULL AUTO_INCREMENT,
  name TEXT NOT NULL,
  date TEXT NOT NULL,
  comment TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS audio.frequency(
  sweep_id INTEGER,
  id INTEGER NOT NULL,
  frequency DOUBLE NOT NULL,
  FOREIGN KEY(sweep_id) REFERENCES sweep(id)
);

CREATE TABLE IF NOT EXISTS audio.channel(
  sweep_id INTEGER NOT NULL,
  id INTEGER NOT NULL,
  name TEXT NOT NULL,
  comment TEXT,
  FOREIGN KEY(sweep_id) REFERENCES sweep(id)
);

CREATE TABLE IF NOT EXISTS audio.sweepVoltage(
  frequency_id INTEGER NOT NULL,
  channel_id INTEGER NOT NULL,
  id INTEGER NOT NULL,
  voltage DOUBLE NOT NULL,
  FOREIGN KEY(frequency_id) REFERENCES frequency(id),
  FOREIGN KEY(channel_id) REFERENCES channel(id)
);

CREATE TABLE IF NOT EXISTS audio.sweepConfig(
  frequency_id INTEGER NOT NULL,
  rms DOUBLE NOT NULL,
  dBV DOUBLE NOT NULL,
  Fs DOUBLE NOT NULL,
  number_of_samples INTEGER NOT NULL,
  FOREIGN KEY(frequency_id) REFERENCES frequency(id)
);