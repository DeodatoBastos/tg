import yaml
import shutil

filepath = '/home/deodato/ita/CSC27/tg/citus/docker-compose-patroni.yml'
services_to_limit = [
    'coordinator1', 'coordinator2', 'coordinator3',
    'worker1_primary', 'worker1_standby',
    'worker2_primary', 'worker2_standby'
]

shutil.copy(filepath, filepath + '.bak')
with open(filepath, 'r') as f:
    data = yaml.safe_load(f)

modified = False
for service_name, service_cfg in data.get('services', {}).items():
    if service_name in services_to_limit:
        service_cfg['cpus'] = 2.0
        service_cfg['mem_limit'] = '4g'
        modified = True
        
if modified:
    with open(filepath, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)
    print(f"Updated {filepath}")
else:
    print(f"No changes made to {filepath}")
