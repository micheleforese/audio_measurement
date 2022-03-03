# Common Commands

## Update the repository

```console
git pull
```

## How to Use it

### Install

```console
python3 -m pip install --editable .
```

### Use it

1. Create a folder for containing the measurements and plot files

   ```console
   cd ~
   mkdir audio
   ```

2. Create the configuration file, starting from the template: `audio_measurements/config/config_template.json`
3. Run the cli script

   ```console
   audio_measurement <config.json file>
   ```

   For Example:

   ```console
   audio_measurement config.json
   ```

   Will be created the `.csv` and the `.png` files inside the current directory

## NI-DRIVER

In the `driver` there are all the packages for installing the ni-daqmx driver.
