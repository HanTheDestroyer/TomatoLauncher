# start by importing necessary libraries.
import numpy as np
import pandas as pd
import settings as st
from time import sleep
import colorama
from colorama import Fore, Style



# initialize TomatoLauncher class.
# it takes targets as input.
# assumption: It can only see 0.1 radians of area in front of its nozzle at a given time.
# assumption: It is fast enough to change directions instantaneously.
# assumption: Its calculations are instant.
class TomatoLauncher:
    def __init__(self):
        colorama.init()
        self.xy_angular_nozzle_speed = np.float16(-0.1)
        self.max_tomato_velocity_mag = np.float16(20)
        self.position = np.array([0, 0, 0], dtype=float)  # Where launcher is located.
        self.nozzle_dir = np.array([1, 0])  # Where launcher is looking on xy plane.
        self.flight_time = np.float16(10)  # Tomatoes can fly for ten seconds.
        self.targets = []
        self.read_dataset()
        pass

    # reads the dataset created by dataset.py.
    def read_dataset(self):
        targets = pd.read_csv('targets.csv')
        targets_pos_x = targets['x_Position'].values.astype(float)
        targets_pos_y = targets['y_Position'].values.astype(float)
        targets_pos_z = targets['z_Position'].values.astype(float)
        targets_vel_x = targets['x_Velocity'].values.astype(float)
        targets_vel_y = targets['y_Velocity'].values.astype(float)
        targets_vel_z = targets['z_Velocity'].values.astype(float)

        for t in range(st.number_of_targets):
            pos = np.array([targets_pos_x[t], targets_pos_y[t], targets_pos_z[t]], dtype='float32')
            vel = np.array([targets_vel_x[t], targets_vel_y[t], targets_vel_z[t]], dtype='float32')
            self.targets.append(Target(pos=pos, vel=vel))

    def show_targets(self):
        pass

    @staticmethod
    def rotate_vector(vector, angle):  # Rotates XY plane by an angle.
        rotation_matrix = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
        rotated_vector = np.dot(rotation_matrix, vector)
        return rotated_vector

    @staticmethod
    def get_direction(vector):
        vector = vector[0:2]
        vector_abs = np.abs(vector)
        vector_mag = np.sum(vector_abs)
        return vector / vector_mag

    def search(self):  # system slowly turns and searches between two angles.

        while self.targets:
            old_dir = self.nozzle_dir.copy()
            old_angle = np.arctan2(old_dir[1], old_dir[0])
            # update positions of targets and nozzle dir
            self.nozzle_dir = self.rotate_vector(self.nozzle_dir, self.xy_angular_nozzle_speed)
            sleep(0.1)
            new_angle = np.arctan2(self.nozzle_dir[1], self.nozzle_dir[0])
            max_angle = np.max([old_angle, new_angle])
            min_angle = np.min([old_angle, new_angle])
            print(Fore.LIGHTGREEN_EX + f'checking between angles ' + Fore.YELLOW + f'{old_angle}'
                  + Fore.LIGHTGREEN_EX + ' and ' + Fore.YELLOW + f'{new_angle}' + Style.RESET_ALL)
            for t in self.targets:
                t.move()

            # check if there are any targets between old and new angles.
            if np.abs(max_angle - min_angle) > 0.2:
                # Don't want to deal with it. Sue me.
                continue
            for counter, target in enumerate(self.targets):
                target_angle = np.arctan2(target.pos[1], target.pos[0])
                if min_angle <= target_angle <= max_angle:
                    print(Fore.CYAN + f'found target ' + Fore.YELLOW + f'@{target_angle}' + Style.RESET_ALL)
                    self.nozzle_dir = self.destroy(counter)
                    del self.targets[counter]

    def destroy(self, hit):
        # this part requires a few assumptions.
        # the time of collision, velocity of tomato and position of target at the time of collision are unknown.
        # Assumption: Tomato Launcher is set in a way such that it always hits target within 8 frames.
        # Assumption: Tomato Launcher requires 2 frames to set its nozzle in target's desired direction.
        # Assumption: Tomato Launcher has to be reloaded for 8 frames once it has shot.
        # last assumption assures that within the eight frames of flight time, it doesn't move.

        # calculate the distance between nozzle and target at desired position.
        desired_target_pos = self.targets[hit].pos + self.targets[hit].vel * self.flight_time
        distance = desired_target_pos - self.position
        tomato_velocity = distance / (self.flight_time - 2)
        print(Fore.LIGHTRED_EX + f'Taking shot. Tomato velocity is '
              + Fore.LIGHTWHITE_EX + f'{tomato_velocity}' + Style.RESET_ALL)
        tomato_position = self.position.copy()
        frame_counter = 0
        while True:
            # note that tomato takes 2 frames to be shot. Frame 0 and Frame 1.
            sleep(0.1)
            if frame_counter > 1:
                tomato_position += tomato_velocity
            # self.targets[hit].move()

            for t in self.targets:
                t.move()
            print(Fore.RED + f'Tomato at {tomato_position}' + Style.RESET_ALL)
            print(Fore.CYAN + f'Target at {self.targets[hit].pos}')
            curr_distance = np.linalg.norm(tomato_position - self.targets[hit].pos)
            if curr_distance < 1:
                print(f'Tomato hit target with positional difference of {curr_distance}')
                break
            frame_counter += 1
        return self.get_direction(tomato_position)


# initialize Target class.
# it takes positional and velocity data as input. They both have to be np.array objects.
class Target:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel

    def move(self):
        self.pos += self.vel

    def __repr__(self):
        return 'tomato'


if __name__ == '__main__':
    a = TomatoLauncher()
    a.show_targets()
    a.search()
