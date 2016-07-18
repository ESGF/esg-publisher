#!/usr/bin/env python


import logging
import sys, os, time, datetime, getopt, stat, string
import xml.dom, lxml
import ConfigParser
import solr

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from esgcet.config import loadConfig, getHandler, getHandlerByName, initLogging, registerHandlers, splitLine, getOfflineLister
from esgcet.exceptions import *
from esgcet.query import queryDatasetMap
from esgcet.model import Dataset, Catalog, DatasetVersion, File, FileVersion
from lxml import etree


usage = """
Usage:
    meta_syncro.py [-h | --help] [-v | --verbose] [--DT | --SD | --ST] [-a | --all] [-p | --project <project_name] [-m | --model <model name>] [-e | --experiment <exper.name>] [-l report_file]

    Compares contents of DB, THREDDS and Solr and report discrepancies. Only last versions of datasets are verified. 

Arguments:
    project, model, experiment define constraint where to limit verification (applicable to projects with DRS standards only). Use -a|--all for processing all datasets. 
	DT - compare only DB <-> TDS; SD - Solr <-> DB; ST - Solr <-> TDS. Skip it for doing all comparisons.
	Report by default (skipped -l <report_file> option) goes to file meta_synchro.<YYYY-MM-DD.HH:MM:SS>.log
"""

help_message = """
INTRODUCTION

meta_synchro.py tool is intended for comparison of metadata content of three sources - 
Postgresql DB (DB), THREDD Server (TDS) and Solr Server (Solr).

The comparison is limited by datasets list and files belonging to datasets. It does not comprise 
all other aspects of metadata saved in theses three servers though some integrity of metadata is 
checked. 

The tool works in environment where esgpublish script does (machine, user, directory) without any 
additional setup needs (except solr python module).

COMPARISON

Execution is split in three separated comparisons (DB/TDS, Solr/DB, Solr/TDS) and corresponding 
reports are prepared. 

Before actual comparison all datasets are got from sources and some integrity is checked:
 - existing URL's in DB;
 - existing corresponding XML files on ESGF Node machine referenced in main TDS catalog;
 - datasets multiversions on Solr (note that only last versions are examined);
 - datasets redundancy in DB (the same datasets with different ids) 
Broken datasets are excluded from examination. 
  
Each comparison is done in several stages:
 - datasets test;
 - files in missed datasets;
 - peer datasets files examination. 

OPTIONS

There are options for controlling what to compare:
- DB/TDS, Solr/DB, Solr/TDS or all;
- constraints for datasets to compare (project, model, experiment, all). Constraints are applicable only to 
  projects complied with DRS standards. 

OUTPUT REPORT

Report and cout output has 2 modes (standard and verbose). Report contains summary about datasets 
being examined (size and full list) and actually the results of examination:
 - 3 similar sections for each comparison;
 - each section includes datasets difference in a format  <dataset_name> : ['Y','N'] | ['N','Y'],
   where ['Y','N'] means dataset exists in one source and does not in a peer and vice versa;
 - list of files of each non-paired datasets in a format <source>: <dataset_name>|<file_anme>;
 - list of files different in peer datasets.   

Usage:
    meta_syncro.py [-h | --help] [-v | --verbose] [--DT | --SD | --ST] [-a | --all] [-p | --project <project_name] [-m | --model <model name>] [-e | --experiment <exper.name>] [-l report_file]

    Compares contents of DB, THREDDS and Solr and report discrepancies. Only last versions of datasets are verified. 

Arguments:
    project, model, experiment define constraints where to limit verification (only with DRS standards). Use -a|--all for processing all datasets. 
	DT - compare only DB <-> TDS; SD - Solr <-> DB; ST - Solr <-> TDS. Skip it for doing all comparisons.
	Report by default (skipped -l <report_file> option) goes to file meta_synchro.<YYYY-MM-DD.HH:MM:SS>.log
"""


VERBOSE = False
init_dir = '/esg/config/esgcet/'
echoSql = False

Ref_XML_Errors = []  # xml files referenced in main TDS catalog but not existing.
DBNoneValueURL = []
DB_Dict = {}
TDS_Dict = {}
rprt_fl = None

HOST = os.environ.get("HOST")
if HOST is None or len(HOST) ==0:
	print "ERROR finding 'HOST' environment variable for Solr server. Please, set up it."
	exit(1)
SOLR_HTTP = "http://" + HOST + ":8983/solr"


def getTDSDatasetDict(config, constr):
# returns dictionary of TDS datasets {datset_name:dataset_ref_xml}
	global Ref_XML_Errors
	TDS_Dict = {}
	TDS_Dict_Broken = {}
	TDS_Dict_Redund = []  # [(ds_name, xml_ref_file),...]

	try:
		thredd_catalog_path = config.get("DEFAULT","thredds_root")
	except ESGPublishError:
		print "ERROR! Configuration file option missing: 'threddds_root' in section: DEFAULT of esg.ini."  
		exit(1)
		
	thredd_catalog_xml = thredd_catalog_path + "/" + "catalog.xml" 

	if not os.path.isfile(thredd_catalog_xml):
		print "ERROR! Can not find THREDDS catalog.xml. File '" + thredd_catalog_xml + "' does not exist."
		exit(1)

	tree = etree.parse(thredd_catalog_xml)
	root_nd = tree.getroot()
	children = root_nd.getchildren()
	for ch in children:
		if not ch.tag.endswith("catalogRef"):
			continue
		keys = ch.keys()
		k_href = ""
		for k in keys:
			if k.endswith("href"):
				k_href = k
				break
		ref_xml_name = ch.get(k_href)
		ref_xml_name_full_pth = thredd_catalog_path + "/" + ref_xml_name
		#print "from getTDSDatasetDict(): ", ref_xml_name_full_pth
		
		if not os.path.isfile(ref_xml_name_full_pth) or os.stat(ref_xml_name_full_pth)[6]==0:
			print "WARNING! THREDDS XML reference catalog " + ref_xml_name_full_pth + " does not exist or empty;"
			print "dataset =", ch.get("name").strip(), " is excluded from validation."
			continue
			
		if k_href in TDS_Dict.keys() and TDS_Dict_Redund[k_href]!=ref_xml_name:
			TDS_Dict_Redund.append((k_href,ref_xml_name))
			continue
		fndFlg = True
		if len(filter(lambda x: x is not None, constr))>0:
			ds_nm = ch.get("name")
			fndFlg = filter_TDS_dataset_name(ds_nm, constr, config)	
		if fndFlg:		
			TDS_Dict[ch.get("name").strip()] = ref_xml_name
		
	# check whether dataset names correspond to reference catalog xml names
	for d in TDS_Dict.keys():
		v = TDS_Dict[d]
		_v = v[ v.find("/")+1 : v.rfind(".xml") ]
		if d != _v:
			TDS_Dict_Broken[d] = _v
			del TDS_Dict[d]	
	TDS_Dict = removeOldVerTDS(TDS_Dict)		
	return (TDS_Dict, TDS_Dict_Redund, TDS_Dict_Broken)


def removeOldVerTDS(TDS_Dict):
	multiVersions = {}
	KeyLst = list(TDS_Dict.keys())
	ds_names = map(lambda k: k[0:k.rfind(".v")], KeyLst)

	Indx_lst = []
	for ds in ds_names:
		if ds_names.count(ds)==1:
			continue	
		Indx_lst = [indx for indx in range(len(ds_names)) if ds_names[indx]==ds]
		multiVersions[ds] = Indx_lst
		del Indx_lst
	for ds in multiVersions.keys():
		Indx = multiVersions[ds] 
		srtLst = []
		for i in Indx:
			srtLst.append(KeyLst[i])
		srtLst.sort()	
		srtLst.pop()
		for k in srtLst:
			del TDS_Dict[k]	
	return TDS_Dict		


