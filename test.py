import breaker


def bad_func():
    a = {'test': 1}
    b = a['test2']  # Woops
    print a
    print b


if __name__ == '__main__':
    bad_func()
