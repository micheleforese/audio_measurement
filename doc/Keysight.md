# Command Quick Reference

> Be sure to read language syntax conventions. Commands or parameters shown in blue apply only to the 34465A/70A, all other commands/parameters apply to all Truevolt DMMs.


## Configuration Commands

```SCPI
CONFigure?

CONFigure:CAPacitance [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure:CONTinuity

CONFigure:CURRent:{AC|DC} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure:DIODe

CONFigure:{FREQuency|PERiod} [{<range>|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure:{RESistance|FRESistance} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure:TEMPerature [{FRTD|RTD|FTHermistor|THERmistor|TCouple|DEFault} [, {<type>|DEFault} [,1 , {<resolution>|MIN|MAX|DEF}]]]]

CONFigure[:VOLTage]:{AC|DC} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure[:VOLTage][:DC]:RATio [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]
```

## Measurement Commands

```
MEASure:CAPacitance? [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

MEASure:CONTinuity?

MEASure:CURRent:{AC|DC}? [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

MEASure:DIODe?

MEASure:{FREQuency|PERiod}? [{<range>|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

MEASure:{RESistance|FRESistance}? [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

MEASure:TEMPerature? [{FRTD|RTD|FTHermistor|THERmistor|TCouple|DEFault} [, {<type>|DEFault} [,1 , {<resolution>|MIN|MAX|DEF}]]]]

MEASure[:VOLTage]:{AC|DC}? [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

MEASure[:VOLTage][:DC]:RATio? [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]
```

## Measurement Configuration Commands

```
[SENSe:]FUNCtion[:ON] "<function>"
[SENSe:]FUNCtion[:ON]?
```

## AC and DC Voltage and DC Ratio Configuration Commands

```
CONFigure[:VOLTage]:{AC|DC} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure[:VOLTage][:DC]:RATio [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure?

[SENSe:]VOLTage:AC:BANDwidth {<filter>|MIN|MAX|DEF}
[SENSe:]VOLTage:AC:BANDwidth? [{MIN|MAX|DEF}]

[SENSe:]VOLTage:{AC|DC}:NULL[:STATe] {OFF|ON}
[SENSe:]VOLTage:{AC|DC}:NULL[:STATe]?

[SENSe:]VOLTage:{AC|DC}:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]VOLTage:{AC|DC}:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]VOLTage:{AC|DC}:NULL:VALue:AUTO {OFF|ON}
[SENSe:]VOLTage:{AC|DC}:NULL:VALue:AUTO?

[SENSe:]VOLTage:{AC|DC}:RANGe {<range>|MIN|MAX|DEF}
[SENSe:]VOLTage:{AC|DC}:RANGe? [{MIN|MAX|DEF}]

[SENSe:]VOLTage:{AC|DC}:RANGe:AUTO {OFF|ON|ONCE}
[SENSe:]VOLTage:{AC|DC}:RANGe:AUTO?

[SENSe:]VOLTage:AC:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"VOLTage[:DC]"}
[SENSe:]VOLTage:AC:SECondary?

[SENSe:]VOLTage[:DC]:APERture {<seconds>|MIN|MAX|DEF}
[SENSe:]VOLTage[:DC]:APERture? [{MIN|MAX|DEF}]

[SENSe:]VOLTage[:DC]:APERture:ENABled {OFF|ON}
[SENSe:]VOLTage[:DC]:APERture:ENABled?

[SENSe:]VOLTage[:DC]:IMPedance:AUTO {OFF|ON}
[SENSe:]VOLTage[:DC]:IMPedance:AUTO?

[SENSe:]VOLTage[:DC]:NPLC {<PLCs>|MIN|MAX|DEF}
[SENSe:]VOLTage[:DC]:NPLC? [{MIN|MAX|DEF}]

[SENSe:]VOLTage[:DC]:RATio:SECondary {"OFF"|"CALCulate:DATA"|"SENSe:DATA"}
[SENSe:]VOLTage[:DC]:RATio:SECondary?

[SENSe:]VOLTage[:DC]:RESolution {<resolution>|MIN|MAX|DEF}
[SENSe:]VOLTage[:DC]:RESolution? [{MIN|MAX|DEF}]

[SENSe:]VOLTage[:DC]:SECondary {"OFF"|"CALCulate:DATA"|"VOLTage:AC"|"PTPeak"}
[SENSe:]VOLTage[:DC]:SECondary?

[SENSe:]VOLTage[:DC]:ZERO:AUTO {OFF|ON|ONCE}
[SENSe:]VOLTage[:DC]:ZERO:AUTO?
```