def removeOldVerSolr(Solr_Lst):	
# return DS_Versions := {datasetname:[v1,v2,v3,..], } and 
# Solr_Lst with excluded multiversions
	DS_Versions = {}  
	multiVersions = {}
	
	# datasets names without versions:
	ds_names = map(lambda k: k[0:k.rfind(".v")], Solr_Lst)
	
	Indx_lst = []
	for ds in ds_names:
		if ds_names.count(ds)==1:
			continue
		# list of indeces of versions of the same dataset: 		
		Indx_lst = [indx for indx in range(len(ds_names)) if ds_names[indx]==ds]
		multiVersions[ds] = Indx_lst
		vrs = map(lambda k: Solr_Lst[k][Solr_Lst[k].rfind(".v")+1:], Indx_lst)
		DS_Versions[ds] = vrs
		del Indx_lst
	for ds in DS_Versions.keys():
		vrs = DS_Versions[ds]
		vrs.sort()
		vrs.pop()
		for v in vrs:
			Solr_Lst.remove(ds + "." + v)
	return (DS_Versions, Solr_Lst)		
			 
		
def getDBDatasetDict(session, constr):
# returns dictionary of DB datasets {datset_id:dataset_name}
# Check integrity of DB dictionary (DB_Dict) whether it does not contain 
# the same values under different keys.
# The dublicated pairs will be saved in DB_Dict_Redund = {ds_id:ds_name} and 
# DB_Dict will be free of such redundancy.
	
	global VERBOSE
	DB_Dict = {}
	DB_Dict_Redund = {}

	db_tbl_obj_lst = [Dataset.project, Dataset.model, Dataset.experiment]
	if len(constr) == 0:
		result = session.query(DatasetVersion.dataset_id, DatasetVersion.name, DatasetVersion.version)
	else:
		result = session.query(DatasetVersion.dataset_id, DatasetVersion.name, DatasetVersion.version).\
			 	 join(Dataset, DatasetVersion.dataset_id==Dataset.id)			 
		for i in range(0,len(constr)):
			if constr[i] is not None:
				result = result.filter(db_tbl_obj_lst[i]==constr[i])
			
# single version datasets:			 
#	result_single = result.filter(DatasetVersion.dataset_id.in_(session.query(DatasetVersion.dataset_id).\
#		 	  	  	group_by(DatasetVersion.dataset_id).having(func.count(DatasetVersion.version)==1)))
#	for ds_id, ds_nm, ver in result_single.all():		 

# multi version datasets (not used):
	DB_Dict_Multi = {}
	result_multi = result.filter(DatasetVersion.dataset_id.in_(session.query(DatasetVersion.dataset_id).\
			 	   group_by(DatasetVersion.dataset_id).having(func.count(DatasetVersion.version)>1))).\
				   order_by(DatasetVersion.version)
	for ds_id, ds_nm, ver in result_multi.all():
		ds_shrt_nm = ds_nm[0:ds_nm.rfind(".v")]
		if not ds_shrt_nm in DB_Dict_Multi.keys():
			Vers = ["v"+str(ver)]
		else:
			Vers = DB_Dict_Multi[ds_shrt_nm]
			Vers.append("v"+str(ver))
		DB_Dict_Multi[ds_shrt_nm] = Vers

# REMARK: code grabs only last versions of multiversion datasets cause different verions of datasets have 
# the same id and insertion them into dictionary results to preserving only last version in dictionary as
# they were sorted in SQL query by version.  	
	for ds_id, ds_nm, ver in result.order_by(DatasetVersion.version).all():		 
		DB_Dict[str(ds_id)] = ds_nm

	
	for id1 in DB_Dict:
		for id2 in DB_Dict:
			if DB_Dict[id1] == DB_Dict[id2] and id1!=id2:
				DB_Dict_Redund[id1] = DB_Dict[id1]
				DB_Dict_Redund[id2] = DB_Dict[id1]

	return	(DB_Dict, DB_Dict_Redund)	
					
	
def getTDSRefCatalogFiles(config,ref_xml):	
	# Returns list of files TDS_Files from ref_xml catalog
	global Ref_XML_Errors
	TDS_Files = []
	thredd_catalog_path = config.get("DEFAULT","thredds_root")
	thredd_ref_catalog_pthname = thredd_catalog_path + "/" + ref_xml
	if not os.path.isfile(thredd_ref_catalog_pthname):
		Ref_XML_Errors.append(ref_xml)
		print "\nWARNING! " + ref_xml + " does not exist. Excluded from comparison."
		return TDS_Files
	root_nd = etree.parse(thredd_ref_catalog_pthname).getroot()
	children = root_nd.getchildren()
	for ch in children:
		if ch.tag.rfind("dataset") != -1:
			ds_chlds = ch.getchildren()
			for ds_ch in ds_chlds:
				if ds_ch.tag.rfind("dataset") != -1:
					if not ds_ch.get("name").endswith(".nc"):
						continue
					TDS_Files.append(ds_ch.get("name"))
				else: 	
					continue
		else:
			continue	
	return	TDS_Files		


def getDBDatasetFiles(session, dataset):
# returns from DB all files belonging to dataset (full name or id)
	global DB_Dict, DBNoneValueURL
	DB_Files = []
	if dataset.isdigit():
		res = session.query(FileVersion.url, File.base).join(File).filter(File.dataset_id==dataset).all()		
	elif (dataset.split("."))>0:
		res = session.query(File.dataset_id, File.base).filter(File.dataset_id.in_\
			   (session.query(DatasetVersion.dataset_id).filter(DatasetVersion.name==dataset))).all()
	for fl in res:
		if dataset.isdigit() and fl[0] is None:
			DBNoneValueURL.append((DB_Dict[dataset],fl[1]))
		if fl[1][-2:] == "nc":  # base ends on '.nc_0' (not .nc) for older datasets version; don't take them
			DB_Files.append(fl[1])
	return 	DB_Files


def getSolrDatasetList(constr):
# returns list of datasets names limited by constraint 'constr'
	global SOLR_HTTP, VERBOSE
	s_ds = solr.SolrConnection(SOLR_HTTP+"/datasets")
	Solr_DS_Lst = []
	Solr_MultiVersions_DS = {}
	fld = "id"
	
	# This is temporary approach - just for these 3 constraints. 
	# General constraint should be of shape <project>.*.<model>.<experiment>.* 
	# if some of ingradients is None it should be substituted by '*'
	# e.g. cmip5.*.*.historical.*  or cmip5.*.*.*.*
	if constr[0] is not None:	str_constr = constr[0] + ".*."
	else:						str_constr = "*.*."
	if constr[1] is not None:	str_constr = str_constr + constr[1] + "."
	else:						str_constr = str_constr + "*."
	if constr[2] is not None:	str_constr = str_constr + constr[2] + ".*"
	else: 						str_constr = str_constr + "*"
	if constr[0] is None and constr[1] is None and constr[2] is None:
		str_constr = "*"	

	i=0
	while True:
		response = s_ds.query(fld+":"+str_constr, start=i*100,rows=100)
		Nres = len(response.results)
		if Nres>0: 
			for res in response.results:
				tmp_val = res[fld]
				ds_id = tmp_val[:tmp_val.find("|")]				
				Solr_DS_Lst.append(ds_id)
		else:
			break		
		i=i+1	
	s_ds.close()

	(Solr_MultiVersions_DS, Solr_Lst) = removeOldVerSolr(Solr_DS_Lst)
	return 	(Solr_MultiVersions_DS, Solr_Lst)
	

