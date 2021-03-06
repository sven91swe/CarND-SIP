#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

# created class to cleanly pass vehicle parameters
class VehicleParams(object):
    def __init__(self):
        self.vehicle_mass = None
        self.fuel_capacity = None
        self.brake_deadband = None
        self.decel_limit = None
        self.accel_limit = None
        self.wheel_radius = None
        self.wheel_base = None
        self.steer_ratio = None
        self.max_lat_accel = None 
        self.minspeed = None
        self.max_steer_angle = None
      
class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        vehParams = VehicleParams()

        vehParams.vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        vehParams.fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        vehParams.brake_deadband = rospy.get_param('~brake_deadband', .1)
        vehParams.decel_limit = rospy.get_param('~decel_limit', -5)
        vehParams.accel_limit = rospy.get_param('~accel_limit', 1.)
        vehParams.wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        vehParams.wheel_base = rospy.get_param('~wheel_base', 2.8498)
        vehParams.steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        vehParams.max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        vehParams.max_steer_angle = rospy.get_param('~max_steer_angle', 8.)
        vehParams.min_speed = 0.01

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)
        self.dbw_enabled = False
        self.twist_cmd = None
        self.current_velocity = None

        # Create `TwistController` object
        self.controller = Controller(vehParams)

        # DONE: Subscribe to all the topics you need to
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cmd_cb)
        rospy.Subscriber('/current_velocity', TwistStamped, self.current_velocity_cb)
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)

        # set previous time for sample_time delta
        self.prev_time = rospy.get_time()

        self.loop()

    # the callback (_cb) functions for the Subscribed topics
    def twist_cmd_cb(self, msg):
        self.twist_cmd = msg 

    def current_velocity_cb(self, msg):
        self.current_velocity = msg 

    def dbw_enabled_cb(self, msg):
        rospy.loginfo("dbw enabled: %s", msg)
        self.dbw_enabled = bool(msg.data)

    def loop(self):
        rate = rospy.Rate(50) # 50Hz
        while not rospy.is_shutdown():
            time_now = rospy.get_time()
            sample_time = time_now - self.prev_time
            self.prev_time = time_now

            # DONE: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            if self.dbw_enabled and self.twist_cmd is not None:
                throttle, brake, steering = self.controller.control(
                    self.twist_cmd,
                    self.current_velocity,
                    sample_time)

                self.publish(throttle, brake, steering)

            # In case of manual steering, reset pid controller
            elif not self.dbw_enabled:
                self.controller.pid.reset()


            rate.sleep()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
