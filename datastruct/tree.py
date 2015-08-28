def quick_sort(array, p, r):
    if p < r:
        q = partition(array, p, r)
        quick_sort(array, p, q - 1)
        quick_sort(array, q + 1, r)


def partition(be_sorted, pivot, last_element):
    x = be_sorted[last_element]
    i = pivot - 1   # what's the i doing?
    for j in range(pivot, last_element):
        print(be_sorted)
        if be_sorted[j] < x:
            i += 1
            be_sorted[j], be_sorted[i] = be_sorted[i], be_sorted[j]
    i += 1
    be_sorted[i], be_sorted[last_element] = be_sorted[last_element], be_sorted[i]
    return i

if __name__ == "__main__":
    sorted = [1, 99, 5, 23, 64, 7, 23, 6, 34, 98, 100, 9]
    quick_sort(sorted, 0, len(sorted) - 1)