def getSolrDatasetFiles(ds_nm, s):
	global VERBOSE
	SLR_Files = []
	j=0
	while True:
		response = s.query("id:"+ds_nm+"*", start=j*1000,rows=1000)
		Nres = len(response.results)
		if Nres>0: 
			for res in response.results:
				inst_id = res["instance_id"]				
				if inst_id.index(ds_nm)>=0:
					fl = res["title"]
					SLR_Files.append(fl)
		else:
			break		
		j=j+1		
	return 	SLR_Files	


def compareLists(L1, L2):
# compares 2 lists (L1,L2) and returns tuple of lists: (L1_diff, L2_diff)
# where L1_diff - unique elements in L1;
#       L2_diff - unique elements in L2;
	L1_diff = []
	L2_diff = [] 
	S1 = set(L1)
	S2 = set(L2)
	N1 = len(L1)
	N2 = len(L2)
	lenFlg = (N1==N2)
	if lenFlg:  # lacky case when number of elements in lists the same and 
				# overlaping list also has the same cardinality		
		S_comm = S1 & S2		
		if len(S_comm) == N1:
			del S_comm
			return 	(L1_diff, L2_diff) 
	S1_diff = S1 - S2 
	S2_diff = S2 - S1 
	for s in S1_diff:
		L1_diff.append(s)
	for s in S2_diff:
		L2_diff.append(s)
	S1.clear()
	S2.clear()
	S1_diff.clear()
	S2_diff.clear()
	return (L1_diff, L2_diff)	


def compare_DB_TDS_DatasetsOnly(TDS_Dict, DB_Dict):
	#   Compare DB and TDS datasets names (without files); 
	#    get as a result dictionary DB_TDS_DIFF_DS = {<dataset_name ds_id|xml_rel_pth> : <'Y','N'>|<'N','Y'>} 
	#     - differences in datasets only (no files comparing) and
	#    and DB_TDS_Shared_DS_Dict = {"DB_dataset_id TDS_rel_xmlpth" : TDS_xml_pthnm} 
	#      - shared dataset names for both servers (by set, not list);
	#	 this dictionary is well defined and does not contain broken datasets, that means:
	#    - all datasets there exist on both servers DB and TDS;
	#    - in DB all datasets names are unique (no ones with different ids have the same names); 
	#    - in TDS catalog all datasets have correspondence: name <=> xml
	#    - in TDS all xml's exist.
	global VERBOSE
	
	DB_TDS_Shared_DS_Dict = {}
	DB_TDS_DIFF_DS = {}  
	TDS_DataSets = TDS_Dict.keys()
	DB_DataSets = DB_Dict.values()	
	
	for d1 in TDS_DataSets:
		fndFlg = False
		for d2 in DB_DataSets:
			if d1==d2:
				fndFlg = True
				break
		ref_xml = TDS_Dict[d1]
		rel_pth = ref_xml[0:ref_xml.find("/")]
		if not fndFlg:
			ds_diff = d1 + " " + rel_pth
			DB_TDS_DIFF_DS[ds_diff] = ["N","Y"]
		else:
			k = DB_Dict.keys()[DB_DataSets.index(d2)] 
			DB_TDS_Shared_DS_Dict[k + " " + str(rel_pth)] = d1
	for d1 in DB_DataSets:
		fndFlg = False
		for d2 in TDS_DataSets:
			if d1==d2:
				fndFlg = True
				break
		if not fndFlg:
			i2del = DB_Dict.values().index(d1)
			key2del = DB_Dict.keys()[i2del]
			ds_diff = d1 + " " +key2del
			DB_TDS_DIFF_DS[ds_diff] = ["Y","N"]			
	return (DB_TDS_Shared_DS_Dict, DB_TDS_DIFF_DS)


def compare_SOLR_DB_DatasetsOnly(Solr_DataSets, DB_Dict):
# returns tuple of dictionaries - datasets existing in both sources and datasets differences
	Solr_DB_Shared_DS_Dict = {}
	Solr_DB_DIFF_DS = {}  
	DB_DataSets = DB_Dict.values()	
	
	for d1 in Solr_DataSets:
		fndFlg = False
		for d2 in DB_DataSets:
			if d1==d2:
				fndFlg = True
				break
		if not fndFlg:
			Solr_DB_DIFF_DS[d1] = ["Y","N"]
		else:
			k = DB_Dict.keys()[DB_DataSets.index(d2)] 
			Solr_DB_Shared_DS_Dict[str(k)] = d1
	for d1 in DB_DataSets:
		fndFlg = False
		for d2 in Solr_DataSets:
			if d1==d2:
				fndFlg = True
				break
		if not fndFlg:
			Solr_DB_DIFF_DS[d1] = ["N","Y"]			
	return (Solr_DB_Shared_DS_Dict, Solr_DB_DIFF_DS)
	
	
def compare_SOLR_TDS_DatasetsOnly(Solr_DataSets, TDS_Dict):
# returns tuple of dictionaries - datasets existing in both sources and datasets differences
	Solr_TDS_Shared_DS_Lst = []
	Solr_TDS_DIFF_DS = {}  
	TDS_DataSets = TDS_Dict.keys()
	
	for d1 in Solr_DataSets:
		fndFlg = False
		for d2 in TDS_DataSets:
			if d1==d2:
				fndFlg = True
				break
		if not fndFlg:
			Solr_TDS_DIFF_DS[d1] = ["Y","N"]
		else:
			Solr_TDS_Shared_DS_Lst.append(d1)
	for d1 in TDS_DataSets:
		fndFlg = False
		for d2 in Solr_DataSets:
			if d1==d2:
				fndFlg = True
				break
		if not fndFlg:
			Solr_TDS_DIFF_DS[d1] = ["N","Y"]			
	return (Solr_TDS_Shared_DS_Lst, Solr_TDS_DIFF_DS)


def getFiles_DB_TDS_MissedDatasets(DB_TDS_DIFF_DS, config, session):
	#    Fill with .nc files the datasets belonging to only DB or TDS servers 
	#    (files from those datasets which are only on one server)
	#    DB_Only_Files_Dict = { "datset_name dataset_id" : [files] } 
	#    TDS_Only_Files_Dict = { "dataset_name rel_xmlpath" : [files] }
	#    at the end of key may be 'all' indicating that given dataset is comptetly missed in peer source
	DB_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}
	
	i = 1		
	for d in DB_TDS_DIFF_DS.keys():
		DB_Files = []
		TDS_Files = []
		if i%2==0:				
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(DB_TDS_DIFF_DS) 
		i = i + 1
		v = DB_TDS_DIFF_DS[d]
		if v[0] == "Y" and v[1] == "N":  # get files from DB
			ds_id = d.split(" ")[1]
			DB_Files = getDBDatasetFiles(session, ds_id)		
					
		elif v[0] == "N" and v[1] == "Y":  # get files from TDS
			xml = d.split(" ")[1] + "/" + d.split(" ")[0] + ".xml"		
			TDS_Files = getTDSRefCatalogFiles(config, xml)
		
		if len(DB_Files)>0:
			DB_Only_Files_Dict[d + " all"] = DB_Files
		if len(TDS_Files)>0:
			TDS_Only_Files_Dict[d + " all"] = TDS_Files	
	print ""
	return (DB_Only_Files_Dict, TDS_Only_Files_Dict)


