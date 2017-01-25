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

def searchboards(boardname):

	html="https://api.pinterest.com/v1/boards/"+boardname+"/pins/?access_token="+APIKEY+"&fields=id%2Clink%2Cnote%2Curl"

	data=requests.get(url=html).json()
	print data
	pinid=[]
	if "data" in data:

		for d in data["data"]:
			pinid.append(d["id"])

	return pinid

def getpininfo(pinid):

	html = "https://api.pinterest.com/v1/pins/"+str(pinid)+"/?access_token="+APIKEY+"&fields=note%2Curl%2Cimage%2Cmetadata%2Ccounts%2Cattribution%2Ccreator%2Cmedia"


	data = requests.get(url=html).json()
	hasloc=0

	#print data
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
				photodict["likes"]=str(score*3)
				photodict["link"]=opurl
				photodict["location_name"]=placename
				photodict["op_name"]=name
				photodict["url"]=jpgurl
				photodict["source"]="pinterest"
				photodict["op_profile"]=op_profile


				response = table.put_item(
			                        Item = photodict
			                    )

				time.sleep(30)

	else:
		"could not find pin# " + str(pinid)

	return hasloc

if __name__=="__main__":
	
	df_pinboards = pd.read_csv('./pinterest_boards')
	boards = df_pinboards['boards']
	for b in boards:
		print b
		pinids=searchboards(b)
		pinids=list(set(pinids))
		for p in pinids:

			print p
			try:
				hasloc=getpininfo(p)
			except:
				None
			

		#time.sleep(150+np.random.randint(0,10)) # delays for 5 or so seconds until the next requests.


