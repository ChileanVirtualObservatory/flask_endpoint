import subprocess
import urllib
import urllib2
import requests
from os import system
from flask import Flask, render_template, request, Response, redirect


#Hash with every catalog and inside another hash with the url from the services
catalogsIvoa = {
"alma" : {
	"tap" : "http://wfaudata.roe.ac.uk/twomass-dsa/TAP", 
	"scs" : "http://wfaudata.roe.ac.uk/twomass-dsa/DirectCone?DSACAT=TWOMASS&DSATAB=twomass_psc", 
	"ssa": "http://wfaudata.roe.ac.uk/6dF-ssap/?" , 
	"sia" : "http://irsa.ipac.caltech.edu/ibe/sia/wise/prelim/p3am_cdd?"} ,
"2mass": {
	"tap" : "http://wfaudata.roe.ac.uk/twomass-dsa/TAP",
	"sia" : "http://skyview.gsfc.nasa.gov/cgi-bin/vo/sia.pl?survey=2mass&"
	}
}


#Catalog class, made once in the application and change the catalog in use in execution time
class Catalog:
	#Default came with "alma" catalog
	def __init__(self,catalog= None):
		try:                
			if catalog:
				self.dic = catalogsIvoa[catalog]
			else:
				self.dic = catalogsIvoa["alma"]
		except:
			return False
	#Change the object to another catalog
	def setCatalog(self,catalog):
		self.dic = catalogsIvoa[catalog]
		return None	
	#Get the services from the catalog in use
	def getServices(self):
		serv = self.dic.keys()
		return serv	
	#Generic query method, it call the other query types.
	def query(self,parameters, method, queryType, route = None):
		#All services
		if method == "GET":	
			if queryType == "scs" :
				r=self.scsQuery(parameters)
				return r
			elif queryType == "sia":
				r=self.siaQuery(parameters)
				return r

			elif queryType == "ssa":
				r=self.ssaQuery(parameters)
				return r
			elif queryType == "tap":
				r = self.tapQuery(parameters, method, route)
				return r
			else:
				return False
		#Only tap 
		elif method == "POST" and queryType == "tap":
			r=self.tapQuery(parameters, method, route)
			return r
		else:
			return False

	#SCS
	def scsQuery(self,parameters):
		r = requests.get(self.dic["scs"] , params = parameters, stream = True)
		return r
	#SSA
	def ssaQuery(self, parameters):
		r = requests.get(self.dic["ssa"] , params = parameters, stream = True)
		return r
	#SIA
	def siaQuery(self,parameters):
		r = requests.get(self.dic["sia"] , params = parameters, stream = True)
		return r
	#TAP
	def tapQuery(self, query , method , route):
		
		if method == "GET":
			params  = "/" + route["option"]
			if "qid" in route.keys():
					params += "/" + route["qid"]
			if "qidOption" in route.keys():
					params += "/" + route["qidOption"]
			if "qidOptionRequest" in route.keys():
					params += "/" + route["qidOptionRequest"]
			
			r = requests.get(self.dic["tap"] + params , stream = True)
			
			return r

		elif method == "POST":
			if not "qid" in route.keys():
				data = query
				
				print self.dic["tap"]+"/"+route["option"]
				
                req = urllib2.Request(self.dic["tap"]+"/"+route["option"], data)
                response = urllib2.urlopen(req)
                return response	
		return False 


#Functions for data streaming
def streamDataGet(r):
	for line in r.iter_lines():
			if line: # filter out keep-alive new lines
				yield line

def streamDataPost(r):
	CHUNK = 1024
	for the_page in iter(lambda: r.read(CHUNK), ''):
		yield the_page

#Application Itself
app = Flask(__name__)
catalogIvoa = Catalog()



@app.route('/')
def index():
	return 'Index Page'

@app.route('/<catalog>/')
def catalogServices(catalog):
	if catalog in catalogsIvoa.keys():
		catalogIvoa.setCatalog(catalog)
		return " ".join(catalogIvoa.getServices())
	else:
		return 'Catalog not found'

@app.route('/<catalog>/<queryType>/', methods=['POST', 'GET'])
def query(catalog, queryType):
	try:
		catalogIvoa.setCatalog(catalog)
		if queryType in catalogIvoa.getServices():
			if request.method == "GET":
				r = catalogIvoa.query(request.args, request.method, queryType) 
				return Response(streamDataGet(r))
			elif request.method == "POST" and queryType == "tap":
				r = catalogIvoa.query(urllib.urlencode(request.form), request.method, queryType)
				return Response(streamDataPost(r))
			
		return 'Catalog without service'
	except:
		return 'No catalog found'

@app.route('/<catalog>/tap/')
def tap(catalog):
	catalogIvoa.setCatalog(catalog)
	if 'tap' in catalogIvoa.getServices():
		return 'OK'

@app.route('/<catalog>/tap/<path:route>', methods = ['GET', 'POST'])
def queryTap(catalog,route=None):

	catalogIvoa.setCatalog(catalog)
	route = map(str,route.split("/"))
	dictRoute = dict()
	if len(route) > 0:
		dictRoute["option"] = route[0]
	if len(route) > 1:
		dictRoute["qid"] = route[1]
	if len(route) > 2:
		dictRoute["qidOption"] = route[2]
	if len(route) > 3:
		dictRoute["qidOption"] = route[3]
	
	if len(route) > 4:
		return "Bad Tap Request"
	
	if 'tap' in catalogIvoa.getServices():
		
		if request.method == "GET":
		
			r = catalogIvoa.query(None, request.method, "tap" , dictRoute)
			return Response(streamDataGet(r))
		elif request.method == "POST":
			print urllib.urlencode(request.form)
			print dictRoute
			r = catalogIvoa.query(urllib.urlencode(request.form), request.method, "tap",dictRoute)
			return Response(streamDataPost(r))
	return 'Bad Tap Request1'




if __name__ == '__main__':
    app.run(debug=True)