## 2-Wire and 4-Wire Resistance Configuration Commands

```
CONFigure:{RESistance|FRESistance} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure?

[SENSe:]{RESistance|FRESistance}:APERture {<seconds>|MIN|MAX|DEF}
[SENSe:]{RESistance|FRESistance}:APERture? [{MIN|MAX|DEF}]

[SENSe:]{RESistance|FRESistance}:APERture:ENABled {OFF|ON}
[SENSe:]{RESistance|FRESistance}:APERture:ENABled?

[SENSe:]{RESistance|FRESistance}:NPLC {<PLCs>|MIN|MAX|DEF}
[SENSe:]{RESistance|FRESistance}:NPLC? [{MIN|MAX|DEF}]

[SENSe:]{RESistance|FRESistance}:NULL[:STATe] {OFF|ON}
[SENSe:]{RESistance|FRESistance}:NULL[:STATe]?

[SENSe:]{RESistance|FRESistance}:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]{RESistance|FRESistance}:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]{RESistance|FRESistance}:NULL:VALue:AUTO {OFF|ON}
[SENSe:]{RESistance|FRESistance}:NULL:VALue:AUTO?

[SENSe:]{RESistance|FRESistance}:OCOMpensated {OFF|ON}
[SENSe:]{RESistance|FRESistance}:OCOMpensated?

[SENSe:]{RESistance|FRESistance}:POWer:LIMit[:STATe] {OFF|ON}
[SENSe:]{RESistance|FRESistance}:POWer:LIMit[:STATe]?

[SENSe:]{RESistance|FRESistance}:RANGe {<range>|MIN|MAX|DEF}
[SENSe:]{RESistance|FRESistance}:RANGe? [{MIN|MAX|DEF}]

[SENSe:]{RESistance|FRESistance}:RANGe:AUTO {OFF|ON|ONCE}
[SENSe:]{RESistance|FRESistance}:RANGe:AUTO?

[SENSe:]{RESistance|FRESistance}:RESolution {<resolution>|MIN|MAX|DEF}
[SENSe:]{RESistance|FRESistance}:RESolution? [{MIN|MAX|DEF}]

[SENSe:]{FRESistance|RESistance}:SECondary {"OFF"|"CALCulate:DATA"}
[SENSe:]{FRESistance|RESistance}:SECondary?

[SENSe:]RESistance:ZERO:AUTO {OFF|ON|ONCE}
[SENSe:]RESistance:ZERO:AUTO?
```

## AC and DC Current Configuration Commands

