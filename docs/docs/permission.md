# Permission

1. Create group `usbtmc`

   ```console
   sudo groupadd usbtmc
   ```

2. Add User to the group

   ```console
   sudo usermod -a -G usbtmc <user_name>
   ```

3. Check the groups:

   ```console
   groups michele
   ```

4. Create a file `/etc/udev/rules.d/50-myusbtmc.rules`:

   ```console
   sudo nano /etc/udev/rules.d/50-myusbtmc.rules
   ```

5. Write this:

   ```console
   # USBTMC Instruments

   # Rigol DG812
   UBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="<idVendor>", ATTRS{idProduct}=="<idProduct>", GROUP="usbtmc", MODE="0660"

   # Kernel devices
   KERNEL=="usbtmc/*",       MODE="0660", GROUP="usbtmc"
   KERNEL=="usbtmc[0-9]*",   MODE="0660", GROUP="usbtmc"
   KERNEL=="ttyUSB[0-9]*",   MODE="0660", GROUP="usbtmc"
   ```

   substitute `<idVendor>` and `<idProduct>` with the id of the device

6. Reload the device

   ```console
   sudo udevadm control --reload
   ```
