import sys
parts = sys.argv[1].split('.')
template='/p/user_pub/work/input4MIPs/CMIP6/C4MIP/ImperialCollege/ImperialCollege_yr_{}_{}_gm_v20200914.json'
print(template.format(parts[4],parts[7]))
