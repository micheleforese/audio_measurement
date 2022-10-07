# Configuration XML Scheme

## Rigol

```xml
<rigol>
  <amplitude_peak_to_peak></amplitude_peak_to_peak>
</rigol>
```

Parameters:

- `amplitude_peak_to_peak`:

  Amplitude in `V`.

  > type: float

  Example:

  ```xml
  <amplitude_peak_to_peak>10</amplitude_peak_to_peak>
  <amplitude_peak_to_peak>2.54645</amplitude_peak_to_peak>
  ```

## NiDaq

```xml
<nidaq>
  <Fs_max></Fs_max>
  <voltage_min></voltage_min>
  <voltage_max></voltage_max>
  <input_channel></input_channel>
</nidaq>
```

Parameters:

- `Fs_max`:

  Max Sampling Frequency in `Hz`.

  > type: float

  Example:

  ```xml
  <Fs_max>10</Fs_max>
  <Fs_max>2.54645</Fs_max>
  ```

- `voltage_min`:

  Minimum Input Voltage of the Device in `V`.

  > type: float

  Example:

  ```xml
  <voltage_min>-10</voltage_min>
  <voltage_min>-2.54645</voltage_min>
  ```

- `voltage_max`:

  Maximum Input Voltage of the Device in `V`.

  > type: float

  Example:

  ```xml
  <voltage_max>10</voltage_max>
  <voltage_max>2.54645</voltage_max>
  ```

- `input_channel`:

  Input Channel of the Device in `string`.

  > type: string

  Example:

  ```xml
  <input_channel>cDAQ9189-1CDBE0AMod5/ai0</input_channel>
  <input_channel>cDAQ9189-1CDBE0AMod1/ai1</input_channel>
  ```

## Sampling

```xml
<sampling>
  <Fs_multiplier></Fs_multiplier>
  <points_per_decade></points_per_decade>
  <number_of_samples></number_of_samples>
  <number_of_samples_max></number_of_samples_max>
  <frequency_min></frequency_min>
  <frequency_max></frequency_max>
  <interpolation_rate></interpolation_rate>
  <delay_measurements></delay_measurements>
</sampling>
```

- `Fs_multiplier`:

  Sampling Frequency Multiplier of the device in `Hz`.
  Given an Input Frequency, for example `1000 Hz` and a multiplier
  of `50`, the Device will try to sample the signal with a Frequency
  of: `50000 Hz`, or it will trim the value to the `Fs_max` value

  > type: float

  Example:

  ```xml
  <Fs_multiplier>40</Fs_multiplier>
  <Fs_multiplier>1</Fs_multiplier>
  ```

- `points_per_decade`:

  Sampling Points per decade.

  > type: int

  Example:

  ```xml
  <points_per_decade>10</points_per_decade>
  <points_per_decade>244</points_per_decade>
  ```

- `number_of_samples`:

  Number of Samples per Measurement.

  > type: int

  Example:

  ```xml
  <number_of_samples>100</number_of_samples>
  <number_of_samples>370</number_of_samples>
  ```

- `number_of_samples_max`:

  Max Number of Samples per Measurement.

  > type: int

  Example:

  ```xml
  <number_of_samples_max>1000</number_of_samples_max>
  <number_of_samples_max>1200</number_of_samples_max>
  ```

- `frequency_min`:

  Minimum Frequency for Sweep Range. In `Hz`.

  > type: float

  Example:

  ```xml
  <frequency_min>10</frequency_min>
  <frequency_min>4000</frequency_min>
  ```

- `frequency_max`:

  Maximum Frequency for Sweep Range. In `Hz`.

  > type: float

  Example:

  ```xml
  <frequency_max>100000</frequency_max>
  <frequency_max>124366</frequency_max>
  ```

- `interpolation_rate`:

  Interpolation rate for RMS calculations.

  > type: int

  Example:

  ```xml
  <interpolation_rate>10</interpolation_rate>
  <interpolation_rate>34</interpolation_rate>
  ```

- `delay_measurements`:

  Delay time in `s` between each measurement.

  > type: float

  Example:

  ```xml
  <interpolation_rate>1</interpolation_rate>
  <interpolation_rate>3.5</interpolation_rate>
  ```

## Plot

```xml
<plot>
  <y_offset></y_offset>
  <x_limit>
    <min></min>
    <max></max>
  </x_limit>
  <y_limit>
    <min></min>
    <max></max>
  </y_limit>
  <interpolation_rate></interpolation_rate>
  <dpi></dpi>
  <color></color>
  <legend></legend>
</plot>
```

- `y_offset`:

  Y Axes Offset for graph.

  > type: float

  Example:

  ```xml
  <y_offset>1</y_offset>
  <y_offset>3.5</y_offset>
  ```

- `x_limit`:

  X Axes Limits for graph.

  > type: float

  Example:

  ```xml
  <x_limit>
    <min>-10</min>
    <max>2</max>
  </x_limit>
  ```

- `y_limit`:

  X Axes Limits for graph.

  > type: float

  Example:

  ```xml
  <y_limit>
    <min>-2</min>
    <max>30</max>
  </y_limit>
  ```

- `interpolation_rate`:

  Interpolation multiplier for graphs.

  > type: float

  Example:

  ```xml
  <interpolation_rate>1</interpolation_rate>
  <interpolation_rate>30</interpolation_rate>
  ```

- `dpi`:

  DPI value for tht `.png` plot.

  > type: int

  Example:

  ```xml
  <dpi>300</dpi>
  <dpi>600</dpi>
  ```

- `color`:

  Color value for the line graph.

  > type: string

  Example:

  ```xml
  <color>#abcdef</color>
  <color>#ff2233</color>
  ```

- `legend`:

  Legend string for the line graph.

  > type: string

  Example:

  ```xml
  <legend>Line with gain: 2.3 dB</legend>
  <legend>Simple Description</legend>
  ```

## Full Scheme

```xml
<config>
  <rigol>
    <amplitude_peak_to_peak></amplitude_peak_to_peak>
  </rigol>
  <nidaq>
    <Fs_max></Fs_max>
    <voltage_min></voltage_min>
    <voltage_max></voltage_max>
    <input_channel></input_channel>
  </nidaq>
  <sampling>
    <Fs_multiplier></Fs_multiplier>
    <points_per_decade></points_per_decade>
    <number_of_samples></number_of_samples>
    <number_of_samples_max></number_of_samples_max>
    <frequency_min></frequency_min>
    <frequency_max></frequency_max>
    <interpolation_rate></interpolation_rate>
    <delay_measurements></delay_measurements>
  </sampling>
  <plot>
    <y_offset></y_offset>
    <x_limit>
      <min></min>
      <max></max>
    </x_limit>
    <y_limit>
      <min></min>
      <max></max>
    </y_limit>
    <interpolation_rate></interpolation_rate>
    <dpi></dpi>
    <color></color>
    <legend></legend>
  </plot>
</config>
```