```
CONFigure:CURRent:{AC|DC} [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure?

[SENSe:]CURRent:AC:BANDwidth {<filter>|MIN|MAX|DEF}
[SENSe:]CURRent:AC:BANDwidth? [{MIN|MAX|DEF}]

[SENSe:]CURRent:{AC|DC}:NULL[:STATe] {OFF|ON}
[SENSe:]CURRent:{AC|DC}:NULL[:STATe]?

[SENSe:]CURRent:{AC|DC}:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]CURRent:{AC|DC}:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]CURRent:{AC|DC}:NULL:VALue:AUTO {OFF|ON}
[SENSe:]CURRent:{AC|DC}:NULL:VALue:AUTO?

[SENSe:]CURRent:{AC|DC}:RANGe {<range>|MIN|MAX|DEF}
[SENSe:]CURRent:{AC|DC}:RANGe? [{MIN|MAX|DEF}]

[SENSe:]CURRent:{AC|DC}:RANGe:AUTO {OFF|ON|ONCE}
[SENSe:]CURRent:{AC|DC}:RANGe:AUTO?

[SENSe:]CURRent:{AC|DC}:TERMinals {3|10}
[SENSe:]CURRent:{AC|DC}:TERMinals?

[SENSe:]CURRent:AC:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"CURRent[:DC]"}
[SENSe:]CURRent:AC:SECondary?

[SENSe:]CURRent[:DC]:APERture {<seconds>|MIN|MAX|DEF}
[SENSe:]CURRent[:DC]:APERture? [{MIN|MAX|DEF}]

[SENSe:]CURRent[:DC]:APERture:ENABled{OFF|ON}
[SENSe:]CURRent[:DC]:APERture:ENABled?

[SENSe:]CURRent[:DC]:NPLC {<PLCs>|MIN|MAX|DEF}
[SENSe:]CURRent[:DC]:NPLC? [{MIN|MAX|DEF}]

[SENSe:]CURRent[:DC]:RESolution {<resolution>|MIN|MAX|DEF}
[SENSe:]CURRent[:DC]:RESolution? [{MIN|MAX|DEF}]

[SENSe:]CURRent[:DC]:SECondary {"OFF"|"CALCulate:DATA"|"CURRent:AC"|"PTPeak"}
[SENSe:]CURRent[:DC]:SECondary?

[SENSe:]CURRent[:DC]:ZERO:AUTO {OFF|ON|ONCE}
[SENSe:]CURRent[:DC]:ZERO:AUTO?

[SENSe:]CURRent:SWITch:MODE {FAST|CONTinuous}

[SENSe:]CURRent:SWITch:MODE?
```

## Capacitance Configuration Commands

```
CONFigure:CAPacitance [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]

CONFigure?

[SENSe:]CAPacitance:NULL[:STATe]{OFF|ON}
[SENSe:]CAPacitance:NULL[:STATe]?

[SENSe:]CAPacitance:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]CAPacitance:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]CAPacitance:NULL:VALue:AUTO {OFF|ON}
[SENSe:]CAPacitance:NULL:VALue:AUTO?

[SENSe:]CAPacitance:RANGe {<range>|MIN|MAX|DEF}
[SENSe:]CAPacitance:RANGe? [{MIN|MAX|DEF}]

[SENSe:]CAPacitance:RANGe:AUTO {OFF|ON|ONCE}
[SENSe:]CAPacitance:RANGe:AUTO?

[SENSe:]CAPacitance:SECondary{"OFF"|"CALCulate:DATA"}

[SENSe:]CAPacitance:SECondary?
```

## Temperature Configuration Commands

