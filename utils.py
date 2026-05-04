import pandas as pd

from environment import EDModel

def single_sample(params):
    simulation_type = params['simulation_type']

    if 'real' in simulation_type:
        output_folder = params['output_folder']

        model = EDModel(**params)
        while True:
            model.step()

            day_now = model._get_time_in_days()
            if day_now > 30:
                model.running = False
                break

        df_synthetic_ehrs = pd.DataFrame.from_dict(model.synthetic_ehrs, orient='index')
        df_synthetic_ehrs = df_synthetic_ehrs.head(len(model.df_test))
        df_synthetic_ehrs.to_csv(f'{output_folder}/synthetic_ehr.csv', index=False)

        return None

def run_experiment(params):
    simulation_type = params['simulation_type']

    if 'real' in simulation_type:
        no_iterations = params['no_iteration']

        results_list = []
        for iter_idx in range(no_iterations):
            results = single_sample(params)
            results_list.append(results)

        return results_list