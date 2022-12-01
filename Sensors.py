# For System
from nntplib import GroupInfo
import pyrebase
import time
from time import sleep

# For Humidity and Temperature Sensor:
import board 
import adafruit_dht
import psutil

# For LCD
import drivers

# For Light Sensor 
import busio
import adafruit_tsl2591

# For Button
import RPi.GPIO as GPIO

# Config
config = {
    "apiKey": "AIzaSyCN1hEaiZ9TbFmO8A_O4iDQh37utLUoZYI",
    "authDomain": "sprinkle-bot-ece-196.firebaseapp.com",
    "databaseURL": "https://sprinkle-bot-ece-196-default-rtdb.firebaseio.com",
    "storageBucket": "sprinkle-bot-ece-196.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

# GPIO Pin Declarations
moisture_sensor = 21 
system_power = 13 
buzzer = 23
relay_pin = 5

# Make GPIO Pins available
GPIO.setmode(GPIO.BCM)

# Set Pin Outputs
GPIO.setup(moisture_sensor, GPIO.IN)
GPIO.setup(system_power, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.setup(buzzer, GPIO.OUT)

temp_hum_sensor = adafruit_dht.DHT11(board.D4)  # Initialize Temp/Hum Sensor
display = drivers.Lcd()                         # Initialize LCD
i2c = busio.I2C(board.SCL, board.SDA)           # Set up i2C 
light_sensor = adafruit_tsl2591.TSL2591(i2c)    # Initialize Light Sensor

water_system = True
pump_status = False
returned_hum = 1
pump_forced_off = False
start_time = 0.0
end_time = 0.0
start_switch = 1

def control_buzzer(): 
    '''
    :Description: this function controls when the buzzer makes noise. 
    '''
    GPIO.output(buzzer, GPIO.HIGH)
    sleep(1)
    GPIO.output(buzzer, GPIO.LOW)
    sleep(1)
    
    
def light_sensor_function():
    '''
    :Description: this function controls the light sensor. 
    '''
    lux_amount = light_sensor.lux
    full_spectrum = light_sensor.full_spectrum
    print("Total Light:{0} lux ".format(lux_amount))
    print("Full Spectrum (IR + Visible) Light: {0}".format(full_spectrum))
    return full_spectrum
    
def temperature_humidity_sensor():
    '''
    :Description: this function controls the temp/hum sensor. 
    '''
    try:
        temp = temp_hum_sensor.temperature
        hum = temp_hum_sensor.humidity
        global returned_hum 
        returned_hum = temp_hum_sensor.humidity
        print("Temperature:{0} C ".format(temp))
        print("Humidity:{0}".format(hum))
        return temp
        
    except RuntimeError as error:
        print(error.args[0])
    
     
def moisture_check():
    '''
    :Description: this function uses the status of the soil moisture 
                  sensor and then changes the status of the pumps.
                  NOTE: a moisture sensor 
                  value of 1 means that there is no moisture detected, 
                  and a value of 0 means moisture is detected 
    '''
    moist_val = GPIO.input(moisture_sensor)
    print("Moisture Sensor Value: {0}".format(moist_val))
    global end_time
    global start_switch
    if GPIO.input(moisture_sensor): # when no moisture is detected
        
        if pump_forced_off != True:
            print("No moisture detected. Pump turned on")
            display.lcd_display_string("Pump turned on", 2)
            GPIO.output(relay_pin, GPIO.HIGH) # turn on pump
            if start_switch == 1:
                global start_time
                start_time = time.time()
                start_switch = 0
            end_time = time.time()
        else:
            GPIO.output(relay_pin, GPIO.LOW) # turn off pump
            print("Pump is forced off right now due to button press")
            end_time = 0
            start_switch = 1
        
    else: # when moisture is detected
        print("Moisture detected. Pump turned off.")
        pump_status = False  # turn pumps off
        display.lcd_display_string("Pumps turned off", 2)
        GPIO.output(relay_pin, GPIO.LOW) # turn off pump
        end_time = 0
        start_switch = 1
    
    return moist_val
        

def use_sensors():
        
    returned_moisture = moisture_check()
    returned_light = light_sensor_function()
    returned_temp = temperature_humidity_sensor()
    
    
    # Sending Info to Firebase
    data = {
        "Temperature" : returned_temp,
        "Humidity" : returned_hum,
        "Light" : returned_light,
        "Moisture" : returned_moisture
    }
    db.child("Status").push(data)
    db.update(data)
    print("Data Submitted to Firebase")
    
    display.lcd_display_string("T:{0} H:{1} L:{2}".format(returned_temp, returned_hum, returned_light), 1) 
    
    time.sleep(5.0)
        
        
# Boolean to determine whether sensors are collecting data. When system starts, 
# the sensors will automatically begin collectin data
collection_counter = 0

while water_system:
    
    use_sensors()
    
    total_time = end_time - start_time
    if total_time > 150:
        control_buzzer()
    
    # When the User presses button 
    if GPIO.input(system_power) == GPIO.HIGH:
        sleep(3) # Ensures system only registers one click of the button 
        if collection_counter % 2 == 0: # Turn the pumps off (force)
            collection_counter = collection_counter + 1 
            display.lcd_display_string("SprinkleBot", 1)  
            display.lcd_display_string("Pump Stopped (F)", 2)
            print("Pumps forced off.")
            pump_forced_off = True
            GPIO.output(relay_pin, GPIO.LOW) # turn off pump
        else: # Turn pumps on (force)
            pump_forced_off = False
            collection_counter = collection_counter + 1 
            
        
display.lcd_clear()
GPIO.cleanup()

