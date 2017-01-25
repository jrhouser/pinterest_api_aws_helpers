import requests
import numpy as np
import pandas as pd
import boto3
import re
import urllib,urllib2, cookielib, httplib
import ast
import time

APIKEY=""
base = 'https://pinterest.com'
dynamodb=boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ScrapedPhoto')

df_airports = pd.read_table("./major-airport-codes-nparks.tsv")

def searchpins(keyword, page_num=1):
        keyword = re.sub('\s *', '+', keyword)
        postids = list()
        for page in xrange(page_num):
            #try:
            data = urllib2.urlopen(base + r'/search/?q=' + keyword + '&page=' + str(page+1)).read()
            #except (urllib2.URLError, urllib2.HTTPError, httplib.HTTPException), e:
            #    continue
            #    print e
                #raise pypinterestError('Error in searchpins():'+ str(e))
            #print data
            #_tmp_postids = list(re.findall(r'"resourceDataCache":"\d*" ', data))
            #print data.split('resourceDataCache')[-1]


        datadict=re.findall('"pin_id": ".\d*"',data)
        pinidout=[]
        for d in datadict:
        	#print d
        	pinid=ast.literal_eval('{'+d+'}')["pin_id"]
        	#if len(pinid)==16:
        	pinidout.append(int(pinid))
        #postids += [_tmp_postid.replace('<div class="pin" data-id="','').replace('" ','').strip() for _tmp_postid in _tmp_postids]

        return pinidout



def getpininfo(pinid,tripname,airportcode):

	html = "https://api.pinterest.com/v1/pins/"+str(pinid)+"/?access_token="+APIKEY+"&fields=note%2Curl%2Cimage%2Cmetadata%2Ccounts%2Cattribution%2Ccreator%2Cmedia"

	data = requests.get(url=html).json()
	hasloc=0

	if "data" in data:

		d=data["data"]
	    
		opurl=d["url"]
		jpgurl=d["image"]["original"]["url"]

		if "place" in d["metadata"]:
			lat=d["metadata"]["place"]["latitude"]
			lon=d["metadata"]["place"]["longitude"]

			if len(str(lat))>0:
				x=(df_airports["lat"]-float(lat))**2+(df_airports["long"]-float(lon))**2
				idx=np.argmin(np.array(x))

				tripname=str(df_airports.loc[idx,"names"])
				tripname=tripname
				airportcode=str(df_airports.loc[idx,"codes"])
				print airportcode,tripname
				placename=d["metadata"]["place"]["name"]
				hasloc=1
		
		

				score=sum(d["counts"].values())
				caption=d["note"]
				name=d["creator"]["first_name"]+' '+d["creator"]["last_name"]
				opid=d["creator"]["id"]

				op_profile_link=d["creator"]["url"]
				photoid = d["id"]

				html  = "https://api.pinterest.com/v1/users/" + opid+"/?access_token="+APIKEY+"&fields=image"
				data = requests.get(url=html).json()

				#print data["data"]["image"]
				op_profile=data["data"]["image"]["60x60"]["url"]

				photodict=dict()
				photodict["trip_name"]=tripname
				photodict["photoid"]=str(photoid)
				photodict["airport_code"]=airportcode
				photodict["caption"]=caption
				photodict["lat"]=str(lat)
				photodict["lon"]=str(lon)
				photodict["likes"]=str(score)
				photodict["link"]=opurl
				photodict["location_name"]=placename
				photodict["op_name"]=name
				photodict["url"]=jpgurl
				photodict["source"]="pinterest"
				photodict["op_profile"]=op_profile


				response = table.put_item(
			                        Item = photodict
			                    )

				time.sleep(5)

	else:
		"could not find pin# " + str(pinid)

	return hasloc

if __name__=="__main__":


	for i in np.arange(15,len(df_airports)):
		ix = df_airports.index[i]
		print ix
		
		tripname = df_airports.loc[ix,"names"]
		airportcode = df_airports.loc[ix,"codes"]
		keywords = tripname + " photography nature"
		pinids=searchpins(keywords)
		pinids=list(set(pinids))	
		maxcount=5
		currentcount=1
		for p in pinids:


			hasloc=getpininfo(p,tripname,airportcode)
			currentcount=currentcount+hasloc
			if currentcount>maxcount:
				break

		time.sleep(150+np.random.randint(0,10)) # delays for 5 or so seconds until the next requests.


