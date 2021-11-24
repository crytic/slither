from collections import defaultdict
from flask import Flask,render_template,request,redirect, templating,url_for,jsonify,json
import os,sys
from flask.helpers import make_response
import jinja2.exceptions
from werkzeug.utils import secure_filename
import json
import re

UPLOAD_FOLDER = './files/'
ALLOWED_EXTENSIONS = set(['sol'])

app=Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/', methods=['GET'])	
def index():
	return render_template('index.html')

printers = ['call-graph', 'cfg', 'constructor-calls', 'contract-summary','data-dependency',
            'function-id','human-summary','inheritance','inheritance-graph','slithir','vars-and-auth']

detectors = ['all','abiencoderv2-array','addition-uint-overflow','adress-not-exist-set','adress-not-exist-transfer','arbitrary-send','array-by-reference',
			'assembly','assert-state-change','boolean-cst','boolean-equal','byte',
			'calls-loop','complex-fallback','constable-states','constant-function-asm','constant-function-state',
			'controlled-array-length','controlled-delegatecall','costly-loop','dead-code','delete-array',
			'deprecated-standards','divide-before-multiply','do-continue-while','enum-conversion','erc20-indexed',
			'erc20-interface','erc721-interface','events-access','events-maths','external-function',
			'function-init-state','hash-collision','implicit-visibility','incorrect-equality','incorrect-modifier','incorrect-shift',
			'incorrect-unary','inheritance-order','invariant-in-loop','locked-ether','low-level-calls','mapping-deletion',
			'missing-inheritance','missing-zero-check','multiple-constructors','multiplication-uint-overflow','name-reused',
			'naming-convention','pragma','public-mappings-nested','redundant-statements',
			'reentrancy-benign','reentrancy-eth','reentrancy-events','reentrancy-no-eth',
			'reentrancy-unlimited-gas','reused-constructor','rtlo','shadowing-abstract',
			'shadowing-builtin','shadowing-local','shadowing-state','sig-wrong-para','signedness','similar-names',
			'solc-version','storage-array','suicidal','tautology','timestamp','too-many-digits',
			'tod-amount','tod-erc20','tod-receiver','tod-transfer','truncation',
			'tx-origin','uint-underflow','unchecked-lowlevel','unchecked-send','unchecked-transfer',
			'unimplemented-functions','uninitialized-fptr-cst','uninitialized-local','uninitialized-state',
			'uninitialized-storage','unprotected-upgrade','unused-return','unused-state',
			'variable-scope','void-cst','weak-prng','write-after-write']

solc = ['0.8.6','0.8.5','0.8.4','0.8.3','0.8.2','0.8.1','0.8.0',
		'0.7.6','0.7.5','0.7.4','0.7.3','0.7.2','0.7.1','0.7.0',
		'0.6.12','0.6.11','0.6.10','0.6.9','0.6.8','0.6.7',
		'0.6.6','0.6.5','0.6.4','0.6.3','0.6.2','0.6.1','0.6.0',
		'0.5.17','0.5.16','0.5.15','0.5.14','0.5.13',
		'0.5.12','0.5.11','0.5.10','0.5.9','0.5.8','0.5.7',
		'0.5.6','0.5.5','0.5.4','0.5.3','0.5.2','0.5.1','0.5.0',
		'0.4.26','0.4.25','0.4.24','0.4.23','0.4.22','0.4.21','0.4.20',
		'0.4.19','0.4.18','0.4.17','0.4.16','0.4.15','0.4.14','0.4.13',
		'0.4.12','0.4.11','0.4.10','0.4.9','0.4.8','0.4.7',
		'0.4.6','0.4.5','0.4.4','0.4.3','0.4.2','0.4.1','0.4.0']

net = ['ethereum','ropsten','kovan','rinkeby','goerli']


#insure security of upload file (avoid user upload virus...)
#check file sub filename
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS



