# Common Commands

## Basics - [HERE](https://wiki.epfl.ch/me412-emem-2020/documents/34460-90901.pdf#page=194)

Chain commands

```
TRIG:SOUR EXT;COUNT 10

TRIG:SOUR EXT
TRIG:COUNT 10
```

```
TRIG:COUN MIN;:SAMP:COUN MIN

TRIG:COUN MIN
SAMP:COUN MIN
```

Display Text

```
DISP:TEXT "WAITING..."
```

To Terminate a measurement

```
ABORt
```

Commands by Subsystem: [here](https://wiki.epfl.ch/me412-emem-2020/documents/34460-90901.pdf#page=194)

## FETCh - [HERE](https://wiki.epfl.ch/me412-emem-2020/documents/34460-90901.pdf#page=201)

```
CONF:VOLT:DC 10,0.003
TRIG:SOUR EXT
SAMP:COUN 4
INIT
FETC?
```

USE `DATA:REMove?` to read and erase all memory
use `ABORt` to return idle

## NI-DRIVER

Nella cartella `driver` ci sono i pacchetti da installare.