def getFiles_SOLR_DB_MissedDatasets(Solr_DB_DIFF_DS, session):
	global  SOLR_HTTP
	s_fl = solr.SolrConnection(SOLR_HTTP+"/files")
	DB_Only_Files_Dict = {}
	Solr_Only_Files_Dict = {}
	i = 1
	for d in Solr_DB_DIFF_DS.keys():
		DB_Files = []
		Solr_Files = []
		if i%2==0:	
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(Solr_DB_DIFF_DS) 
		i = i + 1
		v = Solr_DB_DIFF_DS[d]
		if v[0] == "Y" and v[1] == "N":  # get files from Solr
			Solr_Files = getSolrDatasetFiles(d, s_fl)
		elif v[0] == "N" and v[1] == "Y":  # get files from DB
			DB_Files = getDBDatasetFiles(session, d)		
							
		if len(DB_Files)>0:
			DB_Only_Files_Dict[d + " all"] = DB_Files
		if len(Solr_Files)>0:
			Solr_Only_Files_Dict[d + " all"] = Solr_Files	
	print ""
	s_fl.close()
	return (Solr_Only_Files_Dict, DB_Only_Files_Dict) 


def getFiles_SOLR_TDS_MissedDatasets(Solr_TDS_DIFF_DS, config):
	global  TDS_Dict, SOLR_HTTP, VERBOSE
	s_fl = solr.SolrConnection(SOLR_HTTP+"/files")
	TDS_Only_Files_Dict = {}
	Solr_Only_Files_Dict = {}
	i = 1
	for d in Solr_TDS_DIFF_DS.keys():
		TDS_Files = []
		Solr_Files = []
		if i%2==0:	
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(Solr_TDS_DIFF_DS) 
		i = i + 1
		v = Solr_TDS_DIFF_DS[d]
		if v[0] == "Y" and v[1] == "N":  # get files from Solr
			Solr_Files = getSolrDatasetFiles(d, s_fl)
		elif v[0] == "N" and v[1] == "Y":  # get files from TDS catalog
			xml = TDS_Dict[d]
			TDS_Files = getTDSRefCatalogFiles(config, xml)		
		
		if len(TDS_Files)>0:
			TDS_Only_Files_Dict[d + " all"] = TDS_Files
		if len(Solr_Files)>0:
			Solr_Only_Files_Dict[d + " all"] = Solr_Files	
	print ""
	s_fl.close()
	return (Solr_Only_Files_Dict, TDS_Only_Files_Dict)


def compare_DB_TDS_DatasetsFiles(DB_TDS_Shared_DS_Dict, session, config):
	#  Walk through all datasets common for both sources (DB,TDS)
	#  getting corresponding files and compare them;
	#  the result will be returned as tuple: (DB_Only_Files_Dict, TDS_Only_Files_Dict)
	
	print "\nComparing files in DB/TDS peer datasets:"	

	DB_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}

	i = 1
	ts_prev =  time.time()
	ts_cur = 1
	for k in DB_TDS_Shared_DS_Dict:	
		if i%2==0:	
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(DB_TDS_Shared_DS_Dict) 
		i = i + 1
		DB_Only_Files = []
		TDS_Only_Files = []		
		ds_id =  (k.split(" ")[0]).strip()
		rel_xmlpath = k.split(" ")[1]
		dataset_name = DB_TDS_Shared_DS_Dict[k]

		TDS_Files = getTDSRefCatalogFiles(config, rel_xmlpath+"/"+dataset_name+".xml")
		DB_Files = getDBDatasetFiles(session, ds_id)
		
		(DB_Only_Files, TDS_Only_Files) = compareLists(DB_Files, TDS_Files)	
		if len(DB_Only_Files)>0:	
			DB_Only_Files_Dict[str(ds_id) + " " + dataset_name] = DB_Only_Files
		if len(TDS_Only_Files)>0:	
			TDS_Only_Files_Dict[rel_xmlpath + " " +	dataset_name] = TDS_Only_Files
	print ""		
	return (DB_Only_Files_Dict, TDS_Only_Files_Dict)


def compare_SOLR_DB_DatasetsFiles(Common_Dict, session):
# compares DS files from Solr and DB
# returns dictionaries:
# Solr_Only_Files_Dict = {(ds_id ds_name):[file_list]} - exist only in Solr peer dataset
# DB_Only_Files_Dict = {(ds_id ds_name):[file_list]} - exist only in DB peer dataset

	global DB_Dict, SOLR_HTTP
	s_fl = solr.SolrConnection(SOLR_HTTP+"/files")
	Solr_Only_Files_Dict = {}
	DB_Only_Files_Dict = {}
	print "Comparing files in Solr/DB peer datasets:"
	i=1
	for ds_id in Common_Dict.keys():
		if i%2==0:	
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(Common_Dict) 
		ds_nm = Common_Dict[ds_id]
		Solr_Fl_Lst = getSolrDatasetFiles(ds_nm, s_fl)
		DB_Fl_Lst = getDBDatasetFiles(session, ds_id)
		(Solr_Only_Files, DB_Only_Files) = compareLists(Solr_Fl_Lst, DB_Fl_Lst)
		if len(Solr_Only_Files)>0:	
			Solr_Only_Files_Dict[ds_id + " " + ds_nm] = Solr_Only_Files
		if len(DB_Only_Files)>0:	
			DB_Only_Files_Dict[ds_id + " " + ds_nm] = DB_Only_Files
		i = i +1	
	print ""
	s_fl.close()
	return (Solr_Only_Files_Dict, DB_Only_Files_Dict)


def compare_SOLR_TDS_DatasetsFiles(Solr_TDS_Shared_DS_Lst, config):
# compares DS files from Solr and TDS
# returns dictionaries:
# Solr_Only_Files_Dict = {(ds_id ds_name):[file_list]} - exist only in Solr peer dataset
# TDS_Only_Files_Dict = {(ds_id ds_name):[file_list]} - exist only in TDS peer dataset

	global TDS_Dict, SOLR_HTTP
	s_fl = solr.SolrConnection(SOLR_HTTP+"/files")
	Solr_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}
	print "\nComparing files in Solr/TDS peer datasets:"
	i=1
	for ds_nm in Solr_TDS_Shared_DS_Lst:
		if i%2==0:	
			sys.stdout.write(".")
			sys.stdout.flush()
		if i%100==0:	print ""
		if i%500==0:	print "\t", i, " out of ",len(Solr_TDS_Shared_DS_Lst) 
		Solr_Fl_Lst = getSolrDatasetFiles(ds_nm, s_fl)
		TDS_Fl_Lst = getTDSRefCatalogFiles(config, TDS_Dict[ds_nm])					
		(Solr_Only_Files, TDS_Only_Files) = compareLists(Solr_Fl_Lst, TDS_Fl_Lst)
		if len(Solr_Only_Files)>0:	
			Solr_Only_Files_Dict[ds_nm] = Solr_Only_Files
		if len(TDS_Only_Files)>0:	
			TDS_Only_Files_Dict[ds_nm] = TDS_Only_Files
		i = i +1	
	print ""
	s_fl.close()
	return (Solr_Only_Files_Dict, TDS_Only_Files_Dict)

	
def DB_THREDDS_Comparison(DB_Dict,TDS_Dict, config, session):
# Postgresql DB - THREDDS Comparison
	global rprt_fl, VERBOSE

	DB_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}
	
	print "\n\n==============================================================================="
	print "===================== Posgresql DB - THREDDS  Comparison ======================"
	print "==============================================================================="
	print "DB and TDS comparison started..."
	
	# comparing datasets in DB and TDS (without files)
	(DB_TDS_Shared_DS_Dict, DB_TDS_DIFF_DS) = compare_DB_TDS_DatasetsOnly(TDS_Dict, DB_Dict)
	
