# Procedure

## CLI use

```shell
audio_measurements procedure <procedure_file>
```

ex:

```shell
audio_measurements procedure proc.xml
```

## XML

This is the base XML structure

```xml
<proc name="la_125_8">
  <steps>

  </steps>
</proc>
```

Every step must be placed inside the `steps` tag.

There are different types of steps:

- `ProcedureSerialNumber`

  This Step creates the home directory of the measurements.
  Every step will refer to this namespace for file paths.

  ```xml
  <serial_number>
    <text>ID Device:</text>
  </serial_number>
  ```

- `ProcedureText`

  This step will display the text inside the xml tag and then ask for confirmation.

  ```xml
  <text>
    Collegare L'Output al DUT.
    GAIN 1.
  </text>
  ```

- `ProcedureSetLevel`

  This step will start the `set_level` function to retrieve the base offset of the devices.

  - `file_set_level`

    Name of the set_level File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    ```

  - `file_set_level_plot`

    Name of the Plot

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    ```

  - `config`

    Inside the `config` tag there is the configuration data for the devices.

    Those are the required ones for this procedure:

    ```xml
    <config>
      <nidaq>
        <Fs_max></Fs_max>
        <voltage_min></voltage_min>
        <voltage_max></voltage_max>
        <input_channel></input_channel>
      </nidaq>
      <sampling>
        <Fs_multiplier></Fs_multiplier>
        <number_of_samples></number_of_samples>
      </sampling>
    </config>
    ```

  ```xml
  <set_level>
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    <file_set_level_plot>
      <key>set_level_1_plot</key>
      <name>set_level_1_plot.set_level.png</name>
    </file_set_level_plot>
    <config>
      <nidaq>
        <Fs_max>1000000</Fs_max>
        <voltage_min>-10</voltage_min>
        <voltage_max>10</voltage_max>
        <input_channel>cDAQ9189-1CDBE0AMod5/ai0</input_channel>
      </nidaq>
      <sampling>
        <Fs_multiplier>50</Fs_multiplier>
        <number_of_samples>900</number_of_samples>
      </sampling>
    </config>
  </set_level>
  ```

- `ProcedurePrint`

  This tag will print the listed variables refering to the `key`s provided in other steps.

  ```xml
  <print>
    <var></var>
  </print>
  ```

- `ProcedureInsertionGain`

  Calculates the Insertion gain value.

  - `file_calibration`

    Name of the Master Calibration File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_calibration>
      <key>master</key>
      <name>master.calibration.dat</name>
    </file_calibration>
    ```

  - `file_set_level`

    Name of the Set level File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    ```

  - `file_gain`

    Name of the Gain File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_gain>
      <key>gain_1</key>
      <name>gain_1.dat</name>
    </file_gain>
    ```

  Example:

  ```xml
  <insertion_gain>
    <file_calibration>
      <key>master</key>
      <name>master.calibration.dat</name>
    </file_calibration>
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    <file_gain>
      <key>gain_1</key>
      <name>gain_1.dat</name>
    </file_gain>
  </insertion_gain>
  ```

- `ProcedureSweep`

  - `name_folder`

    Name of the Sweep Folder

    ```xml
    <name_folder>sweep PRE G1</name_folder>
    ```

  - `file_set_level`

    Name of the Set level File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    ```

  - `file_offset`

    Name of the Offset File

    - `key`: key value that is stored inside the running program for up-to-date reference of the data.
    - `name`: name of the file that holds the data.

    > If the key is not found, the program will find the data in the file
    > structure using the `name` that is provided.

    ```xml
    <file_offset>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_offset>
    ```

  - `config`

    Inside the `config` tag there is the configuration data for the devices.

    Those are the required ones for this procedure:

    ```xml
    <config>
      <nidaq>
        <Fs_max></Fs_max>
        <voltage_min></voltage_min>
        <voltage_max></voltage_max>
        <input_channel></input_channel>
      </nidaq>
      <sampling>
        <Fs_multiplier></Fs_multiplier>
        <points_per_decade></points_per_decade>
        <frequency_min></frequency_min>
        <frequency_max></frequency_max>
        <number_of_samples></number_of_samples>
      </sampling>
      <plot>
        <interpolation_rate></interpolation_rate>
        <color></color>
        <legend></legend>
      </plot>
    </config>
    ```

    Example:

    ```xml
    <config>
      <nidaq>
        <Fs_max>1000000</Fs_max>
        <voltage_min>-10</voltage_min>
        <voltage_max>10</voltage_max>
        <input_channel>cDAQ9189-1CDBE0AMod5/ai0</input_channel>
      </nidaq>
      <sampling>
        <Fs_multiplier>50</Fs_multiplier>
        <points_per_decade>10</points_per_decade>
        <frequency_min>10</frequency_min>
        <frequency_max>300000</frequency_max>
        <number_of_samples>900</number_of_samples>
      </sampling>
      <plot>
        <interpolation_rate>10</interpolation_rate>
        <color>#ff0000</color>
        <legend>PRE G1</legend>
      </plot>
    </config>
    ```

    Example:

  ```xml
  <sweep>
    <name_folder>sweep PRE G1</name_folder>
    <file_set_level>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_set_level>
    <file_offset>
      <key>set_level_1</key>
      <name>set_level_1.set_level.dat</name>
    </file_offset>
    <file_insertion_gain>
      <key>gain_1</key>
      <name>gain_1.dat</name>
    </file_insertion_gain>
    <config>
      <nidaq>
        <Fs_max>1000000</Fs_max>
        <voltage_min>-10</voltage_min>
        <voltage_max>10</voltage_max>
        <input_channel>cDAQ9189-1CDBE0AMod5/ai0</input_channel>
      </nidaq>
      <sampling>
        <Fs_multiplier>50</Fs_multiplier>
        <points_per_decade>10</points_per_decade>
        <frequency_min>10</frequency_min>
        <frequency_max>300000</frequency_max>
        <number_of_samples>900</number_of_samples>
      </sampling>
      <plot>
        <interpolation_rate>10</interpolation_rate>
        <color>#ff0000</color>
        <legend>PRE G1</legend>
      </plot>
    </config>
  </sweep>
  ```

- `ProcedureMultiPlot`

  - `file_plot`: Name of the `.png` output file
  - `folder_sweep`: List of the sweep folders

  Example:

  ```xml
  <multiplot name="multiplot">
    <file_plot>multiplot.png</file_plot>
    <folder_sweep>
      <var>sweep PRE G1</var>
      <var>sweep PRE G5</var>
      <var>sweep PRE G9</var>
    </folder_sweep>
  </multiplot>
  ```
