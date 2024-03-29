from brach_ode import BrachODE
import dymos as dm
import openmdao.api as om
import pickle
from autoscaling.api import autoscale, PJRNScaler, IsoScaler


def main():
    prob = om.Problem()
    model = prob.model

    traj = model.add_subsystem('traj', dm.Trajectory())
    phase = dm.Phase(ode_class=BrachODE, transcription=dm.GaussLobatto(num_segments=10))
    traj.add_phase('phase0', phase)

    prob.driver = om.pyOptSparseDriver()
    prob.driver.options['optimizer'] = 'SNOPT'

    phase.set_time_options(fix_initial=True)
    phase.set_state_options('x', fix_initial=True, fix_final=True)
    phase.set_state_options('y', fix_initial=True, fix_final=True)
    phase.set_state_options('v', fix_initial=True)
    phase.add_control('th', lower=0.01, upper=179.9, units='deg')
    phase.add_design_parameter('g', opt=False, val=9.80665, units='m/s**2')

    phase.add_objective('time', loc='final')

    prob.setup()

    prob['traj.phase0.t_initial'] = 0.0
    prob['traj.phase0.t_duration'] = 1.0
    prob['traj.phase0.states:x'] = phase.interpolate(ys=[0, 100], nodes='state_input')
    prob['traj.phase0.states:y'] = phase.interpolate(ys=[0, 1], nodes='state_input')
    prob['traj.phase0.states:v'] = phase.interpolate(ys=[0, 10], nodes='state_input')
    prob['traj.phase0.controls:th'] = phase.interpolate(ys=[5, 100.5], nodes='control_input')

    with open('total_jac_info.pickle', 'rb') as file:
        jac = pickle.load(file)
    with open('lower_bounds_info.pickle', 'rb') as file:
        lbs = pickle.load(file)
    with open('upper_bounds_info.pickle', 'rb') as file:
        ubs = pickle.load(file)

    # sc = None
    # sc = IsoScaler(jac, lbs, ubs)
    sc = PJRNScaler(jac, lbs, ubs)

    autoscale(prob, autoscaler=sc)

    prob.run_driver()

    return prob, sc


if __name__ == '__main__':
    main()