# 	DB_TDS_DIFF_DS shape : {<dataset_name> <dataset_id>|<rel_xmlpath> : ['Y','N'] | ['N','Y']}
#	DB_TDS_DIFF_DS["cmip5.output1.NOAA-GFDL.GFDL-CM3.piControl.mon.seaIce.OImon.r1i1p1.v20110601 6023"] = ["Y","N"]
#	DB_TDS_DIFF_DS["cmip5.output1.NOAA-GFDL.GFDL-CM3.piControl.day.land.day.r1i1p1.v20110601 8"] = ["N","Y"]

	
	print "\n=================> DB_TDS_Shared_Datasets_Dict.size=" + str(len(DB_TDS_Shared_DS_Dict))
	if VERBOSE:
		print "\n".join((k + " : " + DB_TDS_Shared_DS_Dict[k]) for k in DB_TDS_Shared_DS_Dict.keys())		
		
	print "\nNumber of peer datasets in DB and TDS: " + str(len(DB_TDS_Shared_DS_Dict))
#	print "Number of different datasets in DB and TDS: " + str(len(DB_TDS_DIFF_DS.keys()))  
	

	#  DB_Only_Files_Dict = { "datset_name dataset_id" : [files] } 
	#  TDS_Only_Files_Dict = { "dataset_name rel_xmlpath" : [files] }
	#  at the end of key may be 'all' indicating that given dataset is comptetly missed in peer source

	(DB_Only_Files_Dict, TDS_Only_Files_Dict) = getFiles_DB_TDS_MissedDatasets(DB_TDS_DIFF_DS, config, session)	

	rprt_fl.write("\n\n\n===============================================================================")
	rprt_fl.write("\n===================== Posgresql DB - THREDDS  Comparison ======================")		
	rprt_fl.write("\n===============================================================================\n\n")
	
	if 	len(Ref_XML_Errors)>0:
		rprt_fl.write("\n ===========> TDS broken integrity:\n")
		rprt_fl.write("                These TDS xml files do not exist though are referenced in TDS Catalog: =====>\n")
		rprt_fl.write("\n".join(f for f in Ref_XML_Errors))

	if len(DB_TDS_DIFF_DS)>0:
		rprt_fl.write("\n\n=========> Datasets Difference between DB and TDS (size= " + str(len(DB_TDS_DIFF_DS.keys())) +" ) ===========>\n") 
		rprt_fl.write("             shape: {<dataset_name> <dataset_id>|<rel_xmlpath> : ['Y','N'] | ['N','Y']}\n")
		rprt_fl.write("             (['Y','N'] means dataset exists in DB and does not in TDS and vice versa)\n")
		rprt_fl.write("\n".join(k+":"+str(DB_TDS_DIFF_DS[k]) for k in DB_TDS_DIFF_DS.keys()))	
	else:
		print "No diferences in DB/TDS datasets."
		rprt_fl.write("\nNo diferences in DB/TDS datasets.\n") 
	if len(DB_Only_Files_Dict)>0 or len(TDS_Only_Files_Dict)>0:
		rprt_fl.write("\n\n\n===========================>  These are the files in missed datasets ===============>")
	if len(DB_Only_Files_Dict)>0:
		rprt_fl.write("\n\n===========> In DB only:\n")
		for k in DB_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("DB: " + k.split(" ")[0] + "|" + f) for f in DB_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")
	if len(TDS_Only_Files_Dict)>0:
		rprt_fl.write("\n===========> In TDS only:\n")
		for k in TDS_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("TDS: " + k.split(" ")[0] + "|" + f) for f in TDS_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")

	if VERBOSE:
		if len(DB_TDS_DIFF_DS.keys()) > 0:
			print "\n=================> len(Solr_DB_Shared_DS_Dict)=", len(DB_TDS_Shared_DS_Dict)
			print "\n\n===============> len(Solr_DB_DIFF_DS)=", len(DB_TDS_DIFF_DS)
			print "\n=========> Datasets Difference between Solr and DB (size= " + str(len(DB_TDS_DIFF_DS.keys())) +" ) ===========>\n" 
			print "             shape: {<dataset_name dataset_id> <rel_xmlpath> : ['Y','N'] | ['N','Y']}"
			print "             (['Y','N'] means dataset exists in Solr and does not in DB and vice versa)"
			print "\n".join(k+":"+str(DB_TDS_DIFF_DS[k]) for k in DB_TDS_DIFF_DS.keys())
    
	# Walk through all peer datasets for both sources (DB, TDS) getting corresponding files and compare them;
	
	DB_Only_Files_Dict.clear()
	TDS_Only_Files_Dict.clear()
	
	N_shared = len(DB_TDS_Shared_DS_Dict.keys())
	Ndiff = 0		
	if N_shared > 0:
		(DB_Only_Files_Dict, TDS_Only_Files_Dict) = compare_DB_TDS_DatasetsFiles(DB_TDS_Shared_DS_Dict, session, config)	
		for k in DB_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(DB_Only_Files_Dict[k])
		for k in TDS_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(TDS_Only_Files_Dict[k])
		
		print "Total number of files different in DB and TDS: " + str(Ndiff)		
			
	if VERBOSE: 
		if len(DBNoneValueURL)>0:
			print "\n================> 'None' URL value in DB file_version.url field (N="+ str(len(DBNoneValueURL)) +") =========>"
			print "\n".join((f[0]+"|"+f[1]) for f in DBNoneValueURL)
			print "\n"
		
	if len(DBNoneValueURL)>0:
		rprt_fl.write("\n======> Postgress DB issue: ")
		rprt_fl.write("'None' URL value in DB file_version.url field (N="+ str(len(DBNoneValueURL)) +") =========>\n")
		rprt_fl.write("\n".join((f[0]+"|"+f[1]) for f in DBNoneValueURL))
		rprt_fl.write("\n<======\n\n")		

	if Ndiff==0 and N_shared>0:
		rprt_fl.write("\nNo diferences in DB/TDS files belonging to peer datasets.\n")
	elif N_shared==0:
		print "No peer datasets in DB and TDS."
		rprt_fl.write("\nNo peer datasets in DB and TDS.\n\n")
	else:
		rprt_fl.write("\nTotal number of different files in existing peer DB-TDS datasets: " + str(Ndiff))
		if len(DB_Only_Files_Dict)>0:
			rprt_fl.write("\n\n===========> These DB Datasets differ from those in TDS by these files (missed in TDS): ============>\n")
			for k in DB_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + ":\n")
				rprt_fl.write("\n".join("\t"+f for f in DB_Only_Files_Dict[k]))
		if len(TDS_Only_Files_Dict)>0:
			rprt_fl.write("\n===========> These TDS Datasets differ from those in DB by these files (missed in DB): ============>\n")
			for k in TDS_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + " :\n")
				rprt_fl.write("\n".join("\t"+f for f in TDS_Only_Files_Dict[k]))

	print "DB and TDS comparison completed."


		 	
def SOLR_DB_Comparison(Solr_DS_Lst, DB_Dict, SOLR_HTTP, session):
# Solr - PostgreSQL comparison
	global rprt_fl, VERBOSE

	DB_Only_Files_Dict = {}
	Solr_Only_Files_Dict = {}

	print "\n\n==============================================================================="
	print "===================== SOLR - Posgresql DB Comparison =========================="
	print "==============================================================================="
	print "Solr and DB comparison started..."
	
	(Solr_DB_Shared_DS_Dict, Solr_DB_DIFF_DS) = compare_SOLR_DB_DatasetsOnly(Solr_DS_Lst, DB_Dict)
	
	print "\n=================> Solr_DB_Shared_Datasets_Dict, size= " + str(len(Solr_DB_Shared_DS_Dict)) 
	print "\nNumber of peer datasets in Solr and TDS: ", len(Solr_DB_Shared_DS_Dict)
#	print "Number of different datasets in Solr and DB: " + str(len(Solr_DB_DIFF_DS.keys()))  

	# get list of files from datasets missed in either source:
