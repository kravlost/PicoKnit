# PicoKnit

PicoKnit is a row and stitch counter written in MicroPython for the Raspberry Pi Pico with a Waveshare 1.3 OLED display which comes with two buttons. It should be useful to knitters and crocheters alike. 

![Image of display](Screen.jpg)
The two buttons are used to increment, decrement and reset the row count. The row count is stored in a JSON file and can be edited with Thonny or similar. 

The stich count is calculated from the current row, and can be changed to suit the pattern.

The Pico can be powered either from USB or a battery on Vsys. PicoKnit is written to detect if there is a LiPo battery on Vsys and to use a lower-power sleep mode if so. It can also detect a low battery voltage and shut down.
