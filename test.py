import numpy as np

ones = np.ones((5,5))

print(ones[0:3, 0:3])

# one = np.ones((3,3,3))
# one[2,2,:] = 0
# one = np.pad(one, ((2,2), (2,2), (0,0)), mode='wrap')
# for i in range(0, 7):
#     print(one[0,i,:], one[1,i,:], one[2,i,:], one[3,i,:], one[4,i,:], one[5,i,:], one[6,i,:])


'''

full_map = np.zeros((20,20,6))

full_map[0, 0][0:3] = 1
full_map[0, 1][2:5] = 1
full_map[0, 2][2:5] = 1

print(full_map[20,20])

# print(full_map)


the_map = np.zeros((20,20))
the_map[:, 0:3] = 15

coord = (10,4)

the_map[coord] = 1

row_idxs = [(coord[0] + r) % the_map.shape[0] for r in range(-6, 7)]
column_idxs = [(coord[1] + c) % the_map.shape[1] for c in range(-6, 7)]

ant_sight = the_map[np.ix_(row_idxs, column_idxs)]

print(ant_sight)'''