#	Solr_DB_DIFF_DS = {}
#	Solr_DB_DIFF_DS["cmip5.output1.NOAA-GFDL.GFDL-CM3.piControl.mon.aerosol.aero.r1i1p1.v20110601"] = ["Y","N"]
#	Solr_DB_DIFF_DS["cmip5.output1.NOAA-GFDL.GFDL-CM3.piControl.day.seaIce.day.r1i1p1.v20110601"] = ["N","Y"]
	
	(Solr_Only_Files_Dict, DB_Only_Files_Dict) = getFiles_SOLR_DB_MissedDatasets(Solr_DB_DIFF_DS, session)
	

	rprt_fl.write("\n\n\n===========================================================================")
	rprt_fl.write("\n===================== SOLR - Posgresql DB Comparison ======================")		
	rprt_fl.write("\n===========================================================================\n\n")

	if len(Solr_DB_DIFF_DS.keys()) > 0:
		rprt_fl.write("\n=========> Datasets Difference between Solr and Postgresql DB (size= " + str(len(Solr_DB_DIFF_DS.keys())) +" ) ===========>\n")
		rprt_fl.write("             shape: {<dataset_name> : ['Y','N'] | ['N','Y']}\n")
		rprt_fl.write("             (['Y','N'] means dataset exists in Solr and does not in DB and vice versa)\n")
		rprt_fl.write("\n".join(k+":"+str(Solr_DB_DIFF_DS[k]) for k in Solr_DB_DIFF_DS.keys()))	
	else:
		print "No diferences in Solr/DB datasets."
		rprt_fl.write("\nNo diferences in Solr/DB datasets.\n") 
	if len(DB_Only_Files_Dict)>0 or len(Solr_Only_Files_Dict)>0:
		rprt_fl.write("\n\n\n===========================>  These are the files in missed datasets ===============>")
	if len(DB_Only_Files_Dict)>0:
		rprt_fl.write("\n\n===========> In DB only:\n")
		for k in DB_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("DB: " + k.split(" ")[0] + "|" + f) for f in DB_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")
	if len(Solr_Only_Files_Dict)>0:
		rprt_fl.write("\n===========> In SOLR only:\n")
		for k in Solr_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("SOLR: " + k.split(" ")[0] + "|" + f) for f in Solr_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")

	if VERBOSE:
		if len(Solr_DB_DIFF_DS.keys()) > 0:
			print "\n=================> len(Solr_DB_Shared_DS_Dict)=", len(Solr_DB_Shared_DS_Dict)
			print "\n\n===============> len(Solr_DB_DIFF_DS)=", len(Solr_DB_DIFF_DS)
			print "\n=========> Datasets Difference between Solr and DB (size= " + str(len(Solr_DB_DIFF_DS.keys())) +" ) ===========>\n" 
			print "             shape: {<dataset_name dataset_id> <rel_xmlpath> : ['Y','N'] | ['N','Y']}"
			print "             (['Y','N'] means dataset exists in Solr and does not in DB and vice versa)"
			print "\n".join(k+":"+str(Solr_DB_DIFF_DS[k]) for k in Solr_DB_DIFF_DS.keys())
		
	DB_Only_Files_Dict.clear()
	Solr_Only_Files_Dict.clear()
	
	Ndiff = 0		
	N_shared = len(Solr_DB_Shared_DS_Dict.keys())
	if N_shared > 0:	
		(Solr_Only_Files_Dict, DB_Only_Files_Dict) = compare_SOLR_DB_DatasetsFiles(Solr_DB_Shared_DS_Dict, session)				

		for k in DB_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(DB_Only_Files_Dict[k])
		for k in Solr_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(Solr_Only_Files_Dict[k])
		print "\nTotal number of files different in Solr / Postgresql DB peer datasets: " + str(Ndiff)		

	if Ndiff==0 and N_shared>0:
		rprt_fl.write("\nNo diferences in Solr/DB files belonging to peer datasets.") 
	elif N_shared==0:
		print "No peer datasets in Solr and DB."
		rprt_fl.write("\nNo peer datasets in Solr and DB.\n\n")
	else:
		rprt_fl.write("\nTotal number of different files in existing peer Solr/DB datasets: " + str(Ndiff))
		if len(Solr_Only_Files_Dict)>0:
			rprt_fl.write("\n===========> These Solr Datasets differ from those in DB by these files (missed in DB): ============>\n")
			for k in Solr_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + " :\n")
				rprt_fl.write("\n".join("\t"+f for f in Solr_Only_Files_Dict[k]))
		if len(DB_Only_Files_Dict)>0:
			rprt_fl.write("\n\n===========> These DB Datasets differ from those in Solr by these files (missed in Solr): ============>\n")
			for k in DB_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + ":\n")
				rprt_fl.write("\n".join("\t"+f for f in DB_Only_Files_Dict[k]))
	print "Solr and DB comparison completed."

	

