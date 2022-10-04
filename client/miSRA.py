from genericpath import isfile
import requests
import sys
import argparse
import os.path
import json
import time

#profiler_url = "http://127.0.0.1:8080/profiler/"
profiler_url = "https://arn.ugr.es/miSRA/profiler/"
check_url = "https://arn.ugr.es/miSRA/profiler/status"
dbquery_url = "http://127.0.0.1:8000/mirdb/"

# client = requests.session()

# Retrieve the CSRF token first
# response = client.post(test_url)  # sets cookie
# print(response.text)

# if 'csrftoken' in client.cookies:
#     # Django 1.6 and up
#     csrftoken = client.cookies['csrftoken']
# else:
#     # older versions
#     csrftoken = client.cookies['csrf']

# login_data = dict(username="", password="",csrfmiddlewaretoken=csrftoken, next='/')
# r = client.post(test_url, login_data,  headers=dict(Referer=test_url))
# client.post()

def prepareSummary(data):
    matrixPath = data['localOut']
    # if(data)

# take the json from api
def checkProcess(backJson,data):
    print (backJson)
    if 'launched' in backJson:
        print("Your job has been launched. Waiting for results ...")
        check = False
        time.sleep(30)
        
        while check == False:

            r = requests.post(check_url, data=backJson,stream=True)
            check = postProcess(r,data['localOut']) 
            print ("Process is still running ...")
            time.sleep(30)
        
        
        return True
    else:
        print("Unexpected error. Probably the web-server is down. Please contact: ")
        sys.exit()
        
def postProcess(r,localOut):
    """
    Takes the response object and the path to the local output
    return
    """
    print (r.status_code)
    if r.status_code == 200:
        handle = open(localOut+"/back.zip", "wb")
        for chunk in r.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
        handle.close()
        import zipfile
        with zipfile.ZipFile(localOut+"/back.zip", 'r') as zip_ref:
            zip_ref.extractall(localOut)
        return True
        # file = r.raw.read()
        # with open(localOut+"/zipped", 'wb') as f:
        #     f.write(file)
    else:
#        print(r.text())
        return False

#send query to server
def post_profiler(data,files):
    
    postfiles={}
    for k in files:
        postfiles[k] = open(files[k],"rb")
        
    
    r = requests.post(profiler_url, files=postfiles, data=data,stream=True)
#    backData = json.loads(r)
    return r.json()

def parseArgs():
    parser = argparse.ArgumentParser(description='python miSRAclient: query > 40,000 SRA samples i) receive precalculated miRNA expression values, ii) profiling of user provided annotations')
    parser.add_argument('-config',type=str,help='the path to the config file in json format. If not given, than the data will be asked on the command line. ')
    parser.add_argument('-mode', type=str,
                        help='possible values: i) profile, ii) query, iii) dbstat')
   
    args = parser.parse_args()
    if(len(sys.argv)  <= 1):
        parser.print_help()
    return args

def getdbSummary():
    return {}
def getDBArgs():
    return {}
def getProfilerArgs():
    return {}

def getArguments():
    """ 
This function will ask the user for the parameters.
It returns i) dictionary with the parameters, ii) the analysis type (i.e. profiler, DB query etc)
    """
    while True:
        mode = input("Specify the analysis type: i) profiler, ii) db, iii) dbsummary")
        if(mode == "profiler"):
            return getProfilerArgs()
        elif(mode=="db"):
            return getDBArgs()
        elif(mode=="dbsummary"):
            return getdbSummary()
        else:
            print("Input was not recognized")

def getJson(file):
   #check if json is valid
    try:
        f = open(file,"r")
        data = json.load(f)
        return data
    except ValueError as e:
        print(e)
        print("Errors in json format!")
        sys.exit(0)


def checkScope(data):
    """
    Checks if either experiments= or studies= was given in the config file
    """
    backdata={}
    if(not (data.get("experiments") or data.get("studies"))):
        print("You need to specify either experiments=SRX/DRX/ERX (comma separated) or studies=SRP/DRP/ERP (comma separated)")
        sys.exit(0)
    if(data.get("experiments")):
        backdata["experiments"]=data["experiments"]
    if(data.get("studies")):
        backdata["studies"]=data["studies"]
    return backdata
    

def parseConfig(file):
    """
    Parse and error check the config file in json format
    Return: python dictionary with paramters
    """
    data = getJson(file)
    backdata=checkScope(data)
    type =""
    if(data.get("localOut")):

        backdata['localOut'] = data['localOut']
        print("Local outfile was specified")
        try:
            os.mkdir(data['localOut'])
        except OSError:
            print ("Make directory %s failed" % data['localOut'])
        else:
            print ("Created the directory %s" % data['localOut'])
    else:
        backdata['localOut']="pySRA_results"
        print("localOut= was not specified in config file. Will create default output pySRA_results")
        try:
            os.mkdir(backdata['localOut'])
        except OSError:
            print ("Make directory %s failed" % backdata['localOut'])
        else:
            print ("Created the directory %s" % backdata['localOut'])        
    if(data.get("mode")):
        backdata["type"]="profiler"
        print("Detected analysis type: "+data["mode"])

        #check if mode is spike and the file is specified and does exist
        if(data["mode"] == "spike"):
            if(data.get("spikeFile") and os.path.isfile(data["spikeFile"])):
                backdata["mode"]="spike"
                return (backdata,{"spikeFile":data["spikeFile"]})
            else:
                    print("The fasta file (spikeFile=) with localOut spike-in sequences could not be detected")
                    sys.exit(0)
            #check if mode is libs and the file is specified and does exist
        elif(data["mode"] == "libs"):
            if(data.get("libs") and os.path.isfile(data["libs"])):
                backdata["mode"]="libs"
                return (backdata,{"libs":data["libs"]})
            else:
                print("The fasta file (libs=) with the library sequences could not be detected")
                sys.exit(0)    
            # check if mode is mirna and mature/hairpin was specified and files do exist
        elif(data["mode"] == "mirna"):  
            if(data.get("mature") and os.path.isfile(data["mature"])):
                if(data.get("hairpin") and os.path.isfile(data["hairpin"])):
                    backdata["mode"]="mirna"
                    return (backdata,{"mature":data["mature"],"hairpin":data["hairpin"]})
                else:
                    print("The fasta file (hairpin=) with the hairpin miRNA sequences could not be detected")
                    sys.exit(0)                                                   
            else:
                print("The fasta file (mature=) with the mature miRNA sequences could not be detected")
                sys.exit(0)                                
                  
    else:
        type="dbquery"
        print ("start to query the DB")
        
 
        
def main():
    args = parseArgs()
    data={}
    files={}   
    type=""
    
    if(args.config == None):
        getArguments()
    else:
        if not os.path.isfile(args.config):
            print("The specified config file is not accessable")
            sys.exit(0)
            
        (data,files) = parseConfig(args.config)
    
    if(data["type"]=="profiler"):
        # get back the response object from requests
        r = post_profiler(data,files)  
        
# monitor the process: wait until it finshes       
        check = checkProcess(r,data)
        

        if check == True:
            print("Successfully received the output. Will prepare the summary now")
            prepareSummary(data)
        
    
    
        
if __name__ == '__main__':
    main()