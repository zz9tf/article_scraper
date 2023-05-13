def view_dict(dictionary: dict):
    """ View dictionary in formated form """
    for key, value in dictionary.items():
        if len(key) + len(value) < 100:
            print("{}={}".format(key, value))
        else:
            print("key: ", key)
            print("value: ", value)


def view_proxys(proxys: list):
    """ View a list of proxyin formated form"""
    for element in proxys:
        view_dict(element)
        print()
    
    print('length of proxys:', len(proxys))