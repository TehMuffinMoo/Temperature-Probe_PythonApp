## Import Libraries
import network, machine, onewire, ds18x20, time, json, os
from machine import I2C
from machine import Pin
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from math import sin
from umqtt.simple import MQTTClient

I2C_ADDR     = 0x27      # LCD Display address
I2C_NUM_ROWS = 4         # Number of rows on the LCD Display
I2C_NUM_COLS = 20        # Number of columns on the LCD Display
DS_PIN = machine.Pin(22) # Temperature Probes Data Pin

pico_ssid = 'Pico-WiFi'
pico_pw = 'picopico'
pico_config = 'config.json'

DS_SENSOR = ds18x20.DS18X20(onewire.OneWire(DS_PIN))
ROMS = DS_SENSOR.scan()

i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

def launchWebConfig():
    time.sleep(3)
    lcd.clear()
    lcd.putstr(f'SSID: {pico_ssid}\n')
    lcd.putstr(f'PASS: {pico_pw}\n')
    lcd.putstr('Browse to:\nhttp://192.168.4.1\n')
    import web_config
    ## Set config labels
    web_config.set_label("SSID","Password","MQTT Host","MQTT Username","MQTT Password","MQTT Client ID","MQTT Polling Frequency","Display Awake Duration (s)")
    ## Set probes pin
    web_config.set_probes_pin(DS_PIN)
    web_config.set_AP(pico_ssid, pico_pw)
    web_config.set_filename(pico_config)
    result = web_config.configure_pico()
    if result == 'reloading':
        lcd.clear()
        lcd.putstr('\n   Configuration   \n    Reloading..    \n')
        time.sleep(3)
        machine.reset()
    elif result == 'resetting':
        lcd.clear()
        lcd.putstr('\n    Restoring to    \n  Factory Defaults  \n')
        time.sleep(3)
        machine.reset()

if (pico_config not in os.listdir()):
    lcd.clear()
    lcd.putstr('\n    Initilising    \n First time setup..\n')
    launchWebConfig()

file = open(pico_config, "r")
config = json.load(file)

lcd.clear()
lcd.putstr('Starting up...')

interrupt_flag=0
debounce_time=0
press_start = 0
press_end = 0
last_press = time.ticks_ms()
last_depression = time.ticks_ms()
display_sleep_seconds = config['Display Awake Duration (s)']
display_wake_duration = time.time()
mqtt_delay_seconds = config['MQTT Polling Frequency']
ipconfig = ''
mqtt_timer = 0
mqtt_published = True
button_pin = 21

pin = Pin(button_pin,Pin.IN,Pin.PULL_UP)

def callback(pin):
    pin = Pin(button_pin,Pin.IN,Pin.PULL_UP)
    global interrupt_flag, debounce_time, press_start, press_end, ipconfig, last_depression, last_press, display_wake_duration
    if (time.ticks_ms()-debounce_time) > 500:
        if (pin.value() == 0):
            if (time.ticks_ms()-last_press) > 1000:
                #print('Button Pressed!')
                #print('Time Now:')
                #print(time.ticks_ms())
                #print('Last Press: ')
                #print(last_press)
                press_start = time.time()
                last_press=time.ticks_ms()
                display_wake_duration = time.time()
                lcd.display_on()
                lcd.backlight_on()
                print('Waking up display..')
        elif (pin.value() == 1):
            if (time.ticks_ms()-last_depression > 4000 and time.ticks_ms()-last_press < 10000 and time.ticks_ms()-last_press > 4000):
                #print('Button Released!')
                #print('Time Now:')
                #print(time.ticks_ms())
                #print('Last Depression: ')
                #print(last_depression)
                if ((time.time()-press_start) > 5 and (time.time()-press_start) < 10):
                    print('Button pressed for > 5 seconds! Showing IP Config')
                    display_wake_duration = time.time()
                    lcd.display_on()
                    lcd.backlight_on()
                    lcd.clear()
                    lcd.putstr('IP  : '+ipconfig[0]+'\n')
                    lcd.putstr('GW  : '+ipconfig[2]+'\n')
                    lcd.putstr('DNS : '+ipconfig[3]+'\n')
                    lcd.putstr('Mask: '+ipconfig[1]+'\n')
                    time.sleep(10)
                    lcd.clear()
            elif (time.ticks_ms()-last_depression > 8000 and time.ticks_ms()-last_press < 20000 and time.ticks_ms()-last_press > 8000):
                #print('Button Released!')
                #print('Time Now:')
                #print(time.ticks_ms())
                #print('Last Depression: ')
                #print(last_depression)
                if ((time.time()-press_start) > 10):
                    print('Button pressed for > 10 seconds! Entering setup mode..')
                    display_wake_duration = time.time()
                    lcd.display_on()
                    lcd.backlight_on()
                    lcd.clear()
                    lcd.putstr('\n')
                    lcd.putstr('      Entering      \n')
                    lcd.putstr('     Setup Mode..    \n')
                    time.sleep(5)
                    launchWebConfig()
            last_depression=time.ticks_ms()

    debounce_time=time.ticks_ms()

