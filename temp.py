def calculate_final_vel(curVel, newVel, axis):
    # cek apa mereka selaras
    curVel_isPositive = curVel > 0.0
    newVel_isPositive = newVel > 0.0
    if(curVel_isPositive == newVel_isPositive):
        print('ues')
    else:
        print('no')


calculate_final_vel(1.0, 2.0, 0) # should yes
calculate_final_vel(2.0, -3.0, 1) # shuold no
calculate_final_vel(-5.0, 4.0, 0) # should no
calculate_final_vel(-6.0, -7.0, 1) # should yes