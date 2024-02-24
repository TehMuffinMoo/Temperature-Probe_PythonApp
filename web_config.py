#web_config.py
# config tool for pi pico w
# opens an access point on default ip
#allows user to store a number of attributes in a file on the pico
#each attribute on a new line
#attributes may be wifi SSID and passwords
#the following characters must not be used in attributes "£", "+", "&", "%", "^"
#lightweight implementation, no style sheets etc.
#"set_labels()" and "web_page() could be reorganised with *args and accept a flexible number of args
#default ssid PicoConfig, default pw 12345678, default attributes "Attribute 1:" - "Attribute 10:"
#v1.0
#patrick bray 2023
import network, json, os, machine, time
import urllib.parse as urlparse
try:
  import usocket as socket
except:
  import socket

AP_ssid = 'Pico-WiFi'
AP_password = 'picopico'

filename = "config.json"

label_1 = "Attribute 1:"
label_2 = "Attribute 2:"
label_3 = "Attribute 3:"
label_4 = "Attribute 4:"
label_5 = "Attribute 5:"
label_6 = "Attribute 6:"
label_7 = "Attribute 7:"
label_8 = "Attribute 8:"

reloadConfig = False
factoryDefaults = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.SO_REUSEADDR)
s.bind(('', 80))
s.listen(5)

#sets config attribute label names 
def set_label(l1,l2,l3,l4,l5,l6,l7,l8):
    global label_1, label_2, label_3, label_4, label_5, label_6, label_7, label_8
    label_1=l1
    label_2=l2
    label_3=l3
    label_4=l4
    label_5=l5
    label_6=l6
    label_7=l7
    label_8=l8

#sets config filename
def set_filename(aName):
    global filename
    filename = aName

#sets the pw and ssid of teh AP used for configuration 
def set_AP(ss_id, pw):
    global AP_ssid, AP_password
    AP_ssid = ss_id
    AP_password = pw
    
def set_probes_pin(aPin):
    global probesPin
    probesPin = aPin
    
def rescanProbes():
    import onewire, ds18x20
    DS_SENSOR = ds18x20.DS18X20(onewire.OneWire(probesPin))
    ROMS = DS_SENSOR.scan()
    probes = {}
    for ROM in ROMS:
        TEMP = str(round(DS_SENSOR.read_temp(ROM),2))
        ADDR = hex(int.from_bytes(ROM, 'little'))
        probes[ADDR] = {
            "Description": "",
            "MQTT Topic": ""
        }
    return probes

# internal helper function to convert url special characters to txt
def urldecode(str): # courtesy of devnull, removed dependency on urllib
    dic = {"%20":" ","%21":"!","%22":'"',"%23":"#","%24":"$","%26":"&","%27":"'","%28":"(","%29":")","%2A":"*","%2B":"+","%2C":",","%2F":"/","%3A":":","%3B":";","%3D":"=","%3F":"?","%40":"@","%5B":"[","%5D":"]","%7B":"{","%7D":"}"}
    for k,v in dic.items(): str=str.replace(k,v)
    return str

def parse_querystring(query_string):
    variables = dict()

    for item in query_string.split('&'):
        if (item != ''):
            key, value = item.split('=')

            # if value is an int, parse it
            if value.isdigit():
                value = int(value)

            variables[key] = value

    return variables

def checkConfigFile(filename,defaults):
    global label_1, label_2, label_3, label_4, label_5, label_6, label_7, label_8, probes
    if (filename not in os.listdir() or defaults is True):
        print('Config file does not exist, creating..')
        probes = rescanProbes()
        file = open(filename, "w")
        dictionary = {
            label_1: "",
            label_2: "",
            label_3: "",
            label_4: "",
            label_5: "",
            label_6: "",
            label_7: "",
            label_8: "",
            "probes": probes
        }
        json.dump(dictionary, file)
        file.close()
    else:
        print('Config file exists!')


