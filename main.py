import argparse
import os
import pandas as pd
import yaml

from datetime import datetime

from utils import run_experiment

def main(config):
    '''
    Setting up experiment configurations and storage paths.
    '''
    # Name of experiment
    simulation_type = config['SIMULATION_TYPE']

    # Get storage paths
    experiments_folder = 'experiments'
    if not os.path.isdir(experiments_folder):
        os.makedirs(experiments_folder)

    simulations_folder = f'{experiments_folder}/{simulation_type}'
    if not os.path.isdir(simulations_folder):
        os.makedirs(simulations_folder)

    # Assign a unique run id based on records file and add it to config
    records_file = f'{simulations_folder}/records.csv'
    if not os.path.isfile(records_file):
        with open(records_file, 'w+') as recordsfile:
            recordsfile.write('RUN_ID,')
            for key in config.keys():
                recordsfile.write(key + ',')
            recordsfile.write('TIMESTAMP\n')

    df_records = pd.read_csv(records_file)
    if len(df_records) == 0:
        unique_runid = 1
    else:
        unique_runid = str(max(df_records['RUN_ID'])+1)
    config['RUN_ID'] = unique_runid

    # Add current time to config
    now = datetime.now()
    current_time = now.strftime('%Y%m%d_%H%M%S')
    config['TIMESTAMP'] = current_time

    # Create output folder
    output_folder = f'{simulations_folder}/output_{unique_runid}'
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # Store config file
    with open(f'{output_folder}/{unique_runid}_config.yaml', 'w') as configfile:
        yaml.dump(config, configfile, sort_keys=True)

    # Update records file
    df_records = pd.concat([df_records, pd.DataFrame.from_dict(config, orient='index').T], ignore_index=True)
    df_records.to_csv(f'{records_file}', index=False)

    '''
    Running and recording the simulations.
    '''
    params = {'run_id': unique_runid,
              'output_folder': output_folder,
              'simulation_type': simulation_type,
              'no_iteration': config['NO_ITERATION'],
              'period_runin': config['PERIOD_RUNIN'],
              'no_beds': config['NO_BEDS'],
              'no_clinicians': config['NO_CLINICIANS'],
              'no_imaging': config['NO_IMAGING'],
              'hourly_arrival_rate': config['HOURLY_ARRIVAL_RATE'],
              'process_model': config['PROCESS_MODEL'],
              'path_cohort_frequency': config['COHORT_FREQUENCY'],
              'increase_arrival': config['INCREASE_ARRIVAL'],
              'increase_resource': config['INCREASE_RESOURCE'],
              'increase_workflow': config['INCREASE_WORKFLOW'],
              'path_test_data': config['DATA_TEST'],
              }

    if 'real' in simulation_type:
        run_experiment(params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', type=str, required=True)
    args = parser.parse_args()

    # Get config file
    config_file = args.file
    assert os.path.isfile(config_file), 'Create config.yaml file'
    with open(f'{config_file}') as configfile:
        config = yaml.safe_load(configfile)

    main(config)
