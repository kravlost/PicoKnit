import time
from machine import Pin, ADC, SPI
import ujson as json
import sh1107
import framebuf2 as framebuf

def save(rows):
    '''
    save saves the row count to json
    
    :param rows: The row count
    '''
    dict = {'count': rows}

    # Save data to file.
    with open(save_file, 'w') as f:
        json.dump(dict, f)


def load():
    '''
    load loads data from json and extracts the row count
    
    :return: the row count
    '''
    try:
        f = open(save_file, 'r')
    except OSError:
        print('Could not open file')
        return 0
    
    with f:
        dict = json.load(f)

        # Loaded data is a dict
        rows = dict['count']
        print("Rows: "+str(rows))
        return rows
    

def print_int(display,i,x,y):
    '''
    print_int prints a large integer on the OLED display
    
    :param display: OLED object
    :param i: integer value to show
    :param x: x position
    :param y: y position
    '''
    s = f'{i:5}' 						# formatted string

    display.large_text(s,x,y,2)			# show 2 x normal size


def stitch_count(rows):
    '''
    stitch_count calculates the expected number of stitches for the current row
    
    :param rows: row count
    :return: number of stitches
    '''
    return 6+int((9+rows)/10)


def read_vsys():
    '''
    read_vsys reads the voltage on Vsys and returns it
    
    :return: The voltage on Vsys 
    '''
    Pin(25, Pin.OUT, value=1)
    Pin(29, Pin.IN, pull=None)
    reading = ADC(3).read_u16() * 9.9 / 2**16
    Pin(25, Pin.OUT, value=0, pull=Pin.PULL_DOWN)
    Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
    return reading


def low_battery_shutdown(display):
    '''
    low_battery_shutdown goes into a low power mode to preserve battery
    '''
    display.fill(0)
    display.text("  LOW BATTERY   ",1,39,white)
    display.text(" SHUTTING DOWN  ",1,48,white)
    display.show()
    time.sleep_ms(2000)
    display.reset()
    display.poweroff()
    while True:
        machine.lightsleep(10000)


def startup_screen(vsys):
    '''
    startup_screen displays the various messages at startup
    
    :param vsys: the voltage on Vsys
    '''
    display.fill(0)
    display.text("  ROW COUNTER   ",1,1,white)
    display.text(f"  Battery {vsys:.1f}V  ",1,20,white)
    
    if vsys < 3.4 and vsys >= 3.3:
        display.text("  LOW BATTERY   ",1,39,white)
        display.text("  REPLACE NOW   ",1,48,white)
    elif vsys < 3.3:
        low_battery_shutdown(display)
        
    display.show()


def draw_screen(rows, adown, bdown, lightsleep, lowbatt, resetMs):
    '''
    draw_screen displays the row and stitch count on the display
    
    :param rows: row count
    :param adown: button A down flag
    :param bdown: button B down flag
    :param lightsleep: use lower power lightsleep flag
    :param lowbatt: low battery flag
    :param resetMs: milliseconds until row count reset
    '''
    display.fill(0)
    
    if lightsleep == False:
        display.text("*",120,rowsrow,white)
    
    display.text("Click + / Hold -",1,toprow,white)
    
    if adown:
        display.fill_rect(0,rowsrow-1,48,10,white)
        display.text("Rows: ",1,rowsrow,black)
    else:
        display.text("Rows: ",1,rowsrow,white)
    
    print_int(display,rows,int_xpos,rowsrow-5)
    
    display.text("Stitches: "+str(stitch_count(rows)),1,stitchesrow,white)
        
    if lowbatt:
        display.text(f"LOW BATTERY {vsys:.1f}V",1,39,white)
        display.text("  REPLACE NOW   ",1,48,white)
    elif bdown:
        if resetMs <= 0:
            display.fill_rect(0,bottomrow-1,128,10,white)
            display.text("Counter reset   ",1,bottomrow,black)
        else:
            display.fill_rect(0,bottomrow-1,128,10,white)
            display.text("Reset in "+str(1+int(resetMs/1000))+"s    ",1,bottomrow,black)
    else:
        display.text("Hold to reset",1,bottomrow,white)
    
    display.show()

# OLED SPI pins
DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9

# Buttons
keyA = Pin(15,Pin.IN,Pin.PULL_UP) # increment
keyB = Pin(17,Pin.IN,Pin.PULL_UP) # reset

# Setup OLED
spi1 = SPI(1, baudrate=1_000_000, sck=Pin(SCK), mosi=Pin(MOSI), miso=None)

display = sh1107.SH1107_SPI(128, 64, spi1, Pin(DC), Pin(RST), Pin(CS), rotate=0)

display.flip()
display.sleep(False)
display.fill(0x0000) 
display.show()

# Constants
black = 0
white = 1
reset_ms = 5000
save_file = "counts.json"
int_xpos = 32

# positions of text
toprow = 0
rowsrow = 20
stitchesrow = 38
bottomrow=56

# load data
rows = load()

# read battery
vsys = read_vsys()

# If LiPo battery detected on Vsys (max 4.2V) use machine.lightsleep()
# as it saves power over time.sleep(). Disable lightsleep if on
# USB power (Vsys > 4.5) as it interferes with reprogramming.
lightsleep = vsys < 4.5

# startup screen
startup_screen(vsys)

# show a star on the startup screen if using time.sleep()
if lightsleep == False:
    display.text("*",120,rowsrow,white)
    display.show()
    time.sleep(1)
else:
    time.sleep(2)

# draw the main screen
draw_screen(rows, False, False, lightsleep, vsys < 3.4, 0)

# previous elapsed mins at which Vsys was read.
prev_mins = (time.ticks_ms()/1000.0)/60

# initialise low battery flag
lowbatt = False

# loop until battery runs low
while True:
    if lightsleep:
        machine.lightsleep(50)
    else:
        time.sleep_ms(100)
    
    elapsed_mins = (time.ticks_ms()/1000.0)/60

    # read Vsys once a minute
    if elapsed_mins - prev_mins > 1:
        prev_mins = elapsed_mins
        
        vsys = read_vsys()
        
        if vsys < 3.3:
            low_battery_shutdown(display)
        elif vsys < 3.4:
            lowbatt = True
        else:
            lowbatt = False
    
    # handle button A presses
    if keyA.value() == 0:
        start_press = time.ticks_ms()
        
        # increment row count and save it
        rows = rows + 1
        save(rows)
        show_rows = rows
        
        # if key A is held down, decrement rows once per second
        while keyA.value() == 0:
            elapsed_ms = time.ticks_diff(time.ticks_ms(),start_press)
            show_rows = rows - int(elapsed_ms/1000)
            
            draw_screen(show_rows, True, False, lightsleep, lowbatt, 0)

        # update rows with shown row count
        if rows != show_rows:
            rows = show_rows
            save(rows)    

        draw_screen(rows, False, False, lightsleep, lowbatt, 0)

    # handle button B presses
    if keyB.value() == 0:
        start_press = time.ticks_ms()
        
        while keyB.value() == 0:
            tdiff = time.ticks_diff(time.ticks_ms(),start_press)
            
            # if B is pressed longer than reset_ms, the row count is reset
            if tdiff > reset_ms:
                rows = 0
                save(rows)

            draw_screen(rows, False, True, lightsleep, lowbatt, reset_ms - tdiff)

        draw_screen(rows, False, False, lightsleep, lowbatt, 0)           

# end of main loop
