#!/usr/bin/env python

# TODO is it necessary here?
import roslib; roslib.load_manifest('lab1_turtlebot')
import rospy

from driver import driver

if __name__ == '__main__':
    try:
        rospy.init_node('driver')

        # Get the distance from the parameter server.  Default is 0.5
        distance = rospy.get_param('distance', 0.5)

        # Set up the controller
        stopper = driver(distance)

        # Hand control over to ROS
        rospy.spin() 

            
    except rospy.ROSInterruptException:
        pass