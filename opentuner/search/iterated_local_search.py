from opentuner.search import technique
import random
import math

class IteratedLocalSearch(technique.SequentialSearchTechnique):
    def main_generator(self):
        objective   = self.objective
        driver      = self.driver
        manipulator = self.manipulator
        acceptance  = 0.2
        max_step    = 0.01
        iterations  = 250

        # start at a random position
        center = driver.get_configuration(manipulator.random())
        yield center

        while True:
            points = list()
            # Iterations of the subsidiary local search
            # (probabilistic improvement)
            for i in range(iterations):
                old_center = center
                # Perturb starting point,
                # generating candidates
                for param in self.manipulator.parameters(center.data):
                    if param.is_primitive():
                        unit_value = param.get_unit_value(center.data)
                        if unit_value > 0.0:
                            # produce new config with param set step_size lower
                            down_cfg = manipulator.copy(center.data)
                            param.set_unit_value(down_cfg, max(0.0, unit_value - (random.random() * max_step)))
                            down_cfg = driver.get_configuration(down_cfg)
                            self.yield_nonblocking(down_cfg)
                            points.append(down_cfg)
                        if unit_value < 1.0:
                            # produce new config with param set step_size higher
                            up_cfg = manipulator.copy(center.data)
                            param.set_unit_value(up_cfg, min(1.0, unit_value + (random.random() * max_step)))
                            up_cfg = driver.get_configuration(up_cfg)
                            self.yield_nonblocking(up_cfg)
                            points.append(up_cfg)
                        else: # ComplexParameter
                            for mutate_function in param.manipulators(center.data):
                                cfg = manipulator.copy(center.data)
                                mutate_function(cfg)
                                cfg = driver.get_configuration(cfg)
                                self.yield_nonblocking(cfg)
                                points.append(cfg)
                yield None
                points.sort(cmp=objective.compare)
                # For this iteration, move if the new point is best
                # than the starting point.
                if objective.lt(points[0], center) or random.random() <= acceptance:
                    center = points[0]

            if (objective.lt(driver.best_result.configuration, center)
                and driver.best_result.configuration != points[0]):
                # another technique found a new global best, switch to that
                center = driver.best_result.configuration
            elif objective.lt(old_center, center) or random.random() <= acceptance:
                center = old_center

technique.register(IteratedLocalSearch())