def SOLR_TDS_Comparison(Solr_DS_Lst, TDS_Dict, SOLR_HTTP, config):
# Solr - THREDDS comparison
	global rprt_fl, VERBOSE

	Solr_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}

	print "\n\n==============================================================================="
	print "=============================  SOLR - TDS Comparison ========================="
	print "==============================================================================="
	print "Solr and TDS comparison started..."
	
	(Solr_TDS_Shared_DS_Lst, Solr_TDS_DIFF_DS) = compare_SOLR_TDS_DatasetsOnly(Solr_DS_Lst, TDS_Dict)
	print "\nNumber of peer datasets in Solr and TDS: ", len(Solr_TDS_Shared_DS_Lst)

	# get list of files from datasets missed in either source:
	(Solr_Only_Files_Dict, TDS_Only_Files_Dict) = getFiles_SOLR_TDS_MissedDatasets(Solr_TDS_DIFF_DS, config)
	
	rprt_fl.write("\n\n\n===========================================================================")
	rprt_fl.write("\n=========================== SOLR - THREDDS Comparison ======================")		
	rprt_fl.write("\n===========================================================================\n\n")

	if 	len(Ref_XML_Errors)>0:
		rprt_fl.write("\n ===========> TDS broken integrity:\n")
		rprt_fl.write("                These TDS xml files do not exist though are referenced in TDS Catalog: =====>\n")
		rprt_fl.write("\n".join(f for f in Ref_XML_Errors))

	if len(Solr_TDS_DIFF_DS.keys()) > 0:
		rprt_fl.write("\n\n=========> Datasets Difference between Solr and TDS (size= " + str(len(Solr_TDS_DIFF_DS.keys())) +" ) ===========>\n")
		rprt_fl.write("             shape: {<dataset_name> : ['Y','N'] | ['N','Y']}\n")
		rprt_fl.write("             (['Y','N'] means dataset exists in Solr and does not in TDS and vice versa)\n")
		rprt_fl.write("\n".join(k+":"+str(Solr_TDS_DIFF_DS[k]) for k in Solr_TDS_DIFF_DS.keys()))	
	else:
		print "No diferences in DB/TDS datasets."
		rprt_fl.write("\nNo diferences in Solr/TDS datasets.\n") 

	if len(TDS_Only_Files_Dict)>0 or len(Solr_Only_Files_Dict)>0:
		rprt_fl.write("\n\n\n===========================>  These are the files in missed datasets ===============>")
	if len(TDS_Only_Files_Dict)>0:
		rprt_fl.write("\n\n===========> In TDS only:\n")
		for k in TDS_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("TDS: " + k.split(" ")[0] + "|" + f) for f in TDS_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")
	if len(Solr_Only_Files_Dict)>0:
		rprt_fl.write("\n===========> In SOLR only:\n")
		for k in Solr_Only_Files_Dict.keys():
			rprt_fl.write("\n"+k.split(" ")[0]+":\n")
			rprt_fl.write("\n".join(("SOLR: " + k.split(" ")[0] + "|" + f) for f in Solr_Only_Files_Dict[k]))
		rprt_fl.write("\n<====================\n")

	if VERBOSE:
		if len(Solr_TDS_DIFF_DS.keys()) > 0:
			print "\n=========> Datasets Difference between Solr and TDS (size= " + str(len(Solr_TDS_DIFF_DS.keys())) +" ) ===========>\n" 
			print "             shape: {<dataset_name dataset_id> <rel_xmlpath> : ['Y','N'] | ['N','Y']}"
			print "             (['Y','N'] means dataset exists in Solr and does not in TDS and vice versa)"
			print "\n".join(k+":"+str(Solr_TDS_DIFF_DS[k]) for k in Solr_TDS_DIFF_DS.keys())
		else:
			print "No diferences in Solr/TDS datasets.\n"
		if len(Solr_Only_Files_Dict.keys())>0:	
			print "\nNumber of files in Solr non-peer datasets: ", sum(len(v) for v in Solr_Only_Files_Dict.itervalues()) 
		if len(TDS_Only_Files_Dict.keys())>0:
			print "\nNumber of files in TDS non-peer datasets: ", sum(len(v) for v in TDS_Only_Files_Dict.itervalues()) 

	
	TDS_Only_Files_Dict.clear()
	Solr_Only_Files_Dict.clear()

	Ndiff = 0		
	N_shared = len(Solr_TDS_Shared_DS_Lst)
	if N_shared > 0:
		(Solr_Only_Files_Dict, TDS_Only_Files_Dict) = compare_SOLR_TDS_DatasetsFiles(Solr_TDS_Shared_DS_Lst, config)

		for k in TDS_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(TDS_Only_Files_Dict[k])
		for k in Solr_Only_Files_Dict.keys():
			Ndiff = Ndiff + len(Solr_Only_Files_Dict[k])
		print "\nTotal number of files different in Solr and TDS: " + str(Ndiff)		
	
	if Ndiff==0 and N_shared>0:
		rprt_fl.write("\nNo diferences in Solr/TDS files belonging to peer datasets.\n") 
	elif N_shared==0:
		print "No peer datasets in DB and TDS."
		rprt_fl.write("\nNo peer datasets in Solr and TDS.\n\n")
	else:
		rprt_fl.write("\nTotal number of different files in peer Solr/TDS datasets: " + str(Ndiff))
		if len(Solr_Only_Files_Dict)>0:
			rprt_fl.write("\n===========> These Solr Datasets differ from those in TDS by these files (missed in TDS): ============>\n")
			for k in Solr_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + " :\n")
				rprt_fl.write("\n".join("\t"+f for f in Solr_Only_Files_Dict[k]))
		if len(TDS_Only_Files_Dict)>0:
			rprt_fl.write("\n\n===========> These TDS Datasets differ from those in Solr by these files (missed in Solr): ============>\n")
			for k in TDS_Only_Files_Dict.keys():
				rprt_fl.write("\n" + k.split(" ")[1] + ":\n")
				rprt_fl.write("\n".join("\t"+f for f in TDS_Only_Files_Dict[k]))
			
	if VERBOSE:
		print "\n=================> len(Solr_TDS_Shared_DS_Lst) = ", len(Solr_TDS_Shared_DS_Lst), " <================="
		print "\n".join(k for k in Solr_TDS_Shared_DS_Lst)
		
	print "Solr and TDS comparison completed."


def constrImposeTDS(dataset_name, constr):
# suggested that all fields in dataset_name are different. So, check 3 constraints for any 3 fields 
# and put dataset in comparison bin is all 3 found.
	dataset_name_flds = dataset_name.split(".")
	tmp_flds = dataset_name_flds[:]
	fndFlg = False
	# check if all fields are different:
	for i in range(len(dataset_name_flds)):
		for j in range(i+1,len(dataset_name_flds)):
			if dataset_name_flds[i]==dataset_name_flds[j]:
				print "ERROR! 2 identical fields '"+dataset_name_flds[i]+"' found in TDS dataset ", dataset_name
				print "Using constraints suggested that all fields in dataset are different. Skip constraints."
				exit (1)		
	for c in constr:
		if c is None:	continue
		for f in tmp_flds:
			if c==f:
				fndFlg = True
				break
		if not fndFlg:	return False
		fndFlg = False	
	return True				
		

def filter_TDS_dataset_name(dataset_name, constr, config):
# check constraints in datasets based on dataset_id format from esg.ini; 
#it's suggested that 1st field in dataset is project and if dataset_id format contains only one facet (project) 
# then all constraints except project are ignored.

	dataset_name_tkns = dataset_name.split(".")

	if len(filter(lambda x: x is not None, constr))>len(dataset_name_tkns):	return False
	
	if constr[0] is not None and dataset_name_tkns[0]!=constr[0]:	return False
	elif constr[0] == dataset_name_tkns[0] and constr[1] is None and constr[2] is None:
		return True

	dataset_name_tkns1 = dataset_name_tkns[1:]		# without project
	constr1 = constr[1:]
	  
	try:  # without project
		ds_frmt_flds = config.get("project:"+ dataset_name_tkns[0], "dataset_id", raw=True).split(".")
		ds_frmt_flds1 = ds_frmt_flds[1:]
	except	ConfigParser.NoSectionError:
		print "WARNING! Can not get dataset_id format from esg.ini for dataset " + dataset_name +". Skip it."
		return False

	if len(dataset_name_tkns1)!=len(ds_frmt_flds):
		print "ERROR! Dataset '" + dataset_name + "' does not correspond to dataset_id format in esg.ini:"
		print ".".join(f for f in ds_frmt_flds)
		print "Comparison is stopped."
		exit(1)
		
	constr_ctgs1 = map(lambda x, y: None if x is None else y, constr1, ["model","experiment"])  # project is skipped as it's verified directly
	constr_notnull_ctgs = filter(lambda x: x is not None, constr_ctgs1)  # categories correspondented to notnull constraints
	constr_notnull = filter(lambda x: x is not None, constr1)
	
	impl_ctgs = filter(lambda x: x.find("%(") >=0, ds_frmt_flds1)  # categories of general form (%(categ)s)
	for c in constr_notnull_ctgs:
		if len(filter(lambda x: c in x, impl_ctgs))==0:
			print "ERROR! Can not find facet '" + c + "' in esg.ini dataset_id format ",\
				 ".".join(f for f in ds_frmt_flds)
			exit(1)
	fndFlg = False
	
	for i in range(len(constr_notnull_ctgs)):
		fndFlg = False
		c = constr_notnull_ctgs[i]
		for j in range(len(ds_frmt_flds1)):
			if c in ds_frmt_flds1[j] and constr_notnull[i]==dataset_name_tkns1[j]:
				fndFlg = True	
				break
		if not fndFlg:	return False		
	return True			
	


