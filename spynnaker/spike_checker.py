import numpy


def synfire_spike_checker(spikes, nNeurons):
    if isinstance(spikes, numpy.ndarray):
        sorted = spikes[spikes[:, 1].argsort()]
        print len(sorted)
        num = 0
        for row in sorted:
            if num != round(row[0]):
                numpy.savetxt("spikes.csv", sorted, fmt=['%d', '%d'],
                              delimiter=',')
                raise Exception("Unexpected spike at time " + str(row[1]))
            num += 1
            if num >= nNeurons:
                num = 0
    else:
        for single in spikes:
            synfire_spike_checker(single, nNeurons)

def synfire_multiple_lines_spike_checker(spikes, nNeurons, lines):
    sorted = spikes[spikes[:, 1].argsort()]
    nums = [0] * lines
    used = [False] * lines
    for row in sorted:
        node = round(row[0])
        found = False
        for i in range(lines):
            if nums[i] == node:
                found = True
                nums[i] += 1
                if nums[i] >= nNeurons:
                    nums[i] = 0
                used[i] = True
                break
        if not found:
            numpy.savetxt("sorted_spikes.csv", sorted, fmt=['%d', '%d'],
                          delimiter=',')
            raise Exception("Unexpected spike at time " + str(row[1]))
    if False in used:
        numpy.savetxt("sorted_spikes.csv", sorted, fmt=['%d', '%d'],
                      delimiter=',')
        print used
        raise Exception("Expected " + str(lines) + " spike lines")


if __name__ == '__main__':
    spikes = numpy.loadtxt("spikes.csv", delimiter=',')
    synfire_spike_checker(spikes, 20)
