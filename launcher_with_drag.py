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
        while self.launcher.targets:
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
# assumption: It can only see a set area in front of its nozzle at a given time in radians.
# assumption: It is fast enough to change directions instantaneously when it sees a target.
# assumption: Its calculations are instant.
class TomatoLauncher:
    def __init__(self, screen):
        colorama.init()
        self.screen = screen
        self.xy_angular_nozzle_speed = np.float16(-0.05)
        self.max_tomato_velocity_mag = np.float16(20)
        self.gravity = st.gravity
        self.position = np.array([st.screen_size[0] / 2,
                                  st.screen_size[1] / 2, 0], dtype=float)  # where launcher is located.
        self.nozzle_dir = np.array([1, 0])  # Where launcher is looking on xy plane.
        self.flight_time = 10  # Tomatoes can fly for this many frames.
        self.targets = []
        self.read_dataset()

        # feel free to change these numbers.
        self.damping = 0.5
        self.mass = 1
        self.gravity = 40

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
    def rotate_vector(vector, angle):
        """Rotates XY plane by an angle.""" 
        rotation_matrix = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
        rotated_vector = np.dot(rotation_matrix, vector)
        return rotated_vector

    @staticmethod
    def get_direction(vector):
        vector = vector[0:2]
        vector_abs = np.abs(vector)
        vector_mag = np.sum(vector_abs)
        return vector / vector_mag

    def search(self): 
        """Turns the system slowly and searches for targets"""
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

    def destroy(self, hit):
        """Shoots at the target"""
        # this part requires a few assumptions.
        # Assumption: Tomato Launcher is set in a way such that it always hits target within 10 frames.
        # Assumption: Tomato Launcher has to be reloaded for 10 frames once it has shot.
        # last assumption assures that within the 10 frames of flight time, it doesn't move.
        desired_target_pos = self.targets[hit].pos + self.targets[hit].vel * self.flight_time
        tomato_velocity = np.array([calc_x_y_initial_vel(desired_target_pos[0],
                                                         self.position[0],
                                                         self.flight_time,
                                                         self.damping,
                                                         self.mass),
                                    calc_x_y_initial_vel(desired_target_pos[1],
                                                         self.position[1],
                                                         self.flight_time,
                                                         self.damping,
                                                         self.mass),
                                    calc_z_initial_vel(desired_target_pos[2],
                                                       self.position[2],
                                                       self.flight_time,
                                                       self.damping,
                                                       self.mass,
                                                       self.gravity)])

        tomato_position = np.array([1, 1, 1], dtype=float)
        print(Fore.LIGHTRED_EX + f'Taking shot. Tomato velocity is '
              + Fore.LIGHTWHITE_EX + f'{tomato_velocity}' + Style.RESET_ALL)
        tomato_position = self.position.copy()
        frame_counter = 0
        while True:
            frame_counter += 1
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
            self.draw(tomato_velocity[0:2], tomato_velocity[0:2])
            sleep(0.05)
            for t in self.targets:
                t.move()
            tomato_position[0] = calc_x_y_pos(self.position[0], tomato_velocity[0],
                                              frame_counter, self.damping, self.mass)
            tomato_position[1] = calc_x_y_pos(self.position[1], tomato_velocity[1],
                                              frame_counter, self.damping, self.mass)
            tomato_position[2] = calc_z_pos(self.position[2], tomato_velocity[2],
                                            frame_counter, self.damping, self.mass, self.gravity)

            print(Fore.RED + f'Tomato at {tomato_position}' + Style.RESET_ALL)
            print(Fore.CYAN + f'Target at {self.targets[hit].pos}')
            # if distance is smaller than 2, assume that target was hit.
            curr_distance = np.linalg.norm(tomato_position - self.targets[hit].pos)
            if curr_distance < 2:
                print(f'Tomato hit target with positional difference of {curr_distance}')
                break

        return self.get_direction(tomato_position - self.position)

    def draw(self, old_dir, new_dir):
        """Draw the visualization. It is top view."""
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


# these are pure math. Basically solutions of differential equation of motion when linear drag and gravity are present.
def calc_x_y_pos(x_0, v_0, t, b, m):
    return x_0 + (m * v_0 / b) - (m * v_0 / b) * (np.e ** (-b * t / m))


def calc_x_y_initial_vel(x_f, x_0, t, b, m):
    coefficient_1 = (x_f - x_0) * b
    coefficient_2 = m * (1 - (np.e ** (-b * t / m)))
    return coefficient_1 / coefficient_2


def calc_z_pos(z_0, v_0, t, b, m, g):
    answer = z_0 - m * g * t / b
    coefficient1 = 1 - np.e ** (-b * t * m)
    coefficient2 = (v_0 + m * g / b) * (m / b)
    answer += coefficient2 * coefficient1
    return answer


def calc_z_initial_vel(z_f, z_0, t, b, m, g):
    coefficient1 = z_f - z_0 + m * g * t / b
    coefficient2 = (1 / (1 - np.e ** (-b * t / m))) * b / m
    return coefficient1 * coefficient2 - m * g / b


if __name__ == '__main__':
    simulation = Simulation()
    simulation.update()