pin.irq(trigger=Pin.IRQ_FALLING, handler=callback)
pin.irq(trigger=Pin.IRQ_RISING, handler=callback)

def connectWifi():
    global ipconfig
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config['SSID'], config['Password'])
    
    connectCount = 0
    while wlan.isconnected() == False:
        if (connectCount < 15):
            lcd.clear()
            lcd.putstr('Waiting for WiFi...\n')
            print('Waiting for WiFi Connection...')
            time.sleep(1)
            connectCount += 1
        else:
            lcd.clear()
            print('Failed to connect to WiFi\n')
            lcd.putstr('WiFi did not connect\n\n')
            lcd.putstr('Loading Setup Mode..\n')
            launchWebConfig()
    
    if (wlan.ifconfig()[3] == '0.0.0.0'):
        lcd.clear()
        lcd.putstr('\nFailed to get DNS\nServer from DHCP')
        time.sleep(3)
        machine.reset()
        
    lcd.clear()
    lcd.putstr('WiFi Connected!\n')
    time.sleep(2)
    lcd.clear()
    lcd.putstr('IP  : '+wlan.ifconfig()[0]+'\n')
    lcd.putstr('GW  : '+wlan.ifconfig()[2]+'\n')
    lcd.putstr('DNS : '+wlan.ifconfig()[3]+'\n')
    lcd.putstr('Mask: '+wlan.ifconfig()[1]+'\n')
    ipconfig = wlan.ifconfig()
    print(ipconfig)

def publishMQTT(topic,data):
    global mqtt_delay_seconds, mqtt_timer, mqtt_published
    if ((time.time()-mqtt_timer) > mqtt_delay_seconds):
        #print(f'Published {data} to {topic}')
        try:
            mqtt_client.publish(topic, str(data))
            mqtt_published = True
        except Exception as e:
            print(f'Failed to publish {data} to {topic}: {e}')

try:
    connectWifi()
    time.sleep(5)
except KeyboardInterrupt:
    machine.reset()

if "" not in (config['MQTT Client ID'], config['MQTT Host'], config['MQTT Username'], config['MQTT Password']):
    # Initialize our MQTTClient and connect to the MQTT server
    mqtt_client = MQTTClient(
            client_id=config['MQTT Client ID'],
            server=config['MQTT Host'],
            user=config['MQTT Username'],
            password=config['MQTT Password'])
    try:
        mqtt_client.connect()
    except Exception as e:
        print(f'Failed to connect to MQTT: {e}')
        lcd.clear()
        lcd.putstr('MQTT connect failed\n\n')
        lcd.putstr('Loading Setup Mode..\n')
        launchWebConfig()
else:
    lcd.clear()
    print('MQTT Notification Details Missing\n')
    lcd.putstr('MQTT Config Missing\n\n')
    lcd.putstr('Loading Setup Mode..\n')
    
    launchWebConfig()

while True:
  if (mqtt_published == True):
    mqtt_timer = time.time()
    mqtt_published = False

  time.sleep_ms(50)
  if (len(ROMS) >= 1):
    DS_SENSOR.convert_temp()
 
  for ROM in ROMS:
 
    TEMP = str(round(DS_SENSOR.read_temp(ROM),2))
    ADDR = hex(int.from_bytes(ROM, 'little'))
    if (ADDR in config['probes']):
        lcd.putstr(config['probes'][ADDR]['Description']+": "+str(TEMP)+"\n")
        publishMQTT(config['probes'][ADDR]['MQTT Topic'], str(TEMP))
    else:
        lcd.putstr(ADDR+": "+str(TEMP)+"\n")
        print("Unknown Probe: "+ADDR+"\n"+TEMP+"\n")

  if (len(ROMS) < 4):
      FILL = 4 - len(ROMS)
      for i in range(FILL):
          lcd.putstr("No Probe Conected\n")
          
  if ((time.time()-display_wake_duration) > display_sleep_seconds):
      lcd.display_off()
      lcd.backlight_off()
      

  time.sleep(1)
  