@app.route('/detect_file', methods=['POST'])
def detect_file():
	if request.method == 'POST':
		detector=request.form.get('str')
		solc = request.form['select_solc']
		file = request.files['result_data']   #get file 
		
		if file and allowed_file(file.filename):
			#avoid Directory traversal attack 
			#Ex : /../../../filename
			filename = secure_filename(file.filename)

			
			file.save(os.path.join(app.config['UPLOAD_FOLDER'] , filename))

			solc_cmd = "solc-select use {0}".format(solc)

			tool_cmd = "slither  {0} ".format(UPLOAD_FOLDER+filename)

			det_cmd = ""
			if detector != "":
				det_cmd = "  --detect {0}".format(detector)

			json_cmd = "  --json {0}.json".format(os.path.join(app.config['UPLOAD_FOLDER'] , filename))

			total_cmd = solc_cmd + " && " + tool_cmd + det_cmd + json_cmd
			os.system(total_cmd)
			
			json_url = "{0}.json".format(os.path.join(app.config['UPLOAD_FOLDER'] , filename))

			with open(json_url,'r') as reader :
				jf=json.loads(reader.read())


			if jf['success'] == False:
				return render_template('fail.html')

			if jf['results']=={}:
				return render_template('no_bugs.html')

			data={}
			title=[]
			total_num=0
			optimization_num=0
			informational_num=0
			low_num=0
			medium_num=0
			high_num=0
			for i in range(len(jf['results']['detectors'])):
				str1 = "{0}".format(jf['results']['detectors'][i]['check'])
				str2 = "{0}".format(jf['results']['detectors'][i]['description'])

				str2 = str2.split('\n')

				total_num+=1
				impact=jf['results']['detectors'][i]['impact']
				if impact=="Optimization":
					optimization_num+=1
				elif impact=="Informational":
					informational_num+=1
				elif impact=="Low":
					low_num+=1
				elif impact=="Medium":
					medium_num+=1
				else:
					high_num+=1


				if len(title) > 0 and str1 == title[-1]:
					data[str1] += [str2]
					continue
				
				else:
					title.append(str1)
					data[str1] = [str2]

		return render_template('result.html',data=data,title=title,total_num=total_num,optimization_num=optimization_num,
					informational_num=informational_num,low_num=low_num,medium_num=medium_num,high_num=high_num)
			
@app.route('/detect_file', methods=['GET','POST'])
def detect_file_dropdown_list():
	rm_cmd = "rm -fr ./files/*"
	os.system(rm_cmd)
	return render_template('detect_file.html', detectors=detectors,solc = solc)



@app.route('/detect_address', methods=['POST'])
def detect_address():
	if request.method == 'POST':
		detector=request.form.get('str')
		solc = request.form['select_solc']
		addr = request.form['address']
		net = request.form['select_net']

		solc_cmd = "solc-select use {0}".format(solc)

		if net=='ethereum':
			tool_cmd = "slither  {0}".format(addr)
		else:
			tool_cmd = "slither  {0}:{1}".format(net,addr)

		det_cmd = ""
		if detector != "":
			det_cmd = "  --detect {0}".format(detector)

		json_cmd = "  --json {0}.json".format(os.path.join(app.config['UPLOAD_FOLDER'] , addr))

		total_cmd = solc_cmd + " && " + tool_cmd + det_cmd + json_cmd
		os.system(total_cmd)
		json_url = "{0}.json".format(os.path.join(app.config['UPLOAD_FOLDER'] , addr))

		with open(json_url,'r') as reader :
			jf=json.loads(reader.read())


		if jf['success'] == False:
			return render_template('fail.html')

		if jf['results']=={}:
				return render_template('no_bugs.html')

		data={}
		title=[]
		total_num=0
		optimization_num=0
		informational_num=0
		low_num=0
		medium_num=0
		high_num=0
		for i in range(len(jf['results']['detectors'])):
			str1 = "{0}".format(jf['results']['detectors'][i]['check'])
			str2 = "{0}".format(jf['results']['detectors'][i]['description'])

			str2 = str2.split('\n')


			total_num+=1
			impact=jf['results']['detectors'][i]['impact']
			if impact=="Optimization":
				optimization_num+=1
			elif impact=="Informational":
				informational_num+=1
			elif impact=="Low":
				low_num+=1
			elif impact=="Medium":
				medium_num+=1
			else:
				high_num+=1

			if len(title) > 0 and str1 == title[-1]:
				data[str1] += [str2]
				continue
				
			else:
				title.append(str1)
				data[str1] = [str2]

	return render_template('result.html',data=data,title=title,total_num=total_num,optimization_num=optimization_num,
					informational_num=informational_num,low_num=low_num,medium_num=medium_num,high_num=high_num)

@app.route('/detect_address', methods=['GET','POST'])
def detect_address_dropdown_list():
	rm_cmd = "rm -fr ./files/*"
	os.system(rm_cmd)
	return render_template('detect_address.html', detectors=detectors,solc=solc,net=net)



