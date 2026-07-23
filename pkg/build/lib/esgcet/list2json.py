from datetime import datetime

DRS = { 'CMIP6' : [ 'mip_era' , 'activity_drs','institution_id','source_id','experiment_id','member_id','table_id','variable_id','grid_label', 'version' ] }


from random import sample

def get_rand_lines(infile, count):

	return sample([line for line in infile], count)


def list_to_json(in_arr, node, **kwargs):

	increment = False
	if ('increment' in kwargs and kwargs['increment']):
		increment=True
	ret = []
	for line in in_arr:

		parts = line.split('.')

		key = parts[0]
		facets = DRS[key]
		d = {}
		for i, f in enumerate(facets):
			d[f] = parts[i]

		d['data_node'] = node
		d['index_node'] = node
		DRSlen = len(DRS[key])
		if increment:
			newvers = int(d['version'][1:]) + 1 
			d['version'] = newvers
			prev_id = '.'.join(parts[0:DRSlen])
			instance_id = '.'.join(parts[0:DRSlen - 1] + ['v' + str(newvers)])
			d['prev_id'] = prev_id
		else:
			instance_id = '.'.join(parts[0:DRSlen])
			d['version'] = d['version'][1:]
		d['instance_id'] = instance_id
		d['master_id'] = '.'.join(parts[0:DRSlen-1])
		d['id'] = instance_id + '|' + node
		d['title'] = instance_id
		d['replica'] = 'false'
		d['latest'] = 'true'
		d['type'] = 'Dataset'
		d['project'] = key + '-test'

		ret.append(d)

	return ret


def gen_xml(d):
    out = []
    out.append("<doc>\n")
    for key in d:

        val = d[key]
        if key == "description":
            val = ' '.join(val)
            out.append('  <field name="{}">{}</field>\n'.format(key, val))
        elif type(val) is list:
            for vv in val:
               out.append('  <field name="{}">{}</field>\n'.format(key, vv))
        else:
            out.append('  <field name="{}">{}</field>\n'.format(key, val))
    out.append("</doc>\n")
    return ''.join(out)

def write_xml(fn, txt, *args):
    pp = ""
    if len(args) > 0:
        pp = args[1]
    with open(pp + '/' + fn, 'w') as f:
        f.write(txt)


def gen_hide_xml(id, *args):

    dateFormat = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.utcnow()
    ts = now.strftime(dateFormat)
    txt =  """<updates core="datasets" action="set">
        <update>
          <query>instance_id={}</query>
          <field name="latest">
             <value>false</value>
          </field>
          <field name="_timestamp">
             <value>{}</value>
          </field>
        </update>
    </updates>
    \n""".format(id, ts)

    return txt

import sys

def main():
	d = list_to_json(get_rand_lines(sys.stdin, int(sys.argv[1])), 'esgf-test-data.llnl.gov', increment=True)

	path_prefix = ""

	if len(sys.argv) > 2:

		path_prefix = sys.argv[2]

	for rec in d:
		gen_hide_xml(rec['prev_id'], path_prefix)
		gen_xml(path_prefix+rec['instance_id'] + '.xml', rec)



if __name__ == '__main__':
	main()



