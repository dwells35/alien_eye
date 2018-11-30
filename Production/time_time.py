import time

list = []
for x in range(1000):
    start = time.time()
    temp = time.time()
    end = time.time()
    list.append(start - end)

average = sum(list)/len(list)
print('Average: ' + str(average))