@app.route('/print_file', methods=['POST'])
def print_file():
	if request.method == 'POST':
		solc = request.form['select_solc']
		printer=request.form['printers']
		file = request.files['result_data']   #get file 
		
		if file and allowed_file(file.filename):
			#avoid Directory traversal attack 
			#Ex : /../../../filename
			filename = secure_filename(file.filename)

			f=os.path.join(app.config['UPLOAD_FOLDER'] , filename)
			file.save(f)
			solc_cmd = "solc-select use {0}".format(solc)

			tool_cmd = " && slither  {0} --print {1}".format(f,printer)

			json_cmd = " --json {0}.json".format(f)
			total_cmd = solc_cmd + tool_cmd + json_cmd
			os.system(total_cmd)

			json_url = "{0}.json".format(f)
			with open(json_url,'r') as reader :
				jf=json.loads(reader.read())


			if jf['success'] == False:
				return render_template('fail.html')

			if printer=="call-graph" or printer=="cfg" or printer=="inheritance-graph":
				img_url = []
				for i in range(len(jf['results']['printers'][0]['elements'])):
					dot_filename = jf['results']['printers'][0]['elements'][i]['name']['filename']
					
					rename=dot_filename
					rename_cmd=""
					if printer =="cfg":
						index = rename.find('(')
						rename = rename[:index] + '\\' + rename[index:]
						index = rename.find(')')
						rename = rename[:index] + '\\' + rename[index:]

					dot_cmd = "dot {0} -Tpng -o {1}.png".format(rename,rename)
					rm_cmd = " && mv {0}.png ./static/result/".format(rename)
					os.system(rename_cmd + dot_cmd + rm_cmd)
					dot_filename = dot_filename[8:]
					img = "./static/result/{0}.png".format(dot_filename)
					img_url.append(img)
					return render_template('printer_png_result.html' , printer = printer, img_url=img_url)

			elif printer=="contract-summary" or printer=="data-dependency" or printer=="constructor-calls" or \
				printer=="function-id" or printer =="human-summary" or printer =="inheritance" or printer=="vars-and-auth" or printer=="slithir":
				result = "{0}".format(jf['results']['printers'][0]['description'])
				result = result.replace('[0m', '') 
				result = result.replace('[92m', '') 
				result = result.replace('[94m', '') 
				result = result.split('\n')
				
				return render_template('printer_result.html' , printer = printer, result=result)

	return render_template("404.html")

@app.route('/print_file', methods=['GET','POST'])
def print_file_dropdown_list():
	rm_cmd = "rm -fr ./files/* && rm -fr ./static/result/*"
	os.system(rm_cmd)
	return render_template('print_file.html', printers=printers,solc=solc)


@app.route('/print_address', methods=['POST'])
def print_address():
	if request.method == 'POST':
		solc = request.form['select_solc']
		printer=request.form['printers']
		addr = request.form['address'] 
		net = request.form['select_net']
		
		solc_cmd = "solc-select use {0}".format(solc)

		if net=='ethereum':
			tool_cmd = "slither  {0}".format(addr)
		else:
			tool_cmd = "slither  {0}:{1}".format(net,addr)
		
		print_cmd = " --print {0}".format(printer)

		f=os.path.join(app.config['UPLOAD_FOLDER'] , addr)
		json_cmd = "  --json {0}.json".format(f)

		total_cmd = solc_cmd + " && " + tool_cmd  + print_cmd +json_cmd
		os.system(total_cmd)

		json_url = "{0}.json".format(f)
		with open(json_url,'r') as reader :
			jf=json.loads(reader.read())

		if jf['success'] == False:
			return render_template('fail.html')

		if printer=="call-graph" or printer=="cfg" or printer=="inheritance-graph":
			img_url = []
			for i in range(len(jf['results']['printers'][0]['elements'])):
				dot_filename = jf['results']['printers'][0]['elements'][i]['name']['filename']
					
				rename=dot_filename
				rename_cmd=""
				if printer =="cfg":
					index = rename.find('(')
					rename = rename[:index] + '\\' + rename[index:]
					index = rename.find(')')
					rename = rename[:index] + '\\' + rename[index:]

				#mv_cmd = "mv {0} ./files/".format(dot_filename)
				#rename = "./files/{0}".format(dot_filename)
				dot_cmd = "dot {0} -Tpng -o {1}.png".format(rename,rename)
				rm_cmd = " && mv {0}.png ./static/result/".format(rename)
				os.system(rename_cmd + dot_cmd + rm_cmd)
				img = "./static/result/{0}.png".format(dot_filename)
				img_url.append(img)
			return render_template('printer_png_result.html' , printer = printer, img_url=img_url)

		elif printer=="contract-summary" or printer=="data-dependency" or printer=="constructor-calls" or \
			printer=="function-id" or printer =="human-summary" or printer =="inheritance" or printer=="vars-and-auth" or printer=="slithir":
			result = "{0}".format(jf['results']['printers'][0]['description'])
			result = result.replace('[0m', '') 
			result = result.replace('[92m', '') 
			result = result.replace('[94m', '') 
			result = result.split('\n')
				
			return render_template('printer_result.html' , printer = printer, result=result)

	return render_template("404.html")

@app.route('/print_address', methods=['GET','POST'])
def print_address_dropdown_list():
	rm_cmd = "rm -fr ./files/* && rm -fr ./static/result/*"
	os.system(rm_cmd)
	return render_template('print_address.html', printers=printers,solc=solc , net = net)

@app.route('/<pagename>')
def admin(pagename):
    return render_template(pagename+'.html')

@app.errorhandler(jinja2.exceptions.TemplateNotFound)
def template_not_found(e):
    return not_found(e)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')

if __name__ == "__main__":
    app.run(debug=True)