```
CONFigure:TEMPerature [{FRTD|RTD|FTHermistor|THERmistor|TCouple|DEFault} [, {<type>|DEFault} [,1 , {<resolution>|MIN|MAX|DEF}]]]]
CONFigure?

[SENSe:]TEMPerature:APERture {<seconds>|MIN|MAX|DEF}
[SENSe:]TEMPerature:APERture? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:APERture:ENABled {OFF|ON}
[SENSe:]TEMPerature:APERture:ENABled?

[SENSe:]TEMPerature:NPLC {<PLCs>|MIN|MAX|DEF}
[SENSe:]TEMPerature:NPLC? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:NULL[:STATe] {OFF|ON}
[SENSe:]TEMPerature:NULL[:STATe]?

[SENSe:]TEMPerature:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]TEMPerature:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:NULL:VALue:AUTO {OFF|ON}
[SENSe:]TEMPerature:NULL:VALue:AUTO?

[SENSe:]TEMPerature:SECondary {"OFF"|"CALCulate:DATA"|"SENSe:DATA"}
[SENSe:]TEMPerature:SECondary?

[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:OCOMpensated {OFF|ON}
[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:OCOMpensated?

[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:POWer:LIMit[:STATe] {OFF|ON}
[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:POWer:LIMit[:STATe]?

[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:RESistance[:REFerence] {<reference>|MIN|MAX|DEF}
[SENSe:]TEMPerature:TRANsducer:{FRTD|RTD}:RESistance[:REFerence]? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:TRANsducer:{FTHermistor|THERmistor}:POWer:LIMit[:STATe] {OFF|ON}
[SENSe:]TEMPerature:TRANsducer:{FTHermistor|THERmistor}:POWer:LIMit[:STATe]?

[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk {OFF|ON}
[SENSe:]TEMPerature:TRANsducer:TCouple:CHECk?

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction {<temperature>|MIN|MAX|DEF}
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:OFFSet:ADJust {<temperature>|MIN|MAX|DEF}
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:OFFSet:ADJust? [{MIN|MAX|DEF}]

[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE {INTernal|FIXed}
[SENSe:]TEMPerature:TRANsducer:TCouple:RJUNction:TYPE?

[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE {E|J|K|N|R|T}
[SENSe:]TEMPerature:TRANsducer:TCouple:TYPE?

[SENSe:]TEMPerature:TRANsducer:TYPE {FRTD|RTD|FTHermistor|THERmistor|TCouple}
[SENSe:]TEMPerature:TRANsducer:TYPE?

[SENSe:]TEMPerature:ZERO:AUTO {OFF|ON|ONCE}
[SENSe:]TEMPerature:ZERO:AUTO?

UNIT:TEMPerature {C|F|K}
UNIT:TEMPerature?

Frequency/Period Configuration Commands
CONFigure:{FREQuency|PERiod} [{<range>|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}]]
CONFigure?

[SENSe:]{FREQuency|PERiod}:APERture {<seconds>|MIN|MAX|DEF}
[SENSe:]{FREQuency|PERiod}:APERture? [{MIN|MAX|DEF}]

[SENSe:]{FREQuency|PERiod}:NULL[:STATe] {OFF|ON}
[SENSe:]{FREQuency|PERiod}:NULL[:STATe]?

[SENSe:]{FREQuency|PERiod}:NULL:VALue {<value>|MIN|MAX|DEF}
[SENSe:]{FREQuency|PERiod}:NULL:VALue? [{MIN|MAX|DEF}]

[SENSe:]{FREQuency|PERiod}:NULL:VALue:AUTO {OFF|ON}
[SENSe:]{FREQuency|PERiod}:NULL:VALue:AUTO?

[SENSe:]{FREQuency|PERiod}:RANGe:LOWer{<freq>|MIN|MAX|DEF}
[SENSe:]{FREQuency|PERiod}:RANGe:LOWer?

[SENSe:]{FREQuency|PERiod}:TIMeout:AUTO {OFF|ON}

[SENSe:]{FREQuency|PERiod}:VOLTage:RANGe {<range>|MIN|MAX|DEF}
[SENSe:]{FREQuency|PERiod}:VOLTage:RANGe? [{MIN|MAX|DEF}]

[SENSe:]{FREQuency|PERiod}:VOLTage:RANGe:AUTO {OFF|ON|ONCE}
[SENSe:]{FREQuency|PERiod}:VOLTage:RANGe:AUTO?

[SENSe:]FREQuency:SECondary {"OFF"|"CALCulate:DATA"|"PERiod"|"VOLTage:AC"}
[SENSe:]FREQuency:SECondary?

[SENSe:]PERiod:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"VOLTage:AC"}
[SENSe:]PERiod:SECondary?

Continuity and Diode Configuration Commands
CONFigure:CONTinuity

CONFigure:DIODe

Secondary Measurement Commands
[SENSe:]CAPacitance:SECondary {"OFF"|"CALCulate:DATA"}

[SENSe:]CAPacitance:SECondary?

[SENSe:]CURRent:AC:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"CURRent[:DC]"}
[SENSe:]CURRent:AC:SECondary?

[SENSe:]CURRent[:DC]:SECondary {"OFF"|"CALCulate:DATA"|"CURRent:AC"|"PTPeak"}
[SENSe:]CURRent[:DC]:SECondary?

[SENSe:]DATA2?

[SENSe:]DATA2:CLEar[:IMMediate]

[SENSe:]{FRESistance|RESistance}:SECondary {"OFF"|"CALCulate:DATA"}
[SENSe:]{FRESistance|RESistance}:SECondary?

[SENSe:]FREQuency:SECondary {"OFF"|"CALCulate:DATA"|"PERiod"|"VOLTage:AC"}
[SENSe:]PERiod:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"VOLTage:AC"}

[SENSe:]TEMPerature:SECondary {"OFF"|"CALCulate:DATA"|"SENSe:DATA"}
[SENSe:]TEMPerature:SECondary?

[SENSe:]VOLTage:AC:SECondary {"OFF"|"CALCulate:DATA"|"FREQuency"|"VOLTage[:DC]"}
[SENSe:]VOLTage:AC:SECondary?

[SENSe:]VOLTage[:DC]:RATio:SECondary {"OFF"|"CALCulate:DATA"|"SENSe:DATA"}
[SENSe:]VOLTage[:DC]:RATio:SECondary?

[SENSe:]VOLTage[:DC]:SECondary {"OFF"|"CALCulate:DATA"|"VOLTage:AC"|"PTPeak"}
[SENSe:]VOLTage[:DC]:SECondary?

Miscellaneous Configuration Commands
ROUTe:TERMinals?

Sample Commands
SAMPle:COUNt {<count>|MIN|MAX|DEF}
SAMPle:COUNt? [{MIN|MAX|DEF}]

SAMPle:COUNt:PRETrigger {<count>|MIN|MAX|DEF}
SAMPle:COUNt:PRETrigger? [{MIN|MAX|DEF}]

SAMPle:SOURce {IMMediate|TIMer}
SAMPle:SOURce?

SAMPle:TIMer {<interval>|MIN|MAX|DEF}
SAMPle:TIMer? [{MIN|MAX|DEF}]

Triggering Commands
ABORt

INITiate[:IMMediate]

OUTPut:TRIGger:SLOPe {POSitive|NEGative}
OUTPut:TRIGger:SLOPe?

READ?

SAMPle:COUNt {<count>|MIN|MAX|DEF}
SAMPle:COUNt? [{MIN|MAX|DEF}]

SAMPle:COUNt:PRETrigger {<count>|MIN|MAX|DEF}
SAMPle:COUNt:PRETrigger? [{MIN|MAX|DEF}]

*TRG

TRIGger:COUNt {<count>|MIN|MAX|DEF|INFinity}
TRIGger:COUNt? [{MIN|MAX|DEF}]

TRIGger:DELay {<seconds>|MIN|MAX|DEF}
TRIGger:DELay? [{MIN|MAX|DEF}]

TRIGger:DELay:AUTO {OFF|ON}
TRIGger:DELay:AUTO?

TRIGger:LEVel {<level>|MIN|MAX|DEF}
TRIGger:LEVel? [{MIN|MAX|DEF}]

TRIGger:SLOPe {POSitive|NEGative}
TRIGger:SLOPe?

TRIGger:SOURce {IMMediate|EXTernal|BUS|INTernal}
TRIGger:SOURce?

Calculation (Math) Commands
Overall
CALCulate:CLEar[:IMMediate]

Histogram
CALCulate:TRANsform:HISTogram:ALL?

CALCulate:TRANsform:HISTogram:CLEar[:IMMediate]

CALCulate:TRANsform:HISTogram:COUNt?

CALCulate:TRANsform:HISTogram:DATA?

CALCulate:TRANsform:HISTogram:POINts {<value>|MIN|MAX|DEF}
CALCulate:TRANsform:HISTogram:POINts? [{MIN|MAX|DEF}]

CALCulate:TRANsform:HISTogram:RANGe:AUTO {OFF|ON}
CALCulate:TRANsform:HISTogram:RANGe:AUTO?

CALCulate:TRANsform:HISTogram:RANGe:{LOWer|UPPer} {<value>|MIN|MAX|DEF}
CALCulate:TRANsform:HISTogram:RANGe:{LOWer|UPPer}? [{MIN|MAX|DEF}]

CALCulate:TRANsform:HISTogram[:STATe] {OFF|ON}
CALCulate:TRANsform:HISTogram[:STATe]?

Limit Testing
CALCulate:LIMit:CLEar[:IMMediate]

CALCulate:LIMit:{LOWer|UPPer}[:DATA] {<value>|MIN|MAX|DEF}
CALCulate:LIMit:{LOWer|UPPer}[:DATA]? [{MIN|MAX|DEF}]

CALCulate:LIMit[:STATe] {OFF|ON}
CALCulate:LIMit[:STATe]?

Scaling
CALCulate:SCALe:DB:REFerence {<reference>|MIN|MAX|DEF}
CALCulate:SCALe:DB:REFerence? [{MIN|MAX|DEF}]

CALCulate:SCALe:DBM:REFerence {<reference>|MIN|MAX|DEF}
CALCulate:SCALe:DBM:REFerence? [{MIN|MAX|DEF}]

CALCulate:SCALe:FUNCtion{DB|DBM|PCT|SCALe}

CALCulate:SCALe:FUNCtion?

CALCulate:SCALe:GAIN {<gain>|MIN|MAX|DEF}
CALCulate:SCALe:GAIN? [{MIN|MAX|DEF}]

CALCulate:SCALe:OFFSet {<offset>|MIN|MAX|DEF}
CALCulate:SCALe:OFFSet? [{MIN|MAX|DEF}]

CALCulate:SCALe:REFerence:AUTO {OFF|ON}
CALCulate:SCALe:REFerence:AUTO?

CALCulate:SCALe:REFerence {<reference>|MIN|MAX|DEF}
CALCulate:SCALe:REFerence? [{MIN|MAX|DEF}]

CALCulate:SCALe[:STATe] {OFF|ON}
CALCulate:SCALe[:STATe]?

CALCulate:SCALe:UNIT <quoted_string>
CALCulate:SCALe:UNIT?

CALCulate:SCALe:UNIT:STATe {OFF|ON}
CALCulate:SCALe:UNIT:STATe?

Statistics
CALCulate:AVERage:ALL?

CALCulate:AVERage:AVERage?

CALCulate:AVERage:CLEar[:IMMediate]

CALCulate:AVERage:COUNt?

CALCulate:AVERage:MAXimum?

CALCulate:AVERage:MINimum?

CALCulate:AVERage:PTPeak?

CALCulate:AVERage:SDEViation?

CALCulate:AVERage[:STATe] {OFF|ON}
CALCulate:AVERage[:STATe]?

Smoothing
CALCulate:SMOothing:RESPonse {SLOW|MEDium|FAST}
CALCulate:SMOothing:RESPonse?

CALCulate:SMOothing[:STATe] {OFF|ON}
CALCulate:SMOothing[:STATe]?

Trend Chart
CALCulate:TCHart[:STATe] {OFF|ON}
CALCulate:TCHart[:STATe]?

Reading Memory Commands
DATA:LAST?

DATA:POINts:EVENt:THReshold <count>
DATA:POINts:EVENt:THReshold?

DATA:POINts?

DATA:REMove? <num_readings> [,WAIT]

FETCh?

R? [<max_readings>]

Calibration Commands
*CAL?

CALibration:ADC?

CALibration[:ALL]?

CALibration:COUNt?

CALibration:DATE?

CALibration:SECure:CODE <new_code>

CALibration:SECure:STATe {OFF|ON} [, <code>]
CALibration:SECure:STATe?

CALibration:STORe

CALibration:STRing "<string>"
CALibration:STRing?

CALibration:TEMPerature?

CALibration:TIME?

CALibration:VALue <value>
CALibration:VALue?

SYSTem:ACALibration:DATE?

SYSTem:ACALibration:TEMPerature?

SYSTem:ACALibration:TIME?

State Storage and Preferences Commands
*LRN?

MMEMory:LOAD:PREFerences <file>

MMEMory:LOAD:STATe <file>

MMEMory:STORe:PREFerences <file>

MMEMory:STORe:STATe <file>

MMEMory:STATe:RECall:AUTO {OFF|ON}
MMEMory:STATe:RECall:AUTO?

MMEMory:STATe:RECall:SELect <file>
MMEMory:STATe:RECall:SELect?

MMEMory:STATe:VALid? <file>

*RCL {0|1|2|3|4}

*SAV {0|1|2|3|4}

General Purpose File Management Commands
MMEMory:CATalog[:ALL]? [<folder>[<filespec>]]

MMEMory:CDIRectory <folder>
MMEMory:CDIRectory?

MMEMory:COPY <file1>, <file2>

MMEMory:DELete {<file>|<filespec>}

MMEMory:MDIRectory <folder>

MMEMory:MOVE <file1>, <file2>

MMEMory:RDIRectory <folder>

Data Transfer Commands
MMEMory:DOWNload:DATA <binary_block>

MMEMory:DOWNload:FNAMe <file>

MMEMory:DOWNload:FNAMe?

MMEMory:FORMat:READing:CSEParator {COMMa|SEMicolon|TAB}

MMEMory:FORMat:READing:CSEParator?

MMEMory:FORMat:READing:INFormation {OFF|ON}
MMEMory:FORMat:READing:INFormation?

MMEMory:FORMat:READing:RLIMit {OFF|ON}
MMEMory:FORMat:READing:RLIMit?

MMEMory:STORe:DATA RDG_STORE, <file>

MMEMory:UPLoad? <file>

IEEE-488 Commands
*CAL?

*CLS

*ESE <enable_value>
*ESE?

*ESR?

*IDN?

*LRN?

*OPC

*OPC?

*OPT?

*PSC {0|1}
*PSC?

*RCL {0|1|2|3|4}

*RST

*SAV {0|1|2|3|4}

*SRE <enable_value>
*SRE?

*STB?

*TRG

*TST?

*WAI

Format Subsystem
FORMat:BORDer {NORMal|SWAPped}
FORMat:BORDer?

FORMat[:DATA] {ASCii|REAL} [, <length>]
FORMat[:DATA]?

System-Related Commands
*CAL?

DISPlay[:STATe] {OFF|ON}
DISPlay[:STATe]?

DISPlay:TEXT:CLEar

DISPlay:TEXT[:DATA] "<string>"
DISPlay:TEXT[:DATA]?

DISPlay:VIEW {NUMeric|HISTogram|TCHart|METer}
DISPlay:VIEW?

HCOPy:SDUMp:DATA:FORMat {PNG|BMP}
HCOPy:SDUMp:DATA:FORMat?

HCOPy:SDUMp:DATA?

*IDN?

LXI:IDENtify[:STATe] {OFF|ON}
LXI:IDENtify[:STATe]?

LXI:MDNS:ENABle {OFF|ON}
LXI:MDNS:ENABle?

LXI:MDNS:HNAMe[:RESolved]?

LXI:MDNS:SNAMe:DESired "<name>"
LXI:MDNS:SNAMe:DESired?

LXI:MDNS:SNAMe[:RESolved]?

LXI:RESet

LXI:RESTart

*RST

SYSTem:ACALibration:DATE?

SYSTem:ACALibration:TEMPerature?

SYSTem:ACALibration:TIME?

SYSTem:BEEPer[:IMMediate]

SYSTem:BEEPer:STATe {OFF|ON}
SYSTem:BEEPer:STATe?

SYSTem:CLICk:STATe {OFF|ON}
SYSTem:CLICk:STATe?

SYSTem:DATE <year>, <month>, <day>
SYSTem:DATE?

SYSTem:ERRor[:NEXT]?

SYSTem:HELP?

SYSTem:IDENtify {DEFault|AT34460A|AT34461A|AT34410A|AT34411A|HP34401A}*
SYSTem:IDENtify?

SYSTem:LABel "<string>"
SYSTem:LABel?

SYSTem:PRESet

SYSTem:SECurity:COUNt?

SYSTem:SECurity:IMMediate

SYSTem:TEMPerature?

SYSTem:TIME <hour>, <minute>, <second>
SYSTem:TIME?

SYSTem:UPTime?

SYSTem:USB:HOST:ENABle {OFF|ON}
SYSTem:USB:HOST:ENABle?

SYSTem:VERSion?

SYSTem:WMESsage "<string>"
SYSTem:WMESsage?

TEST:ALL?

*TST?

*Parameters vary by DMM model number. See SYSTem:IDENtify for details.

Interface Locking Commands
SYSTem:LOCK:NAME?

SYSTem:LOCK:OWNer?

SYSTem:LOCK:RELease

SYSTem:LOCK:REQuest?

License Management Commands
SYSTem:LICense:CATalog?

SYSTem:LICense:DELete "<option_name>"

SYSTem:LICense:DELete:ALL

SYSTem:LICense:DESCription? "<option_name>"

SYSTem:LICense:ERRor?

SYSTem:LICense:ERRor:COUNt?

SYSTem:LICense:INSTall [{<folder>|<file>}]
SYSTem:LICense:INSTall? "<option_name>"

Interface Configuration Commands
SYSTem:COMMunicate:ENABle {OFF|ON}, {GPIB|HISLip|USB|LAN|SOCKets|TELNet|VXI11|WEB|USBMtp|USBHost}
SYSTem:COMMunicate:ENABle? {GPIB|HISLip|USB|LAN|SOCKets|TELNet|VXI11|WEB|USBMtp|USBHost}

SYSTem:COMMunicate:GPIB:ADDRess <address>
SYSTem:COMMunicate:GPIB:ADDRess?

SYSTem:COMMunicate:LAN:CONTrol?

SYSTem:COMMunicate:LAN:DHCP {OFF|ON}
SYSTem:COMMunicate:LAN:DHCP?

SYSTem:COMMunicate:LAN:DNS[{1|2}] "<address>"
SYSTem:COMMunicate:LAN:DNS[{1|2}]? [{CURRent|STATic}]

SYSTem:COMMunicate:LAN:DOMain?

SYSTem:COMMunicate:LAN:GATeway "<address>"
SYSTem:COMMunicate:LAN:GATeway? [{CURRent|STATic}]

SYSTem:COMMunicate:LAN:HOSTname "<name>"
SYSTem:COMMunicate:LAN:HOSTname? [{CURRent|STATic}]

SYSTem:COMMunicate:LAN:IPADdress "<address>"
SYSTem:COMMunicate:LAN:IPADdress? [{CURRent|STATic}]

SYSTem:COMMunicate:LAN:MAC?

SYSTem:COMMunicate:LAN:SMASk "<mask>"
SYSTem:COMMunicate:LAN:SMASk? [{CURRent|STATic}]

SYSTem:COMMunicate:LAN:TELNet:PROMpt "<string>"
SYSTem:COMMunicate:LAN:TELNet:PROMpt?

SYSTem:COMMunicate:LAN:TELNet:WMESsage "<string>"
SYSTem:COMMunicate:LAN:TELNet:WMESsage?

SYSTem:COMMunicate:LAN:UPDate

SYSTem:COMMunicate:LAN:WINS[{1|2}] "<address>"
SYSTem:COMMunicate:LAN:WINS[{1|2}]? [{CURRent|STATic}]

SYSTem:USB:HOST:ENABle {OFF|ON}
SYSTem:USB:HOST:ENABle?

Status System Commands
*CLS

*ESE <enable_value>
*ESE?

*ESR?

*PSC {0|1}
*PSC?

*SRE <enable_value>
*SRE?

STATus:OPERation:CONDition?

STATus:OPERation:ENABle <enable_value>
STATus:OPERation:ENABle?

STATus:OPERation[:EVENt]?

STATus:PRESet

STATus:QUEStionable:CONDition?

STATus:QUEStionable:ENABle <enable_value>
STATus:QUEStionable:ENABle?

STATus:QUEStionable[:EVENt]?

*STB?
```