def main(argv):

	global DB_Dict, TDS_Dict, Ref_XML_Errors, VERBOSE, SOLR_HTTP, rprt_fl, DBNoneValueURL, DB_Dict_Redund

	try:
		opts, args = getopt.getopt(argv, "ahve:m:p:l:", ['all', 'help', 'verbose', 'DT', 'SD', 'ST', 'log=', 'project=',  'model=', 'experiment='])
	except getopt.GetoptError:
		print sys.exc_value
		print usage
		sys.exit(1)
	
	CMP_FLG = 0	 
	Task_Message = "comparison all metadata sources: DB, TDS, Solr" 
	proj_cnstr = None
	model_cnstr = None
	exper_cnstr = None

	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')	
	fl_stmp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d.%H:%M:%S')	
	rprt_file_name = "meta_synchro." + fl_stmp + ".log"
	constr_categ = ["project","model","experiment"]
	if len(args) > 0:
			print "Wrong argumnet: ",  args[0]
			print usage
			exit(1)

	if len(opts) == 0:
		print usage
		exit(0)
		 
	for opt, arg in opts:
		if opt in ['-a', '--all']:
			proj_cnstr = None
			model_cnstr = None
			exper_cnstr = None
		elif opt in ['--DT']:
			CMP_FLG = 1
			Task_Message = "comparison DB <-> TDS" 
		elif opt in ['--SD']:
			CMP_FLG = 2
			Task_Message = "comparison Solr <-> DB" 
		elif opt in ['--ST']:
			CMP_FLG = 3
			Task_Message = "comparison Solr <-> TDS" 
		elif opt in ['-p', '--project']:
			proj_cnstr = arg
		elif opt in ['-m', '--model']:
			model_cnstr = arg
		elif opt in ['-e', '--experiment']:
			exper_cnstr = arg
		elif opt in ['-l', '--log']:
			rprt_file_name = arg
		elif opt in ['-v', '--verbose']:
			VERBOSE = True
		elif opt in ['-h', '--help']:
			print help_message
			exit(0)
		else:
			print "Wrong option: ", opt 
			print usage
			exit(1)
			
	rprt_fl = open(rprt_file_name,'w')
	rprt_fl.write(st)

	config = loadConfig(init_dir)
	
	engine = create_engine(config.getdburl('extract'), echo=echoSql, pool_recycle=3600)
	Session = sessionmaker(bind=engine, autoflush=True, autocommit=False)
	session = Session()

	# TDS_Dict = {ds_name:xml_ref_file}
	# DB_Dict = {ds_id:ds_name}
	# Solr_DS_Lst = [ds] 

	# DB_TDS_DIFF_DS = {"dataset_name ds_id":["Y", "N"], "dataset_name xml_rel_path":["N", "Y"]}
	# e.g.: {"cmip5.output1.NOAA-GFDL.GFDL-ESM2M.1pctCO2.mon.atmos.Amon.r1i1p2.v20130214 51" ["N","Y"], 
	#        "cmip5.output1.NOAA-GFDL.GFDL-ESM2M.abrupt4xCO2.day.atmos.day.r1i1p1 5213" ["Y", "N"], ...}
	# DB_TDS_Shared_DS_Dict = {"DB_dataset_id rel_xmlpath" : TDS ref_xml}
	
	DB_DS_URLS = {}
	DB_TDS_DIFF_DS = {}  
	Solr_Only_Files_Dict = {}
	DB_Only_Files_Dict = {}
	TDS_Only_Files_Dict = {}
	
	constr = (proj_cnstr, model_cnstr, exper_cnstr)

	if proj_cnstr is None and model_cnstr is None and exper_cnstr is None:	
		cnstr_msg = "No constraints: all datasets are going to be verified."
	else:
		cnstr_msg = "\nConstraints choosen: "
		for i in range(len(constr)):
			if constr[i] is not None:	
				cnstr_msg = cnstr_msg + "\n\t" + constr_categ[i] +": " + constr[i]
	print st			
	print "\n=================> Started ", Task_Message
	print "report ->", rprt_file_name
	print cnstr_msg	
		
	rprt_fl.write("\n\n"+Task_Message)
	rprt_fl.write("\n"+cnstr_msg+"\n")	

	if CMP_FLG != 3:  # PostgreSQL
		(DB_Dict, DB_Dict_Redund) = getDBDatasetDict(session, constr)
		print "\n=================> DB Dictionary (size= " + str(len(DB_Dict)) +")"
		if VERBOSE:
			print "\n".join((str(k) + " : " + DB_Dict[k]) for k in DB_Dict.keys())		
		rprt_fl.write("\n\n=================> DB Datasets (size= " + str(len(DB_Dict)) +")\n")
		if VERBOSE:
			rprt_fl.write( "\n".join((str(k) + " : " + DB_Dict[k]) for k in DB_Dict.keys()) )
	
		if len(DB_Dict_Redund)>0:
			rprt_fl.write("=====> DB table 'dataset' contains records (" + str(len(DB_Dict_Redund)) +\
						  ") with different ids but the same dataset name/version: =====")
			rprt_fl.write( "\n".join( (k + " " + DB_Dict_Redund[k]) for k in DB_Dict_Redund.keys() ) ) 
			
	if CMP_FLG != 2:   # THREDDS
		(TDS_Dict, TDS_Dict_Redund, TDS_Dict_Broken) = getTDSDatasetDict(config, constr)
		print "\n=================> TDS Dictionary (size= " + str(len(TDS_Dict)) +")"		
		rprt_fl.write("\n\n=================> TDS Datasets (size= " + str(len(TDS_Dict)) +")\n")
		if VERBOSE:
			print "\n".join((k + " : " + TDS_Dict[k]) for k in TDS_Dict.keys())		
			rprt_fl.write( "\n".join((k + " : " + TDS_Dict[k]) for k in TDS_Dict.keys()) )
		if len(TDS_Dict_Redund)>1:
			rprt_fl.write("=====> TDS_Dict_Redund: (the same dataset names are listed multple times in main TDS catalog: =====>\n") 
			rprt_fl.write("\n".join( (k + " : " + TDS_Dict_Redund[k]) for k in TDS_Dict_Redund.keys() ) )
		if len(TDS_Dict_Broken)>0:
			rprt_fl.write("=====> TDS_dataset names do not correspond to reference catalog xmls in main catalog. There are " + str (len(TDS_Dict_Broken)) + " records: =====>\n") 
			rprt_fl.write("\n".join( (k + " " + TDS_Dict_Broken[k]) for k in TDS_Dict_Broken.keys() ) ) 

	if CMP_FLG != 1:   # Solr
		(Solr_MultiVersion_DS, Solr_DS_Lst) = getSolrDatasetList(constr)
		print "\n=================> Solr Dataset List (size= " + str(len(Solr_DS_Lst)) + ")"
		if VERBOSE:
			print "\n".join(ds for ds in Solr_DS_Lst)		
		rprt_fl.write("\n\n=================> Solr Datasets (size= " + str(len(Solr_DS_Lst)) + ")\n")
		if VERBOSE:
			rprt_fl.write("\n".join(ds for ds in Solr_DS_Lst))
		if len(Solr_MultiVersion_DS) > 0:
			rprt_fl.write(" \n\n =======> These Datasets are reperesented in Solr in multiversions (only last version is used in comparison): =====>\n")
			rprt_fl.write("\n".join( (ds + " : [" + ", ".join(v for v in Solr_MultiVersion_DS[ds]) + "]") for ds in Solr_MultiVersion_DS.keys()))

	if (CMP_FLG == 1 or CMP_FLG == 0) and (len(DB_Dict)>0 or len(TDS_Dict)>0):
		DB_THREDDS_Comparison(DB_Dict,TDS_Dict, config, session)
	if (CMP_FLG == 2 or CMP_FLG == 0) and (len(DB_Dict)>0 or len(Solr_DS_Lst)>0):
		SOLR_DB_Comparison(Solr_DS_Lst, DB_Dict, SOLR_HTTP, session)	
	if (CMP_FLG == 3 or CMP_FLG == 0) and (len(TDS_Dict)>0 or len(Solr_DS_Lst)>0):
		SOLR_TDS_Comparison(Solr_DS_Lst, TDS_Dict, SOLR_HTTP, config)
		
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	print "\n",st
	rprt_fl.write("\n"+st)
	rprt_fl.close()
	session.close()
	
if __name__=='__main__':
	main(sys.argv[1:])
	
