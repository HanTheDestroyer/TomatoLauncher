# start by importing necessary libraries.
import numpy as np
import pandas as pd
import settings as st
from time import sleep
import colorama
from colorama import Fore, Style
import pygame as pg
import sys


# initialize Simulation class to handle pygame
class Simulation:
    def __init__(self):
        pg.init()
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode(np.array(st.screen_size, dtype='int16'))
        self.screen.fill(pg.Color('black'))
        self.launcher = TomatoLauncher(self.screen)

    def update(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            self.logic()
            pg.display.update()

    def logic(self):
        self.launcher.search()


# targets are stored in another class
class Target:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.destroyed = False

    def move(self):
        self.pos += self.vel

    def draw(self, screen):
        if self.destroyed is False:
            radius = np.max([int((self.pos[2] + 150) / 15), 1])
            pg.draw.circle(surface=screen,
                           center=self.pos[0:2].astype(np.int32),
                           radius=radius,
                           color=np.array([255, 255, 255]))

    def __repr__(self):
        return 'tomato'


# initialize TomatoLauncher class.
# it takes targets as input.
# assumption: It can only see 0.1 radians of area in front of its nozzle at a given time.
# assumption: It is fast enough to change directions instantaneously.
# assumption: Its calculations are instant.
class TomatoLauncher:
    def __init__(self, screen):
        colorama.init()
        self.screen = screen
        self.xy_angular_nozzle_speed = np.float16(-0.05)
        self.max_tomato_velocity_mag = np.float16(20)
        self.gravity = st.gravity
        # Where launcher is located.
        self.position = np.array([st.screen_size[0] / 2,
                                  st.screen_size[1] / 2, 0], dtype=float)
        self.nozzle_dir = np.array([1, 0])  # Where launcher is looking on xy plane.
        self.flight_time = np.float16(10)  # Tomatoes can fly for ten seconds.
        self.targets = []
        self.read_dataset()

    def read_dataset(self):
        """reads the dataset created by dataset.py."""
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
        sleep(0.05)
        old_dir = self.nozzle_dir.copy()
        old_angle = np.degrees(np.arctan2(old_dir[1], old_dir[0])) + 180
        # update positions of targets and nozzle dir
        self.nozzle_dir = self.rotate_vector(self.nozzle_dir, self.xy_angular_nozzle_speed)
        new_angle = np.degrees(np.arctan2(self.nozzle_dir[1], self.nozzle_dir[0])) + 180
        max_angle = np.max([old_angle, new_angle])
        min_angle = np.min([old_angle, new_angle])
        print(Fore.LIGHTGREEN_EX + f'checking between angles ' + Fore.YELLOW + f'{old_angle}'
              + Fore.LIGHTGREEN_EX + ' and ' + Fore.YELLOW + f'{new_angle}' + Style.RESET_ALL)
        for t in self.targets:
            t.move()
        # check if there are any targets between old and new angles.
        self.draw(old_dir, self.nozzle_dir)
        for counter, target in enumerate(self.targets):
            relative_target_pos = target.pos - self.position
            target_angle = np.degrees(np.arctan2(relative_target_pos[1], relative_target_pos[0])) + 180
            key = False
            if np.abs(max_angle - min_angle) < 10:
                if min_angle <= target_angle <= max_angle:
                    key = True
            else:
                if max_angle <= target_angle <= 360:
                    key = True
                if 0 <= target_angle <= min_angle:
                    key = True
            if key:
                print(Fore.CYAN + f'found target ' + Fore.YELLOW + f'@{target_angle}' + Style.RESET_ALL)
                self.nozzle_dir = self.destroy(counter)
                del self.targets[counter]

    def calculate_initial_vy(self, vector1, vector2, time):
        return (1 / time) * (vector2 - vector1 - 0.5 * self.gravity * (time ** 2))

    def destroy(self, hit):
        # this part requires a few assumptions.
        # the time of collision, velocity of tomato and position of target at the time of collision are unknown.
        # Assumption: Tomato Launcher is set in a way such that it always hits target within 8 frames.
        # Assumption: Tomato Launcher requires 2 frames to set its nozzle in target's desired direction.
        # Assumption: Tomato Launcher has to be reloaded for 8 frames once it has shot.
        # last assumption assures that within the eight frames of flight time, it doesn't move.
        desired_target_pos = self.targets[hit].pos + self.targets[hit].vel * self.flight_time
        distance = desired_target_pos - self.position
        tomato_velocity = np.array([1, 1, 1], dtype=float)
        tomato_velocity[0:2] = distance[0:2] / (8)
        tomato_velocity[2] = self.calculate_initial_vy(self.position[2], desired_target_pos[2], self.flight_time - 2)
        print(Fore.LIGHTRED_EX + f'Taking shot. Tomato velocity is '
              + Fore.LIGHTWHITE_EX + f'{tomato_velocity}' + Style.RESET_ALL)
        tomato_position = self.position.copy()
        frame_counter = 0
        while True:
            # note that tomato takes 2 frames to be shot. Frame 0 and Frame 1.
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            self.draw(tomato_velocity[0:2], tomato_velocity[0:2])
            sleep(0.15)
            if frame_counter > 1:
                tomato_position[2] += tomato_velocity[2] + 0.5 * self.gravity
                tomato_position[0:2] += tomato_velocity[0:2]
                tomato_velocity[2] += self.gravity
            for t in self.targets:
                t.move()
            print(Fore.RED + f'Tomato at {tomato_position}' + Style.RESET_ALL)
            print(Fore.CYAN + f'Target at {self.targets[hit].pos}')

            curr_distance = np.linalg.norm(tomato_position - self.targets[hit].pos)
            if curr_distance < 1:
                print(f'Tomato hit target with positional difference of {curr_distance}')
                break
            frame_counter += 1
        return self.get_direction(tomato_position - self.position)

    def draw(self, old_dir, new_dir):
        self.screen.fill(pg.Color('black'))
        for t in self.targets:
            t.draw(self.screen)
        end_pos = self.position[0:2] + 10000 * new_dir
        end_pos2 = self.position[0:2] + 10000 * old_dir

        pg.draw.line(surface=self.screen,
                     width=1,
                     color=np.array([255, 0, 0]),
                     start_pos=self.position[0:2].astype(np.int32),
                     end_pos=end_pos)
        pg.draw.line(surface=self.screen,
                     width=1,
                     color=np.array([0, 255, 0]),
                     start_pos=self.position[0:2].astype(np.int32),
                     end_pos=end_pos2)
        pg.draw.circle(surface=self.screen,
                       color=np.array([255, 255, 0]),
                       radius=10,
                       center=self.position[0:2])
        pg.display.update()


if __name__ == '__main__':
    simulation = Simulation()
    simulation.update()