#internal function that returns the html, parses url response and writes config file
def web_page(request):
    global label_1, label_2, label_3, label_4, label_5, label_6, label_7, label_8
    global filename, reloadConfig, factoryDefaults
    
    if (request != ''):
        print(request)
        request = str(request).split()[1]
        
        checkConfigFile(filename,False)
        
        if request.find("favicon.ico") > 0: # Ignore favicon.ico requests
            return ''
        if request.find("getConfig") > 0: # Only process requests which are querying current config
            file = open(filename, "r")
            configJson = json.dumps(file.read())
            file.close()
            return configJson
        elif request.find("rescanProbes") > 0: # Only process requests which are requesting a probe rescan
            probes = rescanProbes()
            return json.dumps(probes)
        elif request.find("reloadConfig") > 0: # Only process requests which are to reload the config
            reloadConfig = True
            return 'reloading'
        elif request.find("submitGeneralSettings") > 0: # Only process requests which are submitting data
            print('Submit General Settings!')
            decoded = urldecode(request)
            parts = urlparse.urlparse(decoded)
            attributes = parse_querystring(urlparse.unquote_plus(parts.query))

            file = open(filename, "r")
            config = json.load(file)
            file.close()
            
            config[label_1] = attributes[label_1]
            config[label_2] = attributes[label_2]
            config[label_3] = attributes[label_3]
            config[label_4] = attributes[label_4]
            config[label_5] = attributes[label_5]
            config[label_6] = attributes[label_6]
            config[label_7] = attributes[label_7]
            config[label_8] = attributes[label_8]
            config['probes'] = config['probes']
            
            file = open(filename, "w")
            json.dump(config, file)
            file.close()
            
            attributesJson = json.dumps(config)
            print(attributesJson)
            return attributesJson
        elif request.find("submitProbeSettings") > 0: # Only process requests which are submitting data
            print('Submit Probe Settings!')
            decoded = urldecode(request)
            parts = urlparse.urlparse(decoded)
            attributes = parse_querystring(urlparse.unquote_plus(parts.query))

            file = open(filename, "r")
            config = json.load(file)
            file.close()
            
            config[label_1] = config[label_1]
            config[label_2] = config[label_2]
            config[label_3] = config[label_3]
            config[label_4] = config[label_4]
            config[label_5] = config[label_5]
            config[label_6] = config[label_6]
            config[label_7] = config[label_7]
            config[label_8] = config[label_8]
            config['probes'] = json.loads(attributes['probes'])
            
            file = open(filename, "w")
            json.dump(config, file)
            file.close()
            
            attributesJson = json.dumps(config['probes'])
            print(attributesJson)
            return attributesJson
        elif request.find("factorydefaults") > 0: # Only process requests to reset to factory defaults
            print('Resetting to factory defaults!')
            os.remove(filename)
            factoryDefaults = True
        else:
            file = open(filename, "r")
            config = json.load(file)
            file.close()
            
            if factoryDefaults is True:
                return 'factoryDefaults'
            else:
                html = f"""
                <style>
                    #form > div > div > input {{
                        width:25%
                    }}
                </style>
                <html>
                <form id="form" action="/submit">
                  <div>
                    <div>
                        <label for="uname"> """+label_1+"""  </label>
                        <input type="text" id="" name="""+'"'+label_1+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_2+"""  </label>
                        <input type="text" id="" name="""+'"'+label_2+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_3+"""  </label>
                        <input type="text" id="" name="""+'"'+label_3+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_4+"""  </label>
                        <input type="text" id="" name="""+'"'+label_4+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_5+"""  </label>
                        <input type="text" id="" name="""+'"'+label_5+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_6+"""  </label>
                        <input type="text" id="" name="""+'"'+label_6+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_7+"""  </label>
                        <input type="text" id="" name="""+'"'+label_7+'"'+"""/>
                    </div>
                    <div>
                        <label for="bname"> """+label_8+"""  </label>
                        <input type="text" id="" name="""+'"'+label_8+'"'+"""/>
                    </div><br>
                    <div>
                        <h3>Temperature Probes</h3>
                        <div id="tempProbeDiv">
                        <p>You can assign friendly names to the connected temperature probes here.</p>
                        </div>
                    </div>
                    <p for="bname">The following characters cannot be used in the settings "£", "+", "&", "%", "^"</p><br>
                </div>
                <hr>
                <div>
                    <label>Clicking Save will save changes.</label>
                    <button id="saveGeneral" type="Submit">Save General Settings</button>
                </div>
                <div>
                    <label>Clicking Save Probes will save changes to temperature probes.</label>
                    <button id="saveProbes" type="Submit">Save Probe Settings</button>
                </div>
                <div>
                    <label>Clicking Reload will reload the device immediately.</label>
                    <button id="reload" type="Submit">Reload</button>
                </div>
                </form>
                <hr>
                <div>
                    <label>A device re-scan will overwrite existing temperature probes.</label>
                    <button onclick="rescanProbes();">Rescan Probes</button>
                </div>
                <br>
                <div>
                  <label>Using this button will reset the device to factory defaults and reload.</label>
                  <button onclick="confirmReset();">Reset to factory defaults</button>
                </div>
                </html>
                <script>
                    function loadProbes(probeData) {
                        var container = document.getElementById('tempProbeDiv');
                        container.innerHTML = "";
                        for (let probes of Object.entries(probeData)) {
                            var div = document.createElement('div');
                            div.className = "probeDevice";
                            div.id = probes[0];
                            var label = document.createElement('label');
                            var descriptionInput = document.createElement('input');
                            var topicInput = document.createElement('input');
                            descriptionInput.type = 'text';
                            descriptionInput.value = probes[1]['Description'];
                            descriptionInput.className = "probeDescription";
                            topicInput.type = 'text';
                            topicInput.value = probes[1]['MQTT Topic'];
                            topicInput.className = "probeTopic";
                            label.innerHTML = probes[0];
                            container.appendChild(div);
                            div.appendChild(label);
                            div.appendChild(descriptionInput);
                            div.appendChild(topicInput);
                        }
                    }
                
                    function getConfig(config = "") {
                        const labels = ["SSID","Password","MQTT Host","MQTT Username","MQTT Password","MQTT Client ID","MQTT Polling Frequency","Display Awake Duration (s)"];
                        if (config == "") {
                            var getConfig = new XMLHttpRequest();
                            getConfig.open( "GET", '/getConfig', false );
                            getConfig.send( null );
                            labelJson = JSON.parse(JSON.parse(getConfig.response));
                        } else {
                            labelJson = JSON.parse(config);
                        }

                        console.log(labelJson);
                        
                        for (let labelElem of labels) {
                            document.getElementsByName(labelElem)[0].value = labelJson[labelElem];
                        }
                        
                        loadProbes(labelJson['probes']);
                        
                    }
                
                    function confirmReset() {
                        if (window.confirm("Are you sure you want to restore to factory defaults?")) {
                           var xmlHttp = new XMLHttpRequest();
                           xmlHttp.open( "GET", '/factorydefaults', false );
                           xmlHttp.send( null );
                           alert('Resetting to factory defaults. The system will be reloaded..');
                        } else {
                           alert('Cancelled');
                        }
                    }
                    
                    function rescanProbes() {
                        if (window.confirm("Are you sure you want to rescan connected probes?")) {
                           var probeData = new XMLHttpRequest();
                           probeData.open( "GET", '/rescanProbes', false );
                           probeData.send( null );
                           loadProbes(JSON.parse(probeData.response));
                        } else {
                           alert('Cancelled');
                        }
                    }
                    
                    getConfig();
                    
                    const form = document.getElementById('form');

                    form.addEventListener('click', (evt) => {
                      evt.preventDefault();
                      const formData = new FormData(form);
                      const params = new URLSearchParams(formData);
                      console.log(params.toString());
                    
                      var reloadConfig = 'false';
                      
                      if (evt.target.id == "reload") {
                          alert('Configuration saved! Reloading now..');
                          var reloadConfig = new XMLHttpRequest();
                          reloadConfig.open( "GET", '/reloadConfig?reloadConfig=true', false );
                          reloadConfig.send( null );
                      }
                      
                      if (evt.target.id == "saveGeneral") {
                          var saveGeneral = new XMLHttpRequest();
                          var submitParams = params.toString();
                          saveGeneral.open( "GET", '/submitGeneralSettings?'+submitParams, false );
                          saveGeneral.send( null );
                          if (saveGeneral.response) {
                              getConfig();
                              alert('Configuration saved!');                          
                          }
                      }
                      
                      if (evt.target.id == "saveProbes") {
                          var probes = document.getElementsByClassName('probeDevice')
                          var probeData = new Object();
                          for (probe of probes) {
                              probeData[probe.id] = {
                                  "Description": probe.querySelector(".probeDescription").value,
                                  "MQTT Topic": probe.querySelector(".probeTopic").value
                              }
                          }
                          var probeJson = "&probes="+JSON.stringify(probeData);
                          var saveProbes = new XMLHttpRequest();
                          saveProbes.open( "GET", '/submitProbeSettings?'+encodeURIComponent(probeJson), false );
                          saveProbes.send( null );
                          if (saveProbes.response) {
                              getConfig();
                              alert('Configuration saved!');                          
                          }
                      }
                  });
                </script>
                        """
                return html

#call this function to open an AP and add/update configuration file to pico memory
def configure_pico():
    global s
    station = network.WLAN(network.AP_IF)
    station.config(essid=AP_ssid)
    station.config(password=AP_password)
    station.active(True)
    station.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0'))# this is the defaut ip
    while station.isconnected() == False:
        pass

    #print('Connection success')
    #print(station.ifconfig())
    while True:
        conn, addr = s.accept()
        #print('Connection from %s' % str(addr))
        print('Receive1')
        r1 = conn.recv(1024)
        print('Receieved')
        request = str(r1)
        print(f'Length: {len(request)}')
        response = web_page(request)
        conn.sendall(response)
        conn.close()
        if response == 'factoryDefaults':
            s.close()
            return 'resetting'
        if reloadConfig == True:
            s.close()
            return 'reloading'