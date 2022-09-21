
# Create your views here.
from genericpath import isfile
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.http import StreamingHttpResponse
import random
import os
import json
import subprocess
import shutil
from miSRA.settings import BACKEND_CONFIG
# from django.conf.settings import BACKEND_CONFIG
import string
# from django.shortcuts import render
# from django.forms import UploadFileForm


def generate_uniq_id(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


#
def handle_uploaded_file(f, outname):
    with open(outname, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def writeConfigFile(data, files, configFile, configString):
    """
    The function writes out the config file in 'sRNAbench style' (parameter=value)
    It does not return any value
    """
    f = open(configFile, "w")
    for k in data:
        f.write(k + "=" + data[k] + "\n")
    for k in files:
        f.write(k + "=" + files[k] + "\n")
    f.write(configString + "\n")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def index(request):

        # configFile = "/shared/home/pymiSRA/config.json"
        data = BACKEND_CONFIG
        # # # #
        ### prepare the temporary files
        outbase = data["outbase"]
        # rand = "id"+str(int(1000000*random.random()))
        random_id = "id" + generate_uniq_id()
        userOutBase = os.path.join(outbase, random_id)
        # userOutBase = outbase +"/"+ rand
        os.mkdir(userOutBase)
        clientID = get_client_ip(request)
        ## write the temorary files into the temp folder
        localFiles={}
        if request.FILES:
            for k in request.FILES:
                    print ("go for "+k)
                    tmpFile=userOutBase+"/"+k+".fa"
                    handle_uploaded_file(request.FILES[k],tmpFile)
                    localFiles[k]=tmpFile
        else:
            localFiles["test"] = data.get("test_fasta_file")
                
        ## write the config file in sRNAbench style
        configFile = userOutBase+"/config.txt"
        configString = "output="+userOutBase+" \n" +"javaBasePath="+data["javaBasePath"]+"\njavaBasePath2020="+data['javaBasePath2020']+"\ndbPath="+data['dbPath']
        print ("config "+configString)
        writeConfigFile(request.POST,localFiles,configFile,configString)
        
        status = subprocess.run(data['profiler']+" "+configFile, shell=True)


        
        shutil.rmtree(userOutBase+"/bench")
        zipfile = userOutBase+".zip"
        shutil.make_archive(userOutBase, 'zip', userOutBase )
        

        try:
            with open(zipfile, 'rb') as f:
                file_data = f.read()
                # sending response
                response = HttpResponse(file_data, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename=' + zipfile

        except IOError:
        # handle file not exist case here
                response = HttpResponseNotFound('<h1>File does not exist</h1>')

        return response


def launch(request):
    # configFile = "/shared/home/pymiSRA/config.json"
    data = BACKEND_CONFIG
    # # # #
    ### prepare the temporary files
    outbase = data["outbase"]
    # rand = "id"+str(int(1000000*random.random()))
    random_id = "id" + generate_uniq_id()
    userOutBase = os.path.join(outbase, random_id)
    # userOutBase = outbase +"/"+ rand
    os.mkdir(userOutBase)
    clientID = get_client_ip(request)
    ## write the temorary files into the temp folder
    localFiles = {}
    if request.FILES:
        for k in request.FILES:
            print ("go for " + k)
            tmpFile = userOutBase + "/" + k + ".fa"
            handle_uploaded_file(request.FILES[k], tmpFile)
            localFiles[k] = tmpFile
    else:
        localFiles["test"] = data.get("test_fasta_file")

    ## write the config file in sRNAbench style
    configFile = userOutBase + "/config.txt"
    configString = "output=" + userOutBase + " \n" + "javaBasePath=" + data["javaBasePath"] + "\njavaBasePath2020=" + \
                   data['javaBasePath2020'] + "\ndbPath=" + data['dbPath']
    print ("config " + configString)
    writeConfigFile(request.POST, localFiles, configFile, configString)

    command = data['profiler'] + " " + configFile
    status = subprocess.Popen(command.split(" "),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("launched")
        # , shell=True)

    shutil.rmtree(userOutBase + "/bench")
    zipfile = userOutBase + ".zip"
    shutil.make_archive(userOutBase, 'zip', userOutBase)

    data = {}
    data["launched"] = True

    return JsonResponse(data)


# def getJson(file):
#    #check if json is valid
#     try:
#         f = open(file,"r")
#         data = json.load(f)
#         return data
#     except ValueError as e:
#         print(e)
#         print("Errors in json format!")
#
#     return {}



# def upload_file(request): 
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             handle_uploaded_file(request.FILES['file'],"/home/michael/test")
#             return True
#         #     return HttpResponseRedirect('/success/url/')
# #     else:
#         # form = UploadFileForm()
# #     return render(request, 'upload.html', {'form': form})
#         return False

