
import numpy as np
import pandas as pd
import settings as st


def generate_targets_dataset():
    columns = ['x_Position', 'y_Position', 'z_Position', 'x_Velocity', 'y_Velocity', 'z_Velocity']
    targets = {
        'x_Position': np.random.uniform(200, 760, st.number_of_targets),
        'y_Position': np.random.uniform(200, 440, st.number_of_targets),
        'z_Position': np.random.uniform(-100, 100, st.number_of_targets),
        'x_Velocity': np.random.uniform(-st.max_velocity, st.max_velocity, st.number_of_targets),
        'y_Velocity': np.random.uniform(-st.max_velocity, st.max_velocity, st.number_of_targets),
        'z_Velocity': np.random.uniform(-st.max_velocity, st.max_velocity, st.number_of_targets),
    }
    targets = pd.DataFrame(targets)
    targets.to_csv('targets.csv', index=False)


def read_dataset(dataset):
    targets = pd.read_csv(dataset)
    targets_pos_x = targets['x_Position'].values
    targets_pos_y = targets['y_Position'].values
    targets_pos_z = targets['z_Position'].values

    targets_vel_x = targets['x_Velocity'].values
    targets_vel_y = targets['y_Velocity'].values
    targets_vel_z = targets['z_Velocity'].values

    target_vel = np.zeros([st.number_of_targets, 3])
    target_pos = np.zeros([st.number_of_targets, 3])
    for target in range(st.number_of_targets):
        target_pos[target] = np.array([targets_pos_x[target], targets_pos_y[target], targets_pos_z[target]])
        target_vel[target] = np.array([targets_vel_x[target], targets_vel_y[target], targets_vel_z[target]])

    return target_pos, target_vel


if __name__ == '__main__':
    generate_targets_dataset()

