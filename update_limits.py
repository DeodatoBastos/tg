import yaml
import shutil
import sys

def add_limits(filepath, services_to_limit):
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

# Postgre
add_limits('/home/deodato/ita/CSC27/tg/postgre/docker-compose.yml', ['postgres'])

# Citus Simple
add_limits('/home/deodato/ita/CSC27/tg/citus/docker-compose.yml', ['coordinator', 'worker1', 'worker2'])

# Citus Patroni
try:
    add_limits('/home/deodato/ita/CSC27/tg/citus/docker-compose-patroni.yml', 
               ['citus_coordinator1', 'citus_worker1', 'citus_worker2', 'citus_worker3'])
except Exception as e:
    print("Error updating patroni:", e)
