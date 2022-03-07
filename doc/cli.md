# CLI audio_measurements

## `sweep` Command

For Help on the command

```console
audio_measurements sweep --help
```

You can use a config file, copying from the template folder, `audio_measurements/config/config_template.json5`
Using a config file:

```console
audio_measurements sweep <config.json5 file>
```

Will be created the `.csv` and the `.png` files inside the current directory

## `plot` Command

```console
audio_measurements plot <measurements.csv file>
```

Arguments:

1. `--format`, default `"png"`:

   Can specify multiple formats

   ```console
    audio_measurements plot <measurements.csv file> --format png --format pdf
   ```

2. `--y_lim_min`, default `-10`:

   ```console
    audio_measurements plot <measurements.csv file> --y_lim_min "-1"
   ```

3. `--y_lim_max`, default `10`:

   ```console
    audio_measurements plot <measurements.csv file> --y_lim_max "1"
   ```

4. `--debug`, default `False`:

   Is a flag

   ```console
    audio_measurements plot <measurements.csv file> --debug
   ```
