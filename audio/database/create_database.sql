CREATE DATABASE IF NOT EXISTS audio;

CREATE TABLE IF NOT EXISTS audio.test(
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  date DATETIME NOT NULL,
  comment VARCHAR(500),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS audio.sweep(
  id INT NOT NULL AUTO_INCREMENT,
  test_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  date DATETIME NOT NULL,
  comment VARCHAR(500),
  PRIMARY KEY (id),
  FOREIGN KEY (test_id) REFERENCES audio.test (id)
);

CREATE TABLE IF NOT EXISTS audio.frequency(
  id INT NOT NULL AUTO_INCREMENT,
  sweep_id INT NOT NULL,
  idx INT NOT NULL,
  frequency DOUBLE NOT NULL,
  Fs DOUBLE NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (sweep_id) REFERENCES audio.sweep (id)
);

CREATE TABLE IF NOT EXISTS audio.channel(
  id INT NOT NULL AUTO_INCREMENT,
  sweep_id INT NOT NULL,
  idx INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  comment VARCHAR(500),
  PRIMARY KEY (id),
  FOREIGN KEY (sweep_id) REFERENCES audio.sweep (id)
);

CREATE TABLE IF NOT EXISTS audio.sweepVoltage(
  id INT NOT NULL AUTO_INCREMENT,
  frequency_id INT NOT NULL,
  channel_id INT NOT NULL,
  voltages BLOB NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (frequency_id) REFERENCES audio.frequency (id),
  FOREIGN KEY (channel_id) REFERENCES audio.channel (id)
);

CREATE TABLE IF NOT EXISTS audio.sweepConfig(
  sweep_id INT NOT NULL,
  amplitude DOUBLE,
  frequency_min DOUBLE,
  frequency_max DOUBLE,
  points_per_decade DOUBLE,
  number_of_samples INT,
  Fs_multiplier DOUBLE,
  delay_measurements DOUBLE,
  FOREIGN KEY (sweep_id) REFERENCES audio.sweep (id)
);

CREATE TABLE IF NOT EXISTS audio.testConfig(
  test_id INT NOT NULL,
  config BLOB NOT NULL,
  FOREIGN KEY (test_id) REFERENCES audio.test (id)
);

-- CREATE TABLE IF NOT EXISTS audio.media(
--   id INT NOT NULL AUTO_INCREMENT,
--   test_id INT NOT NULL,
--   name VARCHAR(255) NOT NULL,
--   comment VARCHAR(500),
--   PRIMARY KEY (id),
-- );
